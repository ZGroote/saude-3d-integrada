"""EXP-0025 rodada 2: congela B0 e gera M2a/M2b sem ler músculos Denver."""
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.interpolate import RBFInterpolator

OUT = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
R1_DIR = OUT.parent
sys.path.insert(0, str(R1_DIR))
import adaptar as cfg  # noqa: E402

cfg.OUT = OUT
SEED = cfg.SEED


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    r1 = json.loads((R1_DIR / "hashes_adaptadas.json").read_text(encoding="utf-8"))
    r1_by_name = {x["arquivo"]: x for x in r1["adapted_meshes"]}
    adapted_records: list[dict] = []
    for record in r1["adapted_meshes"]:
        if record["metodo"] != "B0":
            continue
        source = R1_DIR / record["arquivo"]
        if cfg.sha256(source) != record["sha256"]:
            raise RuntimeError(f"Hash B0 da rodada 1 divergente: {source.name}")
        dest = OUT / source.name
        shutil.copyfile(source, dest)
        if cfg.sha256(dest) != record["sha256"]:
            raise RuntimeError(f"Cópia B0 não preservou hash: {dest.name}")
        adapted_records.append({**record, "sha256": cfg.sha256(dest), "origem": "rodada1"})
    if len(adapted_records) != 11:
        raise RuntimeError(f"Esperadas 11 malhas B0 da rodada 1; encontrei {len(adapted_records)}")

    source_bones: dict[str, trimesh.Trimesh] = {}
    target_bones: dict[str, trimesh.Trimesh] = {}
    for name, (fma, side, denver_file) in cfg.BONE_MAP.items():
        _row, bp_path = cfg.resolve_bp3d(fma, side)
        source_bones[name] = cfg.load_mesh(bp_path)
        target_bones[name] = cfg.load_mesh(cfg.DENVER_DIR / denver_file, denver=True)
    fit = cfg.fit_similarity(source_bones, target_bones)
    insertion_rows: list[dict] = []
    insertion_map: dict[str, dict[str, list[int]]] = {}
    fractions: dict[str, dict] = {}

    for group, components in cfg.MUSCLE_GROUPS.items():
        group_count = group_total = 0
        for component, (fma, _target_file) in enumerate(components):
            row, source_path = cfg.resolve_bp3d(fma, "left")
            muscle = cfg.load_mesh(source_path)
            vertices = np.asarray(muscle.vertices, dtype=np.float64)
            all_labels, all_dist = cfg.source_insertions(muscle, source_bones)
            # PCA principal axis; terminal bands are 10% of its projected extent
            # at each end. The two bands may overlap only for a degenerate mesh.
            centered = vertices - vertices.mean(axis=0)
            _u, _s, vh = np.linalg.svd(centered, full_matrices=False)
            axis = vh[0]
            projection = centered @ axis
            lo, hi = float(projection.min()), float(projection.max())
            span = hi - lo
            terminal = ((projection <= lo + 0.10 * span) |
                        (projection >= hi - 0.10 * span)) if span > 0 else np.zeros(len(vertices), bool)
            labels = {bone: np.intersect1d(ids, np.flatnonzero(terminal), assume_unique=True)
                      for bone, ids in all_labels.items()}
            original_attached = [bone for bone, ids in all_labels.items() if len(ids)]
            attached = [bone for bone, ids in labels.items() if len(ids)]
            fallback = False
            # A degenerate/no-anchor component still receives the same TPS field;
            # no vertices are declared insertions or projected in M2b.
            tps_bones = attached or original_attached
            if not tps_bones:
                fallback = True
                center_id = int(np.argmin(np.linalg.norm(vertices - vertices.mean(axis=0), axis=1)))
                nearest = min(source_bones, key=lambda n: float(cfg.SurfaceProjector(source_bones[n]).project(vertices[center_id:center_id+1])[1][0]))
                tps_bones = [nearest]
            insertion_map[f"{group}:{component}"] = {
                bone: [int(i) for i in ids] for bone, ids in labels.items() if len(ids)
            }
            n_insert = sum(len(ids) for ids in labels.values())
            group_count += n_insert
            group_total += len(vertices)
            insertion_rows.append({
                "grupo_muscular": group, "componente": "longa" if group == "biceps_femoris" and component == 0 else ("curta" if group == "biceps_femoris" else "unico"),
                "fma_musculo": fma, "malha_bp3d": row["arquivo"], "vertices_musculo": len(vertices),
                "vertices_insercao_m2b": n_insert, "fracao_vertices_insercao_m2b": n_insert / len(vertices),
                "bones_rotulados": ";".join(b for b, ids in labels.items() if len(ids)),
                "comprimento_eixo_pca_mm": span, "fallback_tps_sem_insercao": fallback,
                "fonte_literatura": "Gray's Anatomy, 42ª ed., capítulo/página: a conferir",
            })
            fractions[f"{group}:{component}"] = {"vertices_musculo": len(vertices), "vertices_insercao": n_insert,
                                                  "fracao": n_insert / len(vertices), "fallback_tps": fallback}

            base_vertices = cfg.transform_points(vertices, fit)

            def tps_result(anchor_bones: list[str]) -> np.ndarray:
                selected = set(anchor_bones)
                for bone in list(selected):
                    selected.update(cfg.ADJACENCY.get(bone, set()))
                selected = [name for name in cfg.BONE_MAP if name in selected]
                x_list, d_list = [], []
                for bi, bone in enumerate(selected):
                    src = cfg.sample_surface(source_bones[bone], 420, SEED + 500 + bi + component * 23)
                    base = cfg.transform_points(src, fit)
                    projected, _ = cfg.SurfaceProjector(target_bones[bone]).project(base)
                    x_list.append(src)
                    d_list.append(projected - base)
                rbf = RBFInterpolator(np.vstack(x_list), np.vstack(d_list), kernel="thin_plate_spline",
                                      smoothing=2.0, neighbors=min(48, sum(map(len, x_list))))
                return base_vertices + rbf(vertices)

            # M2a reproduces the original M TPS anchor selection (all <=3 mm
            # source insertions). M2b uses only the terminally filtered anchors.
            m2a = tps_result(original_attached or tps_bones)
            m2b = tps_result(tps_bones)
            fixed_parts = []
            for bone, ids in labels.items():
                if len(ids):
                    projected, _ = cfg.SurfaceProjector(target_bones[bone]).project(m2b[ids])
                    m2b[ids] = projected
                    fixed_parts.append(ids)
            fixed = np.unique(np.concatenate(fixed_parts)).astype(np.int64) if fixed_parts else np.zeros(0, np.int64)
            if len(fixed):
                m2b = cfg.laplacian_relax(m2b, muscle, fixed, iterations=12, factor=0.22)

            for method, out_vertices in (("M2a", m2a), ("M2b", m2b)):
                mesh = trimesh.Trimesh(vertices=out_vertices, faces=muscle.faces.copy(), process=False)
                name_out = cfg.output_name(group, component, method)
                dest = OUT / name_out
                mesh.export(dest)
                adapted_records.append({"arquivo": name_out, "metodo": method, "grupo": group,
                                        "componente": component, "fma": fma, "vertices": len(mesh.vertices),
                                        "faces": len(mesh.faces), "watertight": bool(mesh.is_watertight),
                                        "sha256": cfg.sha256(dest)})

    with (OUT / "insercoes_m2b.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(insertion_rows[0]))
        writer.writeheader(); writer.writerows(insertion_rows)
    (OUT / "insercoes_vertices_m2b.json").write_text(json.dumps(insertion_map, indent=2), encoding="utf-8")
    manifest = {"experiment": "EXP-0025", "round": 2, "seed_adaptacao": SEED,
                "status": "M2a/M2b congeladas; B0 copiado e SHA conferido da rodada 1 antes da avaliação",
                "r1_manifest": "../hashes_adaptadas.json", "B0_hashes_verified": True,
                "source_insertion_rule": "<=3 mm AND PCA projection in either terminal 10% of muscle extent",
                "pca_axis": "first principal component from centered BP3D muscle vertices",
                "m2a": "TPS residual thin-plate spline only; no projection or Laplacian",
                "m2b": "TPS, terminal insertion projection, Laplacian 12 iterations factor 0.22",
                "denver_files_read_only_bone": [str(cfg.DENVER_DIR / f) for _, _, f in cfg.BONE_MAP.values()],
                "insertion_fractions": fractions, "adapted_meshes": adapted_records}
    (OUT / "hashes_adaptadas_r2.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"outputs": len(adapted_records), "insertions": fractions,
                      "denver_muscle_paths_read": False, "B0_hashes_verified": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
