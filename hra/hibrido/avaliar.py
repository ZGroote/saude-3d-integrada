"""EXP-0016 interface metrics from source RAS-mm STLs and align.py HRA meshes."""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import OrderedDict
from pathlib import Path

import numpy as np
import trimesh
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
STL_BASE = ROOT / "atlas" / "hra-f" / "2.0-1"
HRA_DIR = ROOT / "web" / "public" / "atlas" / "hra-f" / "1.10-1"
VHF_DIR = ROOT / "web" / "public" / "atlas" / "vhf-f" / "0.1-0"
TRANSFORMS = ROOT / "hra" / "alinhar" / "transformacoes.json"
F3_PITCH = 2.0
F3_INTERIOR_POINTS = 2000
F1_PITCH = 3.0
SEED = 15026
HYBRID_F3_RELATION_EXCLUSIONS = {
    frozenset(("denver__bone_sacrum__left", "VH_F_right_uterosacral_ligament")),
}

def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

align = load_module("exp16_align_eval", ROOT / "hra" / "alinhar" / "alinhar.py")
align.HRA_DIR = HRA_DIR
exp15 = load_module("exp16_f3_exclusions", ROOT / "hra" / "vhf" / "avaliar_base.py")

def matrices_for(variant: str) -> dict[str, np.ndarray]:
    stage = json.loads(TRANSFORMS.read_text(encoding="utf-8"))["stage_b"]
    if variant == "A":
        m = np.asarray(stage["similarity"]["matrix_4x4"], dtype=float)
        return {key: m for key in ("head_neck", "thorax", "abdomen_pelvis")}
    return {key: np.asarray(value, dtype=float) for key, value in stage["regional_registration"]["matrices_4x4"].items()}

def region_for(name: str) -> str:
    lower = name.lower()
    if lower.startswith("denver__ligament_"):
        return "abdomen_pelvis"
    groups = {
        "head_neck": ("vertebrae_c", "skull", "mandible", "hyoid"),
        "thorax": ("vertebrae_t", "rib_", "sternum", "costal_cartilage", "clavicula", "scapula", "humerus", "ulna", "radius", "hand", "carpal", "metacarpal"),
        "abdomen_pelvis": ("vertebrae_l", "sacrum", "coccyx", "hip_", "pelvis", "femur", "patella", "tibia", "fibula", "talus", "calcaneous", "calcaneus", "cuboid", "cuneiform", "navicular", "metatarsal", "phalanges"),
    }
    for region, tokens in groups.items():
        if any(token in lower for token in tokens):
            return region
    raise ValueError(f"Região pré-registrada ausente para {name}")

def load_sources(variant: str):
    vhf_index = json.loads((VHF_DIR / "indice.json").read_text(encoding="utf-8"))
    hra_index = json.loads((HRA_DIR / "indice.json").read_text(encoding="utf-8"))
    vrows = [r for r in vhf_index if r["sistema"] in {"esqueletico", "articular"}]
    hrows_all = [r for r in hra_index if r["sistema"] not in {"esqueletico", "articular"}]
    hrows = [r for r in hrows_all if r["sistema"] != "tegumentar"]
    wanted = {r["malha"] for r in hrows_all} | {"VH_F_skin"}
    hmeshes = align.load_hra_meshes(wanted)
    # load_hra_meshes scans the separate skin LOD too; explicitly restore the
    # full indexed HRA skin node from tegumentar.glb for F1.
    hmeshes["VH_F_skin"] = align.load_hra_catalog_mesh("VH_F_skin")
    missing_hra = sorted(wanted - set(hmeshes))
    if missing_hra:
        raise RuntimeError(f"Nós HRA ausentes no GLB fonte: {missing_hra[:12]} ({len(missing_hra)})")
    transforms = matrices_for(variant)
    vmeshes = {}
    for row in vrows:
        name = row["malha"]
        path = STL_BASE / f"{name}.stl"
        mesh = trimesh.load_mesh(path, process=True)
        mesh.apply_transform(transforms[region_for(name)])
        vmeshes[name] = mesh
    return vrows, hrows, hrows_all, vmeshes, hmeshes

def grid_membership(grid, points: np.ndarray):
    ijk = np.asarray(grid.points_to_indices(points), dtype=np.int64)
    solid = np.asarray(grid.matrix, dtype=bool)
    valid = np.all((ijk >= 0) & (ijk < np.asarray(solid.shape)), axis=1)
    result = np.zeros(len(points), dtype=bool)
    q = ijk[valid]
    result[valid] = solid[q[:, 0], q[:, 1], q[:, 2]]
    return result, ijk

def closed_skin_grid(skin: trimesh.Trimesh):
    grid = skin.voxelized(pitch=F1_PITCH, method="subdivide")
    shell = np.asarray(grid.matrix, dtype=bool)
    solid = shell.copy()
    for z in range(solid.shape[2]):
        solid[:, :, z] = ndimage.binary_fill_holes(solid[:, :, z])
    return grid, solid, int(shell.sum()), int(solid.sum())

def f1(vrows, vmeshes, skin):
    grid, solid, shell_n, filled_n = closed_skin_grid(skin)
    # Match query grid after axial filling without mutating source geometry.
    query = trimesh.voxel.VoxelGrid(solid, transform=grid.transform)
    total = inside_total = 0
    escaped = []
    for row in vrows:
        mesh = vmeshes[row["malha"]]
        inside, _ = grid_membership(query, np.asarray(mesh.vertices))
        total += len(inside)
        inside_total += int(inside.sum())
        if not inside.all():
            escaped.append({"malha": row["malha"], "sistema": row["sistema"], "vertices": len(inside),
                            "fora": int((~inside).sum()), "fracao_fora": float((~inside).mean())})
    fraction = inside_total / max(1, total)
    return {"status": "PASSOU" if fraction >= .99 else "REPROVOU", "percentual_dentro": fraction * 100,
            "vertices_total": total, "vertices_dentro": inside_total, "vertices_fora": total-inside_total,
            "pitch_mm": F1_PITCH, "pele_fechada_por_fatia_axial": True,
            "pele_watertight_original": bool(skin.is_watertight), "voxels_casca": shell_n, "voxels_fechados": filled_n,
            "volume_fechado_cm3": filled_n * F1_PITCH**3 / 1000,
            "volume_adicionado_por_fill_cm3": (filled_n-shell_n) * F1_PITCH**3 / 1000,
            "escapes": escaped}

def bbox_intersect(a, b):
    return bool(np.all(a[0] <= b[1]) and np.all(b[0] <= a[1]))

def f3_interface(vrows, hrows, vmeshes, hmeshes):
    # F3 v2 exclusions are imported verbatim; tegumentar is intentionally F1-only.
    excluded = exp15.F3_V2_EXCLUDED_PAIRS | HYBRID_F3_RELATION_EXCLUSIONS
    vnames = [r["malha"] for r in vrows]
    hnames = [r["malha"] for r in hrows]
    mesh_by_name = {**vmeshes, **hmeshes}
    metadata = {name: {"bounds": mesh.bounds, "watertight": bool(mesh.is_watertight),
                       "volume": abs(float(mesh.volume)) if mesh.is_watertight else None}
                for name, mesh in mesh_by_name.items()}
    pairs, open_pairs = [], []
    for a in vnames:
        for b in hnames:
            # The registered cranial-cavity exclusion is total__brain × total__skull.
            # Allen subdivisions are the HRA brain representation, so apply
            # that same registered relation to the skull × Allen equivalents.
            cranial_cavity = a == "total__skull" and b.startswith("Allen_")
            if frozenset((a, b)) in excluded or cranial_cavity or not bbox_intersect(metadata[a]["bounds"], metadata[b]["bounds"]):
                continue
            if not metadata[a]["watertight"] or not metadata[b]["watertight"]:
                open_pairs.append({"a": a, "b": b})
            else:
                pairs.append((a, b))

    grid_cache: OrderedDict[str, object] = OrderedDict()
    samples = {}
    def get_grid(name):
        if name in grid_cache:
            grid_cache.move_to_end(name)
            return grid_cache[name]
        grid = mesh_by_name[name].voxelized(pitch=F3_PITCH, method="subdivide")
        grid.fill(method="holes")
        grid_cache[name] = grid
        if len(grid_cache) > 8:
            grid_cache.popitem(last=False)
        return grid
    def get_samples(name):
        if name not in samples:
            pts = np.asarray(get_grid(name).points, dtype=np.float64)
            if len(pts) > F3_INTERIOR_POINTS:
                stable_offset = sum((index + 1) * ord(char) for index, char in enumerate(name))
                rng = np.random.default_rng(SEED + stable_offset)
                pts = pts[rng.choice(len(pts), F3_INTERIOR_POINTS, replace=False)]
            samples[name] = pts
        return samples[name]
    evaluated = []
    for ix, (a,b) in enumerate(pairs, 1):
        ga, gb = get_grid(a), get_grid(b)
        pa, pb = get_samples(a), get_samples(b)
        a_inside, a_idx = grid_membership(gb, pa)
        b_inside, b_idx = grid_membership(ga, pb)
        frac = max(float(a_inside.mean()), float(b_inside.mean()))
        if not (a_inside.any() or b_inside.any()):
            continue
        depths = []
        for target_name, points, inside, indices, target_grid in ((b,pa,a_inside,a_idx,gb),(a,pb,b_inside,b_idx,ga)):
            if inside.any():
                d = ndimage.distance_transform_edt(np.asarray(target_grid.matrix, dtype=bool)) * F3_PITCH
                q = indices[inside]
                valid = np.all((q >= 0) & (q < np.asarray(d.shape)), axis=1)
                if valid.any(): depths.append(float(d[q[valid,0],q[valid,1],q[valid,2]].max()))
        depth = max(depths, default=0.0)
        vol_a = metadata[a]["volume"] * float(a_inside.mean()) / 1000
        vol_b = metadata[b]["volume"] * float(b_inside.mean()) / 1000
        evaluated.append({"a":a,"b":b,"frac_a_em_b":float(a_inside.mean()),"frac_b_em_a":float(b_inside.mean()),
                          "fracao_maxima":frac,"sobreposicao_media_cm3":(vol_a+vol_b)/2,
                          "profundidade_mm":depth,"volume_a_cm3":vol_a,"volume_b_cm3":vol_b})
        if ix % 100 == 0: print(f"F3 interface {ix}/{len(pairs)}",flush=True)
    over2 = [r for r in evaluated if r["fracao_maxima"] >= .02]
    invasions = [r for r in over2 if r["profundidade_mm"] > 3]
    return {"status":"PASSOU" if not invasions else "REPROVOU", "criterio":"fração >=2% e profundidade >3 mm",
            "exclusoes_f3_v2":"hra/vhf/avaliar_base.py:F3_V2_EXCLUDED_PAIRS", "pele_excluida":True,
            "pares_bbox_fechados":len(pairs),"pares_abertos_ignorados":len(open_pairs),
            "pares_com_sobreposicao_amostrada":len(evaluated),"pares_ge_2pct":len(over2),
            "invasoes_ge_2pct_e_gt_3mm":len(invasions),"invasoes":invasions,
            "top20_volume":sorted(invasions,key=lambda r:r["sobreposicao_media_cm3"],reverse=True)[:20],
            "top20_fracao":sorted(invasions,key=lambda r:r["fracao_maxima"],reverse=True)[:20]}

def f4(vrows, vmeshes):
    totals = {"vhf-f":{"testados":0,"corretos":0,"erros":[]}}
    for row, source, meshes in [(r,"vhf-f",vmeshes) for r in vrows]:
        side=row.get("lateralidade")
        if side not in {"left","right"}: continue
        mesh=meshes[row["malha"]]; mean_x=float(mesh.vertices[:,0].mean())
        ok=mean_x < 0 if side=="left" else mean_x > 0
        totals[source]["testados"]+=1; totals[source]["corretos"]+=int(ok)
        if not ok: totals[source]["erros"].append({"malha":row["malha"],"lado":side,"mean_x_ras_mm":mean_x})
    n=sum(x["testados"] for x in totals.values()); good=sum(x["corretos"] for x in totals.values())
    return {"status":"PASSOU" if good==n else "REPROVOU","testados":n,"corretos":good,"por_fonte":totals,
            "metodo":"sinal do centroide de vértices RAS das estruturas importadas VHF: left x<0, right x>0; HRA existente não é reavaliado"}

def run(variant: str, output: Path):
    vrows,hrows,hrows_all,vmeshes,hmeshes=load_sources(variant)
    result={"rodada":"EXP-0016-R2","variante":variant,"F1":f1(vrows,vmeshes,hmeshes["VH_F_skin"]),
            "F3_interface":f3_interface(vrows,hrows,vmeshes,hmeshes),"F4":f4(vrows,vmeshes),
            "nota":"F2/F3 de mesma fonte herdados do EXP-0015 e não remedidos."}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"variante":variant,"F1":{k:result["F1"][k] for k in ("percentual_dentro","volume_adicionado_por_fill_cm3","status")},
                      "F3":{k:result["F3_interface"][k] for k in ("pares_bbox_fechados","pares_abertos_ignorados","invasoes_ge_2pct_e_gt_3mm","status")},
                      "F4":{k:result["F4"][k] for k in ("testados","corretos","status")},"report":str(output)},ensure_ascii=False,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--variante",choices=("A","B"),required=True);p.add_argument("--saida",type=Path,required=True);a=p.parse_args();run(a.variante,a.saida.resolve())
