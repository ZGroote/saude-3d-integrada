"""Reavalia F1-F4 do EXP-0015 com correções de medição do coordenador.

Distâncias de superfície usam amostragem determinística de pontos e KD-tree,
sem o acelerador rtree opcional. F3 usa pontos internos em grade sólida 5 mm.
"""
from __future__ import annotations

import json
import argparse
from collections import OrderedDict
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "atlas" / "hra-f" / "2.0-1"
OUT = BASE / "avaliacao_F1-F4.json"
SKIN_PITCH = 3.0
F3_PITCH = 2.0
F3_INTERIOR_POINTS = 2000
SURFACE_POINTS = 50000
SEED = 15026


def load(name: str) -> trimesh.Trimesh:
    # STL duplicates each triangle's vertices; weld them before topology checks.
    return trimesh.load_mesh(BASE / f"{name}.stl", process=True)


def surface_samples(mesh: trimesh.Trimesh, count: int, seed: int) -> np.ndarray:
    points, _ = trimesh.sample.sample_surface(mesh, count, seed=seed)
    return np.asarray(points, dtype=np.float64)


def filled_grid(mesh: trimesh.Trimesh, pitch: float):
    vox = mesh.voxelized(pitch=pitch, method="subdivide")
    vox.fill(method="holes")
    return vox


def grid_membership(vox, points: np.ndarray) -> np.ndarray:
    ix = np.asarray(vox.points_to_indices(points), dtype=np.int64)
    solid = np.asarray(vox.matrix)
    valid = np.all((ix >= 0) & (ix < np.asarray(solid.shape)), axis=1)
    result = np.zeros(len(points), dtype=bool)
    q = ix[valid]
    result[valid] = solid[q[:, 0], q[:, 1], q[:, 2]]
    return result


def symmetric_surface_min(a: trimesh.Trimesh, b: trimesh.Trimesh, seed: int,
                          count: int = SURFACE_POINTS) -> dict:
    """Approximate minimum surface gap via dense deterministic surface samples."""
    pa = surface_samples(a, count, seed)
    pb = surface_samples(b, count, seed + 1)
    d_ab, i_ab = cKDTree(pb).query(pa, k=1)
    d_ba, i_ba = cKDTree(pa).query(pb, k=1)
    if d_ab.min() <= d_ba.min():
        idx = int(np.argmin(d_ab))
        return {"distance_mm": float(d_ab[idx]), "point_a_ras_mm": pa[idx].tolist(),
                "point_b_ras_mm": pb[int(i_ab[idx])].tolist(), "sample_count_each_surface": count}
    idx = int(np.argmin(d_ba))
    return {"distance_mm": float(d_ba[idx]), "point_a_ras_mm": pa[int(i_ba[idx])].tolist(),
            "point_b_ras_mm": pb[idx].tolist(), "sample_count_each_surface": count}


def boxes_intersect(a: list, b: list) -> bool:
    aa, ab = np.asarray(a[0]), np.asarray(a[1])
    ba, bb = np.asarray(b[0]), np.asarray(b[1])
    return bool(np.all(aa <= bb) and np.all(ba <= ab))


def f1_containment(mesh_names: list[str], skin: trimesh.Trimesh) -> dict:
    skin_grid = filled_grid(skin, SKIN_PITCH)
    skin_tree = cKDTree(np.asarray(skin.vertices))
    structures = {}
    total_vertices = total_inside = 0
    for index, name in enumerate(mesh_names):
        mesh = load(name)
        vertices = np.asarray(mesh.vertices, dtype=np.float64)
        inside = grid_membership(skin_grid, vertices)
        outside = ~inside
        total_vertices += len(vertices)
        total_inside += int(inside.sum())
        row = {"vertices": len(vertices), "inside_vertices": int(inside.sum()),
               "outside_vertices": int(outside.sum()),
               "inside_fraction": float(inside.mean()) if len(vertices) else None}
        if outside.any():
            out_points = vertices[outside]
            distances, _ = skin_tree.query(out_points, k=1, workers=-1)
            max_index = int(np.argmax(distances))
            row.update({"outside_fraction": float(outside.mean()),
                        "median_outside_distance_to_skin_vertex_mm": float(np.median(distances)),
                        "max_outside_distance_to_skin_vertex_mm": float(distances[max_index]),
                        "max_outside_vertex_ras_mm": out_points[max_index].tolist()})
            structures[name] = row
    aggregate = total_inside / total_vertices if total_vertices else 0.0
    return {"criterion_ge_0_99": aggregate >= 0.99,
            "inside_vertices": total_inside, "total_vertices": total_vertices,
            "aggregate_inside_fraction": aggregate, "skin_watertight": bool(skin.is_watertight),
            "inside_test_voxel_pitch_mm": SKIN_PITCH,
            "outside_distance_method": "nearest indexed skin vertex via cKDTree; reported for vertices classified outside the 3 mm filled skin grid",
            "structures_with_outside_vertices": structures}


def hip_metrics() -> dict:
    result = {}
    for j, side in enumerate(("left", "right")):
        cartilage = load(f"denver__cartilage_femurhead__{side}")
        acetabular_cartilage = load(f"denver__cartilage_pelvisacetabulum__{side}")
        femur = load(f"denver__bone_femur__{side}")
        ts_hip = load(f"total__hip_{side}")
        d_cartilage = symmetric_surface_min(cartilage, ts_hip, SEED + j * 10)
        d_bone = symmetric_surface_min(femur, ts_hip, SEED + j * 10 + 2)
        d_denver_cartilage = symmetric_surface_min(cartilage, acetabular_cartilage, SEED + j * 10 + 4)
        d_denver_bone = symmetric_surface_min(femur, acetabular_cartilage, SEED + j * 10 + 6)
        result[side] = {
            "denver_femur_head_cartilage_to_denver_pelvis_acetabulum_cartilage": d_denver_cartilage,
            "denver_femur_bone_to_denver_pelvis_acetabulum_cartilage": d_denver_bone,
            "denver_femur_head_cartilage_to_total_hip_surface": d_cartilage,
            "denver_femur_bone_to_total_hip_surface": d_bone,
            "denver_cartilage_gap_le_5mm": d_denver_cartilage["distance_mm"] <= 5.0,
            "cartilage_gap_le_5mm": d_cartilage["distance_mm"] <= 5.0,
            "bone_gap_le_5mm": d_bone["distance_mm"] <= 5.0,
            "limitation": "TotalSegmentator hip is a whole hip-bone mask; acetabulum is not separately segmented, so its nearest surface can be a non-acetabular region. Denver PelvisAcetabulum is represented by its dedicated cartilage mesh."
        }
    return result


def rib_metrics() -> dict:
    sides = {}
    vertebra_cache = {}
    for side_index, side in enumerate(("left", "right")):
        rows = []
        for rib_index in range(1, 13):
            rib_name = f"total__rib_{side}_{rib_index}"
            rib_path = BASE / f"{rib_name}.stl"
            if not rib_path.is_file():
                continue
            rib = load(rib_name)
            # The rib head is the proximal surface portion nearest the adjacent
            # vertebral bodies. Sample all rib surface points and report which
            # point supplies the minimum to each candidate T level.
            candidate_levels = [rib_index] if rib_index == 1 else [rib_index - 1, rib_index]
            level_results = []
            for level in candidate_levels:
                vertebra_name = f"total__vertebrae_t{level}"
                if vertebra_name not in vertebra_cache:
                    vertebra_cache[vertebra_name] = load(vertebra_name)
                vertebra = vertebra_cache[vertebra_name]
                gap = symmetric_surface_min(rib, vertebra,
                                            SEED + side_index * 100 + rib_index * 3 + level)
                # End/head support diagnostic: how many sampled rib points lie
                # within 20 mm of vertebral surface samples around this minimum.
                rib_samples = surface_samples(rib, SURFACE_POINTS, SEED + rib_index + side_index * 40)
                spine_samples = surface_samples(vertebra, SURFACE_POINTS, SEED + rib_index + level + 80)
                tree = cKDTree(spine_samples)
                distances = tree.query(rib_samples, k=1, workers=-1)[0]
                proximal = distances <= 20.0
                level_results.append({"vertebra": f"T{level}", **gap,
                                      "rib_surface_samples_within_20mm": int(proximal.sum()),
                                      "rib_surface_sample_fraction_within_20mm": float(proximal.mean()),
                                      "gap_le_5mm": gap["distance_mm"] <= 5.0,
                                      "head_truncation_flag": gap["distance_mm"] > 5.0,
                                      "head_truncation_note": "Gap >5 mm is a possible proximal segmentation truncation, not proof of truncation." if gap["distance_mm"] > 5.0 else None})
            rows.append({"rib": rib_index, "side": side, "candidate_vertebrae": level_results,
                         "minimum_gap_mm": min(x["distance_mm"] for x in level_results)})
        sides[side] = rows
    all_gaps = [v["distance_mm"] for side in sides.values() for rib in side for v in rib["candidate_vertebrae"]]
    return {"method": "50,000 deterministic surface samples per mesh; nearest sampled point between whole rib surface and candidate vertebral body surface. Rib-head proxy is the portion nearest the vertebral surface; reports number of rib samples within 20 mm.",
            "candidate_pairs_le_5mm": sum(v <= 5.0 for v in all_gaps),
            "candidate_pairs_total": len(all_gaps), "sides": sides}


def f3_overlaps(mesh_names: list[str], manifest: dict) -> dict:
    records = {row["name"]: row for row in manifest["meshes"] if row["name"] != "body__skin"}
    names = [n for n in mesh_names if n in records]
    pairs = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]
             if boxes_intersect(records[a]["bounds_ras_mm"], records[b]["bounds_ras_mm"])]
    open_pairs = [(a, b) for a, b in pairs if not records[a]["watertight"] or not records[b]["watertight"]]
    pairs = [(a, b) for a, b in pairs if records[a]["watertight"] and records[b]["watertight"]]
    # Build one deterministic set of 2,000 interior voxel centers per mesh.
    interior_samples = {}
    for index, name in enumerate(names):
        mesh = load(name)
        grid = filled_grid(mesh, F3_PITCH)
        points = np.asarray(grid.points, dtype=np.float64)
        if len(points) > F3_INTERIOR_POINTS:
            rng = np.random.default_rng(SEED + index)
            points = points[rng.choice(len(points), F3_INTERIOR_POINTS, replace=False)]
        interior_samples[name] = points

    # Bounded LRU amortizes repeated target voxelization across nearby bbox pairs.
    cache: OrderedDict[str, object] = OrderedDict()
    def get_grid(name: str):
        if name in cache:
            cache.move_to_end(name)
            return cache[name]
        grid = filled_grid(load(name), F3_PITCH)
        cache[name] = grid
        if len(cache) > 16:
            cache.popitem(last=False)
        return grid

    evaluated = []
    for pair_index, (a, b) in enumerate(pairs, 1):
        ga, gb = get_grid(a), get_grid(b)
        pa, pb = interior_samples[a], interior_samples[b]
        a_in_b = float(grid_membership(gb, pa).mean()) if len(pa) else 0.0
        b_in_a = float(grid_membership(ga, pb).mean()) if len(pb) else 0.0
        if a_in_b > 0 or b_in_a > 0:
            evaluated.append({"a": a, "b": b, "a_interior_fraction_inside_b": a_in_b,
                              "b_interior_fraction_inside_a": b_in_a,
                              "criterion_both_below_0_02": a_in_b < 0.02 and b_in_a < 0.02})
        if pair_index % 100 == 0:
            print(f"F3 {pair_index}/{len(pairs)} bbox pairs; sampled overlaps={len(evaluated)}", flush=True)
    return {"status": "EVALUATED", "method": "axis-aligned bounding-box broad phase; 2,000 random interior voxel centers per structure (2 mm grid); test points against the other filled 2 mm voxel solid.",
            "interior_points_per_structure_max": F3_INTERIOR_POINTS,
            "voxel_pitch_mm": F3_PITCH, "candidate_pairs_bbox_intersect": len(pairs) + len(open_pairs),
            "excluded_pairs_with_open_mesh": [{"a": a, "b": b, "reason": "inside volume is undefined for open mesh"} for a, b in open_pairs],
            "pairs_with_sampled_overlap": len(evaluated), "pairs_over_2pct": sum(not x["criterion_both_below_0_02"] for x in evaluated),
            "overlap_pairs": evaluated}


def f4_laterality(mesh_names: list[str]) -> dict:
    rows = []
    for name in mesh_names:
        side = "left" if name.endswith("_left") else "right" if name.endswith("_right") else None
        if not side:
            continue
        mesh = load(name)
        mean_x = float(np.mean(mesh.vertices[:, 0]))
        # RAS x positive is anatomical Right; negative is Left.
        passed = mean_x < 0 if side == "left" else mean_x > 0
        rows.append({"structure": name, "declared_side": side, "mean_ras_x_mm": mean_x,
                     "matches_ras_laterality": bool(passed)})
    return {"checked": len(rows), "passed": sum(r["matches_ras_laterality"] for r in rows),
            "errors": [r for r in rows if not r["matches_ras_laterality"]]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--f3-only", action="store_true", help="recompute F3 and preserve existing F1/F2/F4")
    parser.add_argument("--f1f2f4-only", action="store_true", help="recompute F1/F2/F4 and preserve existing F3")
    args = parser.parse_args()
    manifest = json.loads((BASE / "manifest.json").read_text(encoding="utf-8-sig"))
    mesh_names = [row["name"] for row in manifest["meshes"] if row["name"] != "body__skin"]
    if args.f3_only:
        report = json.loads(OUT.read_text(encoding="utf-8-sig"))
        report["F3"] = f3_overlaps(mesh_names, manifest)
        report["measurement_correction"]["f3"] = "bbox-intersecting watertight pairs only; 2,000 interior voxel centers per structure on 2 mm grid; open-mesh pairs reported as excluded"
        report["limitations"] = [x for x in report.get("limitations", []) if not x.startswith("F3 interior membership")]
        report["limitations"].append("F3 uses 2 mm voxel solids and 2,000 interior points; pairs involving open meshes are excluded because their interior volume is undefined.")
        OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({"F3": {k: v for k, v in report["F3"].items() if k != "overlap_pairs"}}, indent=2, ensure_ascii=False))
        return
    skin = load("body__skin")
    report = {
        "protocol": "EXP-0015 F1-F4; coordinator-requested measurement correction, acceptance thresholds unchanged",
        "measurement_correction": {"old_measurements_preserved_in_experiment": True,
            "surface_distance": "deterministic sampled surface-to-surface minimum; 50,000 samples each; nearest sampled surface points",
            "f1_outside_distance": "outside vertices measured to nearest indexed skin vertex; outside classification from 3 mm filled skin voxel grid",
            "f3": "bbox-intersecting pairs only; 2,000 interior voxel centers per structure on 5 mm grid"},
        "F1": f1_containment(mesh_names, skin),
        "F2": {"hip": hip_metrics(), "ribs_to_vertebrae": rib_metrics()},
        "F3": (json.loads(OUT.read_text(encoding="utf-8-sig"))["F3"]
               if args.f1f2f4_only else f3_overlaps(mesh_names, manifest)),
        "F4": f4_laterality(mesh_names),
        "limitations": ["Surface minima are dense sampled estimates, not exact continuous triangle-to-triangle distances; the optional rtree accelerator is absent.",
                        "TotalSegmentator hip is not acetabulum-only; nearest hip surface may not be the acetabular surface.",
                        "Rib-head proxy uses the closest region of the complete segmented rib to T(i-1)/T(i); a gap over 5 mm flags possible, not proven, proximal truncation.",
                        "F3 interior membership is voxelized at 5 mm and sampled; small overlaps below this scale may be missed."]}
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"F1_outside_structures": len(report["F1"]["structures_with_outside_vertices"]),
                      "F1_inside_fraction": report["F1"]["aggregate_inside_fraction"],
                      "hip_gaps_mm": {s: {"cartilage": v["denver_femur_head_cartilage_to_total_hip_surface"]["distance_mm"],
                                          "bone": v["denver_femur_bone_to_total_hip_surface"]["distance_mm"]}
                                      for s, v in report["F2"]["hip"].items()},
                      "rib_pairs": report["F2"]["ribs_to_vertebrae"]["candidate_pairs_total"],
                      "F3_candidate_pairs": report["F3"]["candidate_pairs_bbox_intersect"],
                      "F3_overlap_pairs": report["F3"]["pairs_with_sampled_overlap"],
                      "F4": [report["F4"]["passed"], report["F4"]["checked"]],
                      "report": str(OUT)}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
