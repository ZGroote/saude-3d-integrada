"""EXP-0025 rodada 2: métricas R1–R4 e distância Denver→adaptado."""
from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

OUT = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
R1_DIR = OUT.parent
sys.path.insert(0, str(OUT))
import adaptar_r2 as cfg2  # noqa: E402
cfg = cfg2.cfg
cfg.OUT = OUT
SEED = 25022
SURFACE_N = 6000
VOXEL_MM = 1.0

spec = importlib.util.spec_from_file_location("avaliar_r1_helpers", R1_DIR / "avaliar.py")
ev = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.path.insert(0, str(R1_DIR))
spec.loader.exec_module(ev)
ev.OUT = OUT
ev.cfg = cfg


def surface_metrics(adapted, denver, seed: int) -> tuple[float, float, float]:
    pa = cfg.sample_surface(adapted, SURFACE_N, seed)
    pd = cfg.sample_surface(denver, SURFACE_N, seed + 1)
    d_adapted_to_denver = cKDTree(pd).query(pa, workers=-1)[0]
    d_denver_to_adapted = cKDTree(pa).query(pd, workers=-1)[0]
    sym = (float(d_adapted_to_denver.mean()) + float(d_denver_to_adapted.mean())) / 2
    p95 = float(np.quantile(np.concatenate((d_adapted_to_denver, d_denver_to_adapted)), 0.95))
    return sym, p95, float(d_denver_to_adapted.mean())


def main() -> None:
    manifest = json.loads((OUT / "hashes_adaptadas_r2.json").read_text(encoding="utf-8"))
    for record in manifest["adapted_meshes"]:
        path = OUT / record["arquivo"]
        if not path.is_file() or cfg.sha256(path) != record["sha256"]:
            raise RuntimeError(f"Hash ausente/divergente antes da avaliação Denver: {record['arquivo']}")
    if not manifest.get("B0_hashes_verified"):
        raise RuntimeError("Hashes B0 da rodada 1 não foram conferidos")

    insertion_map = json.loads((OUT / "insercoes_vertices_m2b.json").read_text(encoding="utf-8"))
    target_bones = {name: ev.load_mesh(cfg.DENVER_DIR / denver_file)
                    for name, (_fma, _side, denver_file) in cfg.BONE_MAP.items()}
    bone_union = set().union(*(ev.as_tuples(ev.common_voxel_indices(m)[0]) for m in target_bones.values()))

    # Only now, after all adapted SHA-256 checks, read Denver target muscles.
    target_muscles = {
        group: [ev.load_mesh(cfg.DENVER_DIR / denver_file, denver_muscle=True)
                for _fma, denver_file in components]
        for group, components in cfg.MUSCLE_GROUPS.items()
    }
    b0_manifest = {"adapted_meshes": [r for r in manifest["adapted_meshes"] if r["metodo"] == "B0"]}
    methods = ("B0", "M2a", "M2b")
    rows: list[dict] = []
    results: dict[str, dict[str, dict]] = {m: {} for m in methods}
    all_insertions: dict[str, list[np.ndarray]] = {m: [] for m in methods}

    for gi, group in enumerate(cfg.MUSCLE_GROUPS):
        comp_records = ev.group_component_records(b0_manifest, group)
        reference = ev.concatenate(target_muscles[group])
        ref_vox, ref_caps = ev.common_voxel_indices(reference)
        ref_set = ev.as_tuples(ref_vox)
        for method in methods:
            adapted, components = ev.method_meshes_for_group(method, group, comp_records)
            adapted_vox, adapted_caps = ev.common_voxel_indices(adapted)
            adapted_set = ev.as_tuples(adapted_vox)
            intersection = len(adapted_set & ref_set)
            dice = 2 * intersection / (len(adapted_set) + len(ref_set)) if adapted_set or ref_set else float("nan")
            volume_ratio = len(adapted_set) / len(ref_set) if ref_set else float("nan")
            collision = len(adapted_set & bone_union)
            collision_pct = 100 * collision / len(adapted_set) if adapted_set else float("nan")
            method_seed = SEED + gi * 10 + (0 if method == "B0" else 1)
            surf_mean, surf_p95, denver_to_adapted = surface_metrics(adapted, reference, method_seed)
            insertion_d = ev.insertion_distance_values(method, group, comp_records, insertion_map, target_bones)
            all_insertions[method].append(insertion_d)
            rows.append({
                "grupo_muscular": group, "metodo": method,
                "componentes": ";".join(ev.output_component_name(group, i) for i in range(len(components))),
                "vertices_adaptados": sum(len(m.vertices) for m in components),
                "triangulos_adaptados": sum(len(m.faces) for m in components),
                "watertight_adaptado": all(bool(m.is_watertight) for m in components),
                "watertight_denver": all(bool(m.is_watertight) for m in target_muscles[group]),
                "fechamentos_temporarios_adaptado": adapted_caps,
                "fechamentos_temporarios_denver": ref_caps,
                "dist_superficie_simetrica_media_mm": surf_mean,
                "dist_superficie_simetrica_p95_mm": surf_p95,
                "dist_unidirecional_denver_para_adaptado_media_mm": denver_to_adapted,
                "dice_voxel_1mm": dice, "razao_volume_voxel_adaptado_denver": volume_ratio,
                "voxels_adaptado": len(adapted_set), "voxels_denver": len(ref_set),
                "insercoes_vertices_avaliadas": len(insertion_d),
                "dist_insercao_mediana_mm": float(np.median(insertion_d)) if len(insertion_d) else "",
                "dist_insercao_p95_mm": float(np.quantile(insertion_d, .95)) if len(insertion_d) else "",
                "voxels_colisao_ossea": collision, "penetracao_ossea_pct_voxel_1mm": collision_pct,
            })
            results[method][group] = {"mean": surf_mean, "p95": surf_p95, "directed": denver_to_adapted,
                                      "dice": dice, "collision": collision_pct}
            print(f"{group} {method}: simétrica={surf_mean:.3f} mm, Denver→adaptado={denver_to_adapted:.3f} mm")

    with (OUT / "metricas_r2.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)

    verdicts: dict[str, dict] = {}
    for method in ("M2a", "M2b"):
        reductions = {g: (results["B0"][g]["mean"] - results[method][g]["mean"]) / results["B0"][g]["mean"]
                      for g in cfg.MUSCLE_GROUPS}
        r1_count = sum(v >= .20 for v in reductions.values())
        insertion_values = np.concatenate([v for v in all_insertions[method] if len(v)]) if any(len(v) for v in all_insertions[method]) else np.zeros(0)
        r2_median = float(np.median(insertion_values)) if len(insertion_values) else float("nan")
        collisions = [results[method][g]["collision"] for g in cfg.MUSCLE_GROUPS]
        dice_median = float(np.median([results[method][g]["dice"] for g in cfg.MUSCLE_GROUPS]))
        verdicts[method] = {
            "r1_count": r1_count, "r1_reductions": reductions,
            "r2_median_mm": r2_median, "r2_n_vertices": len(insertion_values),
            "r3_max_collision_pct": max(collisions), "r3_groups_below_2pct": sum(x < 2 for x in collisions),
            "r4_dice_median_exploratory": dice_median,
            "R1": "PASSOU" if r1_count >= 8 else "REPROVOU",
            "R2": "PASSOU" if len(insertion_values) and r2_median <= 2 else "REPROVOU",
            "R3": "PASSOU" if all(np.isfinite(x) and x < 2 for x in collisions) else "REPROVOU",
        }
    primary = verdicts["M2b"]
    h25 = "SUSTENTADA" if all(primary[k] == "PASSOU" for k in ("R1", "R2", "R3")) else "REJEITADA" if primary["R1"] == "REPROVOU" else "NÃO SUSTENTADA"
    lines = [
        "EXP-0025 — Rodada 2; critérios originais R1–R4, sem alteração",
        "Seeds/amostragem: avaliação 25022; 6.000 pontos por direção; voxel 1 mm; R1 compara cada variante com B0.",
    ]
    for method in ("M2a", "M2b"):
        v = verdicts[method]
        lines.extend([
            f"{method} (R1–R4): R1 {v['R1']} ({v['r1_count']}/10; reduções %: " + ", ".join(f"{g}={100*x:.1f}" for g, x in v["r1_reductions"].items()) + ")",
            f"{method}: R2 {v['R2']} (mediana={v['r2_median_mm']:.3f} mm; n={v['r2_n_vertices']}); R3 {v['R3']} (máximo={v['r3_max_collision_pct']:.3f}%; grupos <2%={v['r3_groups_below_2pct']}/10); R4 Dice mediano={v['r4_dice_median_exploratory']:.4f} (exploratório).",
        ])
    lines.append(f"Veredito H25 da rodada 2 (decisão exclusiva M2b, R1/R2/R3): {h25}.")
    lines.append("R2 é uma medida de inserções projetadas no osso, portanto parcialmente por construção; R3 é voxelização aproximada a 1 mm com fechamento temporário em memória, como na rodada 1.")
    (OUT / "veredito_r2.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    meta = {"seed": SEED, "surface_samples_each_direction": [SURFACE_N, SURFACE_N], "voxel_pitch_mm": VOXEL_MM,
            "same_sampling_seeds_as_r1": True, "hashes_verified_before_denver_muscles": True,
            "denver_muscle_paths_read_after_hash_verification": [str(cfg.DENVER_DIR / f) for parts in cfg.MUSCLE_GROUPS.values() for _, f in parts],
            "verdicts": verdicts, "H25_decision_uses_only_M2b_R1_R2_R3": h25}
    (OUT / "metricas_meta_r2.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
