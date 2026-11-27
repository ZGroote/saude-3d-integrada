"""EXP-0025 adaptação B0/M. Este módulo nunca lê músculos Denver.

Reprodução: python pesquisa/resultados/EXP-0025/adaptar.py
Dados Denver permitidos: apenas os seis STL *_Bone_* indicados abaixo e
malhas ósseas do pé com correspondência no BodyParts3D. A função única de
leitura Denver valida o nome antes de abrir o arquivo.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import itertools
import json
from pathlib import Path

import numpy as np
import trimesh
from scipy.interpolate import RBFInterpolator
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CATALOG = ROOT / "bodyparts3d" / "catalogo_bp3d.csv"
BP3D_DIR = ROOT / "bodyparts3d" / "bruto" / "isa_BP3D_4.0_obj_99"
DENVER_DIR = ROOT / "hra" / "denver" / "bruto" / "Final 3D STL Models-stl" / "Left"
SEED = 25021
SCALE_SAMPLE_N = 850
BONE_MAP = {
    # Nome interno: FMA, lado no catálogo, STL Denver. Os seis primeiros são
    # os ossos explicitamente nomeados no protocolo; os sete restantes são
    # contraparte do pé disponíveis nos dois catálogos, úteis para inserções.
    "pelvis": ("FMA16587", "left", "VHF_Left_Bone_Pelvis_smooth.stl"),
    "sacrum": ("FMA16202", "", "VHF_Left_Bone_Sacrum_smooth.stl"),
    "femur": ("FMA24475", "left", "VHF_Left_Bone_Femur_smooth.stl"),
    "patella": ("FMA24487", "left", "VHF_Left_Bone_Patella_smooth.stl"),
    "tibia": ("FMA24478", "left", "VHF_Left_Bone_Tibia_smooth.stl"),
    "fibula": ("FMA24481", "left", "VHF_Left_Bone_Fibula_smooth.stl"),
    "calcaneus": ("FMA24498", "left", "VHF_Left_Bone_Calcaneous_smooth.stl"),
    "cuboid": ("FMA24529", "left", "VHF_Left_Bone_Cuboid_smooth.stl"),
    "intermediate_cuneiform": ("FMA24524", "left", "VHF_Left_Bone_IntermediateCuneiform_smooth.stl"),
    "lateral_cuneiform": ("FMA24526", "left", "VHF_Left_Bone_LateralCuneiform_smooth.stl"),
    "medial_cuneiform": ("FMA24522", "left", "VHF_Left_Bone_MedialCuneiform_smooth.stl"),
    "navicular": ("FMA24501", "left", "VHF_Left_Bone_Navicular_smooth.stl"),
    "talus": ("FMA24483", "left", "VHF_Left_Bone_Talus_smooth.stl"),
}
ALIGN_BONES = ("pelvis", "femur", "tibia")
MUSCLE_GROUPS = {
    "rectus_femoris": [("FMA38929", "VHF_Left_Muscle_RectusFemoris_smooth.stl")],
    "vastus_lateralis": [("FMA38931", "VHF_Left_Muscle_VastusLateralis_smooth.stl")],
    "vastus_medialis": [("FMA38933", "VHF_Left_Muscle_VastusMedialis_smooth.stl")],
    "sartorius": [("FMA22355", "VHF_Left_Muscle_Sartorius_smooth.stl")],
    "gracilis": [("FMA43884", "VHF_Left_Muscle_Gracilis_smooth.stl")],
    "adductor_longus": [("FMA22457", "VHF_Left_Muscle_AdductorLongus_smooth.stl")],
    # O protocolo nomeia 10 músculos e lista as duas cabeças do bíceps femoral.
    # Mantêm-se dois arquivos por cabeça, mas as métricas são da união do grupo.
    "biceps_femoris": [
        ("FMA45889", "VHF_Left_Muscle_BicepsFemorisLong_smooth.stl"),
        ("FMA45892", "VHF_Left_Muscle_BicepsFemorisShort_smooth.stl"),
    ],
    "gastrocnemius_medial": [("FMA45958", "VHF_Left_Muscle_GastrocnemiusMedial_smooth.stl")],
    "gluteus_medius": [("FMA22331", "VHF_Left_Muscle_GluteusMedius_smooth.stl")],
    "tibialis_anterior": [("FMA22545", "VHF_Left_Muscle_TibialisAnterior_smooth.stl")],
}
ADJACENCY = {
    "pelvis": {"sacrum", "femur"},
    "sacrum": {"pelvis"},
    "femur": {"pelvis", "patella", "tibia", "fibula"},
    "patella": {"femur", "tibia"},
    "tibia": {"femur", "patella", "fibula", "talus"},
    "fibula": {"tibia", "talus"},
    "talus": {"tibia", "fibula", "calcaneus", "navicular"},
    "calcaneus": {"talus", "cuboid"},
    "cuboid": {"calcaneus", "lateral_cuneiform"},
    "navicular": {"talus", "medial_cuneiform", "intermediate_cuneiform"},
    "medial_cuneiform": {"navicular", "intermediate_cuneiform"},
    "intermediate_cuneiform": {"navicular", "medial_cuneiform", "lateral_cuneiform"},
    "lateral_cuneiform": {"cuboid", "intermediate_cuneiform"},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_catalog() -> list[dict[str, str]]:
    with CATALOG.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


CATALOG_ROWS = load_catalog()


def resolve_bp3d(fma: str, side: str) -> tuple[dict[str, str], Path]:
    rows = [r for r in CATALOG_ROWS if r["fma"] == fma and r["lateralidade"] == side]
    rows = [r for r in rows if (BP3D_DIR / f"{r['arquivo']}.obj").is_file()]
    if len(rows) != 1:
        raise RuntimeError(f"Esperada uma malha BP3D para {fma}/{side}; encontrei {len(rows)}")
    return rows[0], BP3D_DIR / f"{rows[0]['arquivo']}.obj"


def load_mesh(path: Path, *, denver: bool = False) -> trimesh.Trimesh:
    if "_Muscle_" in str(path):
        raise AssertionError(f"ADAPTAÇÃO BLOQUEADA: nenhum caminho *_Muscle_* pode ser aberto: {path}")
    if denver:
        if "_Bone_" not in str(path):
            raise AssertionError(f"ADAPTAÇÃO BLOQUEADA: STL Denver não ósseo: {path}")
    raw = trimesh.load(path, force="mesh", process=False)
    if isinstance(raw, trimesh.Scene):
        raw = trimesh.util.concatenate(tuple(raw.geometry.values()))
    if not isinstance(raw, trimesh.Trimesh) or not len(raw.faces):
        raise RuntimeError(f"Malha vazia/inválida: {path}")
    return raw


def sample_surface(mesh: trimesh.Trimesh, count: int, seed: int) -> np.ndarray:
    pts, _ = trimesh.sample.sample_surface(mesh, count, seed=seed)
    return np.asarray(pts, dtype=np.float64)


def nearest_similarity(source: dict[str, np.ndarray], target: dict[str, np.ndarray],
                       rotation: np.ndarray, scale: float, translation: np.ndarray,
                       iterations: int = 45) -> tuple[float, float, np.ndarray, np.ndarray, int]:
    src = {k: v.copy() for k, v in source.items()}
    tgt_tree = {k: cKDTree(v) for k, v in target.items()}
    converged = 0
    for it in range(iterations):
        xs, ys, ds = [], [], []
        for key in ALIGN_BONES:
            moved = scale * (src[key] @ rotation) + translation
            distances, idx = tgt_tree[key].query(moved, k=1, workers=-1)
            xs.append(src[key])
            ys.append(target[key][idx])
            ds.append(distances)
        x = np.vstack(xs)
        y = np.vstack(ys)
        dist = np.concatenate(ds)
        keep = dist <= np.quantile(dist, 0.88)
        x, y = x[keep], y[keep]
        xc, yc = x.mean(axis=0), y.mean(axis=0)
        x0, y0 = x - xc, y - yc
        u, singular, vt = np.linalg.svd(x0.T @ y0)
        r = u @ vt
        if np.linalg.det(r) < 0:
            u[:, -1] *= -1
            r = u @ vt
        s = float(singular.sum() / np.square(x0).sum())
        t = yc - s * (xc @ r)
        delta = abs(s - scale) + np.linalg.norm(t - translation) / max(np.linalg.norm(translation), 1.0) + np.linalg.norm(r - rotation)
        scale, translation, rotation = s, t, r
        if delta < 1e-7:
            converged = it + 1
            break
    final = []
    for key in ALIGN_BONES:
        moved = scale * (src[key] @ rotation) + translation
        final.append(tgt_tree[key].query(moved, workers=-1)[0])
    score = float(np.mean(np.concatenate(final)))
    return score, scale, rotation, translation, converged or iterations


def proper_axis_rotations() -> list[np.ndarray]:
    rotations: list[np.ndarray] = []
    for perm in itertools.permutations(range(3)):
        p = np.eye(3)[:, perm]
        for signs in itertools.product((-1.0, 1.0), repeat=3):
            r = p @ np.diag(signs)
            if np.linalg.det(r) > 0.5:
                rotations.append(r)
    return rotations


def fit_similarity(source_meshes: dict[str, trimesh.Trimesh], target_meshes: dict[str, trimesh.Trimesh]) -> dict:
    source = {k: sample_surface(source_meshes[k], SCALE_SAMPLE_N, SEED + i) for i, k in enumerate(ALIGN_BONES)}
    target = {k: sample_surface(target_meshes[k], SCALE_SAMPLE_N * 2, SEED + 100 + i) for i, k in enumerate(ALIGN_BONES)}
    src_all, tgt_all = np.vstack(list(source.values())), np.vstack(list(target.values()))
    src_center, tgt_center = src_all.mean(0), tgt_all.mean(0)
    scale0 = float(np.sqrt(np.mean(np.sum((tgt_all - tgt_center) ** 2, axis=1)) /
                           np.mean(np.sum((src_all - src_center) ** 2, axis=1))))
    candidates = []
    for r0 in proper_axis_rotations():
        t0 = tgt_center - scale0 * (src_center @ r0)
        score, scale, r, t, niter = nearest_similarity(source, target, r0, scale0, t0)
        candidates.append((score, scale, r, t, niter))
    candidates.sort(key=lambda v: v[0])
    score, scale, rotation, translation, niter = candidates[0]
    if not 0.50 < scale < 1.50:
        raise RuntimeError(f"Escala ICP inesperada ({scale:.4f}); revisar unidade/alinhamento")
    if np.linalg.det(rotation) < 0.999:
        raise RuntimeError("ICP resultou em reflexão; proibido no alinhamento por similaridade")
    matrix = np.eye(4)
    matrix[:3, :3] = scale * rotation.T
    matrix[:3, 3] = translation
    return {"score_mean_nn_mm": score, "scale": scale, "rotation_row": rotation.tolist(),
            "translation_mm": translation.tolist(), "matrix_source_column_4x4": matrix.tolist(),
            "iterations": niter, "proper_axis_starts": len(candidates),
            "fit_scores_best_5_mm": [float(v[0]) for v in candidates[:5]]}


class SurfaceProjector:
    """Nearest triangle among 64 nearest triangle centroids, exact point-triangle distance."""

    def __init__(self, mesh: trimesh.Trimesh):
        self.triangles = np.asarray(mesh.triangles, dtype=np.float64)
        self.tree = cKDTree(self.triangles.mean(axis=1))

    def project(self, points: np.ndarray, k: int = 64) -> tuple[np.ndarray, np.ndarray]:
        points = np.asarray(points, dtype=np.float64)
        if not len(points):
            return points.copy(), np.zeros(0, dtype=np.float64)
        k = min(k, len(self.triangles))
        _, face_ids = self.tree.query(points, k=k, workers=-1)
        if k == 1:
            face_ids = face_ids[:, None]
        n, kk = face_ids.shape
        candidates = self.triangles[face_ids.reshape(-1)]
        repeated = np.repeat(points, kk, axis=0)
        closest = trimesh.triangles.closest_point(candidates, repeated).reshape(n, kk, 3)
        distances = np.linalg.norm(closest - points[:, None, :], axis=2)
        best = np.argmin(distances, axis=1)
        rows = np.arange(n)
        return closest[rows, best], distances[rows, best]


def source_insertions(muscle: trimesh.Trimesh, bone_meshes: dict[str, trimesh.Trimesh]) -> tuple[dict[str, np.ndarray], np.ndarray]:
    vertices = np.asarray(muscle.vertices, dtype=np.float64)
    nearest_name = np.full(len(vertices), "", dtype=object)
    nearest_dist = np.full(len(vertices), np.inf)
    for name, bone in bone_meshes.items():
        projected, distances = SurfaceProjector(bone).project(vertices)
        better = distances < nearest_dist
        nearest_dist[better] = distances[better]
        nearest_name[better] = name
    labels = {name: np.flatnonzero((nearest_name == name) & (nearest_dist <= 3.0)) for name in bone_meshes}
    return labels, nearest_dist


def adjacency_from_faces(mesh: trimesh.Trimesh) -> list[np.ndarray]:
    faces = np.asarray(mesh.faces, dtype=np.int64)
    edges = np.vstack((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    edges = np.vstack((edges, edges[:, ::-1]))
    adjacency: list[set[int]] = [set() for _ in range(len(mesh.vertices))]
    for a, b in edges:
        adjacency[int(a)].add(int(b))
    return [np.fromiter(v, dtype=np.int64) if v else np.zeros(0, dtype=np.int64) for v in adjacency]


def laplacian_relax(vertices: np.ndarray, mesh: trimesh.Trimesh, fixed: np.ndarray,
                    iterations: int = 12, factor: float = 0.22) -> np.ndarray:
    result = vertices.copy()
    free = np.ones(len(result), dtype=bool)
    free[fixed] = False
    adjacency = adjacency_from_faces(mesh)
    for _ in range(iterations):
        updated = result.copy()
        for i in np.flatnonzero(free):
            nei = adjacency[i]
            if len(nei):
                updated[i] += factor * (result[nei].mean(axis=0) - result[i])
        result = updated
    return result


def transform_points(points: np.ndarray, fit: dict) -> np.ndarray:
    r = np.asarray(fit["rotation_row"], dtype=np.float64)
    s = float(fit["scale"])
    t = np.asarray(fit["translation_mm"], dtype=np.float64)
    return s * (points @ r) + t


def output_name(group: str, component: int, method: str) -> str:
    suffix = "" if len(MUSCLE_GROUPS[group]) == 1 else ("_long" if component == 0 else "_short")
    return f"{method}_{group}{suffix}.ply"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bp3d_rows: dict[str, dict] = {}
    source_bones: dict[str, trimesh.Trimesh] = {}
    target_bones: dict[str, trimesh.Trimesh] = {}
    bone_meta: dict[str, dict] = {}
    read_denver: list[str] = []

    for name, (fma, side, denver_file) in BONE_MAP.items():
        row, bp_path = resolve_bp3d(fma, side)
        bp3d_rows[name] = row
        source_bones[name] = load_mesh(bp_path)
        denver_path = DENVER_DIR / denver_file
        # Guard executes before trimesh opens any Denver input path.
        target_bones[name] = load_mesh(denver_path, denver=True)
        read_denver.append(str(denver_path))
        bone_meta[name] = {"fma": fma, "bp3d_file": row["arquivo"], "bp3d_name": row["nome_en"],
                           "bp3d_vertices": len(source_bones[name].vertices), "bp3d_faces": len(source_bones[name].faces),
                           "bp3d_bounds_mm_assumed": source_bones[name].bounds.tolist(),
                           "denver_file": denver_file, "denver_vertices": len(target_bones[name].vertices),
                           "denver_faces": len(target_bones[name].faces),
                           "denver_bounds_mm_assumed": target_bones[name].bounds.tolist(),
                           "denver_watertight": bool(target_bones[name].is_watertight)}

    if any("_Muscle_" in p for p in read_denver):
        raise AssertionError("ADAPTAÇÃO BLOQUEADA: lista de leituras Denver contém músculo")
    # Coordinate sanity check: Z is expected to increase from tibia to hip;
    # source and target frame handedness is preserved by proper rotations only.
    z_order = {
        "bp3d_hip_gt_tibia": bool(source_bones["pelvis"].centroid[2] > source_bones["tibia"].centroid[2]),
        "denver_hip_gt_tibia": bool(target_bones["pelvis"].centroid[2] > target_bones["tibia"].centroid[2]),
    }
    if not all(z_order.values()):
        raise RuntimeError(f"Sanidade de eixos/unidades falhou: {z_order}")

    fit = fit_similarity(source_bones, target_bones)
    align_diagnostic = {}
    for name in ALIGN_BONES:
        src_pts = sample_surface(source_bones[name], 3000, SEED + 300 + list(ALIGN_BONES).index(name))
        dst_pts = sample_surface(target_bones[name], 10000, SEED + 400 + list(ALIGN_BONES).index(name))
        moved = transform_points(src_pts, fit)
        d = cKDTree(dst_pts).query(moved, workers=-1)[0]
        align_diagnostic[name] = {"mean_mm": float(d.mean()), "p95_mm": float(np.quantile(d, 0.95))}

    insertion_rows: list[dict[str, str | int | float]] = []
    insertion_index_map: dict[str, dict[str, list[int]]] = {}
    output_records: list[dict] = []
    source_muscle_rows: dict[tuple[str, int], dict[str, str]] = {}
    for group, components in MUSCLE_GROUPS.items():
        for component, (fma, _denver_file) in enumerate(components):
            row, path = resolve_bp3d(fma, "left")
            source_muscle_rows[(group, component)] = row
            muscle = load_mesh(path)
            labels, all_dist = source_insertions(muscle, source_bones)
            attached = [name for name, ids in labels.items() if len(ids)]
            fallback = False
            if not attached:
                # Minimal method fallback where no source vertex is <=3 mm from
                # any mapped bone: anchor to nearest bone(s), and record DESVIO.
                fallback = True
                center = muscle.centroid
                nearest = min(source_bones, key=lambda n: float(SurfaceProjector(source_bones[n]).project(center[None, :])[1][0]))
                attached = [nearest]
                ids = np.argsort(all_dist)[:max(1, min(12, len(muscle.vertices)))]
                labels[nearest] = np.unique(np.concatenate((labels[nearest], ids)))

            insertion_index_map[f"{group}:{component}"] = {
                bone_name: [int(v) for v in ids]
                for bone_name, ids in labels.items() if len(ids)
            }

            for bone_name, ids in labels.items():
                if not len(ids):
                    continue
                insertion_rows.append({
                    "grupo_muscular": group, "componente": "longa" if group == "biceps_femoris" and component == 0 else
                    ("curta" if group == "biceps_femoris" else "unico"),
                    "fma_musculo": fma, "malha_bp3d": row["arquivo"], "nome_bp3d": row["nome_en"],
                    "osso_bp3d": bone_name, "fma_osso": BONE_MAP[bone_name][0],
                    "vertices_insercao": int(len(ids)), "vertices_musculo": int(len(muscle.vertices)),
                    "fracao_vertices": float(len(ids) / len(muscle.vertices)),
                    "distancia_max_bp3d_mm": float(all_dist[ids].max()) if len(ids) else "",
                    "fonte_literatura": "Gray's Anatomy, 42ª ed., capítulo/página: a conferir",
                    "estado_conferencia_literatura": "a conferir",
                    "desvio_fallback": "DESVIO: nenhuma inserção <=3 mm; usados 12 vértices mais próximos do osso âncora" if fallback else "",
                })

            selected = set(attached)
            for bone_name in list(selected):
                selected.update(ADJACENCY.get(bone_name, set()))
            selected = [name for name in BONE_MAP if name in selected]
            # Build a local TPS displacement field from corresponding surfaces.
            x_list, displacement_list = [], []
            for bi, bone_name in enumerate(selected):
                src_pts = sample_surface(source_bones[bone_name], 420, SEED + 500 + bi + component * 23)
                base_pts = transform_points(src_pts, fit)
                projected, _ = SurfaceProjector(target_bones[bone_name]).project(base_pts)
                residual = projected - base_pts
                x_list.append(src_pts)
                displacement_list.append(residual)
            rbf_x = np.vstack(x_list)
            rbf_d = np.vstack(displacement_list)
            rbf = RBFInterpolator(rbf_x, rbf_d, kernel="thin_plate_spline", smoothing=2.0,
                                  neighbors=min(48, len(rbf_x)))

            src_vertices = np.asarray(muscle.vertices, dtype=np.float64)
            base_vertices = transform_points(src_vertices, fit)
            m_vertices = base_vertices + rbf(src_vertices)
            fixed = np.unique(np.concatenate([labels[name] for name in attached if len(labels[name])])).astype(np.int64)
            for bone_name in attached:
                ids = labels[bone_name]
                if len(ids):
                    projector = SurfaceProjector(target_bones[bone_name])
                    projected, _ = projector.project(m_vertices[ids])
                    m_vertices[ids] = projected
            m_vertices = laplacian_relax(m_vertices, muscle, fixed, iterations=12, factor=0.22)

            for method, verts in (("B0", base_vertices), ("M", m_vertices)):
                mesh = trimesh.Trimesh(vertices=verts, faces=muscle.faces.copy(), process=False)
                name_out = output_name(group, component, method)
                dest = OUT / name_out
                mesh.export(dest)
                output_records.append({"arquivo": name_out, "metodo": method, "grupo": group,
                                       "componente": component, "fma": fma,
                                       "vertices": len(mesh.vertices), "faces": len(mesh.faces),
                                       "watertight": bool(mesh.is_watertight),
                                       "sha256": sha256(dest)})
            # Output payload is intentionally frozen before evaluator loads any
            # *_Muscle_* Denver path.

    with (OUT / "insercoes.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        fields = list(insertion_rows[0]) if insertion_rows else []
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(insertion_rows)
    (OUT / "insercoes_vertices.json").write_text(
        json.dumps(insertion_index_map, indent=2, ensure_ascii=False), encoding="utf-8")

    versions = {}
    for package in ("numpy", "scipy", "trimesh", "scikit-image"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "não instalado"
    manifest = {
        "experiment": "EXP-0025", "seed": SEED, "status": "malhas congeladas antes da avaliação",
        "input_versions": versions, "units": "mm (inferidos por dimensões anatômicas; cabeçalhos não declaram unidade)",
        "frame_check": {"bp3d_and_denver_z_up": z_order,
                        "orientation_observation": "centros relativos de osso esquerdo indicam inversão dos eixos x/y entre catálogos; ICP testa rotações próprias, sem reflexão",
                        "rotation_determinant": float(np.linalg.det(np.asarray(fit["rotation_row"])))},
        "alignment": {**fit, "diagnostic_per_anchor_bone": align_diagnostic,
                      "protocol_anchor_bones": list(ALIGN_BONES),
                      "icp_sampling": {"source_samples_per_bone": SCALE_SAMPLE_N,
                                       "target_samples_per_bone": SCALE_SAMPLE_N * 2,
                                       "trim_quantile": 0.88}},
        "deformation": {"method": "SciPy RBFInterpolator thin_plate_spline residual displacement",
                        "smoothing": 2.0, "neighbors": 48, "bone_surface_samples_per_selected_bone": 420,
                        "insertion_threshold_mm": 3.0, "laplacian_iterations": 12,
                        "laplacian_factor": 0.22,
                        "bones_used": list(BONE_MAP),
                        "biceps_metric_grouping": "cabeças longa/curta preservadas em malhas separadas; métricas do critério agrupam ambas"},
        "denver_files_read_only_bone": read_denver,
        "muscles": {g: [{"fma": fma, "bp3d_file": source_muscle_rows[(g, i)]["arquivo"],
                         "bp3d_name": source_muscle_rows[(g, i)]["nome_en"], "denver_file": denver}
                        for i, (fma, denver) in enumerate(parts)] for g, parts in MUSCLE_GROUPS.items()},
        "adapted_meshes": output_records,
    }
    (OUT / "hashes_adaptadas.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"outputs": len(output_records), "insertions_rows": len(insertion_rows),
                      "alignment_score_mean_nn_mm": fit["score_mean_nn_mm"], "scale": fit["scale"],
                      "rotation_determinant": manifest["frame_check"]["rotation_determinant"],
                      "denver_reads": len(read_denver), "denver_read_contains_muscle": any("_Muscle_" in p for p in read_denver),
                      "versions": versions}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
