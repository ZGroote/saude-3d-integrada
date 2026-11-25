"""Histograma, superfície de osso e busca STL→TC por distância a bordas.

Executar da raiz: python hra/denver/validar_bordas.py
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np
import scipy.ndimage as ndi
import trimesh
from scipy.signal import find_peaks
from skimage.filters import threshold_multiotsu

ROOT = Path(__file__).resolve().parent
STL_ROOT = ROOT / "bruto" / "Final 3D STL Models-stl"
NIFTI = ROOT / "bruto" / "tc_alinhada.nii.gz"
JSON_PATH = ROOT / "transformacao_stl_para_tc.json"
REPORT_PATH = ROOT / "RELATORIO.md"
OLD_SIGNS = (-1, 1, 1)
OLD_OFFSET = (300, -700, 0)
CHUNK = 32
SAMPLE_SEARCH = 500


def mesh_vertices(path: Path) -> np.ndarray:
    return np.asarray(trimesh.load_mesh(path, process=False).vertices, dtype=np.float64)


def sample_even(points: np.ndarray, n: int) -> np.ndarray:
    if len(points) <= n:
        return points
    indices = np.random.default_rng(314159).choice(len(points), size=n, replace=False)
    return points[np.sort(indices)]


def otsu_and_histogram(data: np.ndarray) -> dict:
    rng = np.random.default_rng(20261125)
    n = min(1_500_000, data.size)
    ids = rng.integers(0, data.size, size=n, dtype=np.int64)
    sample = np.asarray(data.reshape(-1)[ids], dtype=np.float32)
    thresholds = threshold_multiotsu(sample, classes=3, nbins=4096).astype(float)
    lo, hi = float(sample.min()), float(sample.max())
    counts, edges = np.histogram(sample, bins=4096, range=(lo, hi))
    centers = (edges[:-1] + edges[1:]) / 2
    # Peak candidates are supplemental diagnostics; Otsu thresholds define
    # the actual air/soft-tissue/bone partition used below.
    smooth = ndi.gaussian_filter1d(counts.astype(float), sigma=2)
    peaks, props = find_peaks(smooth, prominence=max(smooth.max() * 0.0005, 1))
    peak_order = sorted(peaks, key=lambda i: smooth[i], reverse=True)[:12]
    classes = [sample <= thresholds[0],
               (sample > thresholds[0]) & (sample <= thresholds[1]),
               sample > thresholds[1]]
    labels = ("ar/fundo (inclui exterior)", "tecido mole", "osso")
    class_stats = []
    for label, chosen in zip(labels, classes):
        vals = sample[chosen]
        class_stats.append({"label": label, "sample_count": int(len(vals)),
                            "fraction": float(len(vals) / len(sample)),
                            "median": float(np.median(vals)) if len(vals) else None,
                            "p10": float(np.percentile(vals, 10)) if len(vals) else None,
                            "p90": float(np.percentile(vals, 90)) if len(vals) else None})
    peak_info = [{"value": float(centers[i]), "count_smoothed": float(smooth[i])}
                 for i in peak_order]
    class_peak_info = []
    bounds = ((lo, thresholds[0]), (thresholds[0], thresholds[1]), (thresholds[1], hi))
    for label, (lower, upper) in zip(labels, bounds):
        in_class = (centers >= lower) & (centers <= upper)
        local_ids = np.flatnonzero(in_class)
        if len(local_ids):
            peak_id = int(local_ids[np.argmax(smooth[local_ids])])
            class_peak_info.append({"label": label, "peak": float(centers[peak_id]),
                                    "count_smoothed": float(smooth[peak_id])})
    return {"sample_size": int(n), "seed": 20261125, "range": [lo, hi],
            "thresholds": [float(x) for x in thresholds], "classes": class_stats,
            "prominent_histogram_peaks": peak_info, "dominant_peak_by_class": class_peak_info,
            "zero_sample_count": int(np.count_nonzero(sample == 0))}


def build_edge_shell(data: np.ndarray, bone_threshold: float, path: Path) -> np.memmap:
    """Build (bone XOR 3x3x3 erosion), dilated one voxel, in z chunks."""
    shape = data.shape
    out = np.memmap(path, dtype=np.uint8, mode="w+", shape=shape)
    neighborhood = np.ones((3, 3, 3), dtype=bool)
    nz = shape[2]
    for z0 in range(0, nz, CHUNK):
        z1 = min(z0 + CHUNK, nz)
        lo, hi = max(0, z0 - 2), min(nz, z1 + 2)
        mask = np.asarray(data[:, :, lo:hi] > bone_threshold)
        eroded = ndi.binary_erosion(mask, structure=neighborhood, border_value=0)
        edge = mask ^ eroded
        near_edge = ndi.binary_dilation(edge, structure=neighborhood, border_value=0)
        out[:, :, z0:z1] = near_edge[:, :, z0-lo:z1-lo]
        if z0 % (CHUNK * 8) == 0:
            print(f"borda: {z1}/{nz} cortes", flush=True)
    out.flush()
    return out


def edge_fraction(points: np.ndarray, sign_x: int, offset: tuple[float, float, float],
                  inv_affine: np.ndarray, shell: np.ndarray) -> tuple[float, int, int]:
    p = points * np.asarray((sign_x, 1, 1)) + np.asarray(offset)
    q = np.rint((np.c_[p, np.ones(len(p))] @ inv_affine.T)[:, :3]).astype(np.int64)
    valid = np.all((q >= 0) & (q < np.asarray(shell.shape)), axis=1)
    v = q[valid]
    hit = shell[v[:, 0], v[:, 1], v[:, 2]].astype(bool)
    return float(hit.sum() / len(points)), int(valid.sum()), len(points)


def structure_paths() -> list[tuple[str, Path]]:
    result = []
    for side in ("Left", "Right"):
        result.append((f"Femur {side}", next((STL_ROOT / side).glob("*Bone_Femur*.stl"))))
        result.append((f"Pelvis {side}", next((STL_ROOT / side).glob("*Bone_Pelvis*.stl"))))
    return result


def main():
    img = nib.load(str(NIFTI))
    data = np.asanyarray(img.dataobj)
    inv = np.linalg.inv(img.affine)
    histogram = otsu_and_histogram(data)
    threshold_air_soft, threshold_soft_bone = histogram["thresholds"]
    print("limiares Otsu (ar/tecido, tecido/osso)=", histogram["thresholds"], flush=True)
    print("classes=", histogram["classes"], flush=True)
    print("picos=", histogram["prominent_histogram_peaks"], flush=True)

    fd, tmp_name = tempfile.mkstemp(prefix=".borda-tc-", suffix=".tmp", dir=ROOT)
    os.close(fd)
    try:
        shell = build_edge_shell(data, threshold_soft_bone, Path(tmp_name))
        objects = []
        for name, path in structure_paths():
            all_pts = mesh_vertices(path)
            objects.append({"name": name, "file": path.relative_to(STL_ROOT).as_posix(),
                            "all": all_pts, "search": sample_even(all_pts, SAMPLE_SEARCH)})

        def score(sign_x: int, offset: tuple[float, float, float], full=False):
            vals = []
            for obj in objects:
                pts = obj["all"] if full else obj["search"]
                vals.append(edge_fraction(pts, sign_x, offset, inv, shell)[0])
            return float(np.mean(vals)), vals

        # Coarse translation search across the available field of view. The
        # same four anatomical structures and equal macro-weight are used for
        # both X signs, avoiding a femur-only fit.
        xs = range(-1200, 801, 40)
        ys = range(-1200, 1, 40)
        zs = range(-400, 1201, 40)
        coarse_best = {}
        n_candidates = 0
        for sign_x in (-1, 1):
            best = (-1.0, None, None)
            for ox in xs:
                for oy in ys:
                    for oz in zs:
                        val, per_object = score(sign_x, (ox, oy, oz))
                        n_candidates += 1
                        if val > best[0]:
                            best = (val, (ox, oy, oz), per_object)
            coarse_best[sign_x] = best
            print(f"busca coarse X={sign_x}: score={best[0]:.5%}, offset={best[1]}", flush=True)

        refined = []
        for sign_x, (coarse_score, coarse_offset, _) in coarse_best.items():
            bx, by, bz = coarse_offset
            best = (-1.0, None, None)
            for ox in range(bx - 40, bx + 41, 10):
                for oy in range(by - 40, by + 41, 10):
                    for oz in range(bz - 20, bz + 21, 5):
                        val, per_object = score(sign_x, (ox, oy, oz))
                        if val > best[0]:
                            best = (val, (ox, oy, oz), per_object)
            all_score, all_per_object = score(sign_x, best[1], full=True)
            refined.append({"sign_x": sign_x, "score_sample_macro": best[0],
                            "offset_mm": list(best[1]), "per_object_sample": best[2],
                            "score_all_vertex_macro": all_score,
                            "per_object_all_vertices": all_per_object,
                            "coarse_score_sample_macro": coarse_score,
                            "coarse_offset_mm": list(coarse_offset)})
        winner = max(refined, key=lambda r: r["score_all_vertex_macro"])
        best_sign = int(winner["sign_x"])
        best_offset = tuple(float(x) for x in winner["offset_mm"])
        best_macro_full, best_per_object_full = winner["score_all_vertex_macro"], winner["per_object_all_vertices"]
        old_macro_sample, old_per_sample = score(OLD_SIGNS[0], OLD_OFFSET)
        old_macro_full, old_per_full = score(OLD_SIGNS[0], OLD_OFFSET, full=True)

        # Axis-wise perturbation curves through +/-20 mm around the new fit.
        sensitivity = []
        for obj in objects:
            row = {"name": obj["name"], "baseline": edge_fraction(
                obj["all"], best_sign, best_offset, inv, shell)[0], "deltas": []}
            for axis, axis_name in enumerate("XYZ"):
                for delta in (-20, -10, -5, -2, 2, 5, 10, 20):
                    shift = list(best_offset)
                    shift[axis] += delta
                    frac, inside, total = edge_fraction(obj["all"], best_sign, tuple(shift), inv, shell)
                    row["deltas"].append({"axis": axis_name, "delta_mm": delta,
                                          "fraction": frac, "inside_volume": inside,
                                          "vertices": total})
            sensitivity.append(row)

        # Final, all-vertex edge metric for all 28 bones at the pooled transform.
        bone_validation = []
        for path in sorted(STL_ROOT.glob("**/*Bone*.stl")):
            pts = mesh_vertices(path)
            frac, inside, total = edge_fraction(pts, best_sign, best_offset, inv, shell)
            bone_validation.append({"file": path.relative_to(STL_ROOT).as_posix(),
                                    "vertices": total, "inside_volume": inside,
                                    "within_one_voxel_of_bone_edge_fraction": frac})

        result = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        if "validation" in result:
            result["previous_value_threshold_validation"] = result.pop("validation")
            result["previous_value_threshold_validation_note"] = "Legacy raw-value thresholds from prior review; DICOM does not establish HU, so these are not HU validation results."
        result["coordinate_system"] = "RAS mm of the generated NIfTI; empirical affine metadata limitations are documented in RELATORIO.md"
        result["stl_to_ras"] = {"scale": [best_sign, 1, 1], "translation_mm": list(best_offset)}
        result["empirical_status"] = "NOT VALIDATED: edge-shell match is low and not a narrow peak; do not use as accepted anatomical registration; proceed to ICP with TotalSegmentator"
        result["edge_registration"] = {
            "histogram": histogram,
            "bone_threshold": {"definition": "rescaled value > upper 3-class Otsu threshold",
                               "value": threshold_soft_bone},
            "edge_definition": "bone_mask XOR 3x3x3 binary erosion; one-voxel 3x3x3 dilation (26-neighborhood)",
            "search_structures": [{"name": o["name"], "file": o["file"],
                                   "vertices_total": len(o["all"]), "vertices_search_sample": len(o["search"])} for o in objects],
            "search_objective": "macro-average of four per-structure edge-shell fractions; same coarse grid for both X signs",
            "coarse_grid": {"x_mm": [-1200, 800, 40], "y_mm": [-1200, 0, 40], "z_mm": [-400, 1200, 40]},
            "candidate_count": n_candidates,
            "search_by_x_sign": refined,
            "winner": {"scale": [best_sign, 1, 1], "translation_mm": list(best_offset),
                       "sample_macro_fraction": winner["score_sample_macro"],
                       "all_vertex_macro_fraction": best_macro_full,
                       "all_vertex_per_structure": best_per_object_full},
            "prior_empirical_transform": {"scale": list(OLD_SIGNS), "translation_mm": list(OLD_OFFSET),
                                          "sample_macro_fraction": old_macro_sample,
                                          "sample_per_structure": old_per_sample,
                                          "all_vertex_macro_fraction": old_macro_full,
                                          "all_vertex_per_structure": old_per_full},
            "sensitivity_by_structure": sensitivity,
            "all_28_bones": bone_validation,
        }
        JSON_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        text = ["", "## Busca e validação por borda (Otsu multinível)", "",
                f"Amostra uniforme de **{histogram['sample_size']:,} voxels** (seed {histogram['seed']}); Otsu de 3 classes deu limiares **{threshold_air_soft:.3f}** (ar/fundo→tecido mole) e **{threshold_soft_bone:.3f}** (tecido mole→osso). Os valores são intensidades reescaladas; DICOM não declara HU.",
                "", "| Classe Otsu | Fração da amostra | Mediana | P10–P90 |", "|---|---:|---:|---:|"]
        for c in histogram["classes"]:
            text.append(f"| {c['label']} | {c['fraction']:.2%} | {c['median']:.2f} | {c['p10']:.2f}–{c['p90']:.2f} |")
        text += ["", "Pico dominante por classe Otsu (contagens suavizadas): " +
                 "; ".join(f"{p['label']}≈{p['peak']:.1f}" for p in histogram["dominant_peak_by_class"]) +
                 f". Pico amostral em 0: {histogram['zero_sample_count']:,} voxels.",
                 "Picos locais proeminentes: " +
                 ", ".join(f"{p['value']:.1f}" for p in histogram["prominent_histogram_peaks"][:8]) + ".",
                 f"A máscara óssea é `valor > {threshold_soft_bone:.3f}`. Borda = máscara XOR erosão binária 3×3×3; métrica = fração dos vértices cujo voxel arredondado está na borda dilatada por uma vizinhança 3×3×3 (até 1 voxel, 26-conectividade). Pontos fora do volume contam como falha.",
                 "", "### Busca conjunta em fêmures e pelve", "",
                "Busca coarse nos quatro STLs (Left/Right femur e pelvis), peso igual por estrutura, 500 vértices aleatórios determinísticos por estrutura, seguida de refinamento em torno do melhor coarse. Varredura coarse: X −1200…800, Y −1200…0 e Z −400…1200 em 40 mm; ambos sinais de X foram testados. Os dois refinamentos foram comparados usando todos os vértices.",
                "", "| Sinal X | Offset coarse (mm) | Macro coarse | Offset refinado (mm) | Macro refinado (amostra) | Macro refinado (todos vértices) |", "|---:|---|---:|---|---:|---:|"]
        for r in refined:
            text.append(f"| {r['sign_x']:+d} | {tuple(r['coarse_offset_mm'])} | {r['coarse_score_sample_macro']:.3%} | {tuple(r['offset_mm'])} | {r['score_sample_macro']:.3%} | {r['score_all_vertex_macro']:.3%} |")
        text += ["", "Vencedor escolhido pelo macro score de todos os vértices:", "",
                 "| Estrutura | Fração na casca de borda |", "|---|---:|"]
        text += [f"| {o['name']} | {v:.3%} |" for o, v in zip(objects, best_per_object_full)]
        text += [f"| Macro (peso igual) | {best_macro_full:.3%} |", "",
                 f"Transformação candidata atualizada: `x' = {best_sign:+d}·x{best_offset[0]:+g}`, `y' = y{best_offset[1]:+g}`, `z' = z{best_offset[2]:+g}` mm.",
                 "", "### Curva ao variar um eixo por vez", "",
                 "Frações de todos os vértices de cada estrutura no shell da borda; eixos não listados ficam no offset vencedor.",
                 "", "| Estrutura | Base | Eixo | −20 | −10 | −5 | −2 | +2 | +5 | +10 | +20 |", "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for row in sensitivity:
            by_axis = {axis: {d["delta_mm"]: d["fraction"] for d in row["deltas"] if d["axis"] == axis}
                       for axis in "XYZ"}
            for axis in "XYZ":
                vals = by_axis[axis]
                text.append(f"| {row['name']} | {row['baseline']:.3%} | {axis} | " + " | ".join(f"{vals[d]:.3%}" for d in (-20,-10,-5,-2,2,5,10,20)) + " |")
        text += ["", "### Validação final de todos os 28 ossos", "",
                 "| STL | Fração de vértices a até 1 voxel da borda | Dentro do volume |", "|---|---:|---:|"]
        text += [f"| {Path(r['file']).name.removeprefix('VHF_').removesuffix('_smooth.stl')} | {r['within_one_voxel_of_bone_edge_fraction']:.3%} | {r['inside_volume']}/{r['vertices']} |" for r in bone_validation]
        text += ["", f"A transformação anterior `{OLD_SIGNS}, {OLD_OFFSET}` teve macro score por borda de {old_macro_full:.3%} (todos os vértices), contra {best_macro_full:.3%} para o novo candidato.",
                 "", "**Conclusão: não há pico estreito nem registro robusto.** A melhor fração é baixa e a curva é irregular; deslocamentos vizinhos por vezes pontuam mais que o centro. O sinal/offset fica registrado como melhor candidato desta métrica, mas está marcado no JSON como não validado e não deve ser usado como transformação anatômica aceita. Recomendação: plano B por ICP com o TotalSegmentator.",
                 "Limiar, amostragem, busca e resultados completos estão em `transformacao_stl_para_tc.json`.", ""]
        report = REPORT_PATH.read_text(encoding="utf-8")
        marker = "## Busca e validação por borda (Otsu multinível)"
        if marker in report:
            report = report[:report.index(marker)].rstrip() + "\n"
        REPORT_PATH.write_text(report.rstrip() + "\n" + "\n".join(text), encoding="utf-8")

        print("RESULTADO", {"thresholds": histogram["thresholds"], "winner_sign_x": best_sign,
                            "winner_offset": best_offset, "winner_macro": best_macro_full,
                            "old_macro": old_macro_full}, flush=True)
        print("PICOS", histogram["prominent_histogram_peaks"][:12], flush=True)
        print("PELVIS_FEMUR", list(zip([o["name"] for o in objects], best_per_object_full)), flush=True)
        print("SENSITIVITY", sensitivity, flush=True)
        print("BONES", [(r["file"], round(r["within_one_voxel_of_bone_edge_fraction"], 5)) for r in bone_validation], flush=True)
    finally:
        try:
            del shell
        except UnboundLocalError:
            pass
        if os.path.exists(tmp_name):
            os.remove(tmp_name)


if __name__ == "__main__":
    main()
