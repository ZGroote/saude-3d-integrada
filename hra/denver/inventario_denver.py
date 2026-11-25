"""Inventário dos STLs Denver e conversão/validação da TC feminina.

Execute da raiz do repositório: python hra/denver/inventario_denver.py
Os arquivos em bruto/ são tratados somente como dados.
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

import nibabel as nib
import numpy as np
import pydicom
import trimesh


ROOT = Path(__file__).resolve().parent
BRUTO = ROOT / "bruto"
STL_ROOT = BRUTO / "Final 3D STL Models-stl"
DICOM_ROOT = BRUTO / "Aligned CT-DICOM"
OUT_NII = BRUTO / "tc_alinhada.nii.gz"


def tipo(path: Path) -> str:
    s = (str(path.parent.name) + " " + path.stem).lower()
    if any(x in s for x in ("cartilage", "cartilagem")):
        return "cartilagem"
    if any(x in s for x in ("ligament", "ligamento")):
        return "ligamento"
    if any(x in s for x in ("fat", "adipose", "gordura")):
        return "gordura"
    if "muscle" in s or "musculo" in s or "músculo" in s:
        return "musculo"
    return "osso"


def estrutura(path: Path) -> str:
    name = path.stem
    name = re.sub(r"^VHF_", "", name, flags=re.IGNORECASE)
    name = re.sub(r"_smooth$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"^(Left|Right)_", "", name, flags=re.IGNORECASE)
    name = re.sub(r"[_-]+", " ", name).strip()
    return name


def gerar_inventario() -> tuple[list[dict], str]:
    rows = []
    for path in sorted(STL_ROOT.glob("**/*.stl")):
        mesh = trimesh.load_mesh(path, process=False)
        bounds = np.asarray(mesh.bounds, dtype=float)
        side = path.parent.name if path.parent.name in ("Left", "Right") else ""
        rows.append({
            "arquivo": path.relative_to(STL_ROOT).as_posix(),
            "estrutura": estrutura(path), "tipo": tipo(path), "lateralidade": side,
            "triangulos": int(len(mesh.faces)),
            "min_x_mm": bounds[0, 0], "min_y_mm": bounds[0, 1], "min_z_mm": bounds[0, 2],
            "max_x_mm": bounds[1, 0], "max_y_mm": bounds[1, 1], "max_z_mm": bounds[1, 2],
        })
    with (ROOT / "catalogo_denver.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter(r["tipo"] for r in rows)
    for kind in ("osso", "musculo", "cartilagem", "ligamento", "gordura"):
        counts.setdefault(kind, 0)
    sides = Counter(r["lateralidade"] for r in rows)
    total_tri = sum(r["triangulos"] for r in rows)
    lines = ["# Inventário Denver — Visible Human Female", "",
             "Dados: University of Denver, Visible Human Female; licença CC BY 4.0.",
             "STLs em `bruto/Final 3D STL Models-stl/`; dimensões exportadas em mm conforme unidade do STL.", "",
             f"- Arquivos: **{len(rows)}**", f"- Triângulos: **{total_tri:,}**".replace(",", "."),
             "", "## Contagem por tipo", "", "| Tipo | Arquivos |", "|---|---:|"]
    lines += [f"| {k} | {v} |" for k, v in sorted(counts.items())]
    lines += ["", "## Contagem por lado", "", "| Lado | Arquivos |", "|---|---:|"]
    lines += [f"| {k or 'sem lado'} | {v} |" for k, v in sorted(sides.items())]
    return rows, "\n".join(lines) + "\n"


def load_series():
    files = sorted(DICOM_ROOT.glob("VHF_FullBody_CT*.dcm"), key=lambda p: int(re.search(r"(\d+)\.dcm$", p.name).group(1)))
    if not files:
        raise FileNotFoundError(f"Nenhum DICOM encontrado em {DICOM_ROOT}")
    cached = OUT_NII.exists()
    datasets = [pydicom.dcmread(str(p), stop_before_pixels=cached) for p in files]
    first = datasets[0]
    # Secondary Capture omits IOP/IPP. Preserve the known slice grid and use
    # the conventional axial orientation with a clearly reported XY origin.
    has_iop = hasattr(first, "ImageOrientationPatient")
    has_ipp = all(hasattr(d, "ImagePositionPatient") for d in datasets)
    orient = np.asarray(first.ImageOrientationPatient if has_iop else [1, 0, 0, 0, 1, 0], dtype=float)
    row_dir, col_dir = orient[:3], orient[3:]
    normal = np.cross(row_dir, col_dir)
    if has_ipp:
        datasets.sort(key=lambda d: float(np.dot(np.asarray(d.ImagePositionPatient, dtype=float), normal)))
    else:
        datasets.sort(key=lambda d: float(getattr(d, "SliceLocation", d.InstanceNumber)))
    if has_ipp:
        positions = np.asarray([d.ImagePositionPatient for d in datasets], dtype=float)
        zstep = float(np.median(np.diff(positions @ normal))) if len(datasets) > 1 else float(first.SliceThickness)
    else:
        locations = np.asarray([float(getattr(d, "SliceLocation", i)) for i, d in enumerate(datasets)])
        zstep = float(np.median(np.diff(locations))) if len(datasets) > 1 else float(first.SpacingBetweenSlices)
        positions = np.zeros((len(datasets), 3), dtype=float)
        positions[:, 2] = locations
    pix = np.asarray(first.PixelSpacing, dtype=float)
    # DICOM PixelSpacing is [row, column]; IOP's first vector follows columns.
    if cached:
        img = nib.load(str(OUT_NII))
        data, affine = np.asanyarray(img.dataobj), img.affine
    else:
        raw = np.stack([d.pixel_array.astype(np.float32) * float(getattr(d, "RescaleSlope", 1)) +
                        float(getattr(d, "RescaleIntercept", 0)) for d in datasets], axis=0)
        # NIfTI axes are (column, row, slice); affine maps these indices to RAS mm.
        data = np.transpose(raw, (2, 1, 0))
        affine = np.eye(4, dtype=float)
        affine[:3, 0] = row_dir * pix[1]
        affine[:3, 1] = col_dir * pix[0]
        affine[:3, 2] = normal * zstep
        affine[:3, 3] = positions[0]
        # DICOM patient coordinates are LPS; NIfTI convention here is RAS.
        affine[:2, :] *= -1
        img = nib.Nifti1Image(data, affine)
        img.header.set_xyzt_units("mm")
        img.header.set_slope_inter(1, 0)
        nib.save(img, str(OUT_NII))
    corners = np.array([[i, j, k, 1] for i in (0, data.shape[0]-1)
                        for j in (0, data.shape[1]-1) for k in (0, data.shape[2]-1)]) @ affine.T
    return datasets, data, affine, corners[:, :3], orient, pix, zstep, has_iop, has_ipp


def vertex_points(path: Path, n=2000):
    mesh = trimesh.load_mesh(path, process=False)
    v = np.asarray(mesh.vertices)
    if len(v) > n:
        # Deterministic, evenly distributed sample across vertex index order.
        v = v[np.linspace(0, len(v)-1, n, dtype=int)]
    return v


def fractions(data, affine):
    inv = np.linalg.inv(affine)
    result = {}
    for side in ("Left", "Right"):
        paths = list((STL_ROOT / side).glob("*Bone_Femur*.stl"))
        if len(paths) != 1:
            raise RuntimeError(f"Esperado um STL Femur em {side}; encontrados {len(paths)}")
        pts = vertex_points(paths[0])
        ijk = np.rint((np.c_[pts, np.ones(len(pts))] @ inv.T)[:, :3]).astype(int)
        valid = np.all((ijk >= 0) & (ijk < np.asarray(data.shape)), axis=1)
        hu = np.full(len(pts), np.nan)
        q = ijk[valid]
        hu[valid] = data[q[:, 0], q[:, 1], q[:, 2]]
        result[side] = (int(len(pts)), int(valid.sum()), float(np.mean(hu > 200)), hu)
    return result


def main():
    rows, report = gerar_inventario()
    datasets, data, affine, corners, orient, pix, zstep, has_iop, has_ipp = load_series()
    fracs = fractions(data, affine)
    # Check common plausible coordinate conventions if direct STL-mm to RAS fails.
    transforms = {
        "direto (STL em RAS)": np.eye(4),
        "espelho Z (origem preservada)": np.diag([1, 1, -1, 1]),
        "LPS para RAS": np.diag([-1, -1, 1, 1]),
        "espelho Z + LPS para RAS": np.diag([-1, -1, -1, 1]),
    }
    scores = {}
    inv = np.linalg.inv(affine)
    for label, tf in transforms.items():
        per_side = []
        for side in ("Left", "Right"):
            path = next((STL_ROOT / side).glob("*Bone_Femur*.stl"))
            pts = vertex_points(path)
            q = np.rint((np.c_[pts, np.ones(len(pts))] @ tf.T @ inv.T)[:, :3]).astype(int)
            valid = np.all((q >= 0) & (q < np.asarray(data.shape)), axis=1)
            per_side.append(float(np.count_nonzero(data[q[valid, 0], q[valid, 1], q[valid, 2]] > 200) / len(q)))
        scores[label] = per_side
    # Search for missing in-plane origin using the femur surfaces. This is a
    # diagnostic registration, not a replacement for absent DICOM metadata.
    point_sets = {side: vertex_points(next((STL_ROOT / side).glob("*Bone_Femur*.stl")), n=300) for side in ("Left", "Right")}
    def score_offset(sx, sy, sz, ox, oy):
        part = []
        for side in ("Left", "Right"):
            pts = point_sets[side] * [sx, sy, sz] + [ox, oy, 0]
            q = np.rint((np.c_[pts, np.ones(len(pts))] @ inv.T)[:, :3]).astype(int)
            valid = np.all((q >= 0) & (q < np.asarray(data.shape)), axis=1)
            part.append(float(np.count_nonzero(data[q[valid, 0], q[valid, 1], q[valid, 2]] > 200) / len(q)))
        return sum(part), part
    offset_scores = []
    signs = [(sx,sy,sz) for sx in (1,-1) for sy in (1,-1) for sz in (1,-1)]
    for sx,sy,sz in signs:
        for ox in range(-700, 701, 40):
            for oy in range(-700, 701, 40):
                score, part = score_offset(sx,sy,sz,ox,oy)
                offset_scores.append((score,(sx,sy,sz,ox,oy),part))
    coarse = max(offset_scores, key=lambda item:item[0])
    sx,sy,sz,coarse_x,coarse_y = coarse[1]
    for ox in range(coarse_x-40, coarse_x+41, 10):
        for oy in range(coarse_y-40, coarse_y+41, 10):
            score,part=score_offset(sx,sy,sz,ox,oy)
            offset_scores.append((score,(sx,sy,sz,ox,oy),part))
    shifted_best=max(offset_scores,key=lambda item:item[0])
    sx,sy,sz,ox,oy = shifted_best[1]
    validate_parts=[]
    for side in ("Left", "Right"):
        pts=vertex_points(next((STL_ROOT / side).glob("*Bone_Femur*.stl")), n=2000)
        pts=pts*[sx,sy,sz]+[ox,oy,0]
        q=np.rint((np.c_[pts,np.ones(len(pts))]@inv.T)[:,:3]).astype(int)
        valid=np.all((q>=0)&(q<np.asarray(data.shape)),axis=1)
        validate_parts.append(float(np.count_nonzero(data[q[valid,0],q[valid,1],q[valid,2]]>200)/len(q)))
    shifted_best=(sum(validate_parts),shifted_best[1],validate_parts)

    # Append auditable acquisition geometry and overlap test to the report.
    extent = np.stack([corners.min(axis=0), corners.max(axis=0)])
    report = report.splitlines()
    report += ["", "## TC alinhada", "", f"- Cortes: **{len(datasets):,}**".replace(",", "."),
               f"- Matriz NIfTI (coluna, linha, corte): **{data.shape}**",
               f"- Pixel spacing DICOM [linha, coluna]: **{pix.tolist()} mm**; espaçamento entre cortes: **{zstep:.6g} mm**",
               f"- ImageOrientationPatient: **{orient.tolist()}**",
               f"- ImagePositionPatient disponível: **{has_ipp}**; SliceLocation inicial/final: **{getattr(datasets[0], 'SliceLocation', 'ausente')} / {getattr(datasets[-1], 'SliceLocation', 'ausente')}**",
               f"- Extensão RAS (mm): **X {extent[0,0]:.3f}..{extent[1,0]:.3f}; Y {extent[0,1]:.3f}..{extent[1,1]:.3f}; Z {extent[0,2]:.3f}..{extent[1,2]:.3f}**",
               "- Intensidades convertidas para HU por `pixel * RescaleSlope + RescaleIntercept`; geometria NIfTI em mm, DICOM LPS convertido para RAS.",
               f"- RescaleType no DICOM: **{getattr(datasets[0], 'RescaleType', 'ausente')}**; valores foram calculados com slope/intercept. O tag não declara literalmente HU, então a interpretação como HU é assumida para a prova.",
               f"- IOP ausente: {not has_iop}; orientação axial convencional assumida. Origem XY ausente e assumida como (0,0) mm.",
               f"- NIfTI gerado: `{OUT_NII.relative_to(ROOT).as_posix()}`", "", "## Prova de referencial: fêmures versus TC", "",
               "Amostragem determinística de 2.000 vértices por STL; todos os pontos amostrados entram no denominador e pontos fora do volume contam como HU não maior que 200.",
               "", "| Transformação aplicada aos vértices STL | Left HU > 200 | Right HU > 200 |", "|---|---:|---:|"]
    report += [f"| {k} | {v[0]:.1%} | {v[1]:.1%} |" for k, v in scores.items()]
    best = max(scores, key=lambda k: sum(scores[k]))
    report += ["", f"Melhor resultado entre as conversões sem origem extra: **{best}**. Todos os vértices amostrados entram no denominador; pontos fora contam como negativos.", ""]
    tx,ty,tz,ox,oy = shifted_best[1]
    report += ["", f"Busca diagnóstica de origem XY: melhor sinal XYZ=({tx},{ty},{tz}), deslocamento STL=({ox},{oy},0) mm; frações Left/Right={shifted_best[2][0]:.3%}/{shifted_best[2][1]:.3%}.",
               f"Transformação operacional dos vértices STL para as coordenadas RAS do NIfTI: x'={tx}·x{ox:+} mm; y'={ty}·y{oy:+} mm; z'={tz}·z mm.",
               "A origem estimada não recupera o posicionamento DICOM ausente; a TC NIfTI mantém a origem XY convencional (0,0).", ""]
    (ROOT / "RELATORIO.md").write_text("\n".join(report), encoding="utf-8")
    print(f"STLs={len(rows)}; triângulos={sum(r['triangulos'] for r in rows)}")
    print("contagem_tipo=" + repr(dict(Counter(r['tipo'] for r in rows))))
    print("contagem_lado=" + repr(dict(Counter(r['lateralidade'] for r in rows))))
    print(f"TC shape={data.shape}; pix_spacing={pix.tolist()}; slice_spacing={zstep:.6g}; IOP={orient.tolist()}")
    print("TC range RAS mm=" + repr(extent.tolist()))
    print("teste_femur=" + repr({k.encode("ascii", "replace").decode(): [round(x, 5) for x in v] for k, v in scores.items()}))
    print("melhor_transformacao=" + best.encode("ascii", "replace").decode())


if __name__ == "__main__":
    main()
