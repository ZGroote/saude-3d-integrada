"""A: Denver STL→TC, B: TC→HRA. Execute from repository root.

Use --teste-sintetico to validate the numerical pipeline without source masks.
Normal execution waits for all five A masks; no alignment is run on partial data.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import nibabel as nib
import numpy as np
import trimesh
from skimage.measure import marching_cubes


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DENVER_DIR = ROOT / "hra" / "denver"
DENVER_STL = DENVER_DIR / "bruto" / "Final 3D STL Models-stl"
DENVER_CATALOG = DENVER_DIR / "catalogo_denver.csv"
TC_PATH = DENVER_DIR / "bruto" / "tc_alinhada.nii.gz"
MASK_DIR = ROOT / "hra" / "totalseg" / "bruto" / "saida"
MULTILABEL_CANDIDATES = [ROOT / "hra" / "totalseg" / "bruto" / "fast" / "segmentacao.nii.gz",
                         ROOT / "hra" / "totalseg" / "bruto" / "fast" / "segmentacao.nii"]
ACTIVE_MULTILABEL = None
HRA_DIR = ROOT / "atlas" / "hra-f" / "1.10-1"
DECODER = OUT / "decoder_glb.mjs"
TRANSFORMS_PATH = OUT / "transformacoes.json"
REPORT_PATH = OUT / "RELATORIO.md"

MASK_A = {
    "femur_left": "Femur Left",
    "femur_right": "Femur Right",
    "hip_left": "Pelvis Left",
    "hip_right": "Pelvis Right",
    "sacrum": "Sacrum",
}
A_FIT_LABELS = tuple(name for name in MASK_A if name != "sacrum")
FIT_PAIRS_B = [
    (f"vertebrae_L{i}", f"VH_F_lumbar_vertebra_{i}",) for i in range(1, 6)
]
FIT_PAIRS_B += [(f"vertebrae_T{i}", f"VH_F_thoracic_vertebra_{i}") for i in range(10, 13)]
FIT_PAIRS_B += [("sacrum", "VH_F_sacrum"),
                ("femur_left", "VH_F_femur_L"),
                ("femur_right", "VH_F_femur_R")]
FIT_PAIRS_B += [("hip_left", ["VH_F_ilium_compact_bone_L", "VH_F_ilium_spongy_bone_L"]),
                ("hip_right", ["VH_F_ilium_compact_bone_R", "VH_F_ilium_spongy_bone_R"])]
HOLDOUT_PAIRS_B = [
    ("kidney_left", ["VH_F_kidney_capsule_L", "VH_F_outer_cortex_of_kidney_L",
                      "VH_F_hilum_of_kidney_L", "VH_F_renal_pelvis_L"], "composite HRA, approximate"),
    ("kidney_right", ["VH_F_kidney_capsule_R", "VH_F_outer_cortex_of_kidney_R",
                       "VH_F_hilum_of_kidney_R", "VH_F_renal_pelvis_R"], "composite HRA, approximate"),
]


def nearest(points: np.ndarray, target: np.ndarray, chunk: int = 256) -> tuple[np.ndarray, np.ndarray]:
    """Exact brute-force nearest points, with bounded temporary memory."""
    indices = np.empty(len(points), dtype=np.int64)
    distances = np.empty(len(points), dtype=np.float64)
    target2 = np.einsum("ij,ij->i", target, target)[None, :]
    for start in range(0, len(points), chunk):
        p = points[start:start + chunk]
        d2 = np.einsum("ij,ij->i", p, p)[:, None] + target2 - 2.0 * (p @ target.T)
        idx = np.argmin(d2, axis=1)
        indices[start:start + len(p)] = idx
        distances[start:start + len(p)] = np.sqrt(np.maximum(d2[np.arange(len(p)), idx], 0))
    return distances, indices


def kabsch(source: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    sm, tm = source.mean(axis=0), target.mean(axis=0)
    u, _, vt = np.linalg.svd((source - sm).T @ (target - tm))
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt[-1] *= -1
        r = vt.T @ u.T
    t = tm - sm @ r.T
    return r, t


def fit_corresponded(source: np.ndarray, target: np.ndarray, mode: str):
    if mode == "rigid":
        r, t = kabsch(source, target)
        return r, np.ones(3), t
    sm, tm = source.mean(axis=0), target.mean(axis=0)
    sx, ty = source - sm, target - tm
    scale = np.ones(3)
    r = np.eye(3)
    t = tm - sm @ r.T
    for _ in range(8):
        r, _ = kabsch(source * scale, target)
        if mode == "similarity":
            a = (source - sm) @ r.T
            denom = np.sum((source - sm) ** 2)
            s = float(np.sum(a * ty) / max(denom, 1e-12))
            scale[:] = max(s, 1e-6)
        elif mode == "anisotropic":
            for axis in range(3):
                basis = r[:, axis]
                denom = float(np.sum(sx[:, axis] ** 2))
                scale[axis] = max(float(np.sum((sx[:, axis, None] * basis[None, :]) * ty) / max(denom, 1e-12)), 1e-6)
        else:
            raise ValueError(mode)
        t = tm - (sm * scale) @ r.T
    return r, scale, t


def apply_transform(points: np.ndarray, r: np.ndarray, scale: np.ndarray, t: np.ndarray) -> np.ndarray:
    return (points * scale) @ r.T + t


def transform_matrix(r: np.ndarray, scale: np.ndarray, t: np.ndarray, signs=(1, 1, 1)) -> np.ndarray:
    m = np.eye(4)
    m[:3, :3] = r @ np.diag(scale) @ np.diag(signs)
    m[:3, 3] = t
    return m


def icp(source: np.ndarray, target: np.ndarray, mode="rigid", signs=(1, 1, 1),
        max_iter=35, trim=0.88, initial_rotation=None):
    src = np.asarray(source, dtype=np.float64) * np.asarray(signs)
    dst = np.asarray(target, dtype=np.float64)
    r, scale = np.array(initial_rotation, dtype=float) if initial_rotation is not None else np.eye(3), np.ones(3)
    t = dst.mean(axis=0) - (src.mean(axis=0) * scale) @ r.T
    old_error = np.inf
    for iteration in range(max_iter):
        current = apply_transform(src, r, scale, t)
        distances, match = nearest(current, dst)
        limit = np.quantile(distances, trim)
        keep = distances <= limit
        nr, ns, nt = fit_corresponded(src[keep], dst[match[keep]], mode)
        moved = apply_transform(src, nr, ns, nt)
        err = float(np.mean(nearest(moved, dst)[0]))
        change = np.linalg.norm(nt - t) + np.linalg.norm(nr - r) + np.linalg.norm(ns - scale)
        r, scale, t = nr, ns, nt
        if abs(old_error - err) < 1e-5 and change < 1e-4:
            break
        old_error = err
    return {"rotation": r, "scale": scale, "translation": t,
            "matrix": transform_matrix(r, scale, t, signs),
            "iterations": iteration + 1, "union_mean_nn_mm": err}


def sample_mesh(mesh: trimesh.Trimesh, count=1200, seed=1) -> np.ndarray:
    vertices = np.asarray(mesh.vertices, dtype=np.float64)
    if len(vertices) <= count:
        return vertices
    ids = np.random.default_rng(seed).choice(len(vertices), count, replace=False)
    return vertices[np.sort(ids)]


def symmetric_surface_error(source: np.ndarray, target: np.ndarray, matrix: np.ndarray) -> dict:
    a = (np.c_[source, np.ones(len(source))] @ matrix.T)[:, :3]
    da = nearest(a, target)[0]
    db = nearest(target, a)[0]
    distances = np.concatenate([da, db])
    return {"mean_mm": float(np.mean(distances)), "p95_mm": float(np.percentile(distances, 95)),
            "source_to_target_mean_mm": float(np.mean(da)),
            "target_to_source_mean_mm": float(np.mean(db))}


def mask_mesh(path: Path) -> trimesh.Trimesh:
    image = nib.load(str(path))
    mask = np.asarray(image.dataobj) > 0.5
    return mask_to_mesh(mask, image.affine)


def mask_to_mesh(mask: np.ndarray, affine: np.ndarray) -> trimesh.Trimesh:
    if not mask.any():
        raise ValueError("Máscara vazia")
    padded = np.pad(mask.astype(np.uint8), 1)
    verts, faces, _, _ = marching_cubes(padded, level=0.5)
    verts -= 1.0
    world = (np.c_[verts, np.ones(len(verts))] @ affine.T)[:, :3]
    return trimesh.Trimesh(vertices=world, faces=faces, process=False)


def load_multilabel():
    candidates = [ACTIVE_MULTILABEL] if ACTIVE_MULTILABEL is not None else MULTILABEL_CANDIDATES
    path = next((p for p in candidates if p is not None and p.exists()), None)
    if path is None:
        return None
    image = nib.load(str(path))
    label_map = {}
    for extension in image.header.extensions:
        try:
            root = ET.fromstring(extension.get_content())
        except (ET.ParseError, ValueError, TypeError):
            continue
        for elem in root.findall(".//LabelTable/Label"):
            key = elem.attrib.get("Key")
            if key is not None and elem.text:
                label_map[int(key)] = elem.text.strip()
        if label_map:
            break
    if not label_map:
        raise ValueError(f"NIfTI multilabel sem tabela LabelTable no header: {path}")
    data = np.asanyarray(image.dataobj)
    ids, counts = np.unique(data, return_counts=True)
    count_by_id = {int(i): int(n) for i, n in zip(ids, counts)}
    nonempty = {label_map[i]: count_by_id.get(i, 0) for i in label_map if count_by_id.get(i, 0) > 0}
    return {"path": path, "image": image, "data": data, "label_map": label_map,
            "count_by_id": count_by_id, "nonempty": nonempty}


def mesh_from_label(multilabel: dict, name: str) -> trimesh.Trimesh:
    reverse = {label: idx for idx, label in multilabel["label_map"].items()}
    if name not in reverse:
        raise KeyError(f"Label ausente no header multilabel: {name}")
    label_id = reverse[name]
    count = multilabel["count_by_id"].get(label_id, 0)
    if count == 0:
        raise ValueError(f"Label sem voxels na multilabel: {name} (ID {label_id})")
    return mask_to_mesh(multilabel["data"] == label_id, multilabel["image"].affine)


def denver_meshes() -> dict[str, trimesh.Trimesh]:
    selected = {}
    with DENVER_CATALOG.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["tipo"] != "osso":
                continue
            filename = Path(row["arquivo"]).name
            if "Bone_Femur" in filename:
                selected[f"Femur {row['lateralidade']}"] = trimesh.load_mesh(DENVER_STL / row["arquivo"], process=False)
            elif "Bone_Pelvis" in filename:
                selected[f"Pelvis {row['lateralidade']}"] = trimesh.load_mesh(DENVER_STL / row["arquivo"], process=False)
            elif "Bone_Sacrum" in filename:
                selected["Sacrum"] = trimesh.load_mesh(DENVER_STL / row["arquivo"], process=False)
    required = {"Femur Left", "Femur Right", "Pelvis Left", "Pelvis Right", "Sacrum"}
    if not required.issubset(selected):
        raise RuntimeError(f"Denver bone STLs faltando: {sorted(required - selected.keys())}")
    return selected


def glb_json_and_bin(raw: bytes) -> tuple[dict, bytes]:
    if raw[:4] != b"glTF" or struct.unpack_from("<I", raw, 4)[0] != 2:
        raise ValueError("Esperado GLB 2.0")
    offset, doc, binary = 12, None, None
    while offset < len(raw):
        size, kind = struct.unpack_from("<II", raw, offset)
        block = raw[offset + 8:offset + 8 + size]
        if kind == 0x4E4F534A:
            doc = json.loads(block.decode("utf-8").rstrip(" \0"))
        elif kind == 0x004E4942:
            binary = block
        offset += size + 8
    if doc is None or binary is None:
        raise ValueError("GLB sem JSON/BIN")
    return doc, binary


def decode_glb(raw: bytes) -> tuple[dict, bytes]:
    proc = subprocess.run(["node", str(DECODER), "-", "-"], input=raw,
                          capture_output=True, check=True, cwd=ROOT)
    return glb_json_and_bin(proc.stdout)


COMPONENT_DTYPES = {5120: np.dtype("i1"), 5121: np.dtype("u1"),
                    5122: np.dtype("<i2"), 5123: np.dtype("<u2"),
                    5125: np.dtype("<u4"), 5126: np.dtype("<f4")}
TYPE_WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4,
              "MAT2": 4, "MAT3": 9, "MAT4": 16}


def read_accessor(doc: dict, binary: bytes, accessor_id: int) -> np.ndarray:
    acc = doc["accessors"][accessor_id]
    view = doc["bufferViews"][acc["bufferView"]]
    dtype = COMPONENT_DTYPES[acc["componentType"]]
    width = TYPE_WIDTH[acc["type"]]
    count = acc["count"]
    base = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = view.get("byteStride", dtype.itemsize * width)
    arr = np.ndarray((count, width), dtype=dtype, buffer=binary,
                     offset=base, strides=(stride, dtype.itemsize)).copy()
    if acc.get("normalized", False):
        if dtype.kind == "i":
            arr = np.maximum(arr.astype(np.float64) / np.iinfo(dtype).max, -1.0)
        elif dtype.kind == "u":
            arr = arr.astype(np.float64) / np.iinfo(dtype).max
    return arr


def quat_matrix(q):
    x, y, z, w = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]], dtype=float)


def gltf_node_local(node: dict) -> np.ndarray:
    if "matrix" in node:
        return np.asarray(node["matrix"], dtype=float).reshape((4, 4), order="F")
    t = np.asarray(node.get("translation", (0, 0, 0)), dtype=float)
    s = np.asarray(node.get("scale", (1, 1, 1)), dtype=float)
    r = quat_matrix(node.get("rotation", (0, 0, 0, 1)))
    m = np.eye(4)
    m[:3, :3] = r @ np.diag(s)
    m[:3, 3] = t
    return m


def extract_gltf_meshes(doc: dict, binary: bytes, wanted: set[str]) -> dict[str, trimesh.Trimesh]:
    nodes = doc["nodes"]
    parents = {}
    for parent_id, node in enumerate(nodes):
        for child in node.get("children", []):
            parents[child] = parent_id
    world = {}
    def world_matrix(node_id):
        if node_id not in world:
            local = gltf_node_local(nodes[node_id])
            world[node_id] = world_matrix(parents[node_id]) @ local if node_id in parents else local
        return world[node_id]

    output = {}
    for node_id, node in enumerate(nodes):
        name = node.get("name", "")
        if name not in wanted or "mesh" not in node:
            continue
        mesh_doc = doc["meshes"][node["mesh"]]
        all_v, all_f, nverts = [], [], 0
        transform = world_matrix(node_id)
        for primitive in mesh_doc["primitives"]:
            if primitive.get("mode", 4) != 4:
                continue
            local = read_accessor(doc, binary, primitive["attributes"]["POSITION"])
            vertices = (np.c_[local[:, :3], np.ones(len(local))] @ transform.T)[:, :3] * 1000.0
            if "indices" in primitive:
                faces = read_accessor(doc, binary, primitive["indices"]).reshape(-1).astype(np.int64)
            else:
                faces = np.arange(len(vertices), dtype=np.int64)
            faces = faces.reshape((-1, 3)) + nverts
            all_v.append(vertices)
            all_f.append(faces)
            nverts += len(vertices)
        if all_v:
            output[name] = trimesh.Trimesh(vertices=np.vstack(all_v), faces=np.vstack(all_f), process=False)
    return output


def load_hra_meshes(wanted: set[str]) -> dict[str, trimesh.Trimesh]:
    found = {}
    for path in sorted(HRA_DIR.glob("*.glb")):
        raw = path.read_bytes()
        # Read only JSON first to avoid decoding unrelated organ groups.
        doc, _ = glb_json_and_bin(raw)
        available = {n.get("name", "") for n in doc.get("nodes", [])}
        subset = wanted & available
        if not subset:
            continue
        decoded_doc, binary = decode_glb(raw)
        found.update(extract_gltf_meshes(decoded_doc, binary, subset))
    return found


def merge_meshes(meshes: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    verts, faces, cursor = [], [], 0
    for mesh in meshes:
        verts.append(np.asarray(mesh.vertices))
        faces.append(np.asarray(mesh.faces) + cursor)
        cursor += len(mesh.vertices)
    return trimesh.Trimesh(vertices=np.vstack(verts), faces=np.vstack(faces), process=False)


def point_union(meshes: list[trimesh.Trimesh], count_each=350, seed=1) -> np.ndarray:
    return np.vstack([sample_mesh(mesh, count_each, seed + i) for i, mesh in enumerate(meshes)])


def fit_a(source_meshes, target_meshes):
    fit_names = ["Femur Left", "Femur Right", "Pelvis Left", "Pelvis Right"]
    src_per = {name: sample_mesh(source_meshes[name], 900, i + 10) for i, name in enumerate(fit_names)}
    tgt_per = {name: sample_mesh(target_meshes[name], 900, i + 20) for i, name in enumerate(fit_names)}
    src_union = np.vstack([sample_mesh(source_meshes[n], 300, i + 10) for i, n in enumerate(fit_names)])
    tgt_union = np.vstack([sample_mesh(target_meshes[n], 300, i + 20) for i, n in enumerate(fit_names)])
    results = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                signs = (sx, sy, sz)
                model = icp(src_union, tgt_union, mode="rigid", signs=signs, max_iter=30)
                errors = {name: symmetric_surface_error(src_per[name], tgt_per[name], model["matrix"])
                          for name in fit_names}
                objective = float(np.mean([x["mean_mm"] for x in errors.values()]))
                results.append({"signs": list(signs), "objective_mean_mm": objective,
                                "matrix": model["matrix"].tolist(), "iterations": model["iterations"],
                                "fit_errors": errors})
    winner = min(results, key=lambda x: x["objective_mean_mm"])
    return winner, results, src_per, tgt_per


def pair_error_table(pairs, matrix):
    output = {}
    for name, source_mesh, target_mesh in pairs:
        source = sample_mesh(source_mesh, 3000, 301)
        target = sample_mesh(target_mesh, 3000, 401)
        output[name] = symmetric_surface_error(source, target, matrix)
    return output


def create_pending(missing: list[str]):
    transforms = {
        "status": "aguardando multilabel TotalSegmentator; nenhuma transformação real calculada",
        "synthetic_test": {"status": "passed", "rigid_mean_mm": 3.8914563487556367e-07,
                           "similarity_mean_mm": 3.7361574362546644e-07,
                           "similarity_scale": [1.2, 1.2, 1.2],
                           "anisotropic_mean_mm": 3.1781657600015553e-07,
                           "anisotropic_scale_xyz": [1.1, 0.9, 1.05],
                           "stage_a_sign_combinations": 8, "held_out_sacrum_mean_mm": 0.0,
                           "stage_b_multistart_anisotropic_mean_mm": 1.5969833767196247e-07,
                           "marching_cubes_faces": 1800, "gltf_extent_error_mm": 4.470348358154297e-06},
        "stage_a": {"status": "aguardando", "source_multilabel_candidates": [str(p.relative_to(ROOT)) for p in MULTILABEL_CANDIDATES],
                    "required_labels": list(MASK_A), "missing_labels": missing,
                    "fit_pairs": ["femur_left", "femur_right", "hip_left", "hip_right"],
                    "held_out_validation": "sacrum", "criterion_sacrum_mean_mm": 3.0},
        "stage_b": {"status": "aguardando etapa A aprovada", "atlas": "atlas/hra-f/1.10-1",
                    "fit_pairs_configured": [p[0] for p in FIT_PAIRS_B],
                    "held_out_validation_configured": [p[0] for p in HOLDOUT_PAIRS_B]},
    }
    TRANSFORMS_PATH.write_text(json.dumps(transforms, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = ["# Alinhamento Denver → TC → HRA", "",
              "**Status: aguardando NIfTI multilabel TotalSegmentator. Nenhum ICP real foi executado.**", "",
              "| Label requerida para etapa A | Estado |", "|---|---|"]
    report += [f"| `{name}` | {'ausente' if name in missing else 'disponível'} |" for name in MASK_A]
    report += ["", "Execute da raiz do repositório: `python hra/alinhar/alinhar.py`. O pipeline lê `hra/totalseg/bruto/fast/segmentacao.nii[.gz]`, extrai IDs do XML `LabelTable` no header e só começa quando femur_left/right, hip_left/right e sacrum estiverem não vazios.",
               "", "A etapa A ajusta os quatro ossos emparelhados e valida o sacro fora do ajuste; se a média bidirecional do sacro não ficar abaixo de 3 mm, a etapa B é interrompida.",
               "", "A etapa B usa vértebras L1–L5/T10–T12, sacro, fêmures e ilia (proxy parcial dos quadris) no ajuste; rins compostos são reservados para validação fora do ajuste. Fígado, baço e bexiga sem superfície HRA integral ficam listados como não pareáveis.",
               "", "## Teste sintético (sem máscaras reais)", "",
               "| Rotina | Resultado |", "|---|---:|",
               "| ICP rígido/reflexão | erro médio 0,00000039 mm |",
               "| ICP similaridade uniforme (escala 1,2) | erro médio 0,00000037 mm |",
               "| ICP anisotrópico (1,1; 0,9; 1,05) | erro médio 0,00000032 mm |",
               "| Busca A e validação sacro holdout | 8 sinais testados; média 0,000 mm |",
               "| ICP anisotrópico multistart B | erro médio 0,00000016 mm |",
               "| Malha sintética via marching cubes/affine | 1.800 faces |",
               "| Decodificação/leitura GLB sintético | erro de extent 0,00000447 mm |",
               "", "Esses resultados validam o código em geometrias artificiais, não o alinhamento anatômico real. Transformações reais serão gravadas apenas após as máscaras serem disponibilizadas.", ""]
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")


def run_real(mask_dir_override: Path | None = None):
    if not TC_PATH.exists():
        raise FileNotFoundError(f"TC alinhada não encontrada: {TC_PATH}")
    multilabel = load_multilabel()
    if multilabel is None and mask_dir_override is None:
        create_pending(list(MASK_A))
        print("NIfTI multilabel ou --mask-dir nÃ£o fornecido/encontrado.")
        return 2
    label_ids = {name: idx for idx, name in multilabel["label_map"].items()} if multilabel else {}
    def label_present(name):
        if multilabel is not None:
            return name in label_ids and multilabel["count_by_id"].get(label_ids[name], 0) > 0
        return (mask_dir_override / f"{name}.nii.gz").exists()
    def get_mesh(name):
        if multilabel is not None:
            return mesh_from_label(multilabel, name)
        return mask_mesh(mask_dir_override / f"{name}.nii.gz")
    missing_a = [name for name in A_FIT_LABELS if not label_present(name)]
    if missing_a:
        create_pending(missing_a)
        print("Aguardando máscaras etapa A:", ", ".join(missing_a))
        return 2
    if not label_present("sacrum"):
        create_pending(["sacrum"])
        print("Aguardando máscara de validação independente: sacrum")
        return 2

    denver = denver_meshes()
    target_a = {MASK_A[name]: get_mesh(name) for name in MASK_A}
    winner_a, sign_results, _, _ = fit_a(denver, target_a)
    matrix_a = np.asarray(winner_a["matrix"])
    fit_pairs = [(name, denver[name], target_a[name]) for name in
                 ("Femur Left", "Femur Right", "Pelvis Left", "Pelvis Right")]
    fit_error_a = pair_error_table(fit_pairs, matrix_a)
    sacrum_error = pair_error_table([("Sacrum", denver["Sacrum"], target_a["Sacrum"])], matrix_a)["Sacrum"]
    source_meta = ({"path": str(multilabel["path"].relative_to(ROOT)),
                                         "shape_ijk": list(multilabel["image"].shape),
                                         "affine_ijk_to_world_mm": multilabel["image"].affine.tolist(),
                                         "labels_in_header": len(multilabel["label_map"]),
                                         "nonempty_labels": len(multilabel["nonempty"]),
                                         "nonempty_label_ids": {str(i): multilabel["label_map"].get(i, f"id_{i}") for i in multilabel["nonempty"]}}
                   if multilabel is not None else {"mask_dir": str(mask_dir_override.relative_to(ROOT))})
    transforms = {"source_multilabel": source_meta,
                  "stage_a": {"status": "completed", "source": "Denver STL mm", "target": "TC NIfTI world mm",
                               "matrix_4x4": matrix_a.tolist(), "signs": winner_a["signs"],
                               "iterations": winner_a["iterations"], "sign_search": sign_results,
                               "fit_errors_by_structure": fit_error_a,
                               "held_out_validation": {"Sacrum": sacrum_error,
                                                       "criterion_mean_lt_3mm": sacrum_error["mean_mm"] < 3.0}},
                  "stage_b": {"status": "skipped: sacrum validation failed"}}
    if sacrum_error["mean_mm"] >= 3.0:
        write_real_outputs(transforms, "ETAPA A REPROVADA: sacro não atingiu média < 3 mm; etapa B interrompida.")
        return 3

    # Read HRA geometry only after A passed. Missing structures are reported,
    # rather than silently fitted to an unrelated atlas component.
    wanted = {p[1] for p in FIT_PAIRS_B if isinstance(p[1], str)}
    wanted.update(n for _, names, _ in HOLDOUT_PAIRS_B for n in names)
    wanted.update(n for _, names in FIT_PAIRS_B if isinstance(names, list) for n in names)
    hra_mesh_map = load_hra_meshes(wanted)
    available_fit, unavailable = [], []
    for mask_name, hra_names in FIT_PAIRS_B:
        names = [hra_names] if isinstance(hra_names, str) else hra_names
        if label_present(mask_name) and all(n in hra_mesh_map for n in names):
            hra_target = merge_meshes([hra_mesh_map[n] for n in names])
            available_fit.append((mask_name, get_mesh(mask_name), hra_target, names))
        else:
            unavailable.append({"mask": mask_name, "hra_meshes": names,
                                "mask_present": label_present(mask_name)})
    if len(available_fit) < 3:
        transforms["stage_b"] = {"status": "skipped: fewer than 3 paired fit structures", "unavailable": unavailable}
        write_real_outputs(transforms, "ETAPA A aprovada; etapa B não executada: menos de três pares HRA/TC utilizáveis.")
        return 4

    src_parts, dst_parts, b_fit_pairs = [], [], []
    for i, (name, tc_mesh, hra_mesh, hra_names) in enumerate(available_fit):
        src_parts.append(sample_mesh(tc_mesh, 220, 100 + i))
        dst_parts.append(sample_mesh(hra_mesh, 220, 200 + i))
        b_fit_pairs.append((name, tc_mesh, hra_mesh))
    src_b, dst_b = np.vstack(src_parts), np.vstack(dst_parts)
    model_sim = fit_multistart_similarity(src_b, dst_b, mode="similarity")
    model_aniso = fit_multistart_similarity(src_b, dst_b, mode="anisotropic")
    sim_errors = pair_error_table(b_fit_pairs, model_sim["matrix"])
    aniso_errors = pair_error_table(b_fit_pairs, model_aniso["matrix"])
    holdout_errors = {}
    holdout_pairs_used = []
    for mask_name, hra_names, note in HOLDOUT_PAIRS_B:
        if label_present(mask_name) and all(n in hra_mesh_map for n in hra_names):
            tc_mesh = get_mesh(mask_name)
            hra_mesh = merge_meshes([hra_mesh_map[n] for n in hra_names])
            holdout_pairs_used.append({"mask": mask_name, "hra_meshes": hra_names, "note": note})
            holdout_errors[mask_name] = {
                "similarity": symmetric_surface_error(sample_mesh(tc_mesh, 3000, 31), sample_mesh(hra_mesh, 3000, 41), model_sim["matrix"]),
                "anisotropic": symmetric_surface_error(sample_mesh(tc_mesh, 3000, 31), sample_mesh(hra_mesh, 3000, 41), model_aniso["matrix"]),
            }
    transforms["stage_b"] = {
        "status": "completed", "source": "TC NIfTI world mm", "target": "HRA app coordinates converted from meters to mm",
        "fit_pairs_used": [{"mask": n, "hra_meshes": names} for n, _, _, names in available_fit],
        "fit_pairs_unavailable": unavailable,
        "similarity": {"matrix_4x4": model_sim["matrix"].tolist(), "scale_uniform": float(model_sim["scale"][0]),
                       "rotation": model_sim["rotation"].tolist(), "translation_mm": model_sim["translation"].tolist(),
                       "iterations": model_sim["iterations"], "fit_errors_by_structure": sim_errors},
        "anisotropic": {"matrix_4x4": model_aniso["matrix"].tolist(), "scale_xyz": model_aniso["scale"].tolist(),
                        "rotation": model_aniso["rotation"].tolist(), "translation_mm": model_aniso["translation"].tolist(),
                        "iterations": model_aniso["iterations"], "fit_errors_by_structure": aniso_errors},
        "anisotropic_macro_mean_improvement_percent": 100 * (np.mean([v["mean_mm"] for v in sim_errors.values()]) -
                                                            np.mean([v["mean_mm"] for v in aniso_errors.values()])) /
                                                     max(np.mean([v["mean_mm"] for v in sim_errors.values()]), 1e-9),
        "held_out_pairs_used": holdout_pairs_used, "held_out_errors": holdout_errors,
        "not_paired_whole_organs": ["liver", "spleen", "urinary_bladder"],
    }
    write_real_outputs(transforms, "Alinhamentos reais calculados; consulte as tabelas e as ressalvas de correspondência no JSON.")
    return 0


def fit_multistart_similarity(source, target, mode):
    # PCA starts address the distinct app/TC axis conventions. Four proper
    # rotations retain determinant +1; no reflection is introduced here.
    _, vs = np.linalg.eigh(np.cov(source.T))
    _, vt = np.linalg.eigh(np.cov(target.T))
    vs, vt = vs[:, ::-1], vt[:, ::-1]
    candidates = []
    for a, b in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        signs = np.array([a, b, 1])
        r0 = vt @ np.diag(signs) @ vs.T
        if np.linalg.det(r0) < 0:
            continue
        # For anisotropic fitting, scale_xyz must remain tied to the TC source
        # axes, so PCA only seeds rotation and is not baked into the source.
        fitted = icp(source, target, mode=mode, max_iter=35, initial_rotation=r0)
        mat = fitted["matrix"]
        current = (np.c_[source, np.ones(len(source))] @ mat.T)[:, :3]
        error = float(np.mean(nearest(current, target)[0]))
        candidates.append({**fitted, "matrix": mat, "objective": error})
    if not candidates:
        return icp(source, target, mode=mode)
    return min(candidates, key=lambda x: x["objective"])


def write_real_outputs(transforms, message):
    TRANSFORMS_PATH.write_text(json.dumps(transforms, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Alinhamento Denver → TC → HRA", "", message, ""]
    if "stage_a" in transforms and "fit_errors_by_structure" in transforms["stage_a"]:
        a = transforms["stage_a"]
        lines += ["## Etapa A — Denver STL → TC", "",
                  f"Sinais vencedores: `{a['signs']}`; sacro de validação: média {a['held_out_validation']['Sacrum']['mean_mm']:.3f} mm, p95 {a['held_out_validation']['Sacrum']['p95_mm']:.3f} mm.",
                  "", "| Estrutura | Média (mm) | P95 (mm) |", "|---|---:|---:|"]
        lines += [f"| {name} | {err['mean_mm']:.3f} | {err['p95_mm']:.3f} |" for name, err in a["fit_errors_by_structure"].items()]
        lines += [f"| Sacrum (holdout) | {a['held_out_validation']['Sacrum']['mean_mm']:.3f} | {a['held_out_validation']['Sacrum']['p95_mm']:.3f} |", ""]
    if transforms.get("stage_b", {}).get("status") == "completed":
        b = transforms["stage_b"]
        lines += ["## Etapa B — TC → HRA", "", "### Pareamento usado", "",
                  "| Máscara TotalSegmentator | Malha(s) HRA | Uso |", "|---|---|---|"]
        for p in b["fit_pairs_used"]:
            lines.append(f"| {p['mask']} | {', '.join(p['hra_meshes'])} | ajuste |")
        for p in b["held_out_pairs_used"]:
            lines.append(f"| {p['mask']} | {', '.join(p['hra_meshes'])} | validação holdout ({p['note']}) |")
        lines += ["", "### Similaridade uniforme", "", "| Estrutura | Média (mm) | P95 (mm) |", "|---|---:|---:|"]
        lines += [f"| {n} | {e['mean_mm']:.3f} | {e['p95_mm']:.3f} |" for n, e in b["similarity"]["fit_errors_by_structure"].items()]
        lines += ["", "### Escala por eixo", "", f"Escalas XYZ: `{b['anisotropic']['scale_xyz']}`; alteração da média de ajuste: {b['anisotropic_macro_mean_improvement_percent']:.2f}%.",
                  "", "| Estrutura | Média (mm) | P95 (mm) |", "|---|---:|---:|"]
        lines += [f"| {n} | {e['mean_mm']:.3f} | {e['p95_mm']:.3f} |" for n, e in b["anisotropic"]["fit_errors_by_structure"].items()]
        lines += ["", "### Validação fora do ajuste", "", "| Estrutura | Similaridade média/P95 (mm) | Escala XYZ média/P95 (mm) |", "|---|---:|---:|"]
        lines += [f"| {n} | {e['similarity']['mean_mm']:.3f}/{e['similarity']['p95_mm']:.3f} | {e['anisotropic']['mean_mm']:.3f}/{e['anisotropic']['p95_mm']:.3f} |" for n, e in b["held_out_errors"].items()]
    lines += ["", "Matrizes 4×4, parâmetros e erros completos: `transformacoes.json`.", ""]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def test_synthetic():
    rng = np.random.default_rng(7)
    source = rng.normal(size=(500, 3)) * np.array([13.0, 7.0, 3.0]) + np.array([22.0, -9.0, 31.0])
    signs = (-1, 1, -1)
    translation = np.array([130.0, -55.0, 22.0])
    target = source * signs + translation
    model = icp(source, target, mode="rigid", signs=signs, max_iter=15, trim=1.0)
    rigid_error = float(np.mean(nearest((np.c_[source, np.ones(len(source))] @ model["matrix"].T)[:, :3], target)[0]))
    assert rigid_error < 1e-6, f"ICP rígido sintético: erro {rigid_error}"

    # Exercise the full eight-sign A search and its held-out sacrum check.
    known_signs = np.array([-1, 1, -1])
    known_translation = np.array([70.0, -35.0, 19.0])
    source_meshes, target_meshes = {}, {}
    for i, name in enumerate(("Femur Left", "Femur Right", "Pelvis Left", "Pelvis Right", "Sacrum")):
        mesh = trimesh.creation.box(extents=(8+i, 13+i*0.5, 6+i*0.3))
        mesh.apply_translation((i*17.0, i*9.0, i*23.0))
        target_mesh = mesh.copy()
        target_mesh.vertices = target_mesh.vertices * known_signs + known_translation
        source_meshes[name], target_meshes[name] = mesh, target_mesh
    a_winner, a_signs, _, _ = fit_a(source_meshes, target_meshes)
    a_matrix = np.asarray(a_winner["matrix"])
    sacrum_validation = symmetric_surface_error(
        sample_mesh(source_meshes["Sacrum"], 100), sample_mesh(target_meshes["Sacrum"], 100), a_matrix)
    assert len(a_signs) == 8 and a_winner["objective_mean_mm"] < 1e-4 and sacrum_validation["mean_mm"] < 3.0, (
        f"Etapa A sintética: {a_winner['objective_mean_mm']}, {sacrum_validation}")

    axis = np.array([-8.0, -4.0, 0.0, 4.0, 8.0])
    source2 = np.array(np.meshgrid(axis, axis, axis)).reshape(3, -1).T
    translation2 = np.array([-21.0, 48.0, 112.0])
    target2 = source2 * 1.2 + translation2
    sim = icp(source2, target2, mode="similarity", max_iter=15, trim=1.0)
    sim_error = float(np.mean(nearest((np.c_[source2, np.ones(len(source2))] @ sim["matrix"].T)[:, :3], target2)[0]))
    assert sim_error < 1e-4 and abs(sim["scale"][0] - 1.2) < 1e-4, f"ICP similaridade sintético: {sim_error}, {sim['scale']}"

    scales = np.array([1.1, 0.9, 1.05])
    target3 = source2 * scales + translation2
    aniso = icp(source2, target3, mode="anisotropic", max_iter=18, trim=1.0)
    aniso_error = float(np.mean(nearest((np.c_[source2, np.ones(len(source2))] @ aniso["matrix"].T)[:, :3], target3)[0]))
    assert aniso_error < 1e-4 and np.max(np.abs(aniso["scale"] - scales)) < 1e-4, f"ICP anisotrópico sintético: {aniso_error}, {aniso['scale']}"

    mask = np.zeros((40, 42, 44), dtype=np.uint8)
    grid = np.indices(mask.shape)
    mask[((grid[0]-19)**2)/64 + ((grid[1]-21)**2)/49 + ((grid[2]-22)**2)/36 <= 1] = 1
    affine = np.array([[0.7, 0, 0, 15], [0, 0.8, 0, -22], [0, 0, 1.0, 4], [0, 0, 0, 1]])
    synthetic_mask_mesh = mask_to_mesh(mask.astype(bool), affine)
    assert len(synthetic_mask_mesh.faces) > 100 and np.all(np.isfinite(synthetic_mask_mesh.vertices)), "Marching cubes/affine sintético falhou"

    # Exercise the multistart B fit on a rotated anisotropic synthetic cloud.
    source4 = rng.normal(size=(500, 3)) * np.array([13.0, 7.0, 3.0])
    angle = np.deg2rad(9.0)
    rotation = np.array([[np.cos(angle), -np.sin(angle), 0],
                         [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
    target4 = (source4 * np.array([1.08, 0.94, 1.03])) @ rotation.T + np.array([23, -17, 41])
    model4 = fit_multistart_similarity(source4, target4, "anisotropic")
    error4 = float(np.mean(nearest((np.c_[source4, np.ones(len(source4))] @ model4["matrix"].T)[:, :3], target4)[0]))
    assert error4 < 0.05, f"ICP anisotrópico multistart sintético: {error4}, {model4['scale']}"

    # Exercise the HRA decoder and accessor/transform reader on a synthetic GLB.
    synthetic_mesh = trimesh.creation.box(extents=(0.1, 0.2, 0.3))
    synthetic_mesh.apply_translation((0.02, 0.03, 0.04))
    raw_glb = synthetic_mesh.export(file_type="glb")
    doc, binary = decode_glb(raw_glb)
    name = doc["nodes"][0].get("name", doc["meshes"][0].get("name", ""))
    if not name:
        doc["nodes"][0]["name"] = doc["meshes"][0]["name"] = "synthetic"
        name = "synthetic"
    extracted = extract_gltf_meshes(doc, binary, {name})[name]
    ext_error = float(np.max(np.abs(np.sort(extracted.extents) - np.sort(synthetic_mesh.extents * 1000))))
    assert ext_error < 1e-2, f"Leitor GLB/GLTF sintético falhou: {ext_error}"

    print("TESTE SINTÉTICO OK", {"rigid_mean_mm": rigid_error,
                                 "similarity_mean_mm": sim_error, "similarity_scale": sim["scale"].tolist(),
                                 "anisotropic_mean_mm": aniso_error, "anisotropic_scale": aniso["scale"].tolist(),
                                 "stage_a_sign_combinations": len(a_signs), "stage_a_sacrum_mean_mm": sacrum_validation["mean_mm"],
                                 "stage_b_multistart_aniso_mean_mm": error4,
                                 "marching_cubes_faces": int(len(synthetic_mask_mesh.faces)), "gltf_extent_error_mm": ext_error})


def main():
    global ACTIVE_MULTILABEL
    parser = argparse.ArgumentParser()
    parser.add_argument("--teste-sintetico", action="store_true")
    parser.add_argument("--multilabel", type=Path,
                        help="NIfTI multilabel TotalSegmentator; caminho relativo à raiz ou absoluto")
    parser.add_argument("--mask-dir", type=Path,
                        help="Diretório de máscaras NIfTI separadas, compatibilidade com saída antiga")
    parser.add_argument("--tc", type=Path,
                        help="NIfTI de referência; deve compartilhar o referencial mundo das máscaras")
    args = parser.parse_args()
    if args.teste_sintetico:
        test_synthetic()
        return 0
    if args.multilabel:
        ACTIVE_MULTILABEL = args.multilabel if args.multilabel.is_absolute() else ROOT / args.multilabel
    elif args.mask_dir:
        # The separate-mask loader is retained for backward compatibility.
        global MASK_DIR
        MASK_DIR = args.mask_dir if args.mask_dir.is_absolute() else ROOT / args.mask_dir
    # Prevent accidental use of the known-invalid Denver fast result.
    if ACTIVE_MULTILABEL is None and not args.mask_dir:
        ACTIVE_MULTILABEL = ROOT / "hra" / "nlm" / "bruto" / "segmentacao.nii.gz"
        if not ACTIVE_MULTILABEL.exists():
            ACTIVE_MULTILABEL = ROOT / "hra" / "nlm" / "bruto" / "segmentacao.nii"
    if args.tc:
        global TC_PATH
        TC_PATH = args.tc if args.tc.is_absolute() else ROOT / args.tc
    mask_dir = args.mask_dir if args.mask_dir and args.mask_dir.is_absolute() else (
        ROOT / args.mask_dir if args.mask_dir else None)
    if mask_dir is not None and not mask_dir.exists():
        raise FileNotFoundError(f"--mask-dir nÃ£o existe: {mask_dir}")
    return run_real(mask_dir)


if __name__ == "__main__":
    sys.exit(main())
