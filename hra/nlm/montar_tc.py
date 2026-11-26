"""Monta a TC NLM da Visible Human Female em NIfTI RAS de 1,5 mm."""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage
from scipy.ndimage import map_coordinates
from scipy.signal import find_peaks


RAIZ = Path(__file__).resolve().parent
BRUTO = RAIZ / "bruto"
DIR_CORTES = BRUTO / "normalCT"
DIR_HEADERS = BRUTO / "headers"
ARQUIVO_SAIDA = BRUTO / "tc_nlm_1p5.nii.gz"
PRIMEIRO, ULTIMO = 1001, 2734
HEADER_BYTES = 3416
LARGURA = ALTURA = 512
ALVO_MM = 1.5
FOV_COMUM_MM = 480.0
N_PLANO = round(FOV_COMUM_MM / ALVO_MM)
OFFSET_HU = -1024


def campo(texto: str, rotulo: str) -> float:
    padrao = re.compile(rf"^\s*{re.escape(rotulo)}.*?:\s*([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)\s*$", re.I | re.M)
    achado = padrao.search(texto)
    if not achado:
        raise ValueError(f"Campo ausente no header: {rotulo}")
    return float(achado.group(1))


def metadados(indice: int) -> dict:
    caminho = DIR_HEADERS / f"c_vf{indice:04d}.txt"
    texto = caminho.read_text(encoding="latin-1").replace("\x00", "")
    dados = {
        "indice": indice,
        "pixel_x": campo(texto, "Image pixel size - X"),
        "pixel_y": campo(texto, "Image pixel size - Y"),
        "fov_x": campo(texto, "Display Field of view - X (mm)"),
        "loc": campo(texto, "Image location"),
        "center_r": campo(texto, "Center R coord of plane image"),
        "center_a": campo(texto, "Center A coord of plane image"),
        "center_s": campo(texto, "Center S coord of Plane image"),
        "thickness": campo(texto, "Slice Thickness (mm)"),
        "spacing": campo(texto, "Spacing Between scans(mm)"),
    }
    if not np.isclose(dados["pixel_x"] * LARGURA, dados["fov_x"], atol=0.02):
        raise ValueError(f"FOV/pixel size inconsistente no corte {indice}.")
    if abs(dados["loc"] - dados["center_s"]) > 0.1:
        raise ValueError(f"Image location e Center S divergem no corte {indice}.")
    return dados


def gzip_binario() -> str:
    candidatos = [shutil.which("gzip"), r"C:\Program Files\Git\usr\bin\gzip.exe"]
    for caminho in candidatos:
        if caminho and Path(caminho).is_file():
            return caminho
    raise FileNotFoundError("gzip -dc nao encontrado no PATH nem no Git for Windows.")


def bytes_corte(indice: int, gzip: str) -> bytes:
    caminho = DIR_CORTES / f"c_vf{indice:04d}.fre.Z"
    proc = subprocess.run([gzip, "-dc", str(caminho)], capture_output=True, check=True)
    bruto = proc.stdout
    if len(bruto) != HEADER_BYTES + LARGURA * ALTURA * 2:
        raise ValueError(f"Tamanho descompactado inesperado no corte {indice}: {len(bruto)} bytes.")
    if bruto[:4] != b"IMGF" or int.from_bytes(bruto[4:8], "big") != HEADER_BYTES:
        raise ValueError(f"Cabecalho GE invalido no corte {indice}.")
    return bruto[HEADER_BYTES:]


def inferir_endian(payload: bytes) -> str:
    escores = {}
    for endian in (">u2", "<u2"):
        hu = np.frombuffer(payload, dtype=endian).astype(np.int32) + OFFSET_HU
        faixa_ct = np.count_nonzero((hu >= -1024) & (hu <= 3000))
        ar = np.count_nonzero((hu >= -1050) & (hu <= -800))
        escores[endian] = (int(ar), int(faixa_ct))
    escolhido = max(escores, key=lambda e: (escores[e][0], escores[e][1]))
    if escores[escolhido][0] == 0:
        raise ValueError(f"Nao encontrei ar perto de -1000 HU; candidatos de endian: {escores}")
    return escolhido


def ler_corte(indice: int, meta: dict, gzip: str, endian: str) -> np.ndarray:
    payload = bytes_corte(indice, gzip)
    pixels = np.frombuffer(payload, dtype=endian).reshape(ALTURA, LARGURA)
    return pixels.astype(np.int32) + OFFSET_HU


def reamostrar_plano(hu: np.ndarray, meta: dict) -> np.ndarray:
    coords = (np.arange(N_PLANO, dtype=np.float64) - (N_PLANO - 1) / 2) * ALVO_MM
    grade_r, grade_a = np.meshgrid(coords, coords, indexing="ij")
    # GE axial: colunas crescem para R negativo; linhas crescem para A negativo.
    col = (LARGURA - 1) / 2 - (grade_r - meta["center_r"]) / meta["pixel_x"]
    row = (ALTURA - 1) / 2 - (grade_a - meta["center_a"]) / meta["pixel_y"]
    plano = map_coordinates(hu, [row, col], order=1, mode="constant", cval=-1024, prefilter=False)
    return np.rint(plano).clip(-32768, 32767).astype(np.int16)


def montar_posicoes(metas: list[dict]) -> tuple[np.ndarray, int, list[str]]:
    locs = np.array([m["center_s"] for m in metas], dtype=np.float64)
    diffs = np.diff(locs)
    spacing = np.array([m["spacing"] for m in metas[1:]], dtype=np.float64)
    normais = np.abs(np.abs(diffs) - spacing) <= 0.15
    if not np.any(normais):
        raise ValueError("Headers nao mostram deslocamento regular para inferir a direcao craniocaudal.")
    direcao = 1 if np.median(diffs[normais]) > 0 else -1
    pos = np.empty(len(metas), dtype=np.float64)
    pos[0] = locs[0]
    eventos = []
    for i, (delta, passo) in enumerate(zip(diffs, spacing), start=1):
        esperado = direcao * passo
        if abs(delta - esperado) <= 0.15:
            pos[i] = pos[i - 1] + delta
        else:
            pos[i] = pos[i - 1] + esperado
            if abs(delta) <= 0.15:
                tipo = "posicao repetida"
            elif abs(delta) > 1.5 * passo:
                tipo = "salto/reinicio de Image location"
            else:
                tipo = "mudanca de direcao"
            eventos.append(f"{metas[i-1]['indice']}->{metas[i]['indice']}: {tipo} ({delta:+.3f} mm; usado {esperado:+.3f} mm)")
    return pos, direcao, eventos


def resumo_histograma(vol: np.ndarray) -> str:
    amostra = vol[::2, ::2, ::2].astype(np.int32, copy=False)
    hist, bordas = np.histogram(amostra, bins=np.arange(-1025, 4098))
    suave = ndimage.gaussian_filter1d(hist.astype(np.float64), 2)
    picos, _ = find_peaks(suave, prominence=max(float(suave.max()) * 0.00005, 1))
    valores = bordas[:-1]
    faixas = {"ar": (-1050, -800), "gordura": (-200, -30), "musculo": (-30, 200), "osso": (700, 3000)}
    saida = []
    for nome, (minimo, maximo) in faixas.items():
        candidatos = picos[(valores[picos] >= minimo) & (valores[picos] <= maximo)]
        if len(candidatos):
            idx = int(candidatos[np.argmax(suave[candidatos])])
        else:
            faixa = np.flatnonzero((valores >= minimo) & (valores <= maximo))
            idx = int(faixa[np.argmax(hist[faixa])])
        if nome == "osso" and not len(candidatos):
            saida.append(f"osso sem pico local >700 HU; maior_bin={valores[idx]} HU")
        else:
            saida.append(f"{nome}={valores[idx]} HU")
    pct_osso = 100 * np.count_nonzero(amostra > 700) / amostra.size
    p999 = float(np.percentile(amostra, 99.9))
    saida.append(f">700 HU={pct_osso:.3f}% dos voxels; P99,9={p999:.0f} HU")
    return ", ".join(saida)


def executar(corte_teste: int | None = None, resumo: bool = False) -> None:
    gzip = gzip_binario()
    if resumo:
        img = nib.load(str(ARQUIVO_SAIDA))
        vol = np.asanyarray(img.dataobj)
        print(f"Dimensoes={img.shape}; espacamento={nib.affines.voxel_sizes(img.affine).tolist()} mm; faixa={int(vol.min())}..{int(vol.max())} HU")
        print("Histograma: " + resumo_histograma(vol))
        return
    if corte_teste is not None:
        meta = metadados(corte_teste)
        payload = bytes_corte(corte_teste, gzip)
        endian = inferir_endian(payload)
        hu = np.frombuffer(payload, dtype=endian).astype(np.int32) + OFFSET_HU
        plano = reamostrar_plano(hu.reshape(ALTURA, LARGURA), meta)
        print(f"Corte {corte_teste}: header=IMGF/{HEADER_BYTES} bytes; pixels={len(payload)} bytes; endian={endian}")
        print(f"FOV={meta['fov_x']} mm; pixel={meta['pixel_x']} x {meta['pixel_y']} mm; center R/A/S=({meta['center_r']}, {meta['center_a']}, {meta['center_s']}) mm")
        print(f"HU min/max={int(hu.min())}/{int(hu.max())}; ar [-1050,-800] HU={np.count_nonzero((hu >= -1050) & (hu <= -800))}; grade={plano.shape}; grade min/max={int(plano.min())}/{int(plano.max())}")
        return

    indices = list(range(PRIMEIRO, ULTIMO + 1))
    faltam_cortes = [i for i in indices if not (DIR_CORTES / f"c_vf{i:04d}.fre.Z").is_file()]
    faltam_headers = [i for i in indices if not (DIR_HEADERS / f"c_vf{i:04d}.txt").is_file()]
    if faltam_cortes or faltam_headers:
        raise FileNotFoundError(f"Download incompleto: {len(faltam_cortes)} cortes e {len(faltam_headers)} headers ausentes; primeiro corte/header ausente: {faltam_cortes[:1]}/{faltam_headers[:1]}.")

    metas = [metadados(i) for i in indices]
    pos, direcao, eventos = montar_posicoes(metas)
    primeiro_payload = bytes_corte(indices[0], gzip)
    endian = inferir_endian(primeiro_payload)
    planos = np.empty((len(indices), N_PLANO, N_PLANO), dtype=np.int16)
    for j, (idx, meta) in enumerate(zip(indices, metas)):
        payload = primeiro_payload if j == 0 else bytes_corte(idx, gzip)
        hu = np.frombuffer(payload, dtype=endian).astype(np.int32).reshape(ALTURA, LARGURA) + OFFSET_HU
        planos[j] = reamostrar_plano(hu, meta)
        if j % 100 == 0:
            print(f"Planos reamostrados: {j+1}/{len(indices)}")

    ordem = np.argsort(pos)
    pos_ord = pos[ordem]
    planos = planos[ordem]
    z_count = int(round((pos_ord[-1] - pos_ord[0]) / ALVO_MM)) + 1
    z_out = pos_ord[0] + np.arange(z_count, dtype=np.float64) * ALVO_MM
    z_src = np.interp(z_out, pos_ord, np.arange(len(pos_ord), dtype=np.float64))
    volume = np.empty((N_PLANO, N_PLANO, z_count), dtype=np.int16)
    for k, z in enumerate(z_src):
        lo = int(np.floor(z))
        hi = min(lo + 1, len(planos) - 1)
        alpha = z - lo
        volume[:, :, k] = np.rint((1 - alpha) * planos[lo] + alpha * planos[hi]).astype(np.int16)
        if k % 100 == 0:
            print(f"Planos Z reamostrados: {k+1}/{z_count}")

    affine = np.diag([ALVO_MM, ALVO_MM, ALVO_MM, 1.0])
    affine[:3, 3] = [-(N_PLANO - 1) * ALVO_MM / 2, -(N_PLANO - 1) * ALVO_MM / 2, z_out[0]]
    header = nib.Nifti1Header()
    header.set_data_shape(volume.shape)
    header.set_data_dtype(np.int16)
    header.set_zooms((ALVO_MM, ALVO_MM, ALVO_MM))
    header.set_xyzt_units("mm")
    img = nib.Nifti1Image(volume, affine, header)
    img.set_qform(affine, code=1)
    img.set_sform(affine, code=1)
    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    nib.save(img, str(ARQUIVO_SAIDA))

    fovs = sorted({round(m["fov_x"], 3) for m in metas})
    print(f"Endian: {endian}; cortes: {len(indices)}; direcao dos nomes: {'S+' if direcao > 0 else 'S-'}; localizacoes absolutizadas em S crescente.")
    print(f"FOVs encontrados: {fovs} mm; dimensoes: {volume.shape}; faixa HU={int(volume.min())}..{int(volume.max())}; histogramas: {resumo_histograma(volume)}")
    print(f"S: {z_out[0]:.3f}..{z_out[-1]:.3f} mm; saida {ARQUIVO_SAIDA} ({ARQUIVO_SAIDA.stat().st_size} bytes)")
    print(f"Saltos/reinicios ajustados: {len(eventos)}")
    for evento in eventos:
        print("  " + evento)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corte", type=int, help="Descompacta, valida e reamostra um corte sem montar o volume")
    parser.add_argument("--resumo", action="store_true", help="Resume o NIfTI montado sem reprocessar os cortes")
    args = parser.parse_args()
    executar(args.corte, args.resumo)


if __name__ == "__main__":
    main()
