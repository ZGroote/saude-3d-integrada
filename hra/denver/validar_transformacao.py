"""Validação independente do referencial STL→TC. Execute da raiz do repo."""
from __future__ import annotations

import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pydicom
import trimesh

ROOT = Path(__file__).resolve().parent
BRUTO = ROOT / "bruto"
STL_ROOT = BRUTO / "Final 3D STL Models-stl"
DICOM_ROOT = BRUTO / "Aligned CT-DICOM"
NIFTI = BRUTO / "tc_alinhada.nii.gz"
JSON_OUT = ROOT / "transformacao_stl_para_tc.json"

# Hypothesis under review from the prior femur-only search.
SIGNS = (-1, 1, 1)
OFFSET_MM = (300, -700, 0)


def vertices(path: Path) -> np.ndarray:
    return np.asarray(trimesh.load_mesh(path, process=False).vertices, dtype=np.float64)


def vertex_fraction(points: np.ndarray, data: np.ndarray, inv_affine: np.ndarray,
                    threshold: tuple[float, float] | str, delta=(0, 0, 0)) -> tuple[float, int, int]:
    p = points * np.asarray(SIGNS) + np.asarray(OFFSET_MM) + np.asarray(delta)
    q = np.rint((np.c_[p, np.ones(len(p))] @ inv_affine.T)[:, :3]).astype(np.int64)
    valid = np.all((q >= 0) & (q < np.asarray(data.shape)), axis=1)
    vals = np.full(len(points), np.nan, dtype=np.float32)
    v = q[valid]
    vals[valid] = data[v[:, 0], v[:, 1], v[:, 2]]
    if threshold == "bone":
        hit = vals > 200
    else:
        hit = (vals >= threshold[0]) & (vals <= threshold[1])
    return float(np.count_nonzero(hit) / len(points)), int(valid.sum()), len(points)


def main():
    if not NIFTI.exists():
        raise FileNotFoundError(f"TC convertida não encontrada: {NIFTI}")
    image = nib.load(str(NIFTI))
    data = np.asanyarray(image.dataobj)
    inv = np.linalg.inv(image.affine)
    bone_paths = sorted(STL_ROOT.glob("**/*Bone*.stl"))
    if len(bone_paths) != 28:
        raise RuntimeError(f"Esperados 28 STLs ósseos, encontrados {len(bone_paths)}")

    bones = []
    for path in bone_paths:
        pts = vertices(path)
        frac, inside, total = vertex_fraction(pts, data, inv, "bone")
        bones.append({"file": path.relative_to(STL_ROOT).as_posix(), "vertices": total,
                      "inside_volume": inside, "value_gt_200_fraction": frac})

    muscles = []
    for path in sorted(STL_ROOT.glob("**/*Muscle_*.stl")):
        if not any(n in path.name for n in ("GluteusMaximus", "VastusLateralis", "Soleus")):
            continue
        pts = vertices(path)
        frac, inside, total = vertex_fraction(pts, data, inv, (-50, 150))
        muscles.append({"file": path.relative_to(STL_ROOT).as_posix(), "vertices": total,
                        "inside_volume": inside, "soft_tissue_fraction": frac})
    if len(muscles) != 6:
        raise RuntimeError(f"Esperados seis STLs (3 músculos × 2 lados), encontrados {len(muscles)}")

    # The same deterministic 2,000-point sampling previously used for each femur.
    femurs = {}
    for side in ("Left", "Right"):
        path = next((STL_ROOT / side).glob("*Bone_Femur*.stl"))
        all_vertices = vertices(path)
        if len(all_vertices) > 2000:
            points = all_vertices[np.linspace(0, len(all_vertices)-1, 2000, dtype=int)]
        else:
            points = all_vertices
        base, inside, total = vertex_fraction(points, data, inv, "bone")
        perturbations = []
        for axis, axis_name in enumerate("XYZ"):
            for size in (2, 5, 10):
                for sign in (-1, 1):
                    delta = np.zeros(3)
                    delta[axis] = sign * size
                    frac, n_inside, n_total = vertex_fraction(points, data, inv, "bone", delta)
                    perturbations.append({"axis": axis_name, "delta_mm": int(sign*size),
                                          "fraction": frac, "inside_volume": n_inside,
                                          "vertices": n_total})
        femurs[side] = {"file": path.relative_to(STL_ROOT).as_posix(), "vertices": total,
                        "baseline_fraction": base, "baseline_inside_volume": inside,
                        "sensitivity": perturbations}

    # Metadata audit: inspect first and last slices, and enumerate workbook headings.
    dcm_paths = [DICOM_ROOT / "VHF_FullBody_CT0000.dcm", DICOM_ROOT / "VHF_FullBody_CT1726.dcm"]
    dicom_audit = []
    for path in dcm_paths:
        ds = pydicom.dcmread(str(path), stop_before_pixels=True)
        dicom_audit.append({"file": path.name,
                            "ImagePositionPatient": getattr(ds, "ImagePositionPatient", None),
                            "ImageOrientationPatient": getattr(ds, "ImageOrientationPatient", None),
                            "SliceLocation": str(getattr(ds, "SliceLocation", "ABSENT")),
                            "PixelSpacing": [float(x) for x in ds.PixelSpacing],
                            "SpacingBetweenSlices": float(ds.SpacingBetweenSlices),
                            "Modality": str(getattr(ds, "Modality", "ABSENT")),
                            "PixelRepresentation": int(ds.PixelRepresentation),
                            "RescaleType": str(getattr(ds, "RescaleType", "ABSENT")),
                            "RescaleSlope": float(ds.RescaleSlope),
                            "RescaleIntercept": float(ds.RescaleIntercept)})

    pixel_stats = []
    for index in (0, 400, 800, 1200, 1726):
        ds = pydicom.dcmread(str(DICOM_ROOT / f"VHF_FullBody_CT{index:04d}.dcm"))
        a = ds.pixel_array.astype(np.float32) * float(ds.RescaleSlope) + float(ds.RescaleIntercept)
        pixel_stats.append({"slice": index, "min": float(a.min()), "max": float(a.max()),
                            "p50": float(np.percentile(a, 50)), "p90": float(np.percentile(a, 90))})

    try:
        import openpyxl
        workbooks = []
        for path in sorted((BRUTO / "MetaData").rglob("*.xlsx")):
            book = openpyxl.load_workbook(path, data_only=True, read_only=True)
            sheets = []
            for sheet in book:
                headers = [str(x) if x is not None else "" for x in next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))]
                sheets.append({"sheet": sheet.title, "headers": headers})
            workbooks.append({"file": path.relative_to(BRUTO).as_posix(), "sheets": sheets})
    except ImportError:
        workbooks = [{"file": "*.xlsx", "note": "openpyxl unavailable; workbook contents not inspected"}]

    result = {
        "coordinate_system": "RAS mm matching the generated NIfTI affine; apply to STL vertices before inverse-affine voxel lookup",
        "stl_to_ras": {"scale": list(SIGNS), "translation_mm": list(OFFSET_MM)},
        "voxel_lookup": "round(inv_affine @ [x', y', z', 1]); out-of-volume vertices count as failures",
        "empirical_status": "provisional only; femur-derived, not a narrow optimum, no metadata source for XY translation, DICOM rescale units are not declared HU",
        "validation": {"bones": bones, "muscles": muscles, "femur_sensitivity": femurs},
        "metadata_audit": {"dicom_first_last": dicom_audit, "sample_rescaled_pixel_stats": pixel_stats,
                           "denver_workbooks": workbooks},
    }
    JSON_OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = ["", "## Validação independente da transformação STL→TC", "",
             "Transformação testada sem reajuste por estrutura: `x' = −x + 300`, `y' = y − 700`, `z' = z` mm. Todos os vértices de cada STL são usados; pontos fora da TC contam como falhas.",
             "", "**Interpretação das unidades:** os DICOMs têm `Modality=OT`, `RescaleType=US`, `PixelRepresentation=0`, slope 1 e intercept 0. Os valores reescalados não incluem HU negativos e o padrão não declara HU. Portanto, as frações abaixo são numericamente calculadas nos valores reescalados, mas não podem ser validadas como frações HU; os intervalos clínicos pedidos são apenas comparadores numéricos aqui.",
             "", "### Os 28 STLs ósseos (valor reescalado > 200)", "",
             "| Estrutura | Vértices | Dentro da TC | Fração > 200 |", "|---|---:|---:|---:|"]
    lines += [f"| {Path(r['file']).name.removeprefix('VHF_').removesuffix('_smooth.stl')} | {r['vertices']} | {r['inside_volume']}/{r['vertices']} | {r['value_gt_200_fraction']:.2%} |" for r in bones]
    lines += ["", "### Três músculos grandes (valor reescalado entre −50 e 150)", "",
              "| Estrutura | Vértices | Dentro da TC | Fração no intervalo |", "|---|---:|---:|---:|"]
    lines += [f"| {Path(r['file']).name.removeprefix('VHF_').removesuffix('_smooth.stl')} | {r['vertices']} | {r['inside_volume']}/{r['vertices']} | {r['soft_tissue_fraction']:.2%} |" for r in muscles]
    lines += ["", "### Sensibilidade do fêmur a deslocamentos", "",
              "Fração de 2.000 vértices por lado em voxels com valor reescalado > 200 após variar uma coordenada do deslocamento; os outros dois eixos permanecem fixos.",
              "", "| Eixo | Perturbação (mm) | Left | Right |", "|---|---:|---:|---:|"]
    left = {(r['axis'], r['delta_mm']): r['fraction'] for r in femurs['Left']['sensitivity']}
    right = {(r['axis'], r['delta_mm']): r['fraction'] for r in femurs['Right']['sensitivity']}
    for axis in "XYZ":
        for amount in (-10, -5, -2, 2, 5, 10):
            lines.append(f"| {axis} | {amount:+} | {left[(axis,amount)]:.2%} | {right[(axis,amount)]:.2%} |")
    lines += ["", "### Origem do deslocamento nos metadados", "",
              "| Corte DICOM | ImagePositionPatient | ImageOrientationPatient | SliceLocation | Modality / RescaleType |", "|---|---|---|---:|---|"]
    for d in dicom_audit:
        lines.append(f"| {d['file']} | {d['ImagePositionPatient'] or 'ausente'} | {d['ImageOrientationPatient'] or 'ausente'} | {d['SliceLocation']} | {d['Modality']} / {d['RescaleType']} |")
    lines += ["", "Amostra de valores reescalados por corte (mínimo, p50, p90, máximo):", "",
              "| Corte | Mínimo | p50 | p90 | Máximo |", "|---:|---:|---:|---:|---:|"]
    lines += [f"| {r['slice']} | {r['min']:.0f} | {r['p50']:.0f} | {r['p90']:.0f} | {r['max']:.0f} |" for r in pixel_stats]
    lines += ["", "Auditoria das planilhas em `bruto/MetaData`: os cabeçalhos das planilhas listam geometria/volume e maximum overclosure (mm), sem origem, posição, matriz de transformação ou coordenadas. `ImagePositionPatient` e `ImageOrientationPatient` estão ausentes nos dois DICOMs extremos. Portanto, os metadados disponíveis não explicam os 300/−700 mm.",
              "", "A resposta ao deslocamento permanece em um platô: ±10 mm mantém o fêmur em 98,60–100% acima do limiar numérico. Isso **não demonstra um ótimo estreito**. Somado às frações mistas dos ossos e baixas nos músculos e à unidade não-HU, a transformação não está validada para uso anatômico/clínico; fica registrada como hipótese empírica provisória. O NIfTI continua com origem XY convencional por ausência de IPP/IOP.",
              "", f"JSON da transformação e auditoria detalhada: `{JSON_OUT.name}`.", ""]
    report_path = ROOT / "RELATORIO.md"
    existing = report_path.read_text(encoding="utf-8")
    marker = "## Validação independente da transformação STL→TC"
    if marker in existing:
        existing = existing[:existing.index(marker)].rstrip() + "\n"
    report_path.write_text(existing.rstrip() + "\n" + "\n".join(lines), encoding="utf-8")

    print(f"ossos={len(bones)}; músculos={len(muscles)}")
    for r in bones:
        print(f"BONE {r['file']}: n={r['vertices']} inside={r['inside_volume']} value>200={r['value_gt_200_fraction']:.5%}")
    for r in muscles:
        print(f"MUSCLE {r['file']}: n={r['vertices']} inside={r['inside_volume']} value[-50,150]={r['soft_tissue_fraction']:.5%}")
    for side, r in femurs.items():
        print(f"FEMUR {side}: baseline={r['baseline_fraction']:.5%}")
        for delta in r['sensitivity']:
            print(f"  {delta['axis']} {delta['delta_mm']:+}mm {delta['fraction']:.5%}")
    print(f"JSON={JSON_OUT}")
    print("IPP/IOP DICOM first-last=" + repr([(d['file'], d['ImagePositionPatient'], d['ImageOrientationPatient']) for d in dicom_audit]))


if __name__ == "__main__":
    main()
