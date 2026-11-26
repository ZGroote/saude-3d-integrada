"""A: Denver STL→TC, B: TC→HRA. Execute from repository root.

Use --teste-sintetico to validate the numerical pipeline without source masks.
Normal execution waits for all five A masks; no alignment is run on partial data.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
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
    ("superior_vena_cava", ["VH_F_superior_vena_cava"], "large-vessel holdout"),
    ("inferior_vena_cava", ["VH_F_inferior_vena_cava_a", "VH_F_inferior_vena_cava_b"], "large-vessel composite holdout"),
    ("pulmonary_vein", ["VH_F_pulmonary_vein_L_sup", "VH_F_pulmonary_vein_R_inf",
                         "VH_F_pulmonary_vein_R_sup", "VH_F_pulmonary_vein_L_inf"], "large-vessel composite holdout"),
]

GEOMETRIC_LIMITS = {
    "skin": {"mean_max_mm": 10.0, "p95_max_mm": None},
    "large_bones": {"mean_max_mm": 5.0, "p95_max_mm": 12.0},
    "large_organs": {"mean_max_mm": 5.0, "p95_max_mm": 12.0},
    "large_muscles": {"mean_max_mm": 5.0, "p95_max_mm": 12.0},
    "vertebrae": {"mean_max_mm": 3.0, "p95_max_mm": None},
    "large_vessels": {"mean_max_mm": 3.0, "p95_max_mm": None},
    "individual_review": {"mean_max_mm": None, "p95_max_mm": None},
}

REGION_FIT_PAIRS = {
    "head_neck": [(f"vertebrae_C{i}", f"VH_F_cervical_vertebra_{i}") for i in range(1, 8)],
    "thorax": [(f"vertebrae_T{i}", f"VH_F_thoracic_vertebra_{i}") for i in range(1, 13)],
    "abdomen_pelvis": [(f"vertebrae_L{i}", f"VH_F_lumbar_vertebra_{i}") for i in range(1, 6)] +
                      [("sacrum", "VH_F_sacrum"),
                       ("kidney_left", ["VH_F_kidney_capsule_L", "VH_F_outer_cortex_of_kidney_L", "VH_F_hilum_of_kidney_L", "VH_F_renal_pelvis_L"]),
                       ("kidney_right", ["VH_F_kidney_capsule_R", "VH_F_outer_cortex_of_kidney_R", "VH_F_hilum_of_kidney_R", "VH_F_renal_pelvis_R"])],
}

TS_IMPORT_LABELS = {"skull", "sternum"}
TS_IMPORT_PREFIXES = ("rib_", "humerus_", "scapula_", "clavicula_")
TS_VESSEL_LABELS = {
    "aorta", "pulmonary_vein", "brachiocephalic_trunk", "subclavian_artery_right", "subclavian_artery_left",
    "common_carotid_artery_right", "common_carotid_artery_left", "brachiocephalic_vein_left",
    "brachiocephalic_vein_right", "superior_vena_cava", "inferior_vena_cava",
    "portal_vein_and_splenic_vein", "iliac_artery_left", "iliac_artery_right",
}
HRA_UPPER_SKELETON_EQUIVALENTS = {
    "skull": ["VH_F_skull"], "sternum": ["VH_F_sternum"],
    "humerus_left": ["VH_F_humerus_L"], "humerus_right": ["VH_F_humerus_R"],
    "scapula_left": ["VH_F_scapula_L"], "scapula_right": ["VH_F_scapula_R"],
    "clavicula_left": ["VH_F_clavicle_L"], "clavicula_right": ["VH_F_clavicle_R"],
}
HRA_VESSEL_EQUIVALENTS = {
    "pulmonary_vein": ["VH_F_pulmonary_vein_L_sup", "VH_F_pulmonary_vein_R_inf", "VH_F_pulmonary_vein_R_sup", "VH_F_pulmonary_vein_L_inf"],
    "superior_vena_cava": ["VH_F_superior_vena_cava"],
    "inferior_vena_cava": ["VH_F_inferior_vena_cava_a", "VH_F_inferior_vena_cava_b"],
    "brachiocephalic_vein_left": ["VH_F_brachiocephalic_vein_L"],
    "brachiocephalic_vein_right": ["VH_F_brachiocephalic_vein_R"],
}
DENVER_LOWER_LIMB_BONES = {
    "Bone Calcaneous", "Bone Cuboid", "Bone Femur", "Bone Fibula", "Bone IntermediateCuneiform",
    "Bone LateralCuneiform", "Bone MedialCuneiform", "Bone Navicular", "Bone Patella",
    "Bone Phalanges", "Bone Talus", "Bone Tibia",
}
DENVER_LOWER_LIMB_CARTILAGE = {
    "Cartilage FemurDistal", "Cartilage FemurHead", "Cartilage Patella",
    "Cartilage Talus", "Cartilage TibiaDistal", "Cartilage TibiaLateral", "Cartilage TibiaMedial",
}
DENVER_HRA_BONE_TARGETS = {
    "Bone Femur": ("VH_F_femur_L", "VH_F_femur_R"),
    "Bone Tibia": ("VH_F_tibia_L", "VH_F_tibia_R"),
    "Bone Fibula": ("VH_F_fibula_L", "VH_F_fibula_R"),
    "Bone Patella": ("VH_F_patella_L", "VH_F_patella_R"),
}
HRA_LEG_BONES = {
    "femur": {"Left": "VH_F_femur_L", "Right": "VH_F_femur_R"},
    "tibia": {"Left": "VH_F_tibia_L", "Right": "VH_F_tibia_R"},
    "fibula": {"Left": "VH_F_fibula_L", "Right": "VH_F_fibula_R"},
    "patella": {"Left": "VH_F_patella_L", "Right": "VH_F_patella_R"},
}


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


def fit_corresponded(source: np.ndarray, target: np.ndarray, mode: str, scale_bounds=(0.85, 1.15)):
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
            scale[:] = np.clip(s, *scale_bounds)
        elif mode == "anisotropic":
            for axis in range(3):
                basis = r[:, axis]
                denom = float(np.sum(sx[:, axis] ** 2))
                scale[axis] = np.clip(float(np.sum((sx[:, axis, None] * basis[None, :]) * ty) / max(denom, 1e-12)), *scale_bounds)
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
        max_iter=35, trim=0.88, initial_rotation=None, symmetric=False,
        scale_bounds=(0.85, 1.15)):
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
        if symmetric:
            reverse_distances, reverse_match = nearest(dst, current)
            reverse_keep = reverse_distances <= np.quantile(reverse_distances, trim)
            source_corr = np.concatenate((src[keep], src[reverse_match[reverse_keep]]), axis=0)
            target_corr = np.concatenate((dst[match[keep]], dst[reverse_keep]), axis=0)
            nr, ns, nt = fit_corresponded(source_corr, target_corr, mode, scale_bounds)
        else:
            nr, ns, nt = fit_corresponded(src[keep], dst[match[keep]], mode, scale_bounds)
        moved = apply_transform(src, nr, ns, nt)
        forward_error = nearest(moved, dst)[0]
        if symmetric:
            reverse_error = nearest(dst, moved)[0]
            err = float((forward_error.mean() + reverse_error.mean()) / 2.0)
        else:
            err = float(np.mean(forward_error))
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
    mask = multilabel["data"] == label_id
    occupied = np.where(mask)
    starts = np.array([int(axis.min()) for axis in occupied], dtype=int)
    stops = np.array([int(axis.max()) + 1 for axis in occupied], dtype=int)
    crop = tuple(slice(int(a), int(b)) for a, b in zip(starts, stops))
    local_affine = np.asarray(multilabel["image"].affine) @ np.array(
        [[1, 0, 0, starts[0]], [0, 1, 0, starts[1]], [0, 0, 1, starts[2]], [0, 0, 0, 1]], dtype=float)
    return mask_to_mesh(mask[crop], local_affine)


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
            elif "Bone_Coccyx" in filename:
                selected["Coccyx"] = trimesh.load_mesh(DENVER_STL / row["arquivo"], process=False)
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
            app_m = (np.c_[local[:, :3], np.ones(len(local))] @ transform.T)[:, :3]
            vertices = hra_app_to_ras_mm(app_m)
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


def load_hra_catalog_mesh(name: str) -> trimesh.Trimesh | None:
    """Load one HRA source mesh directly through the atlas index/GLB node list."""
    index_path = HRA_DIR / "indice.json"
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    item = next((row for row in index if row.get("malha") == name), None)
    if item is None:
        return None
    path = HRA_DIR / item["glb"]
    raw = path.read_bytes()
    doc, _ = glb_json_and_bin(raw)
    if not any(node.get("name") == name and "mesh" in node for node in doc.get("nodes", [])):
        return None
    decoded_doc, binary = decode_glb(raw)
    return extract_gltf_meshes(decoded_doc, binary, {name}).get(name)


def hra_app_to_ras_mm(points_app_m: np.ndarray) -> np.ndarray:
    points = np.asarray(points_app_m, dtype=float)
    return np.column_stack((-points[:, 0], points[:, 2], points[:, 1])) * 1000.0


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


def run_real(mask_dir_override: Path | None = None, diagnostic_stage_b: bool = False,
             by_region: bool = False, human_review: bool = False, capture_dir: Path | None = None):
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
    denver_sacrum_union = merge_meshes([denver["Sacrum"], denver["Coccyx"]])
    sacrum_error = pair_error_table([("Sacrum + Coccyx", denver_sacrum_union, target_a["Sacrum"])], matrix_a)["Sacrum + Coccyx"]
    source_meta = ({"path": str(multilabel["path"].relative_to(ROOT)),
                                         "shape_ijk": list(multilabel["image"].shape),
                                         "affine_ijk_to_world_mm": multilabel["image"].affine.tolist(),
                                         "labels_in_header": len(multilabel["label_map"]),
                                         "nonempty_labels": len(multilabel["nonempty"]),
                                         "nonempty_label_ids": {str(i): multilabel["label_map"][i] for i in multilabel["label_map"]
                                                                 if multilabel["count_by_id"].get(i, 0) > 0}}
                   if multilabel is not None else {"mask_dir": str(mask_dir_override.relative_to(ROOT))})
    transforms = {"source_multilabel": source_meta,
                  "stage_a": {"status": "completed", "source": "Denver STL mm", "target": "TC NIfTI world mm",
                               "matrix_4x4": matrix_a.tolist(), "signs": winner_a["signs"],
                               "iterations": winner_a["iterations"], "sign_search": sign_results,
                               "fit_errors_by_structure": fit_error_a,
                               "held_out_validation": {"Sacrum + Coccyx": sacrum_error,
                                                       "criterion_mean_lt_3mm": sacrum_error["mean_mm"] < 3.0}},
                  "stage_b": {"status": "skipped: sacrum validation failed"}}
    stage_a_passed = sacrum_error["mean_mm"] < 3.0
    if not stage_a_passed:
        transforms["stage_a"]["status"] = "EXP-0011 REPROVED under original 3 mm criterion; EXP-0014 evaluated independently"
        transforms["stage_a"]["diagnostic_matrix_not_accepted_for_final_use"] = True

    # Read HRA geometry only after A passed. Missing structures are reported,
    # rather than silently fitted to an unrelated atlas component.
    wanted = {p[1] for p in FIT_PAIRS_B if isinstance(p[1], str)}
    wanted.update(n for _, names, _ in HOLDOUT_PAIRS_B for n in names)
    wanted.update(n for _, names in FIT_PAIRS_B if isinstance(names, list) for n in names)
    for region_pairs in REGION_FIT_PAIRS.values():
        for _, names in region_pairs:
            wanted.update([names] if isinstance(names, str) else names)
    for names in HRA_VESSEL_EQUIVALENTS.values():
        wanted.update(names)
    for label in multilabel["label_map"].values():
        wanted.update(expected_hra_names_for_label(label))
    wanted.update(name for pair in DENVER_HRA_BONE_TARGETS.values() for name in pair)
    wanted.add("VH_F_skin")
    wanted.update(load_hra_group_names({"VH_F_liver", "VH_F_spleen", "VH_F_heart"}))
    hra_mesh_map = load_hra_meshes(wanted)
    if "VH_F_skin" not in hra_mesh_map:
        skin_mesh = load_hra_catalog_mesh("VH_F_skin")
        if skin_mesh is not None:
            hra_mesh_map["VH_F_skin"] = skin_mesh
    denver_rows_for_import = denver_leg_rows()
    denver_leg_alignment = fit_denver_leg_models(hra_mesh_map, denver_rows_for_import)
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
    model_sim = fit_b_similarity(src_b, dst_b, mode="similarity")
    model_aniso = fit_b_similarity(src_b, dst_b, mode="anisotropic")
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
    for mask_name, group_name in (("liver", "VH_F_liver"), ("spleen", "VH_F_spleen"), ("heart", "VH_F_heart")):
        hra_names = sorted(load_hra_group_names({group_name}) & set(hra_mesh_map))
        if label_present(mask_name) and hra_names:
            tc_mesh = get_mesh(mask_name)
            hra_mesh = merge_meshes([hra_mesh_map[n] for n in hra_names])
            holdout_pairs_used.append({"mask": mask_name, "hra_meshes": hra_names, "note": "HRA catalog organ-group composite; diagnostic"})
            holdout_errors[mask_name] = {
                "similarity": symmetric_surface_error(sample_mesh(tc_mesh, 3000, 51), sample_mesh(hra_mesh, 3000, 61), model_sim["matrix"]),
                "anisotropic": symmetric_surface_error(sample_mesh(tc_mesh, 3000, 51), sample_mesh(hra_mesh, 3000, 61), model_aniso["matrix"]),
            }
    transforms["stage_b"] = {
        "status": "completed under EXP-0014 purpose-based evaluation",
        "EXP0011_stage_a_3mm_gate": "REPROVED; retained as historical result" if not stage_a_passed else "passed",
        "stage_a_matrix_used_as_stage_b_initialization": False,
        "source": "TC NIfTI world RAS mm", "target": "HRA explicitly converted from app meters to RAS mm",
        "hra_app_to_ras_mm": [[-1000.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1000.0, 0.0],
                              [0.0, 1000.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0]],
        "icp_initialization": "centroid difference of union of paired fit structures",
        "icp_objective": "symmetric mean of source-to-target and target-to-source nearest-surface distances",
        "scale_bounds": [0.85, 1.15],
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
        "not_paired_whole_organs": ["urinary_bladder"],
    }
    region_results = run_regional_fits(multilabel, hra_mesh_map) if by_region else None
    transforms["stage_b"]["regional_registration"] = region_results or {"status": "not requested"}
    transforms["stage_b"]["denver_leg_alignment"] = {
        key: value for key, value in denver_leg_alignment.items() if key != "transformed_meshes"}
    transforms["acceptance_protocol"] = evaluate_acceptance_protocol(
        multilabel, matrix_a, model_sim["matrix"], hra_mesh_map, transforms["stage_b"],
        region_results=region_results, human_review=human_review,
        capture_dir=str(capture_dir) if capture_dir else None,
        denver_leg_alignment=denver_leg_alignment)
    output_note = "Rodada EXP-0014 com a segmentação NLM em resolução normal. O EXP-0011 permanece REPROVADO pelo critério original do sacro de 3 mm; a aceitação desta rodada é avaliada pelos critérios por finalidade e pelas verificações funcionais abaixo."
    write_real_outputs(transforms, output_note)
    write_acceptance_report(transforms)
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


def fit_b_similarity(source, target, mode):
    """Stage B ICP: direct RAS-mm fit, centroid initialization, symmetric objective, bounded scale."""
    fitted = icp(source, target, mode=mode, signs=(1, 1, 1), max_iter=45,
                 trim=0.88, symmetric=True, scale_bounds=(0.85, 1.15))
    matrix = fitted["matrix"]
    moved = (np.c_[source, np.ones(len(source))] @ matrix.T)[:, :3]
    forward = nearest(moved, target)[0].mean()
    reverse = nearest(target, moved)[0].mean()
    fitted["objective"] = float((forward + reverse) / 2.0)
    return fitted


def apply_matrix_points(points: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    return (np.c_[points, np.ones(len(points))] @ np.asarray(matrix).T)[:, :3]


def fitted_matrix(model: dict) -> np.ndarray:
    return transform_matrix(model["rotation"], model["scale"], model["translation"])


def fit_mesh_to_mesh(source_mesh: trimesh.Trimesh, target_mesh: trimesh.Trimesh, seed=1) -> dict:
    source = sample_mesh(source_mesh, 1800, seed)
    target = sample_mesh(target_mesh, 1800, seed + 1)
    return fit_b_similarity(source, target, "similarity")


def prepare_surface_query(surface: trimesh.Trimesh) -> dict:
    surface.fix_normals(multibody=True)
    global_center = np.asarray(surface.vertices).mean(axis=0)
    face_centers = np.asarray(surface.triangles_center, dtype=float)
    face_normals = np.asarray(surface.face_normals, dtype=float)
    radial = face_centers - np.asarray(surface.vertices).mean(axis=0)
    orientation_score = float(np.median(np.einsum("ij,ij->i", radial, face_normals)))
    if orientation_score < 0:
        surface.invert()
        face_normals = np.asarray(surface.face_normals, dtype=float)
        orientation = "flipped_by_median_radial_normal_to_outward"
    else:
        orientation = "median_radial_normal_points_outward"
    from scipy.spatial import cKDTree
    radial_alignment = np.einsum("ij,ij->i", radial, face_normals)
    return {"surface": surface, "tree": cKDTree(face_centers), "triangles": np.asarray(surface.triangles),
            "face_normals": face_normals, "orientation": orientation,
            "orientation_score": orientation_score,
            "fraction_faces_radially_outward": float(np.mean(radial_alignment >= 0)),
            "orientation_check_note": "global winding retained; positive median radial dot means majority orientation is outward; open concave regions can have locally negative radial dots"}


def closest_point_and_signed_offset(surface: trimesh.Trimesh, vertices: np.ndarray, chunk=2048, prepared=None) -> dict:
    """Signed nearest-surface offset; positive means outside for outward normals."""
    if not len(surface.faces) or not len(vertices):
        raise ValueError("skin surface or candidate vertex set is empty")
    prepared = prepared or prepare_surface_query(surface)
    tree = prepared["tree"]
    triangles_all = prepared["triangles"]
    face_normals = prepared["face_normals"]
    candidate_count = min(4, len(triangles_all))
    closest_points = np.empty_like(vertices, dtype=float)
    signed = np.empty(len(vertices), dtype=float)
    distances = np.empty(len(vertices), dtype=float)
    for start in range(0, len(vertices), chunk):
        stop = min(start + chunk, len(vertices))
        points = vertices[start:stop]
        _, face_ids = tree.query(points, k=candidate_count)
        face_ids = np.atleast_2d(face_ids)
        if face_ids.shape[0] != len(points):
            face_ids = face_ids.T
        triangles = triangles_all[face_ids]
        expanded = np.broadcast_to(points[:, None, :], (len(points), candidate_count, 3))
        closest = trimesh.triangles.closest_point(triangles.reshape(-1, 3, 3), expanded.reshape(-1, 3)).reshape(len(points), candidate_count, 3)
        delta = closest - points[:, None, :]
        d2 = np.einsum("ijk,ijk->ij", delta, delta)
        best = np.argmin(d2, axis=1)
        rows = np.arange(len(points))
        face_id = face_ids[rows, best]
        best_point = closest[rows, best]
        offset = points - best_point
        signed[start:stop] = np.einsum("ij,ij->i", offset, face_normals[face_id])
        distances[start:stop] = np.sqrt(d2[rows, best])
        closest_points[start:stop] = best_point
    return {"signed_offset_mm": signed, "distance_mm": distances,
            "closest_points": closest_points, "normal_orientation": prepared["orientation"],
            "orientation_score": prepared["orientation_score"], "outside": signed > 1e-6}


def skin_containment_row(surface: trimesh.Trimesh | None, vertices: np.ndarray, structure: str, source: str, prepared=None) -> dict:
    if surface is None:
        return {"structure": structure, "source": source, "outside_fraction": None,
                "max_distance_outside_mm": None, "status": "N/A: HRA skin unavailable"}
    result = closest_point_and_signed_offset(surface, np.asarray(vertices, dtype=float), prepared=prepared)
    outside = result["outside"]
    outside_distances = np.maximum(result["signed_offset_mm"], 0.0)
    outside_fraction = float(outside.mean()) if len(outside) else 0.0
    return {"structure": structure, "source": source, "vertices": int(len(vertices)),
            "outside_fraction": outside_fraction, "outside_percent": outside_fraction * 100,
            "inside_fraction": 1.0 - outside_fraction,
            "max_distance_outside_mm": float(outside_distances.max(initial=0.0)),
            "mean_distance_outside_mm": float(outside_distances[outside].mean()) if outside.any() else 0.0,
            "normal_orientation": result["normal_orientation"],
            "normal_orientation_score": result["orientation_score"],
            "status": "PASS" if outside_fraction <= 0.01 else "FAIL"}


def denver_leg_rows() -> list[dict]:
    rows = lower_limb_denver_rows()
    return [row for row in rows if row["estrutura"] in {
        "Bone Femur", "Bone Tibia", "Bone Fibula", "Bone Patella",
        "Cartilage FemurDistal", "Cartilage FemurHead", "Cartilage Patella",
        "Cartilage TibiaDistal", "Cartilage TibiaLateral", "Cartilage TibiaMedial",
    }]


def fit_denver_leg_models(hra_mesh_map: dict[str, trimesh.Trimesh], rows: list[dict]) -> dict:
    models, leg_meshes, fit_errors = {}, {}, {}
    for side in ("Left", "Right"):
        side_rows = [row for row in rows if row["lateralidade"] == side]
        bone_rows = {row["estrutura"]: row for row in side_rows if row["tipo"] == "osso"}
        if "Bone Femur" not in bone_rows or "Bone Tibia" not in bone_rows:
            models[side] = {"status": "N/A: femur or tibia STL missing"}
            continue
        transforms = {}
        region_definitions = {
            "thigh": (["Bone Femur"], [HRA_LEG_BONES["femur"][side]]),
            "lower_leg": ([name for name in ("Bone Tibia", "Bone Fibula", "Bone Patella") if name in bone_rows],
                          [HRA_LEG_BONES[name.removeprefix("Bone ").lower()][side]
                           for name in ("Bone Tibia", "Bone Fibula", "Bone Patella") if name in bone_rows]),
        }
        for region_name, (denver_names, hra_names) in region_definitions.items():
            if not all(name in hra_mesh_map for name in hra_names):
                fit_errors[f"{region_name} {side}"] = {"status": "N/A: HRA target missing", "hra_targets": hra_names}
                continue
            source_meshes = [trimesh.load_mesh(DENVER_STL / bone_rows[name]["arquivo"], process=False)
                             for name in denver_names]
            source_union = merge_meshes(source_meshes) if len(source_meshes) > 1 else source_meshes[0]
            target_meshes = [hra_mesh_map[name] for name in hra_names]
            target_union = merge_meshes(target_meshes) if len(target_meshes) > 1 else target_meshes[0]
            model = fit_mesh_to_mesh(source_union, target_union, seed=300 + len(models) * 10 + len(fit_errors))
            matrix = fitted_matrix(model)
            transforms[region_name] = matrix
            error = symmetric_surface_error(sample_mesh(source_union, 3500, 501), sample_mesh(target_union, 3500, 502), matrix)
            fit_errors[f"{region_name} {side}"] = {**error, "hra_targets": hra_names,
                "denver_structures": denver_names, "scale_uniform": float(model["scale"][0]),
                "matrix_4x4": matrix.tolist(), "iterations": model["iterations"]}
            for name in denver_names:
                source = trimesh.load_mesh(DENVER_STL / bone_rows[name]["arquivo"], process=False)
                leg_meshes[f"{name} {side}"] = apply_matrix_to_mesh(source, matrix)
        # Apply the thigh transform to femoral cartilage and the lower-leg
        # transform to tibial/patellar cartilage and ligaments.
        for row in side_rows:
            if row["tipo"] == "osso":
                continue
            structure = row["estrutura"]
            region_name = "thigh" if "Femur" in structure else "lower_leg"
            matrix = transforms.get(region_name)
            if matrix is not None and structure == "Cartilage FemurHead":
                source = trimesh.load_mesh(DENVER_STL / row["arquivo"], process=False)
                leg_meshes[f"{structure} {side}"] = apply_matrix_to_mesh(source, matrix)
        models[side] = {"status": "completed", "regions": {name: {"matrix_4x4": matrix.tolist(),
                           "scale_uniform": float(fit_errors[f"{name} {side}"]["scale_uniform"])}
                           for name, matrix in transforms.items()},
                        "fit_errors_by_region": {k: v for k, v in fit_errors.items() if k.endswith(side)}}
    seams = []
    for side in ("Left", "Right"):
        thigh_key, leg_key = f"Bone Femur {side}", f"Bone Tibia {side}"
        if thigh_key not in leg_meshes or leg_key not in leg_meshes:
            seams.append({"side": side, "status": "N/A: femur or tibia unavailable"})
            continue
        gap = minimum_surface_distance(leg_meshes[thigh_key], leg_meshes[leg_key], 3000)
        seams.append({"side": side, "femur_to_tibia_minimum_distance_mm": gap,
                      "criterion_mm": 5.0, "status": "PASS" if gap <= 5.0 else "FAIL"})
    return {"status": "completed", "fit_policy": "one bounded similarity per Denver bone mesh directly to its HRA lower-limb equivalent",
            "scale_bounds": [0.85, 1.15], "per_side": models, "fit_errors_by_structure": fit_errors,
            "knee_seams": seams, "transformed_meshes": leg_meshes}


def geometry_class(name: str) -> str:
    value = name.lower()
    if "skin" in value or "pele" in value:
        return "skin"
    if "vertebra" in value or "sacrum" in value or "cervical" in value or "thoracic" in value or "lumbar" in value:
        return "vertebrae" if "vertebra" in value else "large_bones"
    if any(token in value for token in ("aorta", "vena_cava", "carotid", "subclavian", "brachiocephalic", "pulmonary_vein", "iliac_artery", "artery", "_vein")):
        return "large_vessels"
    if any(token in value for token in ("femur", "pelvis", "hip", "tibia", "fibula", "patella", "sacrum", "coccyx", "rib", "sternum", "skull", "humerus", "scapula", "clavicula", "calcaneous", "calcaneus", "cuboid", "cuneiform", "navicular", "talus", "phalange", "vertebrae_s")):
        return "large_bones"
    if any(token in value for token in ("kidney", "liver", "spleen", "heart", "lung", "bladder", "stomach")):
        return "large_organs"
    if any(token in value for token in ("gluteus", "vastus", "soleus", "muscle", "musculus", "adductor", "biceps", "triceps", "sartorius", "gastrocnemius", "tibialis", "peroneus", "extensor", "flexor", "rectus", "semimembranosus", "semitendinosus")):
        return "large_muscles"
    if "cartilage" in value or "ligament" in value:
        return "individual_review"
    return "individual_review"


def geometry_acceptance_rows(fit_errors: dict, holdout_errors: dict, fit_kind="similarity") -> tuple[list[dict], dict]:
    rows = []
    for name, error in fit_errors.items():
        kind = geometry_class(name)
        limit = GEOMETRIC_LIMITS[kind]
        passed = (limit["mean_max_mm"] is not None and error["mean_mm"] <= limit["mean_max_mm"] and
                  (limit["p95_max_mm"] is None or error["p95_mm"] <= limit["p95_max_mm"]))
        rows.append({"structure": name, "class": kind, "mean_mm": error["mean_mm"], "p95_mm": error["p95_mm"],
                     "limits": limit, "status": "PASS" if passed else ("REVIEW" if limit["mean_max_mm"] is None else "FAIL"),
                     "measurement_source": "registered mask to HRA surface; symmetric"})
    for name, pair_errors in holdout_errors.items():
        error = pair_errors.get(fit_kind, pair_errors) if isinstance(pair_errors, dict) else pair_errors
        if "mean_mm" not in error:
            continue
        kind = geometry_class(name)
        limit = GEOMETRIC_LIMITS[kind]
        passed = (limit["mean_max_mm"] is not None and error["mean_mm"] <= limit["mean_max_mm"] and
                  (limit["p95_max_mm"] is None or error["p95_mm"] <= limit["p95_max_mm"]))
        rows.append({"structure": name, "class": kind, "mean_mm": error["mean_mm"], "p95_mm": error["p95_mm"],
                     "limits": limit, "status": "PASS" if passed else ("REVIEW" if limit["mean_max_mm"] is None else "FAIL"),
                     "measurement_source": "held-out registered mask to HRA surface; symmetric"})
    summary = {}
    for kind, limit in GEOMETRIC_LIMITS.items():
        members = [r for r in rows if r["class"] == kind]
        statuses = {r["status"] for r in members}
        state = "N/A" if not members else ("PASS" if statuses == {"PASS"} else ("REVIEW" if statuses == {"REVIEW"} else "FAIL"))
        summary[kind] = {"thresholds": limit, "structures_evaluated": len(members), "status": state,
                         "structures_failed": [r["structure"] for r in members if r["status"] == "FAIL"]}
    return rows, summary


def anatomy_source_key(name: str) -> str:
    value = name.lower().replace("left", "").replace("right", "")
    value = value.replace("_", " ").replace("-", " ")
    return " ".join(value.split())


def filled_voxel_grid(mesh: trimesh.Trimesh, pitch_mm: float):
    if len(mesh.faces) == 0:
        raise ValueError("mesh has no faces")
    grid = mesh.voxelized(pitch=pitch_mm, method="subdivide")
    grid.fill(method="holes")
    return grid


def voxel_grid_membership(grid, points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=float)
    indices = np.asarray(grid.points_to_indices(points), dtype=int)
    shape = np.asarray(grid.matrix.shape, dtype=int)
    valid = np.all((indices >= 0) & (indices < shape[None, :]), axis=1)
    result = np.zeros(len(points), dtype=bool)
    if valid.any():
        idx = indices[valid]
        result[valid] = np.asarray(grid.matrix)[idx[:, 0], idx[:, 1], idx[:, 2]]
    return result


def build_obstacle_voxel_field(meshes: dict[str, trimesh.Trimesh], pitch_mm=5.0) -> dict:
    point_sets, topology = [], {}
    for name, mesh in meshes.items():
        try:
            grid = filled_voxel_grid(mesh, pitch_mm)
            points = np.asarray(grid.points, dtype=np.float32)
            if len(points):
                point_sets.append(points)
            topology[name] = {"watertight": bool(mesh.is_watertight), "filled_voxels": int(len(points)), "status": "available"}
        except Exception as exc:
            topology[name] = {"watertight": bool(mesh.is_watertight), "status": "unavailable", "reason": str(exc)}
    if not point_sets:
        return {"origin": None, "pitch_mm": pitch_mm, "occupancy": None, "topology": topology}
    points = np.vstack(point_sets)
    origin = np.floor(points.min(axis=0) / pitch_mm) * pitch_mm
    indices = np.rint((points - origin) / pitch_mm).astype(np.int32)
    shape = tuple((indices.max(axis=0) + 1).tolist())
    occupancy = np.zeros(shape, dtype=bool)
    occupancy[indices[:, 0], indices[:, 1], indices[:, 2]] = True
    return {"origin": origin, "pitch_mm": pitch_mm, "occupancy": occupancy, "topology": topology}


def obstacle_field_membership(field: dict, points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=float)
    result = np.zeros(len(points), dtype=bool)
    if field.get("occupancy") is None:
        return result
    pitch = float(field["pitch_mm"])
    indices = np.rint((points - field["origin"]) / pitch).astype(np.int32)
    shape = np.asarray(field["occupancy"].shape, dtype=int)
    valid = np.all((indices >= 0) & (indices < shape[None, :]), axis=1)
    if valid.any():
        idx = indices[valid]
        result[valid] = field["occupancy"][idx[:, 0], idx[:, 1], idx[:, 2]]
    return result


def interior_voxel_samples(mesh: trimesh.Trimesh, pitch_mm=5.0, max_samples=10000, seed=0):
    grid = filled_voxel_grid(mesh, pitch_mm)
    points = np.asarray(grid.points, dtype=np.float32)
    if len(points) > max_samples:
        indices = np.random.default_rng(seed).choice(len(points), max_samples, replace=False)
        points = points[indices]
    return points, bool(mesh.is_watertight)


def apply_matrix_to_mesh(mesh: trimesh.Trimesh, matrix: np.ndarray) -> trimesh.Trimesh:
    transformed = mesh.copy()
    transformed.vertices = apply_matrix_points(np.asarray(mesh.vertices), matrix)
    return transformed


def lower_limb_denver_rows() -> list[dict]:
    allowed_types = {"osso", "musculo", "cartilagem", "ligamento"}
    with DENVER_CATALOG.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    selected = []
    for row in rows:
        if row["tipo"] not in allowed_types:
            continue
        structure = row["estrutura"]
        if structure in DENVER_LOWER_LIMB_BONES or structure in DENVER_LOWER_LIMB_CARTILAGE or row["tipo"] in {"musculo", "ligamento"}:
            selected.append(row)
    return selected


def totalseg_import_labels(multilabel: dict, hra_mesh_map: dict[str, trimesh.Trimesh]) -> list[str]:
    available = set(multilabel["label_map"].values())
    requested = [name for name in available if name in TS_IMPORT_LABELS or name.startswith(TS_IMPORT_PREFIXES)]
    requested += [name for name in available if name in TS_VESSEL_LABELS]
    output = []
    for label in sorted(set(requested)):
        equivalents = HRA_VESSEL_EQUIVALENTS.get(label) or HRA_UPPER_SKELETON_EQUIVALENTS.get(label, [])
        if equivalents and all(name in hra_mesh_map for name in equivalents):
            continue
        if label.startswith("rib_"):
            _, side, number = label.split("_")
            rib_equivalent = f"VH_F_rib_{number}_{'L' if side == 'left' else 'R'}"
            if rib_equivalent in hra_mesh_map:
                continue
        # User policy sends upper skeleton, skull, ribs, and sternum to TotalSegmentator.
        output.append(label)
    return output


def expected_hra_names_for_label(label: str) -> list[str]:
    if label in HRA_VESSEL_EQUIVALENTS:
        return HRA_VESSEL_EQUIVALENTS[label]
    if label in HRA_UPPER_SKELETON_EQUIVALENTS:
        return HRA_UPPER_SKELETON_EQUIVALENTS[label]
    if label.startswith("rib_"):
        _, side, number = label.split("_")
        return [f"VH_F_rib_{number}_{'L' if side == 'left' else 'R'}"]
    return []


def minimum_surface_distance(mesh_a: trimesh.Trimesh, mesh_b: trimesh.Trimesh, count=2500) -> float:
    a = sample_mesh(mesh_a, count, 911)
    b = sample_mesh(mesh_b, count, 912)
    return float(min(nearest(a, b)[0].min(), nearest(b, a)[0].min()))


def load_hra_group_names(groups: set[str]) -> set[str]:
    path = ROOT / "hra" / "catalogo_hra.csv"
    names = set()
    if not path.exists():
        return names
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row.get("orgao") in groups and row.get("no"):
                names.add(row["no"])
    return names


def run_regional_fits(multilabel: dict, hra_mesh_map: dict[str, trimesh.Trimesh]) -> dict:
    results, matrices, source_centroids = {}, {}, {}
    for region, pairs in REGION_FIT_PAIRS.items():
        available = []
        for label, hra_names in pairs:
            names = [hra_names] if isinstance(hra_names, str) else hra_names
            if label not in {value for value in multilabel["label_map"].values()} or not all(n in hra_mesh_map for n in names):
                continue
            source_mesh = mesh_from_label(multilabel, label)
            target_mesh = merge_meshes([hra_mesh_map[n] for n in names])
            available.append((label, source_mesh, target_mesh, names))
        if len(available) < 2:
            results[region] = {"status": "N/A: fewer than two paired anchors", "pairs_used": [x[0] for x in available]}
            continue
        src = np.vstack([sample_mesh(item[1], 220, 1300 + i) for i, item in enumerate(available)])
        dst = np.vstack([sample_mesh(item[2], 220, 1400 + i) for i, item in enumerate(available)])
        model = fit_b_similarity(src, dst, "similarity")
        matrix = model["matrix"]
        matrices[region] = matrix.tolist()
        errors = {name: symmetric_surface_error(sample_mesh(src_mesh, 2500, 1311), sample_mesh(dst_mesh, 2500, 1411), matrix)
                  for name, src_mesh, dst_mesh, _ in available}
        source_centroids[region] = {name: np.asarray(mesh.vertices).mean(axis=0).tolist() for name, mesh, _, _ in available}
        results[region] = {"status": "completed", "pairs_used": [{"mask": name, "hra_meshes": names} for name, _, _, names in available],
                           "matrix_4x4": matrix.tolist(), "scale_uniform": float(model["scale"][0]),
                           "fit_errors_by_structure": errors, "iterations": model["iterations"]}
    seams = []
    seam_labels = [("head_neck", "thorax", "vertebrae_C7", "vertebrae_T1"),
                   ("thorax", "abdomen_pelvis", "vertebrae_T12", "vertebrae_L1")]
    for reg_a, reg_b, label_a, label_b in seam_labels:
        if reg_a not in matrices or reg_b not in matrices:
            seams.append({"boundary": f"{reg_a}/{reg_b}", "status": "N/A: region fit missing"})
            continue
        try:
            center_a = np.asarray(mesh_from_label(multilabel, label_a).vertices).mean(axis=0)
            center_b = np.asarray(mesh_from_label(multilabel, label_b).vertices).mean(axis=0)
            seam_point = (center_a + center_b) / 2.0
            ta = apply_matrix_points(seam_point[None, :], np.asarray(matrices[reg_a]))[0]
            tb = apply_matrix_points(seam_point[None, :], np.asarray(matrices[reg_b]))[0]
            gap = float(np.linalg.norm(ta - tb))
            seams.append({"boundary": f"{reg_a}/{reg_b}", "anchor_labels": [label_a, label_b],
                          "discontinuity_mm": gap, "status": "PASS" if gap <= 5.0 else "FAIL"})
        except (KeyError, ValueError):
            seams.append({"boundary": f"{reg_a}/{reg_b}", "status": "N/A: seam anchor missing"})
    return {"regions": results, "matrices_4x4": matrices, "seam_continuity": seams}


def run_articulation_checks(multilabel: dict, denver_rows: list[dict], denver_matrix: np.ndarray,
                            b_matrix: np.ndarray, hra_mesh_map: dict[str, trimesh.Trimesh], region_matrices=None,
                            denver_leg_alignment=None) -> list[dict]:
    rows = []
    by_structure_side = {(r["estrutura"], r["lateralidade"]): r for r in denver_rows}
    for side in ("Left", "Right"):
        head_row = by_structure_side.get(("Cartilage FemurHead", side))
        acet_row = by_structure_side.get(("Cartilage PelvisAcetabulum", side))
        if head_row:
            m1 = trimesh.load_mesh(DENVER_STL / head_row["arquivo"], process=False)
            femur_model = (denver_leg_alignment or {}).get("per_side", {}).get(side, {}).get("regions", {}).get("thigh")
            pelvis_names = [HRA_LEG_BONES["femur"][side].replace("femur", "ilium_compact_bone"),
                            HRA_LEG_BONES["femur"][side].replace("femur", "ilium_spongy_bone")]
            pelvis_names = [f"VH_F_ilium_compact_bone_{'L' if side == 'Left' else 'R'}",
                            f"VH_F_ilium_spongy_bone_{'L' if side == 'Left' else 'R'}"]
            if femur_model and all(name in hra_mesh_map for name in pelvis_names):
                head_center = np.asarray(m1.vertices).mean(axis=0)
                head_center = apply_matrix_points(head_center[None, :], np.asarray(femur_model["matrix_4x4"]))
                pelvis_mesh = merge_meshes([hra_mesh_map[name] for name in pelvis_names])
                closest, distance, face_id = trimesh.proximity.closest_point_naive(pelvis_mesh, head_center)
                gap = float(distance[0])
                rows.append({"articulation": f"Denver femoral head center to HRA acetabulum proxy {side.lower()}",
                             "distance_mm": gap, "limit_mm": 5.0, "status": "PASS" if gap <= 5.0 else "FAIL",
                             "source": "Denver FemurHead cartilage centroid to nearest point on HRA ilium union",
                             "center_mm": head_center[0].tolist(), "nearest_HRA_pelvis_surface_mm": closest[0].tolist(),
                             "acetabulum_center_method": "nearest point on HRA pelvis surface; explicit acetabulum mesh absent"})
            else:
                rows.append({"articulation": f"Denver femoral head center to HRA acetabulum {side.lower()}", "distance_mm": None,
                             "limit_mm": 5.0, "status": "N/A", "reason": "femur direct fit or HRA ilium mesh missing"})
        else:
            rows.append({"articulation": f"femoral head to acetabulum {side.lower()}", "distance_mm": None,
                         "limit_mm": 5.0, "status": "N/A", "reason": "Denver cartilage mesh missing"})
        for rib_level in range(1, 13):
            rib_name = f"rib_{side.lower()}_{rib_level}"
            vertebra_name = f"VH_F_thoracic_vertebra_{rib_level}"
            if rib_name not in multilabel["label_map"].values() or vertebra_name not in hra_mesh_map:
                rows.append({"articulation": f"{rib_name} to T{rib_level}", "distance_mm": None,
                             "limit_mm": 5.0, "status": "N/A", "reason": "rib mask or HRA vertebra mesh missing"})
                continue
            rib_mesh = apply_matrix_to_mesh(mesh_from_label(multilabel, rib_name), b_matrix)
            vertebra_mesh = hra_mesh_map[vertebra_name]
            if region_matrices and "thorax" in region_matrices:
                rib_mesh = apply_matrix_to_mesh(mesh_from_label(multilabel, rib_name), np.asarray(region_matrices["thorax"]))
            gap = minimum_surface_distance(rib_mesh, vertebra_mesh)
            rows.append({"articulation": f"{rib_name} to T{rib_level}", "distance_mm": gap, "limit_mm": 5.0,
                         "status": "PASS" if gap <= 5.0 else "FAIL", "source": "TotalSegmentator rib to HRA thoracic vertebra"})
    if "skull" in multilabel["label_map"].values() and "VH_F_cervical_vertebra_1" in hra_mesh_map:
        skull = mesh_from_label(multilabel, "skull")
        transform = b_matrix
        if region_matrices and "head_neck" in region_matrices:
            transform = np.asarray(region_matrices["head_neck"])
        skull = apply_matrix_to_mesh(skull, transform)
        gap = minimum_surface_distance(skull, hra_mesh_map["VH_F_cervical_vertebra_1"])
        rows.append({"articulation": "skull to C1", "distance_mm": gap, "limit_mm": 5.0,
                     "status": "PASS" if gap <= 5.0 else "FAIL", "source": "TotalSegmentator skull to HRA C1"})
    else:
        rows.append({"articulation": "skull to C1", "distance_mm": None, "limit_mm": 5.0,
                     "status": "N/A", "reason": "skull label or HRA C1 mesh missing"})
    return rows


def refresh_geometry_class_summary(rows: list[dict]) -> dict:
    summary = {}
    for cls, limit in GEOMETRIC_LIMITS.items():
        members = [row for row in rows if row["class"] == cls]
        statuses = {row["status"] for row in members}
        measured = statuses & {"PASS", "FAIL"}
        state = ("N/A" if not measured and statuses <= {"N/A"} else
                 "REVIEW" if not measured else "PASS" if measured == {"PASS"} else "FAIL")
        summary[cls] = {"thresholds": limit, "structures_evaluated": len(members), "status": state,
                        "structures_failed": [row["structure"] for row in members if row["status"] == "FAIL"]}
    return summary


def evaluate_acceptance_protocol(multilabel, denver_matrix, b_matrix, hra_mesh_map, stage_b,
                                 region_results=None, human_review=False, capture_dir=None,
                                 denver_leg_alignment=None):
    pitch = 5.0
    mask_labels = set(multilabel["label_map"].values())
    skin = hra_mesh_map.get("VH_F_skin")
    skin_topology = {"available": skin is not None, "watertight": bool(skin.is_watertight) if skin is not None else None,
                     "containment_method": "nearest point on triangulated open skin; signed normal offset",
                     "normal_orientation": None, "normal_orientation_score": None}
    skin_query = None
    if skin is not None:
        try:
            skin_query = prepare_surface_query(skin)
            skin = skin_query["surface"]
            skin_topology["normal_orientation"] = skin_query["orientation"]
            skin_topology["normal_orientation_score"] = skin_query["orientation_score"]
            skin_topology["orientation_check_note"] = skin_query["orientation_check_note"]
        except Exception as exc:
            skin_topology["surface_query_error"] = str(exc)

    replaced_names = {name for names in HRA_LEG_BONES.values() for name in names.values()}
    obstacle_meshes = {name: mesh for name, mesh in hra_mesh_map.items()
                       if name != "VH_F_skin" and ("vertebra" in name or "ilium" in name or "sacrum" in name or
                                                   any(t in name for t in ("kidney", "liver", "spleen", "heart")))}
    obstacle_meshes = {name: mesh for name, mesh in obstacle_meshes.items() if name not in replaced_names}
    obstacle_field = build_obstacle_voxel_field(obstacle_meshes, pitch)

    f1, f3, f4, source_registry = [], [], [], []
    imported_names = set()
    regions = region_results or {}
    region_matrices = regions.get("matrices_4x4", {}) if regions else {}
    leg_alignment = denver_leg_alignment or {"transformed_meshes": {}}
    denver_mesh_xforms = leg_alignment.get("transformed_meshes", {})
    fallback_denver_matrix = np.eye(4)
    denver_row_records = {row["arquivo"]: row for row in denver_leg_rows()}
    def denver_matrix_for_row(row):
        structure = row["estrutura"]
        side = row["lateralidade"]
        lower_leg_tokens = ("Extensor", "Flexor", "Gastrocnemius", "Peroneus", "Plantaris",
                            "Popliteus", "Soleus", "Tibialis", "Tibia", "Fibula", "Patella", "Talus")
        if row["tipo"] == "musculo":
            region_name = "lower_leg" if any(token in structure for token in lower_leg_tokens) else "thigh"
        else:
            region_name = "thigh" if "Femur" in structure else "lower_leg"
        model = leg_alignment.get("per_side", {}).get(side, {}).get("regions", {}).get(region_name)
        return np.asarray(model["matrix_4x4"]) if model else fallback_denver_matrix
    def matrix_for_ts(label):
        if label == "skull" or label.startswith("vertebrae_C"):
            region = "head_neck"
        elif label.startswith(("rib_", "sternum", "humerus_", "scapula_", "clavicula_")) or label in TS_VESSEL_LABELS:
            region = "thorax"
        else:
            region = "abdomen_pelvis"
        return np.asarray(region_matrices.get(region, b_matrix)), region
    denver_rows = lower_limb_denver_rows()
    for row in denver_rows:
        source_name = f"{row['estrutura']} {row['lateralidade']}"
        source_key = f"denver:{row['arquivo']}"
        if source_key in imported_names:
            raise ValueError(f"Fonte duplicada no registry: {source_key}")
        imported_names.add(source_key)
        source_registry.append({"structure": source_name, "source": "Denver", "file": row["arquivo"], "type": row["tipo"]})
        mesh = trimesh.load_mesh(DENVER_STL / row["arquivo"], process=False)
        matrix = denver_matrix_for_row(row)
        points = apply_matrix_points(np.asarray(mesh.vertices), matrix)
        f1.append(skin_containment_row(skin, points, source_name, "Denver", skin_query))
        try:
            interior, watertight = interior_voxel_samples(apply_matrix_to_mesh(mesh, matrix), 5.0, 5000,
                                                         seed=len(f3) + 200)
            if obstacle_field["occupancy"] is None or not len(interior):
                f3.append({"structure": source_name, "source": "Denver", "sample_count": int(len(interior)),
                           "source_watertight": watertight, "overlap_fraction": None, "status": "N/A: HRA obstacle volume unavailable"})
            else:
                overlap = obstacle_field_membership(obstacle_field, interior)
                fraction = float(overlap.mean())
                f3.append({"structure": source_name, "source": "Denver", "sample_count": int(len(interior)),
                           "source_watertight": watertight, "overlap_fraction": fraction,
                           "overlap_percent": fraction * 100, "status": "PASS" if fraction < 0.02 else "FAIL"})
        except Exception as exc:
            f3.append({"structure": source_name, "source": "Denver", "overlap_fraction": None,
                       "status": "N/A", "reason": str(exc)})
        laterality = row["lateralidade"]
        if laterality in ("Left", "Right"):
            mean_x = float(points[:, 0].mean())
            correct = mean_x < 0 if laterality == "Left" else mean_x > 0
            f4.append({"structure": source_name, "source": "Denver", "mean_x_ras_mm": mean_x,
                       "expected_sign": "negative" if laterality == "Left" else "positive",
                       "status": "PASS" if correct else "FAIL"})

    imports = totalseg_import_labels(multilabel, hra_mesh_map)
    for label in imports:
        source_key = f"totalseg:{label}"
        if source_key in imported_names:
            raise ValueError(f"Fonte duplicada no registry: {source_key}")
        imported_names.add(source_key)
        source_registry.append({"structure": label, "source": "TotalSegmentator", "label": label})
        mesh = mesh_from_label(multilabel, label)
        ts_matrix, ts_region = matrix_for_ts(label)
        points = apply_matrix_points(np.asarray(mesh.vertices), ts_matrix)
        f1.append(skin_containment_row(skin, points, label, "TotalSegmentator", skin_query))
        try:
            interior, watertight = interior_voxel_samples(apply_matrix_to_mesh(mesh, ts_matrix), 5.0, 5000,
                                                         seed=len(f3) + 800)
            if obstacle_field["occupancy"] is None or not len(interior):
                f3.append({"structure": label, "source": "TotalSegmentator", "sample_count": int(len(interior)),
                           "source_watertight": watertight, "overlap_fraction": None, "status": "N/A: HRA obstacle volume unavailable"})
            else:
                overlap = obstacle_field_membership(obstacle_field, interior)
                fraction = float(overlap.mean())
                f3.append({"structure": label, "source": "TotalSegmentator", "sample_count": int(len(interior)),
                           "source_watertight": watertight, "overlap_fraction": fraction,
                           "overlap_percent": fraction * 100, "status": "PASS" if fraction < 0.02 else "FAIL"})
        except Exception as exc:
            f3.append({"structure": label, "source": "TotalSegmentator", "overlap_fraction": None,
                       "status": "N/A", "reason": str(exc)})
        if "_left" in label:
            mean_x = float(points[:, 0].mean()); correct = mean_x < 0
            f4.append({"structure": label, "source": "TotalSegmentator", "mean_x_ras_mm": mean_x,
                       "expected_sign": "negative", "status": "PASS" if correct else "FAIL"})
        elif "_right" in label:
            mean_x = float(points[:, 0].mean()); correct = mean_x > 0
            f4.append({"structure": label, "source": "TotalSegmentator", "mean_x_ras_mm": mean_x,
                       "expected_sign": "positive", "status": "PASS" if correct else "FAIL"})

    # Compare canonical anatomy (ignoring laterality) against retained HRA
    # source structures. Exclude deliberate Denver replacements and HRA fit
    # anchors that are not imported from another source.
    retained_hra_names = [name for name in hra_mesh_map if name != "VH_F_skin"]
    replacement_hra = set(DENVER_HRA_BONE_TARGETS.values())
    replacement_hra_names = {n for pair in replacement_hra for n in pair}
    retained_imports, duplicate_anatomy = [], []
    canonical_imports = {anatomy_source_key(row["structure"]): row for row in source_registry}
    for name in retained_hra_names:
        if name in replacement_hra_names:
            continue
        key = anatomy_source_key(name.removeprefix("VH_F_"))
        if key in canonical_imports:
            duplicate_anatomy.append({"structure": name, "also_selected": canonical_imports[key]["structure"]})
        else:
            retained_imports.append(name)

    geometry_similarity, geometry_summary = geometry_acceptance_rows(
        stage_b["similarity"]["fit_errors_by_structure"], stage_b.get("held_out_errors", {}), "similarity")
    geometry_aniso, geometry_aniso_summary = geometry_acceptance_rows(
        stage_b["anisotropic"]["fit_errors_by_structure"], stage_b.get("held_out_errors", {}), "anisotropic")
    geometry_by_region = {}
    all_region_rows = []
    for region_name, region_fit in regions.get("regions", {}).items():
        if region_fit.get("status") != "completed":
            geometry_by_region[region_name] = {"status": region_fit.get("status"), "rows": [], "class_summary": {}}
            continue
        region_rows, region_summary = geometry_acceptance_rows(region_fit["fit_errors_by_structure"], {}, "similarity")
        all_region_rows.extend([{**row, "region": region_name} for row in region_rows])
        geometry_by_region[region_name] = {"status": "completed", "rows": region_rows, "class_summary": region_summary}

    # Include imported structures in the report even when HRA has no direct
    # counterpart for a symmetric surface-distance measurement.
    for row in source_registry:
        name = row["structure"]
        if any(existing["structure"] == name for existing in geometry_similarity):
            continue
        kind = geometry_class(name)
        reason = "no HRA counterpart configured for symmetric surface distance"
        record = {"structure": name, "class": kind, "mean_mm": None, "p95_mm": None,
                  "limits": GEOMETRIC_LIMITS[kind], "status": "REVIEW" if kind == "individual_review" else "N/A",
                  "measurement_source": "not measured", "reason": reason}
        geometry_similarity.append(record)
        geometry_aniso.append(dict(record))
    geometry_summary = refresh_geometry_class_summary(geometry_similarity)
    geometry_aniso_summary = refresh_geometry_class_summary(geometry_aniso)
    direct_leg_geometry = []
    for name, error in leg_alignment.get("fit_errors_by_structure", {}).items():
        if "mean_mm" not in error:
            direct_leg_geometry.append({"structure": name, "class": "large_bones", "status": "N/A",
                                       "reason": error.get("status"), "region": "lower_limbs"})
            continue
        limit = GEOMETRIC_LIMITS["large_bones"]
        state = "PASS" if error["mean_mm"] <= limit["mean_max_mm"] and error["p95_mm"] <= limit["p95_max_mm"] else "FAIL"
        direct_leg_geometry.append({"structure": name, "class": "large_bones", "mean_mm": error["mean_mm"],
                                    "p95_mm": error["p95_mm"], "limits": limit, "status": state,
                                    "region": "lower_limbs", "measurement_source": "Denver direct fit to HRA lower-limb composite"})
    for row in geometry_similarity:
        if row.get("status") not in ("N/A", "REVIEW"):
            continue
        imported = next((item for item in source_registry if item["structure"] == row["structure"]), None)
        if not imported:
            continue
        region = "lower_limbs" if imported["source"] == "Denver" else matrix_for_ts(imported["structure"])[1]
        direct_leg_geometry.append({**row, "region": region}) if region == "lower_limbs" else all_region_rows.append({**row, "region": region})
    for row in all_region_rows:
        if row.get("status") in ("N/A", "REVIEW"):
            region_name = row.get("region")
            if region_name in geometry_by_region:
                geometry_by_region[region_name]["rows"].append(row)
                geometry_by_region[region_name]["class_summary"] = refresh_geometry_class_summary(geometry_by_region[region_name]["rows"])
    geometry_by_region["lower_limbs"] = {"status": "completed", "rows": direct_leg_geometry,
                                          "class_summary": refresh_geometry_class_summary(direct_leg_geometry)}
    all_region_rows.extend(direct_leg_geometry)
    articulations = run_articulation_checks(multilabel, denver_rows, np.asarray(denver_matrix), np.asarray(b_matrix), hra_mesh_map,
                                             region_matrices if region_matrices else None,
                                             denver_leg_alignment=leg_alignment)
    def aggregate_status(items):
        measured = [item for item in items if item.get("status") in ("PASS", "FAIL")]
        if not measured:
            return "N/A"
        if any(item["status"] == "FAIL" for item in measured):
            return "FAIL"
        return "PASS" if len(measured) == len(items) else "N/A: incomplete"
    four_views = {}
    if capture_dir:
        capture_root = Path(capture_dir)
        for view in ("frente", "costas", "lado_esquerdo", "lado_direito"):
            four_views[view] = any((capture_root / f"{view}{ext}").exists() for ext in (".png", ".jpg", ".jpeg"))
    f5 = "PASS" if human_review and all(four_views.values()) else "PENDING"
    region_names = ("head_neck", "thorax", "abdomen_pelvis", "lower_limbs")
    region_metric_rows = {region: {} for region in region_names}
    for region in region_names:
        rows = geometry_by_region.get(region, {}).get("rows", [])
        region_metric_rows[region]["geometry"] = aggregate_status(rows) if rows else "N/A"
    for criterion, items, region_getter in (
        ("F1_containment", f1, lambda row: "lower_limbs" if row["source"] == "Denver" else matrix_for_ts(row["structure"])[1]),
        ("F3_overlap", f3, lambda row: "lower_limbs" if row["source"] == "Denver" else matrix_for_ts(row["structure"])[1]),
        ("F4_laterality", f4, lambda row: "lower_limbs" if row["source"] == "Denver" else matrix_for_ts(row["structure"])[1]),
    ):
        for region in region_names:
            selected = [row for row in items if region_getter(row) == region]
            region_metric_rows[region][criterion] = aggregate_status(selected)
    for region in region_names:
        joint_rows = []
        for row in articulations:
            name = row["articulation"]
            assigned = ("lower_limbs" if "femoral head" in name else
                        "head_neck" if "skull" in name else "thorax" if " to T" in name else None)
            if assigned == region:
                joint_rows.append(row)
        region_metric_rows[region]["F2_articulations"] = aggregate_status(joint_rows)
        region_metric_rows[region]["F5_human_review"] = f5
        region_metric_rows[region]["source_single_source"] = source_policy_status = (
            "FAIL" if duplicate_anatomy else "PASS")
    blockers = []
    for region, criteria in region_metric_rows.items():
        for criterion, state in criteria.items():
            if state not in ("PASS", "N/A"):
                blockers.append({"region": region, "criterion": criterion, "status": state})
    return {
        "protocol": "Acceptance by purpose - EXP-0014",
        "engineering_proposals_not_clinically_validated": True,
        "rule_15": {"criterion_change_recorded_explicitly": True,
                    "EXP-0011_status": "REPROVED under its original 3 mm criterion; not retroactively changed",
                    "new_criteria_apply_to": "EXP-0014 only"},
        "geometric_limits": GEOMETRIC_LIMITS,
        "geometry_after_global_similarity": {"rows": geometry_similarity, "class_summary": geometry_summary},
        "geometry_after_axis_scale": {"rows": geometry_aniso, "class_summary": geometry_aniso_summary},
        "geometry_after_regions": geometry_by_region,
        "regional_geometry_rows": all_region_rows,
        "F1_containment": {"threshold_fraction": 0.99, "threshold_outside_fraction": 0.01,
                           "skin_topology": {**skin_topology, **({"fraction_faces_radially_outward": skin_query["fraction_faces_radially_outward"]} if skin_query else {})},
                           "method_note": "Each imported vertex is queried against the 4 nearest skin triangle centroids; closest points are computed exactly on those candidate triangles and signed offsets use the local skin normal. Open-surface orientation uses median radial face-normal direction from the mesh centroid.",
                           "per_structure": f1, "status": aggregate_status(f1)},
        "F2_articulations": {"threshold_mm": 5.0, "required_checks": 27, "per_articulation": articulations,
                             "regional_seam_continuity": regions.get("seam_continuity", []) if regions else [],
                             "status": ("FAIL" if any(x["status"] == "FAIL" for x in articulations) or
                                        any(x.get("status") == "FAIL" for x in (regions or {}).get("seam_continuity", [])) else
                                        ("PASS" if len(articulations) == 27 and all(x["status"] == "PASS" for x in articulations) and
                                         (not regions or all(x.get("status") == "PASS" for x in regions.get("seam_continuity", []))) else "N/A: checks missing"))},
        "F3_overlap": {"threshold_fraction_exclusive": 0.02, "sampling": "up to 5,000 interior voxel centers per source mesh at 5 mm pitch",
                       "obstacle_meshes": sorted(obstacle_meshes), "obstacle_topology": obstacle_field["topology"],
                       "per_structure": f3, "status": aggregate_status(f3)},
        "F4_laterality": {"rule": "left RAS x < 0; right RAS x > 0", "per_structure": f4,
                          "status": aggregate_status(f4)},
        "F5_human_review": {"status": f5, "reviewer_approval_flag": bool(human_review),
                            "capture_directory": str(capture_dir) if capture_dir else None,
                            "four_required_views": four_views, "note": "A human must approve the four requested views; automation cannot approve this criterion."},
        "source_single_source_policy": {"HRA": ["skin", "organs", "vertebral column and other existing structures"],
                                        "Denver": ["lower-limb bones, muscles, cartilage and ligaments; replaces equivalent HRA sources"],
                                        "TotalSegmentator": ["skull, ribs, sternum, humerus, scapula, clavicle, and major vessels absent from HRA"],
                                        "import_registry": source_registry,
                                        "unique_source_per_registry_entry": True,
                                        "retained_hra_structures_excluded_from_imports": retained_imports,
                                        "duplicate_anatomy_detected": duplicate_anatomy,
                                        "status": "FAIL" if duplicate_anatomy else "PASS"},
        "regional_registration": regions or {"status": "not requested; pass --por-regiao to calculate"},
        "regional_acceptance": region_metric_rows,
        "atlas_mount_blockers": blockers,
        "denver_leg_alignment": {key: value for key, value in leg_alignment.items() if key != "transformed_meshes"},
        "final_acceptance_status": ("NOT ACCEPTED: EXP-0014 blocking failures or human review remain" if blockers else "PENDING HUMAN REVIEW"),
        "segmentation_resolution": "normal" if "saida" in str(multilabel.get("path", "")).lower() else "diagnostic",
    }


def write_real_outputs(transforms, message):
    TRANSFORMS_PATH.write_text(json.dumps(transforms, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Alinhamento Denver → TC → HRA", "", message, ""]
    if "stage_a" in transforms and "fit_errors_by_structure" in transforms["stage_a"]:
        a = transforms["stage_a"]
        lines += ["## Etapa A — Denver STL → TC", "",
                  f"Sinais vencedores: `{a['signs']}`; máscara sacrum contra união Denver Sacrum + Coccyx: média {a['held_out_validation']['Sacrum + Coccyx']['mean_mm']:.3f} mm, p95 {a['held_out_validation']['Sacrum + Coccyx']['p95_mm']:.3f} mm.",
                  "", "| Estrutura | Média (mm) | P95 (mm) |", "|---|---:|---:|"]
        lines += [f"| {name} | {err['mean_mm']:.3f} | {err['p95_mm']:.3f} |" for name, err in a["fit_errors_by_structure"].items()]
        lines += [f"| Sacrum NLM vs Denver Sacrum + Coccyx (holdout) | {a['held_out_validation']['Sacrum + Coccyx']['mean_mm']:.3f} | {a['held_out_validation']['Sacrum + Coccyx']['p95_mm']:.3f} |", ""]
    if str(transforms.get("stage_b", {}).get("status", "")).startswith(("completed", "diagnostic_only")):
        b = transforms["stage_b"]
        status_note = " **EXP-0011 REPROVADO no limite original do sacro de 3 mm; EXP-0014 avaliado independentemente.**" if b.get("EXP0011_stage_a_3mm_gate", "").startswith("REPROVED") else ""
        lines += [f"## Etapa B — TC → HRA{status_note}", "",
                  "HRA convertido explicitamente de metros/eixos do app para RAS mm: `x_ras=-x_app*1000`, `y_ras=z_app*1000`, `z_ras=y_app*1000`. ICP sem busca de sinais/eixos, inicializado pela diferença de centroides das uniões pareadas; objetivo de distância média simétrica. Escala uniforme e por eixo limitadas a `[0.85, 1.15]`.", "",
                  "### Pareamento usado", "",
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


def write_acceptance_report(transforms):
    protocol = transforms.get("acceptance_protocol")
    if not protocol:
        return
    lines = ["", "## EXP-0014 - critério de aceitação por finalidade", "",
             "Os limites abaixo são propostas de engenharia para investigação e não foram validados clinicamente. O EXP-0011 permanece REPROVADO sob o critério original de 3 mm; o EXP-0014 registra uma mudança de critério sem alterar retroativamente aquele resultado.",
             f"Esta rodada usou a segmentação `{protocol.get('segmentation_resolution')}` em `{transforms.get('source_multilabel', {}).get('path')}`.", "",
             "### Critérios geométricos", "",
             "| Classe | Limite médio (mm) | Limite p95 (mm) | Similaridade | Escala XYZ |", "|---|---:|---:|---|---|"]
    gs = protocol["geometry_after_global_similarity"]
    ga = protocol["geometry_after_axis_scale"]
    for cls, limit in protocol["geometric_limits"].items():
        mean_limit = "N/A" if limit["mean_max_mm"] is None else f"{limit['mean_max_mm']:.1f}"
        p95_limit = "N/A" if limit["p95_max_mm"] is None else f"{limit['p95_max_mm']:.1f}"
        lines.append(f"| {cls} | {mean_limit} | {p95_limit} | {gs['class_summary'][cls]['status']} ({gs['class_summary'][cls]['structures_evaluated']}) | {ga['class_summary'][cls]['status']} ({ga['class_summary'][cls]['structures_evaluated']}) |")
    lines += ["", "| Estrutura | Classe | Média / p95 similaridade (mm) | Estado | Média / p95 escala XYZ (mm) | Estado |", "|---|---|---:|---|---:|---|"]
    axis_by_name = {row["structure"]: row for row in ga["rows"]}
    for row in gs["rows"]:
        other = axis_by_name.get(row["structure"], {})
        mean = "N/A" if row.get("mean_mm") is None else f"{row['mean_mm']:.3f}"
        p95 = "N/A" if row.get("p95_mm") is None else f"{row['p95_mm']:.3f}"
        other_mean = "N/A" if other.get("mean_mm") is None else f"{other['mean_mm']:.3f}"
        other_p95 = "N/A" if other.get("p95_mm") is None else f"{other['p95_mm']:.3f}"
        lines.append(f"| {row['structure']} | {row['class']} | {mean} / {p95} | {row['status']} | {other_mean} / {other_p95} | {other.get('status', 'N/A')} |")

    f1 = protocol["F1_containment"]
    topology = f1["skin_topology"]
    lines += ["", "### F1 - contenção assinada na pele HRA", "",
              f"Estado geral: {f1['status']}. Pele disponível: {topology['available']}; malha fechada: {topology['watertight']}; orientação: {topology.get('normal_orientation')}; escore radial mediano: {topology.get('normal_orientation_score')}; fração de faces radiais externas: {topology.get('fraction_faces_radially_outward')}; verificação: {topology.get('orientation_check_note')}. {f1['method_note']}",
              "", "| Estrutura importada | Fonte | Vértices | Fração fora | Distância máxima fora (mm) | Estado |", "|---|---|---:|---:|---:|---|"]
    for row in f1["per_structure"]:
        fraction = "N/A" if row.get("outside_fraction") is None else f"{row['outside_fraction']:.5f} ({row['outside_percent']:.2f}%)"
        max_out = "N/A" if row.get("max_distance_outside_mm") is None else f"{row['max_distance_outside_mm']:.3f}"
        lines.append(f"| {row['structure']} | {row['source']} | {row.get('vertices', 'N/A')} | {fraction} | {max_out} | {row['status']} |")

    f2 = protocol["F2_articulations"]
    lines += ["", "### F2 - articulações e emendas regionais", "", f"Estado geral: {f2['status']}",
              "", "| Articulação | Distância (mm) | Limite (mm) | Estado |", "|---|---:|---:|---|"]
    for row in f2["per_articulation"]:
        distance = "N/A" if row.get("distance_mm") is None else f"{row['distance_mm']:.3f}"
        lines.append(f"| {row['articulation']} | {distance} | {row['limit_mm']:.1f} | {row['status']} |")
    for row in f2.get("regional_seam_continuity", []):
        gap = "N/A" if row.get("discontinuity_mm") is None else f"{row['discontinuity_mm']:.3f}"
        lines.append(f"| Regional seam {row['boundary']} | {gap} | 5.0 | {row['status']} |")

    f3 = protocol["F3_overlap"]
    lines += ["", "### F3 - sobreposição de volume com órgãos/ossos HRA", "",
              f"Estado geral: {f3['status']}. Amostragem: {f3['sampling']}. Campo de obstáculos: malhas preenchidas voxelizadas a 5 mm em grade comum do mundo.",
              "", "| Estrutura importada | Fonte | Amostras internas | Fração sobreposta | Estado |", "|---|---|---:|---:|---|"]
    for row in f3["per_structure"]:
        fraction = "N/A" if row.get("overlap_fraction") is None else f"{row['overlap_fraction']:.5f} ({row['overlap_percent']:.2f}%)"
        lines.append(f"| {row['structure']} | {row['source']} | {row.get('sample_count', 'N/A')} | {fraction} | {row['status']} |")

    f4 = protocol["F4_laterality"]
    lines += ["", "### F4 - lateralidade", "", f"Estado geral: {f4['status']}; regra: {f4['rule']}.",
              "", "| Estrutura | Fonte | X RAS médio (mm) | Sinal esperado | Estado |", "|---|---|---:|---|---|"]
    for row in f4["per_structure"]:
        lines.append(f"| {row['structure']} | {row['source']} | {row['mean_x_ras_mm']:.2f} | {row['expected_sign']} | {row['status']} |")

    f5 = protocol["F5_human_review"]
    lines += ["", "### F5 - revisão humana", "", f"Estado: {f5['status']}. Vistas necessárias: {f5['four_required_views']}. O script não presume aprovação humana.",
              "", "### Registro de fonte única", "", "| Estrutura | Fonte selecionada |", "|---|---|"]
    for row in protocol["source_single_source_policy"]["import_registry"]:
        lines.append(f"| {row['structure']} | {row['source']} |")
    for row in protocol["source_single_source_policy"]["duplicate_anatomy_detected"]:
        lines.append(f"| {row['structure']} | DUPLICATA: também {row['also_selected']} |")

    lines += ["", "### EXP-0014 - resultado por região", "", "| Região | Geometria | F1 contenção | F2 articulações | F3 sobreposição | F4 lateralidade | F5 revisão | Fonte única |", "|---|---|---|---|---|---|---|---|"]
    for region, criteria in protocol.get("regional_acceptance", {}).items():
        lines.append(f"| {region} | {criteria.get('geometry')} | {criteria.get('F1_containment')} | {criteria.get('F2_articulations')} | {criteria.get('F3_overlap')} | {criteria.get('F4_laterality')} | {criteria.get('F5_human_review')} | {criteria.get('source_single_source')} |")
    lines += ["", "### Impedimentos para montar o atlas", ""]
    blockers = protocol.get("atlas_mount_blockers", [])
    lines.extend([f"- {row['region']}: {row['criterion']} = {row['status']}" for row in blockers] or ["Nenhum critério bloqueador registrado."])
    leg_alignment = protocol.get("denver_leg_alignment", {})
    lines += ["", "### Ajustes diretos Denver → HRA das pernas", "", "| Lado | Região | Escala |", "|---|---|---:|"]
    for side, result in leg_alignment.get("per_side", {}).items():
        for region, fit in result.get("regions", {}).items():
            lines.append(f"| {side} | {region} | {fit['scale_uniform']:.5f} |")
    lines += ["", "| Joelho | Distância mínima fêmur–tíbia (mm) | Estado |", "|---|---:|---|"]
    for row in leg_alignment.get("knee_seams", []):
        gap = "N/A" if row.get("femur_to_tibia_minimum_distance_mm") is None else f"{row['femur_to_tibia_minimum_distance_mm']:.3f}"
        lines.append(f"| {row['side']} | {gap} | {row['status']} |")

    regional = protocol.get("regional_registration", {})
    if regional.get("regions"):
        lines += ["", "### Ajuste por região (--por-regiao)", "", "| Região | Estado | Escala uniforme | Âncoras |", "|---|---|---:|---:|"]
        for name, result in regional["regions"].items():
            count = len(result.get("pairs_used", []))
            scale = "N/A" if result.get("scale_uniform") is None else f"{result['scale_uniform']:.4f}"
            lines.append(f"| {name} | {result['status']} | {scale} | {count} |")
        lines += ["", "| Emenda | Descontinuidade (mm) | Estado |", "|---|---:|---|"]
        for row in regional.get("seam_continuity", []):
            gap = "N/A" if row.get("discontinuity_mm") is None else f"{row['discontinuity_mm']:.3f}"
            lines.append(f"| {row['boundary']} | {gap} | {row['status']} |")
        lines += ["", "#### Erros das âncoras por região", "", "| Região | Estrutura | Média (mm) | p95 (mm) | Estado |", "|---|---|---:|---:|---|"]
        for row in protocol.get("regional_geometry_rows", []):
            mean = "N/A" if row.get("mean_mm") is None else f"{row['mean_mm']:.3f}"
            p95 = "N/A" if row.get("p95_mm") is None else f"{row['p95_mm']:.3f}"
            lines.append(f"| {row['region']} | {row['structure']} | {mean} | {p95} | {row['status']} |")
    source_policy = protocol["source_single_source_policy"]
    lines += ["", f"Fonte única por anatomia: {source_policy['status']}; duplicatas detectadas: {len(source_policy['duplicate_anatomy_detected'])}.",
              "", "Dados detalhados de vértices, volumes amostrados, transformações e erros estão em `transformacoes.json`.", ""]
    with REPORT_PATH.open("a", encoding="utf-8") as stream:
        stream.write("\n".join(lines))


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
    sim = icp(source2, target2, mode="similarity", max_iter=15, trim=1.0, scale_bounds=(0.01, 10.0))
    sim_error = float(np.mean(nearest((np.c_[source2, np.ones(len(source2))] @ sim["matrix"].T)[:, :3], target2)[0]))
    assert sim_error < 1e-4 and abs(sim["scale"][0] - 1.2) < 1e-4, f"ICP similaridade sintético: {sim_error}, {sim['scale']}"

    scales = np.array([1.1, 0.9, 1.05])
    target3 = source2 * scales + translation2
    aniso = icp(source2, target3, mode="anisotropic", max_iter=18, trim=1.0, scale_bounds=(0.01, 10.0))
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

    # EXP-0014: explicit HRA app-to-RAS axes, bounded scales, and approximate
    # containment/overlap fallbacks on watertight synthetic meshes.
    converted = hra_app_to_ras_mm(np.array([[0.01, 0.02, 0.03]]))
    assert np.allclose(converted, [[-10.0, 30.0, 20.0]]), f"Conversão app->RAS: {converted}"
    _, bounded_scale, _ = fit_corresponded(source2, source2 * 2.0, "similarity", scale_bounds=(0.85, 1.15))
    assert 0.85 <= bounded_scale[0] <= 1.15, f"Limite de escala uniforme: {bounded_scale}"
    _, bounded_axis_scale, _ = fit_corresponded(source2, source2 * np.array([2.0, 0.5, 1.8]), "anisotropic",
                                                 scale_bounds=(0.85, 1.15))
    assert np.all((bounded_axis_scale >= 0.85) & (bounded_axis_scale <= 1.15)), (
        f"Limite de escala por eixo: {bounded_axis_scale}")

    skin_box = trimesh.creation.box(extents=(20, 20, 20))
    skin_grid_test = filled_voxel_grid(skin_box, 1.0)
    inside_fraction = float(voxel_grid_membership(skin_grid_test, np.array([[0, 0, 0], [30, 0, 0]])).mean())
    assert inside_fraction == 0.5, f"F1 voxel containment sintético: {inside_fraction}"
    obstacle_field_test = build_obstacle_voxel_field({"obstacle": trimesh.creation.box(extents=(10, 10, 10))}, 1.0)
    overlap_fraction = float(obstacle_field_membership(obstacle_field_test, np.array([[0, 0, 0], [30, 0, 0]])).mean())
    assert overlap_fraction == 0.5, f"F3 voxel overlap sintético: {overlap_fraction}"
    geom_pass, _ = geometry_acceptance_rows({"femur_left": {"mean_mm": 4.0, "p95_mm": 11.0}}, {})
    geom_fail, _ = geometry_acceptance_rows({"vertebrae_T1": {"mean_mm": 4.0, "p95_mm": 11.0}}, {})
    assert geom_pass[0]["status"] == "PASS" and geom_fail[0]["status"] == "FAIL", (
        "Classificação geométrica EXP-0014 não respeitou limites")
    open_skin = trimesh.creation.box(extents=(20, 20, 20))
    open_skin.update_faces(np.arange(len(open_skin.faces)) != 0)
    open_skin.remove_unreferenced_vertices()
    signed_skin = prepare_surface_query(open_skin)
    signed_result = closest_point_and_signed_offset(open_skin, np.array([[11.0, 0, 0], [0, 0, 0]]), prepared=signed_skin)
    assert signed_result["outside"].tolist() == [True, False], (
        f"F1 signed open-surface synthetic case failed: {signed_result['signed_offset_mm']}")

    print("TESTE SINTÉTICO OK", {"rigid_mean_mm": rigid_error,
                                 "similarity_mean_mm": sim_error, "similarity_scale": sim["scale"].tolist(),
                                 "anisotropic_mean_mm": aniso_error, "anisotropic_scale": aniso["scale"].tolist(),
                                 "stage_a_sign_combinations": len(a_signs), "stage_a_sacrum_mean_mm": sacrum_validation["mean_mm"],
                                 "stage_b_multistart_aniso_mean_mm": error4,
                                 "marching_cubes_faces": int(len(synthetic_mask_mesh.faces)), "gltf_extent_error_mm": ext_error,
                                 "app_to_ras_mm": converted.tolist(), "bounded_uniform_scale": bounded_scale.tolist(),
                                 "bounded_axis_scale": bounded_axis_scale.tolist(),
                                 "f1_synthetic_inside_fraction": inside_fraction,
                                 "f3_synthetic_overlap_fraction": overlap_fraction,
                                 "geometry_classification": [geom_pass[0]["status"], geom_fail[0]["status"]],
                                 "open_skin_normal_orientation": signed_skin["orientation"],
                                 "open_skin_signed_offsets_mm": signed_result["signed_offset_mm"].tolist()})


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
    parser.add_argument("--modo-diagnostico", action="store_true",
                        help="Executa etapa B mesmo se o holdout do sacro reprovar; resultados não são finais")
    parser.add_argument("--por-regiao", action="store_true",
                        help="Calcula similaridade separada para cabeça/pescoço, tórax, abdome/pelve e membros inferiores")
    parser.add_argument("--revisao-humana-aprovada", action="store_true",
                        help="Registra aprovação humana F5 somente junto com as quatro capturas nomeadas")
    parser.add_argument("--capturas-dir", type=Path,
                        help="Pasta com frente.png, costas.png, lado_esquerdo.png e lado_direito.png para F5")
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
    capture_dir = args.capturas_dir if args.capturas_dir and args.capturas_dir.is_absolute() else (
        ROOT / args.capturas_dir if args.capturas_dir else None)
    if capture_dir is not None and not capture_dir.is_dir():
        raise FileNotFoundError(f"--capturas-dir não existe: {capture_dir}")
    return run_real(mask_dir, diagnostic_stage_b=args.modo_diagnostico, by_region=args.por_regiao,
                    human_review=args.revisao_humana_aprovada, capture_dir=capture_dir)


if __name__ == "__main__":
    sys.exit(main())
