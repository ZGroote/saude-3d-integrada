"""Segmenta a TC NLM em resolucao normal por partes e recompõe no affine original."""
from __future__ import annotations

import argparse
import ctypes
import os
import subprocess
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

import nibabel as nib
import numpy as np
from totalsegmentator.nifti_ext_header import add_label_map_to_nifti, load_multilabel_nifti


RAIZ = Path(__file__).resolve().parent
BRUTO = RAIZ / "bruto"
PYTHON = Path(r"C:\Users\respawn\venvs\totalseg\Scripts\python.exe")
DIR_PARTES_FAST = BRUTO / "partes"
DIR_PARTES = BRUTO / "partes_normal"
DIR_SAIDA = BRUTO / "saida"
ENTRADA_TC = BRUTO / "tc_nlm_1p5.nii.gz"
SAIDA_FINAL = DIR_SAIDA / "segmentacao.nii.gz"
MIN_RAM_GIB = 8.0
LIMIAR_NOVA_PARTE_GIB = 14.0
THREADS_CPU = "2"


def ram_livre_gib() -> float:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    memoria = MemoryStatus()
    memoria.dwLength = ctypes.sizeof(memoria)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memoria)):
        raise OSError("GlobalMemoryStatusEx falhou.")
    return memoria.ullAvailPhys / (1024 ** 3)


def executar_parte(i: int) -> tuple[int, float]:
    entrada = DIR_PARTES_FAST / f"entrada_{i:02d}.nii.gz"
    saida = DIR_PARTES / f"saida_{i:02d}.nii.gz"
    log = DIR_PARTES / f"log_{i:02d}_cpu.txt"
    if not entrada.is_file():
        raise FileNotFoundError(entrada)
    saida.parent.mkdir(parents=True, exist_ok=True)
    if saida.exists():
        saida.unlink()
    cmd = [
        str(PYTHON), "-I", "-c", "from totalsegmentator.bin.TotalSegmentator import main; main()",
        "-i", str(entrada), "-o", str(saida), "--task", "total", "--device", "cpu",
        "--nr_thr_resamp", "1", "--nr_thr_saving", "1", "--ml",
    ]
    env = os.environ.copy()
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[name] = THREADS_CPU
    inicio = time.monotonic()
    tamanho_log = -1
    print(f"Normal parte {i}: CPU, threads={THREADS_CPU}, RAM livre={ram_livre_gib():.1f} GiB", flush=True)
    with log.open("w", encoding="utf-8", errors="replace") as f:
        proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, env=env)
        while proc.poll() is None:
            time.sleep(30)
            tamanho = log.stat().st_size
            ram = ram_livre_gib()
            if tamanho != tamanho_log:
                tamanho_log = tamanho
            print(f"Normal parte {i}: {(time.monotonic()-inicio)/60:.1f} min; log={tamanho_log} bytes; RAM livre={ram:.1f} GiB", flush=True)
            if ram < MIN_RAM_GIB:
                print(f"ALERTA: RAM livre abaixo de {MIN_RAM_GIB:.0f} GiB; nao iniciar novas partes ate liberar memoria.", flush=True)
        codigo = proc.returncode
    if codigo != 0 or not saida.is_file():
        raise RuntimeError(f"Parte {i} falhou (codigo={codigo}); veja {log}.")
    seg, _ = load_multilabel_nifti(str(saida))
    alvo = nib.load(str(entrada))
    if seg.shape != alvo.shape or not np.allclose(seg.affine, alvo.affine, atol=1e-3):
        raise ValueError(f"Forma/affine incorretos na parte {i}.")
    tempo = time.monotonic() - inicio
    print(f"Normal parte {i}: concluida em {tempo/60:.1f} min (CPU).", flush=True)
    return i, tempo


def executar_em_paralelo() -> dict[int, float]:
    partes = sorted(int(p.name.split("_")[-1].split(".")[0]) for p in DIR_PARTES_FAST.glob("entrada_*.nii.gz"))
    if len(partes) != 5:
        raise ValueError(f"Esperadas 5 partes fast existentes; encontradas {partes}.")
    if DIR_PARTES.exists() and any(DIR_PARTES.iterdir()):
        raise FileExistsError(f"Pasta de saida normal nao esta vazia: {DIR_PARTES}")
    DIR_PARTES.mkdir(parents=True, exist_ok=True)
    tempos = {}
    pendentes = iter(partes)
    ativos = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        while True:
            while len(ativos) < 2 and ram_livre_gib() >= LIMIAR_NOVA_PARTE_GIB:
                try:
                    i = next(pendentes)
                except StopIteration:
                    break
                ativos[pool.submit(executar_parte, i)] = i
            if not ativos:
                try:
                    i = next(pendentes)
                except StopIteration:
                    break
                while ram_livre_gib() < LIMIAR_NOVA_PARTE_GIB:
                    print(f"Aguardando RAM para iniciar parte {i}: livre={ram_livre_gib():.1f} GiB", flush=True)
                    time.sleep(30)
                ativos[pool.submit(executar_parte, i)] = i
            feitos, _ = wait(ativos, timeout=30, return_when=FIRST_COMPLETED)
            if not feitos:
                print(f"Partes normais ativas; RAM livre={ram_livre_gib():.1f} GiB", flush=True)
                continue
            for future in feitos:
                i, elapsed = future.result()
                tempos[i] = elapsed
                ativos.pop(future)
    return tempos


def juntar() -> dict[str, float]:
    original = nib.load(str(ENTRADA_TC))
    corpo = nib.load(str(BRUTO / "tc_nlm_corpo_1p5.nii.gz"))
    crop_start = np.rint(np.linalg.inv(original.affine) @ np.r_[corpo.affine[:3, 3], 1])[:3].astype(int)
    crop_stop = crop_start + np.array(corpo.shape)
    fatias = tuple(slice(int(a), int(b)) for a, b in zip(crop_start, crop_stop))
    janelas = []
    for i in range(1, 6):
        parte = nib.load(str(DIR_PARTES_FAST / f"entrada_{i:02d}.nii.gz"))
        z0 = int(round((parte.affine[2, 3] - corpo.affine[2, 3]) / 1.5))
        janelas.append((z0, z0 + parte.shape[2]))
    dono = np.full(corpo.shape[2], -1, dtype=np.int16)
    for z in range(corpo.shape[2]):
        candidatos = [i for i, (a, b) in enumerate(janelas) if a <= z < b]
        if not candidatos:
            raise ValueError(f"Nenhuma parte cobre o plano z={z}.")
        dono[z] = max(candidatos, key=lambda i: min(z-janelas[i][0], janelas[i][1]-1-z))

    combinado = np.zeros(corpo.shape, dtype=np.uint8)
    label_map = None
    for i, (z0, z1) in enumerate(janelas, 1):
        img, mapa = load_multilabel_nifti(str(DIR_PARTES / f"saida_{i:02d}.nii.gz"))
        if label_map is None:
            label_map = mapa
        elif mapa != label_map:
            raise ValueError(f"Mapa de rotulos diferente na parte normal {i}.")
        dados = np.asanyarray(img.dataobj)
        for z in range(z0, z1):
            if dono[z] == i - 1:
                combinado[:, :, z] = dados[:, :, z-z0]

    dados_final = np.zeros(original.shape, dtype=np.uint8)
    dados_final[fatias] = combinado
    final = nib.Nifti1Image(dados_final, original.affine, original.header.copy())
    final.header.set_data_dtype(np.uint8)
    final.set_qform(original.affine, code=1)
    final.set_sform(original.affine, code=1)
    DIR_SAIDA.mkdir(parents=True, exist_ok=True)
    if SAIDA_FINAL.exists():
        raise FileExistsError(SAIDA_FINAL)
    nib.save(add_label_map_to_nifti(final, label_map), str(SAIDA_FINAL))
    counts = np.bincount(dados_final.ravel().astype(np.int32), minlength=max(label_map)+1)
    voxel_cm3 = float(np.prod(nib.affines.voxel_sizes(original.affine)) / 1000)
    return {name: float(counts[idx] * voxel_cm3) for idx, name in label_map.items()}


def resumo(volumes: dict[str, float]) -> None:
    fast_img, fast_map = load_multilabel_nifti(str(BRUTO / "fast" / "segmentacao.nii.gz"))
    fast = np.asanyarray(fast_img.dataobj)
    fast_counts = np.bincount(fast.ravel().astype(np.int32), minlength=max(fast_map)+1)
    fast_vol = {name: float(fast_counts[idx] * np.prod(nib.affines.voxel_sizes(fast_img.affine)) / 1000)
                for idx, name in fast_map.items()}
    print(f"Saida normal: {SAIDA_FINAL}")
    print(f"Rotulos nao vazios: {sum(v > 0 for v in volumes.values())}/{len(volumes)}; fast: {sum(v > 0 for v in fast_vol.values())}/{len(fast_vol)}")
    controles = ["femur_left", "femur_right", "hip_left", "hip_right", "sacrum",
                 "vertebrae_L1", "vertebrae_L2", "vertebrae_L3", "vertebrae_L4", "vertebrae_L5",
                 "kidney_left", "kidney_right", "liver", "heart"]
    for name in controles:
        nrm, fst = volumes.get(name, 0.0), fast_vol.get(name, 0.0)
        print(f"{name}: normal={nrm:.2f} cm3; fast={fst:.2f} cm3; delta={nrm-fst:+.2f} cm3")
    for lado, lobos in (("left", ("upper_lobe", "lower_lobe")),
                        ("right", ("upper_lobe", "middle_lobe", "lower_lobe"))):
        nome = f"lung_{lado}"
        nrm = sum(volumes.get(f"lung_{l}_{lado}", 0.0) for l in lobos)
        fst = sum(fast_vol.get(f"lung_{l}_{lado}", 0.0) for l in lobos)
        print(f"{nome}: normal={nrm:.2f} cm3; fast={fst:.2f} cm3; delta={nrm-fst:+.2f} cm3")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparar-apenas", action="store_true", help="Valida RAM/partes sem iniciar inferencia")
    args = parser.parse_args()
    if not PYTHON.is_file():
        raise FileNotFoundError(PYTHON)
    if not ENTRADA_TC.is_file() or not DIR_PARTES_FAST.is_dir():
        raise FileNotFoundError("TC montada ou pasta de partes ausente.")
    if args.preparar_apenas:
        print(f"RAM livre={ram_livre_gib():.1f} GiB; GPU={subprocess.run(['nvidia-smi','--query-gpu=memory.free,memory.total','--format=csv,noheader'],capture_output=True,text=True).stdout.strip()}")
        return
    tempos = executar_em_paralelo()
    for i, segundos in sorted(tempos.items()):
        print(f"TEMPO_PARTE_{i}={segundos/60:.1f} min (CPU)")
    volumes = juntar()
    resumo(volumes)


if __name__ == "__main__":
    main()
