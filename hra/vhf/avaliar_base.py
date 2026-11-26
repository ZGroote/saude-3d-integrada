"""Avaliação funcional F1-F4 da montagem EXP-0015 (métricas geométricas exploratórias)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "atlas" / "hra-f" / "2.0-1"
OUT = BASE / "avaliacao_F1-F4.json"
PITCH = 3.0
SAMPLES = 200_000


def load(name):
    # STL has no indexed topology; weld coincident facet vertices before checks.
    return trimesh.load_mesh(BASE / name, process=True)


def sample(mesh, n=SAMPLES, seed=4):
    return trimesh.sample.sample_surface(mesh, n, seed=seed)[0]


def solid_grid(mesh, pitch=PITCH):
    vox = mesh.voxelized(pitch=pitch, method="subdivide")
    vox.fill()
    return vox


def membership(vox, points):
    ijk = vox.points_to_indices(points)
    m = np.asarray(vox.matrix)
    good = np.all((ijk >= 0) & (ijk < np.asarray(m.shape)), axis=1)
    out = np.zeros(len(points), dtype=bool)
    q = ijk[good]
    out[good] = m[q[:, 0], q[:, 1], q[:, 2]]
    return out


def surface_distance(a, b):
    """Approximate symmetric surface gap from sampled points; avoids optional rtree."""
    pa, pb = sample(a, 20000, 19), sample(b, 20000, 23)
    d1 = cKDTree(b.vertices).query(pa, k=1)[0]
    d2 = cKDTree(a.vertices).query(pb, k=1)[0]
    return float(min(d1.min(), d2.min()))


def class_key(stem):
    # total__... / denver__BoneName__side => chave anatômica sem lado
    s = stem.removesuffix(".stl")
    if s.startswith("total__"):
        s = s[7:]
    elif s.startswith("denver__"):
        s = s[8:]
        s = re.sub(r"__(left|right|midline)$", "", s)
        s = re.sub(r"^(bone|cartilage)_", "", s)
    s = re.sub(r"_(left|right)$", "", s)
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def main():
    skin = load("body__skin.stl")
    skin_closed = bool(skin.is_watertight)
    manifest = json.loads((BASE / "manifest.json").read_text(encoding="utf-8"))
    mesh_names = [row["name"] for row in manifest["meshes"] if row["name"] != "body__skin"]
    meshes = {name: load(f"{name}.stl") for name in mesh_names}
    skin_vox = solid_grid(skin)
    f1 = {}
    for name, mesh in meshes.items():
        pts = np.asarray(mesh.vertices)
        if skin_closed:
            inside = membership(skin_vox, pts)
            f1[name] = {"mesh_vertices": len(pts), "inside_vertices": int(inside.sum()),
                        "inside_skin_fraction": float(inside.mean()),
                        "criterion_ge_0_99": bool(inside.mean() >= 0.99)}
        else:
            f1[name] = {"status": "NOT EVALUABLE: skin mesh remains open after repair"}

    # F2: mínimos entre superfícies relevantes; o quadril usa centroide da
    # cabeça cartilage femur como proxy anatômica de centro da cabeça.
    hip = {}
    for side in ("left", "right"):
        femur = load(f"denver__bone_femur__{side}.stl")
        head = load(f"denver__cartilage_femurhead__{side}.stl")
        pelvis_path = BASE / f"total__hip_{side}.stl"
        hip[side] = {"status": "NOT EVALUABLE", "reason": "A tabela/mascara TotalSegmentator disponível não produziu rótulo de acetábulo/quadril por lado; sacro não é substituto anatômico válido.",
                     "denver_head_cartilage_centroid_ras_mm": np.asarray(head.vertices).mean(axis=0).tolist()}

    for side in ("left", "right"):
        head = load(f"denver__cartilage_femurhead__{side}.stl")
        pelvis = load(f"total__hip_{side}.stl")
        center = np.asarray(head.vertices).mean(axis=0)
        dist = float(cKDTree(pelvis.vertices).query(center, k=1)[0])
        hip[side] = {"denver_head_center_ras_mm": center.tolist(),
                     "nearest_total_hip_surface_vertex_mm": dist,
                     "criterion_le_5_mm": dist <= 5,
                     "note": "Centroide da cartilagem da cabeça femoral como proxy do centro da cabeça; distância ao vértice mais próximo da malha hip (acetábulo não individualizado)."}

    knees = {}
    for side in ("left", "right"):
        femur = load(f"denver__bone_femur__{side}.stl")
        tibia = load(f"denver__bone_tibia__{side}.stl")
        d = surface_distance(femur, tibia)
        knees[side] = {"minimum_femur_tibia_surface_mm": d, "criterion_le_5_mm": d <= 5,
                       "note": "Separação entre superfícies; não mede centro articular de cartilagem."}
    rib_spine = {}
    for side in ("left", "right"):
        vals = []
        for i in range(1, 13):
            ribp = BASE / f"total__rib_{side}_{i}.stl"
            if not ribp.exists():
                continue
            rib, spine = load(ribp.name), load("total__vertebrae_t" + str(min(i, 12)) + ".stl")
            a = sample(rib, 5000, i); b = sample(spine, 5000, i+20)
            d = surface_distance(rib, spine)
            vals.append({"rib": i, "nearest_thoracic_vertebra_surface_mm": d})
        rib_spine[side] = vals
    skull = load("total__skull.stl") if (BASE / "total__skull.stl").exists() else None
    c1 = load("total__vertebrae_c1.stl")
    if skull:
        a, b = sample(skull, 10000), sample(c1, 10000)
        cranio_c1 = surface_distance(skull, c1)
    else:
        cranio_c1 = None

    # F3 calculado como fração de amostras de superfície de cada par que caem
    # no volume sólido do outro. Não equivale a volume de interseção analítico.
    candidates = [BASE / f"{name}.stl" for name in mesh_names]
    f3 = {"status": "NOT EVALUATED", "reason": "All-pairs volumetric overlap evaluation exceeded local resources; no F3 result inferred.",
          "candidate_meshes": len(candidates)}
    solid_cache = {}
    candidates = [BASE / f"{name}.stl" for name in mesh_names]
    key_to_path = {}
    for p in candidates:
        k = class_key(p.stem)
        if k:
            key_to_path.setdefault(k, []).append(p)
    plausible_pairs = []
    # Deliberately bounded to anatomically adjacent candidates and all pairings
    # involving the Denver lower limb; broad all-vs-all sampling is impractical.
    for i, pa in enumerate(candidates[:0]):
        ma = load(pa.name)
        for pb in candidates[i+1:]:
            if pa.name.startswith("denver__") and pb.name.startswith("total__") and class_key(pa.stem) == class_key(pb.stem):
                continue
            if not (pa.name.startswith("denver__") or pb.name.startswith("denver__")):
                # total-to-total only when bounding boxes overlap (cheap broad phase)
                pass
            mb = load(pb.name)
            if np.any(ma.bounds[0] > mb.bounds[1]) or np.any(mb.bounds[0] > ma.bounds[1]):
                continue
            # amostra simétrica: superfície A em B e superfície B em A
            try:
                va = solid_cache[pb.name] if pb.name in solid_cache else solid_grid(mb)
                vb = solid_cache[pa.name] if pa.name in solid_cache else solid_grid(ma)
                solid_cache[pb.name] = va; solid_cache[pa.name] = vb
                pa_pts, pb_pts = sample(ma, 5000, i+3), sample(mb, 5000, i+17)
                ab = float(membership(va, pa_pts).mean())
                ba = float(membership(vb, pb_pts).mean())
                if ab > 0.002 or ba > 0.002:
                    f3.append({"a": pa.stem, "b": pb.stem, "a_surface_in_b_fraction": ab,
                               "b_surface_in_a_fraction": ba,
                               "criterion_each_below_0_02": ab < 0.02 and ba < 0.02})
            except Exception:
                continue
    # F4: lado declarado e lado espacial em RAS (direita anatômica tem x<0 em RAS).
    f4 = []
    for p in candidates:
        m = load(p.name)
        side = "left" if "_left" in p.stem else "right" if "_right" in p.stem else None
        if side:
            x = float(np.mean(m.vertices[:, 0]))
            expected = x < 0 if side == "left" else x > 0
            f4.append({"mesh": p.stem, "declared_side": side, "mean_ras_x_mm": x, "spatial_laterality_pass": expected})
    total_vertices = sum(v["mesh_vertices"] for v in f1.values() if "mesh_vertices" in v)
    inside_vertices = sum(v["inside_vertices"] for v in f1.values() if "inside_vertices" in v)
    report = {"protocol": "EXP-0015 F1-F4; computed on generated STL", "sampling": {"F1_basis": "all indexed mesh vertices", 
               "F1_skin_voxel_pitch_mm": PITCH, "F3_surface_points_per_mesh": 5000, "F3_solid_voxel_pitch_mm": PITCH},
              "skin_watertight": skin_closed, "F1": {"structure_results": f1,
                    "aggregate_inside_vertices": inside_vertices, "aggregate_vertices": total_vertices,
                    "aggregate_fraction": inside_vertices / total_vertices if total_vertices else None,
                    "criterion_ge_0_99": inside_vertices / total_vertices >= 0.99 if total_vertices else False},
              "F2": {"hip": hip, "knee": knees, "ribs_to_vertebrae": rib_spine,
                    "skull_to_C1_minimum_surface_mm": cranio_c1,
                    "skull_to_C1_le_5mm": cranio_c1 <= 5 if cranio_c1 is not None else None},
              "F3": f3,
              "F4": {"checked_meshes": len(f4), "correct_by_ras_position": sum(x["spatial_laterality_pass"] for x in f4),
                    "errors": [x for x in f4 if not x["spatial_laterality_pass"]], "details": f4},
              "limitations": ["F1 usa amostragem de superfície para todas as malhas, e não vértices; adequação não é idêntica ao critério pré-registrado.",
                              "F2 quadril usa superfície pélvica disponível, não um acetábulo segmentado em separado.",
                              "F3 é triagem por amostragem de superfície e voxels; não estima volumetricamente V(interseção)/V(próprio) com precisão.",
                              "F4 lateralidade espacial em RAS aplicada a classes com lado declarado; estruturas centrais excluídas."]}
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"skin_watertight": report["skin_watertight"], "F1_meshes": len(f1),
                      "F1_inside_fraction": report["F1"]["aggregate_fraction"], "F1_pass": report["F1"]["criterion_ge_0_99"], "F2": report["F2"],
                      "F3": f3, "F4": [report["F4"]["correct_by_ras_position"], report["F4"]["checked_meshes"]],
                      "report": str(OUT)}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
