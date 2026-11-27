"""EXP-0025 avaliação, chamada somente depois de adaptar.py.

Reprodução: python pesquisa/resultados/EXP-0025/avaliar.py
Pré-condição: hashes_adaptadas.json foi gravado pela adaptação e todas as
malhas B0/M conferem. Só então este script abre os *_Muscle_* Denver.
"""

from __future__ import annotations

import csv
import importlib.metadata
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from scipy.spatial import cKDTree

import adaptar as cfg


OUT = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
DENVER_DIR = ROOT / "hra" / "denver" / "bruto" / "Final 3D STL Models-stl" / "Left"
SEED = 25022
SURFACE_N = 6000
TARGET_SURFACE_N = 6000
VOXEL_MM = 1.0


def load_mesh(path: Path, denver_muscle: bool = False, process: bool = True) -> trimesh.Trimesh:
    if denver_muscle and "_Muscle_" not in str(path):
        raise AssertionError(f"A avaliação deveria ler músculo Denver: {path}")
    # STL stores independent triangle vertices; process=True welds coincident
    # vertices so its topology is recognized for solid voxelization.
    raw = trimesh.load(path, force="mesh", process=process)
    if isinstance(raw, trimesh.Scene):
        raw = trimesh.util.concatenate(tuple(raw.geometry.values()))
    if not isinstance(raw, trimesh.Trimesh) or not len(raw.faces):
        raise RuntimeError(f"Malha vazia/inválida: {path}")
    return raw


def concatenate(meshes: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    if len(meshes) == 1:
        return meshes[0]
    return trimesh.util.concatenate(meshes)


def cap_boundary_loops(mesh: trimesh.Trimesh) -> tuple[trimesh.Trimesh, int]:
    """Cap temporary open boundary loops by centroid fans for volume metrics."""
    mesh = mesh.copy()
    faces = np.asarray(mesh.faces, dtype=np.int64)
    directed = np.vstack((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    undirected = np.sort(directed, axis=1)
    _, inverse, counts = np.unique(undirected, axis=0, return_inverse=True, return_counts=True)
    boundary_directed = directed[counts[inverse] == 1]
    if not len(boundary_directed):
        return mesh, 0
    adjacency: dict[int, set[int]] = {}
    for a, b in boundary_directed:
        adjacency.setdefault(int(a), set()).add(int(b))
        adjacency.setdefault(int(b), set()).add(int(a))
    if any(len(neighbors) != 2 for neighbors in adjacency.values()):
        raise RuntimeError("Limite aberto não é composto por loops simples (grau de contorno diferente de 2)")
    directed_edges = {(int(a), int(b)) for a, b in boundary_directed}
    unused = {tuple(sorted((int(a), int(b)))) for a, b in boundary_directed}
    vertices = np.asarray(mesh.vertices, dtype=np.float64).tolist()
    cap_faces = []
    loops = 0
    while unused:
        first_edge = min(unused)
        start, current = first_edge
        loop = [start, current]
        unused.remove(first_edge)
        previous = start
        while True:
            candidates = adjacency[current] - {previous}
            if len(candidates) != 1:
                raise RuntimeError("Contorno aberto não é simples; fechamento volumétrico não medível")
            nxt = next(iter(candidates))
            edge = tuple(sorted((current, nxt)))
            if nxt == start:
                if edge not in unused:
                    raise RuntimeError("Contorno repetido durante o fechamento")
                unused.remove(edge)
                break
            if edge not in unused:
                raise RuntimeError("Contorno aberto não fecha em ciclo")
            unused.remove(edge)
            loop.append(nxt)
            previous, current = current, nxt
        if len(loop) < 3:
            raise RuntimeError("Contorno com menos de três vértices")
        center_id = len(vertices)
        vertices.append(np.asarray(mesh.vertices)[loop].mean(axis=0).tolist())
        for i, a in enumerate(loop):
            b = loop[(i + 1) % len(loop)]
            # Reverse each existing boundary edge. The original mesh may have
            # inconsistent winding, so use the actual directed edge.
            cap_faces.append([b, a, center_id] if (a, b) in directed_edges else [a, b, center_id])
        loops += 1
    capped = trimesh.Trimesh(vertices=np.asarray(vertices),
                             faces=np.vstack((faces, np.asarray(cap_faces, dtype=np.int64))),
                             process=False)
    if not capped.is_watertight:
        check_edges = np.vstack((capped.faces[:, [0, 1]], capped.faces[:, [1, 2]], capped.faces[:, [2, 0]]))
        _, check_counts = np.unique(np.sort(check_edges, axis=1), axis=0, return_counts=True)
        raise RuntimeError(f"Fechamento temporário por loops não produziu malha fechada; boundary={int(np.sum(check_counts == 1))}, nonmanifold={int(np.sum(check_counts > 2))}")
    return capped, loops


def common_voxel_indices(mesh: trimesh.Trimesh) -> tuple[np.ndarray, int]:
    # M meshes can be open after projecting insertion vertices. For R4/R3 only,
    # add temporary centroid-fan caps; saved B0/M files remain byte-identical.
    closed, cap_count = cap_boundary_loops(mesh)
    # Eight subdivision iterations are enough for the measured meshes and
    # avoid unbounded growth from long BP3D triangles; voxel pitch remains 1mm.
    voxels = closed.voxelized(pitch=VOXEL_MM, method="subdivide", max_iter=8).fill()
    points = np.asarray(voxels.points, dtype=np.float64)
    return np.unique(np.floor(points / VOXEL_MM + 1e-8).astype(np.int32), axis=0), cap_count


def as_tuples(indices: np.ndarray) -> set[tuple[int, int, int]]:
    return set(map(tuple, np.asarray(indices, dtype=np.int32)))


def symmetric_surface_metrics(a: trimesh.Trimesh, b: trimesh.Trimesh,
                              seed: int) -> tuple[float, float]:
    pa = cfg.sample_surface(a, SURFACE_N, seed)
    pb = cfg.sample_surface(b, TARGET_SURFACE_N, seed + 1)
    da = cKDTree(pb).query(pa, workers=-1)[0]
    db = cKDTree(pa).query(pb, workers=-1)[0]
    pooled = np.concatenate((da, db))
    # Equal number of surface samples in each direction; this is the
    # arithmetic mean of source→target and target→source means.
    symmetric_mean = 0.5 * (float(da.mean()) + float(db.mean()))
    return symmetric_mean, float(np.quantile(pooled, 0.95))


def group_component_records(manifest: dict, group: str) -> list[dict]:
    records = [r for r in manifest["adapted_meshes"] if r["grupo"] == group]
    return sorted(records, key=lambda r: int(r["componente"]))


def insertion_distance_values(method: str, group: str, component_records: list[dict],
                              insertion_map: dict, target_bones: dict[str, trimesh.Trimesh]) -> np.ndarray:
    distances = []
    for record in component_records:
        comp_key = f"{group}:{record['componente']}"
        mesh = load_mesh(OUT / f"{method}_{group}{'_long' if group == 'biceps_femoris' and record['componente'] == 0 else ('_short' if group == 'biceps_femoris' else '')}.ply", process=False)
        vertices = np.asarray(mesh.vertices)
        for bone_name, vertex_ids in insertion_map.get(comp_key, {}).items():
            if not vertex_ids:
                continue
            ids = np.asarray(vertex_ids, dtype=np.int64)
            projected, d = cfg.SurfaceProjector(target_bones[bone_name]).project(vertices[ids])
            distances.extend(d.tolist())
    return np.asarray(distances, dtype=np.float64)


def method_meshes_for_group(method: str, group: str, comp_records: list[dict]) -> tuple[trimesh.Trimesh, list[trimesh.Trimesh]]:
    meshes = []
    for record in comp_records:
        path = OUT / record["arquivo"].replace("B0_", f"{method}_", 1)
        meshes.append(load_mesh(path, process=False))
    return concatenate(meshes), meshes


def output_component_name(group: str, index: int) -> str:
    if group != "biceps_femoris":
        return f"{group}"
    return "biceps_femoris_long" if index == 0 else "biceps_femoris_short"


def main() -> None:
    manifest_path = OUT / "hashes_adaptadas.json"
    if not manifest_path.is_file():
        raise RuntimeError("hashes_adaptadas.json ausente; rode adaptar.py primeiro")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Integridade/precondição em primeiro lugar. Nenhuma leitura muscular
    # Denver acontece antes de todos os hashes das malhas adaptadas passarem.
    for record in manifest["adapted_meshes"]:
        path = OUT / record["arquivo"]
        if not path.is_file():
            raise RuntimeError(f"Malha adaptada ausente: {record['arquivo']}")
        actual = cfg.sha256(path)
        if actual != record["sha256"]:
            raise RuntimeError(f"SHA-256 divergente antes da avaliação: {record['arquivo']}")

    insertion_map = json.loads((OUT / "insercoes_vertices.json").read_text(encoding="utf-8"))
    target_bones = {}
    for name, (_, _, denver_file) in cfg.BONE_MAP.items():
        target_bones[name] = load_mesh(cfg.DENVER_DIR / denver_file)
    bone_voxels = [as_tuples(common_voxel_indices(mesh)[0]) for mesh in target_bones.values()]
    bone_union = set().union(*bone_voxels)

    # The Denver target muscles are deliberately loaded only after hash checks.
    target_muscles: dict[str, list[trimesh.Trimesh]] = {}
    for group, components in cfg.MUSCLE_GROUPS.items():
        target_muscles[group] = []
        for _, denver_file in components:
            target_muscles[group].append(load_mesh(DENVER_DIR / denver_file, denver_muscle=True))

    rows = []
    group_results: dict[str, dict] = {}
    all_m_method_insertions = []
    for group_index, group in enumerate(cfg.MUSCLE_GROUPS):
        comp_records = group_component_records(manifest, group)
        reference = concatenate(target_muscles[group])
        reference_vox, reference_caps = common_voxel_indices(reference)
        reference_set = as_tuples(reference_vox)
        group_results[group] = {}
        for method in ("B0", "M"):
            adapted, components = method_meshes_for_group(method, group, comp_records)
            adapted_vox, adapted_caps = common_voxel_indices(adapted)
            adapted_set = as_tuples(adapted_vox)
            intersection = len(adapted_set & reference_set)
            dice = (2.0 * intersection / (len(adapted_set) + len(reference_set))) if (len(adapted_set) + len(reference_set)) else float("nan")
            volume_ratio = len(adapted_set) / len(reference_set) if reference_set else float("nan")
            collision_voxels = len(adapted_set & bone_union)
            collision_pct = 100.0 * collision_voxels / len(adapted_set) if adapted_set else float("nan")
            surface_mean, surface_p95 = symmetric_surface_metrics(adapted, reference, SEED + group_index * 10 + (0 if method == "B0" else 1))
            insertion_d = insertion_distance_values(method, group, comp_records, insertion_map, target_bones)
            if method == "M" and len(insertion_d):
                all_m_method_insertions.append(insertion_d)
            rows.append({
                "grupo_muscular": group, "metodo": method,
                "componentes": ";".join(output_component_name(group, i) for i in range(len(components))),
                "vertices_adaptados": sum(len(m.vertices) for m in components),
                "triangulos_adaptados": sum(len(m.faces) for m in components),
                "watertight_adaptado": all(bool(m.is_watertight) for m in components),
                "watertight_denver": all(bool(m.is_watertight) for m in target_muscles[group]),
                "fechamentos_temporarios_adaptado": adapted_caps,
                "fechamentos_temporarios_denver": reference_caps,
                "dist_superficie_simetrica_media_mm": surface_mean,
                "dist_superficie_simetrica_p95_mm": surface_p95,
                "dice_voxel_1mm": dice,
                "razao_volume_voxel_adaptado_denver": volume_ratio,
                "voxels_adaptado": len(adapted_set), "voxels_denver": len(reference_set),
                "insercoes_vertices_avaliadas": int(len(insertion_d)),
                "dist_insercao_mediana_mm": float(np.median(insertion_d)) if len(insertion_d) else "",
                "dist_insercao_p95_mm": float(np.quantile(insertion_d, 0.95)) if len(insertion_d) else "",
                "voxels_colisao_ossea": collision_voxels,
                "penetracao_ossea_pct_voxel_1mm": collision_pct,
            })
            group_results[group][method] = {"surface_mean": surface_mean, "surface_p95": surface_p95,
                                            "dice": dice, "volume_ratio": volume_ratio,
                                            "collision_pct": collision_pct,
                                            "watertight": bool(adapted.is_watertight)}
            print(f"{group} {method}: mean={surface_mean:.3f} mm; Dice={dice:.4f}; collision={collision_pct:.3f}%")

    fields = list(rows[0])
    with (OUT / "metricas.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    reductions = {}
    for group, result in group_results.items():
        b0 = result["B0"]["surface_mean"]
        method = result["M"]["surface_mean"]
        reduction = (b0 - method) / b0 if b0 > 0 else float("nan")
        reductions[group] = reduction
    r1_count = sum(v >= 0.20 for v in reductions.values())
    r1_status = "PASSOU" if r1_count >= 8 else "REPROVOU"

    insertion_values = np.concatenate(all_m_method_insertions) if all_m_method_insertions else np.zeros(0)
    insertion_median = float(np.median(insertion_values)) if len(insertion_values) else float("nan")
    r2_status = "PASSOU" if len(insertion_values) and insertion_median <= 2.0 else "REPROVOU" if len(insertion_values) else "NÃO MEDIDO"

    m_collisions = [v["M"]["collision_pct"] for v in group_results.values()]
    r3_status = "PASSOU" if all(np.isfinite(v) and v < 2.0 for v in m_collisions) else "REPROVOU"
    m_dice = [v["M"]["dice"] for v in group_results.values()]
    dice_median = float(np.median(m_dice))
    r4_status = "PASSOU" if dice_median >= 0.60 else "REPROVOU"  # exploratório
    if r1_status == "REPROVOU":
        h25 = "REJEITADA (R1 falhou, regra pré-registrada)"
    elif r2_status == "PASSOU" and r3_status == "PASSOU":
        h25 = "SUSTENTADA (R1, R2 e R3 passaram)"
    else:
        h25 = "NÃO SUSTENTADA (R1 passou, mas R2 ou R3 não passou)"

    verdict = [
        "EXP-0025 — veredito pelos critérios pré-registrados",
        f"R1 — redução >=20% em pelo menos 8/10 grupos: {r1_status} ({r1_count}/10; grupos: " +
        ", ".join(f"{g}={100*v:.1f}%" for g, v in reductions.items()) + ")",
        f"R2 — mediana de distância das inserções M <=2 mm: {r2_status} ({insertion_median:.3f} mm; n={len(insertion_values)})",
        f"R3 — colisão M <2% em todos os grupos: {r3_status} (máximo={max(m_collisions):.3f}%)",
        f"R4 — Dice mediano M >=0,60 (exploratório): {r4_status} ({dice_median:.4f})",
        f"H25: {h25}",
        "R3 é estimado por interseção de voxels ocupados a 1 mm entre músculos e união dos ossos Denver mapeados; contato de superfície pode contribuir para voxels de borda.",
        "DESVIO de medição (não de critério): M pode abrir contornos ao projetar inserções. Para Dice/volume/colisão, o avaliador fecha apenas em memória cada ciclo de borda por leque ao centróide antes da voxelização; as malhas salvas não são alteradas. STL Denver é carregado com weld de vértices coincidentes. A voxelização usa subdivide max_iter=8 e pitch=1 mm.",
        "R1 conta o bíceps femoral como um grupo: cabeças longa e curta têm arquivos separados, mas malhas/volumes são unidos para as métricas do grupo.",
    ]
    (OUT / "veredito_R1_R4.txt").write_text("\n".join(verdict) + "\n", encoding="utf-8")

    # Figura: dois grupos, nuvens superficiais B0, M e Denver na mesma vista.
    figure_groups = ("rectus_femoris", "gluteus_medius")
    fig = plt.figure(figsize=(12, 6), constrained_layout=True)
    colors = {"B0": "#2463a6", "M": "#e07a22", "Denver": "#268447"}
    for plot_index, group in enumerate(figure_groups, 1):
        ax = fig.add_subplot(1, 2, plot_index, projection="3d")
        comp_records = group_component_records(manifest, group)
        plot_meshes = {
            "B0": method_meshes_for_group("B0", group, comp_records)[0],
            "M": method_meshes_for_group("M", group, comp_records)[0],
            "Denver": concatenate(target_muscles[group]),
        }
        for sample_index, (label, mesh) in enumerate(plot_meshes.items()):
            points = cfg.sample_surface(mesh, 2200, SEED + 900 + plot_index * 10 + sample_index)
            ax.scatter(points[:, 0], points[:, 1], points[:, 2], s=1.1, alpha=0.32,
                       color=colors[label], label=label, depthshade=False)
        ax.set_title(group.replace("_", " "))
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("y (mm)")
        ax.set_zlabel("z (mm)")
        ax.view_init(elev=16, azim=35)
        ax.legend(loc="upper left", fontsize=8)
    fig.suptitle("EXP-0025 — B0, método M e referência Denver (superfícies amostradas)")
    fig.savefig(OUT / "comparacao_B0_M_Denver.png", dpi=180)
    plt.close(fig)

    versions = {}
    for package in ("numpy", "scipy", "trimesh", "scikit-image", "matplotlib"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "não instalado"
    eval_meta = {
        "seed": SEED, "versions": versions, "surface_samples_each_direction": [SURFACE_N, TARGET_SURFACE_N],
        "voxel_pitch_mm": VOXEL_MM,
        "voxelizer": "trimesh subdivide, max_iter=8, fill; temporary centroid fan caps for boundary loops only in measurement",
        "collision_definition": "overlap of filled 1 mm voxel occupancy of adapted muscle and union of mapped Denver bones",
        "denver_muscle_files_read_after_hash_verification": [
            str(DENVER_DIR / denver_file) for components in cfg.MUSCLE_GROUPS.values()
            for _, denver_file in components],
        "all_adapted_hashes_verified_before_denver_muscles": True,
        "r1_reductions": reductions, "r1_count": r1_count,
        "r2_insertion_median_mm": insertion_median, "r2_insertion_vertex_count": int(len(insertion_values)),
        "r3_max_collision_percent": float(max(m_collisions)), "r4_dice_median": dice_median,
        "verdict": h25,
    }
    (OUT / "metricas_meta.json").write_text(json.dumps(eval_meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n".join(verdict))


if __name__ == "__main__":
    main()
