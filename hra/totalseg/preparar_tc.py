"""Calibra a TC da Denver para HU aproximados e reamostra para 1,5 mm."""
from __future__ import annotations

import argparse
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage
from scipy.signal import find_peaks


ROOT = Path(__file__).resolve().parents[2]
ENTRADA_PADRAO = ROOT / "hra" / "denver" / "bruto" / "tc_alinhada.nii.gz"
SAIDA_PADRAO = Path(__file__).resolve().parent / "bruto" / "tc_hu_1p5.nii.gz"
ESPACAMENTO_ALVO = 1.5
FAIXA_HU = (-1000.0, 3000.0)


def histograma(vol: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Histograma de valores inteiros, acumulado em blocos após uma leitura única."""
    vmin = int(np.floor(np.nanmin(vol)))
    vmax = int(np.ceil(np.nanmax(vol)))
    bordas = np.arange(vmin, vmax + 2, dtype=np.float64) - 0.5
    hist = np.zeros(len(bordas) - 1, dtype=np.int64)
    for z in range(0, vol.shape[2], 32):
        bloco = np.rint(vol[:, :, z : z + 32]).astype(np.int32, copy=False)
        hist += np.histogram(bloco, bins=bordas)[0]
    valores = np.arange(vmin, vmax + 1, dtype=np.float64)
    return valores, hist


def preparar(entrada: Path, saida: Path, analisar: bool = False) -> None:
    img = nib.load(str(entrada))
    affine = img.affine.copy()
    espacamento = nib.affines.voxel_sizes(affine)
    dados = np.asanyarray(img.dataobj).astype(np.float32, copy=False)
    if dados.ndim != 3:
        raise ValueError(f"Esperada TC 3D; dimensões recebidas: {dados.shape}")
    valores, hist = histograma(dados)
    hist_suave = ndimage.gaussian_filter1d(hist.astype(np.float64), sigma=2)
    picos_locais, _ = find_peaks(hist_suave, prominence=max(hist_suave.max() * 0.0002, 1))
    picos_top = sorted(picos_locais, key=lambda i: hist_suave[i], reverse=True)[:18]
    modos = np.asarray(picos_locais)
    candidatos_ar = modos[valores[modos] <= 229]
    candidatos_moles = modos[(valores[modos] > 229) & (valores[modos] <= 726)]
    candidatos_osso = modos[valores[modos] > 726]
    if not (len(candidatos_ar) and len(candidatos_moles) and len(candidatos_osso)):
        raise ValueError("Nao foram encontrados modos de ar, tecido mole e osso nos intervalos do histograma.")
    idx_ar = int(candidatos_ar[np.argmax(hist_suave[candidatos_ar])])
    idx_musculo = int(candidatos_moles[np.argmax(hist_suave[candidatos_moles])])
    idx_osso = int(candidatos_osso[np.argmax(hist_suave[candidatos_osso])])
    corte_ar = float(valores[idx_ar + np.argmin(hist_suave[idx_ar:idx_musculo + 1])])
    corte_osso = float(valores[idx_musculo + np.argmin(hist_suave[idx_musculo:idx_osso + 1])])
    ar = float(valores[idx_ar])
    musculo = float(valores[idx_musculo])
    if musculo <= ar:
        raise ValueError(f"Picos incompatíveis para calibração: ar={ar}, músculo={musculo}.")
    escala = 1040.0 / (musculo - ar)
    hu_valores = (valores - ar) * escala - 1000.0
    faixa_gordura = (hu_valores >= -180) & (hu_valores <= -20)
    fat_candidates = picos_locais[faixa_gordura[picos_locais]]
    gordura_idx = int(fat_candidates[np.argmax(hist_suave[fat_candidates])]) if len(fat_candidates) else int(np.flatnonzero(faixa_gordura)[np.argmax(hist[faixa_gordura])])
    gordura_bruta = float(valores[gordura_idx])
    ajuste_gordura = not (-120 <= hu_valores[gordura_idx] <= -60)
    if ajuste_gordura:
        slope_ar_gordura = 910.0 / (gordura_bruta - ar)
        slope_gordura_musculo = 130.0 / (musculo - gordura_bruta)
        hu_valores = np.where(
            valores <= gordura_bruta,
            -1000.0 + (valores - ar) * slope_ar_gordura,
            np.where(valores <= musculo, -90.0 + (valores - gordura_bruta) * slope_gordura_musculo,
                     40.0 + (valores - musculo) * escala),
        )
    gordura = float(hu_valores[gordura_idx])
    faixa_osso = (hu_valores > 700) & (valores >= corte_osso)
    osso_idx = int(np.flatnonzero(faixa_osso)[np.argmax(hist[faixa_osso])])
    osso = float(hu_valores[osso_idx])

    print(f"Entrada: {entrada}")
    print(f"Dimensões originais: {dados.shape}; espaçamento: {espacamento.tolist()} mm")
    print(f"Vales ar/tecido={corte_ar:.1f}; tecido/osso={corte_osso:.1f} (valores de entrada)")
    print("Picos locais mais altos (valor: voxels suavizados): " + ", ".join(f"{valores[i]:.0f}:{hist_suave[i]:.0f}" for i in picos_top))
    print(f"Calibracao linear inicial: HU=(valor-{ar:.1f})*{escala:.6f}-1000")
    print(f"Pico/ombro adiposo: bruto={gordura_bruta:.1f}; calibrado={gordura:.1f} HU; pico cortical={osso:.1f} HU")
    if ajuste_gordura:
        print("Ajuste: sem pico adiposo local destacado; ombro mais populoso da faixa prevista usado como ancora -90 HU em mapa linear por trechos; ar=-1000 e musculo=+40 preservados.")
    if osso <= 700:
        print("AVISO: pico cortical não excede 700 HU após a calibração linear.")
    if analisar:
        return

    # A maior componente dos voxels não ar localiza o corpo; busca em 1/8 da grade.
    limiar_corpo = corte_ar
    mascara_reduzida = dados[::2, ::2, ::2] > limiar_corpo
    rotulos, numero = ndimage.label(mascara_reduzida)
    if numero == 0:
        raise ValueError("Não foi encontrado componente de corpo acima do limiar do ar.")
    contagens = np.bincount(rotulos.ravel())
    contagens[0] = 0
    componente = int(np.argmax(contagens))
    coords = np.where(rotulos == componente)
    margem = np.ceil(10.0 / espacamento).astype(int)
    inicio = np.maximum(np.array([c.min() for c in coords]) * 2 - margem, 0)
    fim = np.minimum((np.array([c.max() for c in coords]) * 2 + 2 + margem), dados.shape)
    recorte = tuple(slice(int(a), int(b)) for a, b in zip(inicio, fim))
    corpo = dados[recorte]
    affine_recortada = affine @ np.array(
        [[1, 0, 0, inicio[0]], [0, 1, 0, inicio[1]], [0, 0, 1, inicio[2]], [0, 0, 0, 1]],
        dtype=np.float64,
    )
    print(f"Recorte corpo: origem voxel {inicio.tolist()}, dimensões {corpo.shape}, margem 10 mm")

    # Constrói grade de mesma orientação física; o primeiro voxel mantém o referencial.
    direcoes = affine_recortada[:3, :3] / espacamento
    forma_saida = np.ceil((np.array(corpo.shape) - 1) * espacamento / ESPACAMENTO_ALVO).astype(int) + 1
    affine_saida = affine_recortada.copy()
    affine_saida[:3, :3] = direcoes * ESPACAMENTO_ALVO
    matriz = np.linalg.inv(affine_recortada) @ affine_saida
    if ajuste_gordura:
        hu = np.where(
            corpo <= gordura_bruta,
            -1000.0 + (corpo - ar) * slope_ar_gordura,
            np.where(corpo <= musculo, -90.0 + (corpo - gordura_bruta) * slope_gordura_musculo,
                     40.0 + (corpo - musculo) * escala),
        ).astype(np.float32, copy=False)
    else:
        hu = ((corpo - ar) * escala - 1000.0).astype(np.float32, copy=False)
    np.clip(hu, *FAIXA_HU, out=hu)
    reamostrado = ndimage.affine_transform(
        hu,
        matrix=matriz[:3, :3],
        offset=matriz[:3, 3],
        output_shape=tuple(int(x) for x in forma_saida),
        order=1,
        mode="constant",
        cval=-1000.0,
        prefilter=False,
    )
    header = img.header.copy()
    header.set_data_dtype(np.float32)
    header.set_zooms((ESPACAMENTO_ALVO,) * 3)
    header.set_xyzt_units("mm")
    resultado = nib.Nifti1Image(reamostrado, affine_saida, header)
    resultado.set_qform(affine_saida, code=1)
    resultado.set_sform(affine_saida, code=1)
    resultado.header.set_slope_inter(1.0, 0.0)
    saida.parent.mkdir(parents=True, exist_ok=True)
    nib.save(resultado, str(saida))
    print(f"Dimensões finais: {reamostrado.shape}; espaçamento: 1.5 mm isotrópico")
    print(f"Affine de saída preserva a origem física do primeiro voxel recortado: {affine_saida[:3, 3].tolist()}")
    print(f"Saída: {saida} ({saida.stat().st_size / (1024**3):.2f} GiB comprimido)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, default=ENTRADA_PADRAO)
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    parser.add_argument("--analisar", action="store_true", help="Mostra histograma/calibração sem gravar a TC")
    args = parser.parse_args()
    preparar(args.entrada.resolve(), args.saida.resolve(), args.analisar)


if __name__ == "__main__":
    main()
