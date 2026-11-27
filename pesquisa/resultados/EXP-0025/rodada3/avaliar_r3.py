"""Avaliação EXP-0025 rodada 3; roda somente após Q-osso e hashes válidos."""
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
sys.path.insert(0, str(R1_DIR))
import adaptar as cfg  # noqa: E402
cfg.OUT = OUT
SEED, SURFACE_N, VOXEL_MM = 25022, 6000, 1.0

spec = importlib.util.spec_from_file_location("avaliar_r1_helpers", R1_DIR / "avaliar.py")
ev = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(ev)
ev.OUT = OUT
ev.cfg = cfg


def surface_metrics(adapted, denver, seed):
    pa = cfg.sample_surface(adapted, SURFACE_N, seed)
    pd = cfg.sample_surface(denver, SURFACE_N, seed + 1)
    da = cKDTree(pd).query(pa, workers=-1)[0]
    dd = cKDTree(pa).query(pd, workers=-1)[0]
    return .5 * (float(da.mean()) + float(dd.mean())), float(np.quantile(np.r_[da, dd], .95)), float(dd.mean())


def main():
    manifest = json.loads((OUT / "hashes_adaptadas_r3.json").read_text(encoding="utf-8"))
    if manifest.get("qosso_pass") is not True or manifest.get("status", "").startswith("INCONCLUSIVA"):
        raise RuntimeError("Q-osso não passou; protocolo proíbe avaliação muscular")
    records = manifest.get("adapted_meshes", [])
    if len(records) != 22:
        raise RuntimeError(f"Esperadas 11 malhas B0 + 11 M3; encontrei {len(records)}")
    for record in records:
        path = OUT / record["arquivo"]
        if not path.is_file() or cfg.sha256(path) != record["sha256"]:
            raise RuntimeError(f"Hash ausente/divergente antes de ler músculo Denver: {record['arquivo']}")

    insertion_map = json.loads((OUT / "insercoes_vertices_m3.json").read_text(encoding="utf-8"))
    bones = {name: ev.load_mesh(cfg.DENVER_DIR / file)
             for name, (_fma, _side, file) in cfg.BONE_MAP.items()}
    bone_union = set().union(*(ev.as_tuples(ev.common_voxel_indices(mesh)[0]) for mesh in bones.values()))
    # First Denver muscle read is strictly after every B0/M3 hash passed.
    target_muscles = {group: [ev.load_mesh(cfg.DENVER_DIR / filename, denver_muscle=True)
                              for _fma, filename in components]
                      for group, components in cfg.MUSCLE_GROUPS.items()}
    b0_manifest = {"adapted_meshes": [r for r in records if r["metodo"] == "B0"]}
    rows, results, insertion_values = [], {}, []
    for gi, group in enumerate(cfg.MUSCLE_GROUPS):
        comp_records = ev.group_component_records(b0_manifest, group)
        ref = ev.concatenate(target_muscles[group])
        ref_vox, ref_caps = ev.common_voxel_indices(ref)
        ref_set = ev.as_tuples(ref_vox)
        group_results = {}
        for method in ("B0", "M3"):
            adapted, components = ev.method_meshes_for_group(method, group, comp_records)
            vox, caps = ev.common_voxel_indices(adapted)
            aset = ev.as_tuples(vox)
            inter = len(aset & ref_set)
            dice = 2*inter/(len(aset)+len(ref_set)) if aset or ref_set else float("nan")
            ratio = len(aset)/len(ref_set) if ref_set else float("nan")
            collisions = len(aset & bone_union)
            collision_pct = 100*collisions/len(aset) if aset else float("nan")
            seed = SEED + gi*10 + (0 if method == "B0" else 1)
            mean, p95, directed = surface_metrics(adapted, ref, seed)
            ins = ev.insertion_distance_values(method, group, comp_records, insertion_map, bones)
            if method == "M3": insertion_values.append(ins)
            rows.append({
                "grupo_muscular":group,"metodo":method,
                "componentes":";".join(ev.output_component_name(group,i) for i in range(len(components))),
                "vertices_adaptados":sum(len(m.vertices) for m in components),
                "triangulos_adaptados":sum(len(m.faces) for m in components),
                "watertight_adaptado":all(bool(m.is_watertight) for m in components),
                "watertight_denver":all(bool(m.is_watertight) for m in target_muscles[group]),
                "fechamentos_temporarios_adaptado":caps,"fechamentos_temporarios_denver":ref_caps,
                "dist_superficie_simetrica_media_mm":mean,"dist_superficie_simetrica_p95_mm":p95,
                "dist_unidirecional_denver_para_adaptado_media_mm":directed,
                "dice_voxel_1mm":dice,"razao_volume_voxel_adaptado_denver":ratio,
                "voxels_adaptado":len(aset),"voxels_denver":len(ref_set),
                "insercoes_vertices_avaliadas":len(ins),
                "dist_insercao_mediana_mm":float(np.median(ins)) if len(ins) else "",
                "dist_insercao_p95_mm":float(np.quantile(ins,.95)) if len(ins) else "",
                "voxels_colisao_ossea":collisions,"penetracao_ossea_pct_voxel_1mm":collision_pct,
            })
            group_results[method]={"mean":mean,"p95":p95,"directed":directed,"dice":dice,"collision":collision_pct}
            print(f"{group} {method}: simétrica={mean:.3f} mm; Denver->adaptado={directed:.3f} mm")
        results[group]=group_results

    with (OUT/"metricas_r3.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    reductions={g:(results[g]["B0"]["mean"]-results[g]["M3"]["mean"])/results[g]["B0"]["mean"] for g in cfg.MUSCLE_GROUPS}
    r1_count=sum(v>=.20 for v in reductions.values())
    all_ins=np.concatenate([v for v in insertion_values if len(v)]) if any(len(v) for v in insertion_values) else np.zeros(0)
    r2med=float(np.median(all_ins)) if len(all_ins) else float("nan")
    collisions=[results[g]["M3"]["collision"] for g in cfg.MUSCLE_GROUPS]
    dice=float(np.median([results[g]["M3"]["dice"] for g in cfg.MUSCLE_GROUPS]))
    r1="PASSOU" if r1_count>=8 else "REPROVOU"
    r2="PASSOU" if len(all_ins) and r2med<=2 else "REPROVOU"
    r3="PASSOU" if all(np.isfinite(x) and x<2 for x in collisions) else "REPROVOU"
    r4="PASSOU" if dice>=.60 else "REPROVOU"
    verdict="REJEITADA" if r1=="REPROVOU" else "SUSTENTADA" if r2=="PASSOU" and r3=="PASSOU" else "NÃO SUSTENTADA"
    lines=["EXP-0025 — Rodada 3; critérios R1–R4 originais",
           f"Q-osso passou nos {len(manifest['qosso'])} ossos; adaptação só prosseguiu após a barreira.",
           f"R1 — redução >=20% em >=8/10: {r1} ({r1_count}/10; "+", ".join(f"{g}={100*v:.1f}%" for g,v in reductions.items())+")",
           f"R2 — inserções mediana <=2 mm: {r2} ({r2med:.3f} mm; n={len(all_ins)})",
           f"R3 — penetração óssea <2% em todos: {r3} (máximo={max(collisions):.3f}%; grupos <2%={sum(x<2 for x in collisions)}/10)",
           f"R4 — Dice mediano >=0,60 (exploratório): {r4} ({dice:.4f})",
           f"Veredito pela regra de parada: H25 {verdict}." if r1=="REPROVOU" else f"Veredito H25: {verdict}.",
           "Denver->adaptado exploratória por músculo está em metricas_r3.csv. R3/R4: voxelização 1 mm com fechamento temporário em memória, mesma aproximação da rodada 1."]
    (OUT/"veredito_r3.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
    meta={"seed":SEED,"surface_samples_each_direction":[6000,6000],"voxel_pitch_mm":VOXEL_MM,
          "same_sampling_seeds_as_r1":True,"qosso_pass":True,"all_adapted_hashes_verified_before_denver_muscles":True,
          "denver_muscle_paths_read_after_hash_verification":[str(cfg.DENVER_DIR/f) for ps in cfg.MUSCLE_GROUPS.values() for _,f in ps],
          "r1_reductions":reductions,"r1_count":r1_count,"r2_insertion_median_mm":r2med,
          "r2_insertion_vertex_count":len(all_ins),"r3_max_collision_percent":max(collisions),"r4_dice_median":dice,
          "verdict":verdict,"stopping_rule":"EXP-0025 encerrado se R1 reprova"}
    (OUT/"metricas_meta_r3.json").write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding="utf-8")
    print("\n".join(lines))


if __name__=="__main__": main()
