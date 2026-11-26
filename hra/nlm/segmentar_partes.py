"""Recorta o corpo, segmenta em blocos craniocaudais e recompõe o NIfTI."""
from __future__ import annotations

import math
import argparse
import ctypes
import os
import subprocess
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage
from totalsegmentator.nifti_ext_header import add_label_map_to_nifti, load_multilabel_nifti


RAIZ = Path(__file__).resolve().parent
BRUTO = RAIZ / "bruto"
ENTRADA = BRUTO / "tc_nlm_1p5.nii.gz"
CORPO_PATH = BRUTO / "tc_nlm_corpo_1p5.nii.gz"
PARTES_DIR = BRUTO / "partes"
FAST_DIR = BRUTO / "fast"
SAIDA_FINAL = FAST_DIR / "segmentacao.nii.gz"
PYTHON = Path(r"C:\Users\respawn\venvs\totalseg\Scripts\python.exe")
LIMIAR_AR_HU = -500.0
MARGEM_MM = 10.0
COMPRIMENTO_MAX_MM = 400.0
SOBREPOSICAO_MM = 60.0
SEM_PROGRESSO_S = 15 * 60


def recortar_e_partir() -> tuple[nib.Nifti1Image, tuple[slice, slice, slice], list[tuple[int, int]]]:
    img = nib.load(str(ENTRADA))
    dados = np.asanyarray(img.dataobj)
    spacing = nib.affines.voxel_sizes(img.affine)
    mascara = dados[::2, ::2, ::2] > LIMIAR_AR_HU
    rotulos, n = ndimage.label(mascara)
    if not n:
        raise ValueError("O limiar de ar nao encontrou componente corporal.")
    contagens = np.bincount(rotulos.ravel())
    contagens[0] = 0
    corpo_id = int(np.argmax(contagens))
    coords = np.where(rotulos == corpo_id)
    inicio = np.maximum(np.array([c.min() for c in coords]) * 2 - np.ceil(MARGEM_MM / spacing).astype(int), 0)
    fim = np.minimum(np.array([c.max() for c in coords]) * 2 + 2 + np.ceil(MARGEM_MM / spacing).astype(int), dados.shape)
    fatias = tuple(slice(int(a), int(b)) for a, b in zip(inicio, fim))
    translacao = np.eye(4)
    translacao[:3, 3] = inicio
    affine_corpo = img.affine @ translacao
    dados_corpo = dados[fatias]
    corpo = nib.Nifti1Image(dados_corpo, affine_corpo, img.header.copy())
    corpo.set_qform(affine_corpo, code=1)
    corpo.set_sform(affine_corpo, code=1)
    CORPO_PATH.parent.mkdir(parents=True, exist_ok=True)
    nib.save(corpo, str(CORPO_PATH))

    max_vox = max(2, int(math.floor(COMPRIMENTO_MAX_MM / spacing[2])) + 1)
    overlap = max(1, int(round(SOBREPOSICAO_MM / spacing[2])))
    z_len = corpo.shape[2]
    inicios = [0]
    while inicios[-1] + max_vox < z_len:
        inicios.append(inicios[-1] + max_vox - overlap)
    janelas = [(z, min(z + max_vox, z_len)) for z in inicios]
    if PARTES_DIR.exists():
        estranhos = [p.name for p in PARTES_DIR.iterdir() if not p.name.startswith("entrada_")]
        if estranhos:
            raise FileExistsError(f"Pasta de partes contem saidas/logs de outra execucao: {estranhos}")
    PARTES_DIR.mkdir(parents=True, exist_ok=True)
    for i, (z0, z1) in enumerate(janelas, 1):
        t = np.eye(4)
        t[2, 3] = z0
        a = affine_corpo @ t
        parte = nib.Nifti1Image(dados_corpo[:, :, z0:z1], a, corpo.header.copy())
        parte.set_qform(a, code=1)
        parte.set_sform(a, code=1)
        nib.save(parte, str(PARTES_DIR / f"entrada_{i:02d}.nii.gz"))
    print(f"Corpo: inicio={inicio.tolist()}, shape={corpo.shape}, affine_origem={affine_corpo[:3, 3].tolist()}", flush=True)
    print(f"Partes ({len(janelas)}): " + ", ".join(f"{a}:{b} ({(b-a)*spacing[2]:.1f} mm)" for a, b in janelas), flush=True)
    return corpo, fatias, janelas


def gpu_estado() -> tuple[float, int, int] | None:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=power.draw,memory.free,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines()[0].split(",")
        return float(out[0].strip()), int(float(out[1].strip())), int(float(out[2].strip()))
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return None


def ram_livre_gb() -> float:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    estado = MemoryStatus()
    estado.dwLength = ctypes.sizeof(estado)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(estado)):
        raise OSError("GlobalMemoryStatusEx falhou.")
    return estado.ullAvailPhys / (1024 ** 3)


def executar_parte(entrada: Path, saida: Path, log: Path, indice: int, dispositivo_inicial: str) -> str:
    log.parent.mkdir(parents=True, exist_ok=True)
    dispositivos = ("gpu", "cpu") if dispositivo_inicial == "gpu" else ("cpu",)
    for device in dispositivos:
        if saida.exists():
            saida.unlink()
        cmd = [
            str(PYTHON), "-I", "-c", "from totalsegmentator.bin.TotalSegmentator import main; main()",
            "-i", str(entrada), "-o", str(saida), "--task", "total", "--fast",
            "--device", device, "--nr_thr_resamp", "1", "--nr_thr_saving", "1", "--ml",
        ]
        ambiente = os.environ.copy()
        if device == "cpu":
            for chave in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
                ambiente[chave] = "2"
        inicio = time.monotonic()
        ultimo_progresso = inicio
        tamanho_log = 0
        print(f"Parte {indice}: iniciando TotalSegmentator fast em {device}; CUDA livre={gpu_estado()}", flush=True)
        with log.open("w", encoding="utf-8", errors="replace") as f:
            proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, env=ambiente)
            while proc.poll() is None:
                time.sleep(30)
                tamanho = log.stat().st_size
                if tamanho != tamanho_log:
                    tamanho_log = tamanho
                    ultimo_progresso = time.monotonic()
                decorrido = time.monotonic() - inicio
                estado = gpu_estado() if device == "gpu" else None
                ram = ram_livre_gb()
                print(f"Parte {indice} ({device}): {decorrido/60:.1f} min; log={tamanho_log} bytes; GPU={estado}; RAM livre={ram:.1f} GiB", flush=True)
                parado = time.monotonic() - ultimo_progresso
                potencia_baixa = estado is None or estado[0] < 30
                if device == "gpu" and parado >= SEM_PROGRESSO_S and potencia_baixa:
                    print(f"Parte {indice}: sem progresso por 15 min e GPU lenta; encerrando para repetir somente esta parte em CPU.", flush=True)
                    subprocess.run(["taskkill.exe", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
                    proc.wait()
                    break
            codigo = proc.poll()
        if codigo == 0 and saida.is_file():
            try:
                seg, _ = load_multilabel_nifti(str(saida))
                alvo = nib.load(str(entrada))
                if seg.shape == alvo.shape and np.allclose(seg.affine, alvo.affine, atol=1e-3):
                    print(f"Parte {indice}: concluida em {device} ({(time.monotonic()-inicio)/60:.1f} min).", flush=True)
                    return device
            except Exception:
                pass
        if device == "gpu":
            print(f"Parte {indice}: GPU terminou com codigo {codigo}; repetindo apenas esta parte em CPU.", flush=True)
            while ram_livre_gb() < 12.0:
                print(f"Parte {indice}: aguardando RAM para fallback CPU (livre={ram_livre_gb():.1f} GiB; minimo de seguranca 8 GiB).", flush=True)
                time.sleep(30)
    raise RuntimeError(f"A segmentacao da parte {indice} falhou tambem em CPU; consulte {log}.")


def executar_em_paralelo(janelas: list[tuple[int, int]]) -> None:
    # A parte 4 cobre o tronco; pernas e cabeca/pescoco usam CPU em paralelo.
    gpu_idx = min(3, len(janelas) - 1)
    cpu_fila = [i for i in range(len(janelas)) if i != gpu_idx]
    futuros = {}
    cpu_ativos = 0
    ram_minimo_para_nova_cpu = 12.0
    with ThreadPoolExecutor(max_workers=3) as pool:
        def iniciar(i: int, dispositivo: str) -> None:
            nonlocal cpu_ativos
            entrada = PARTES_DIR / f"entrada_{i+1:02d}.nii.gz"
            saida = PARTES_DIR / f"saida_{i+1:02d}.nii.gz"
            log = PARTES_DIR / f"log_{i+1:02d}_{dispositivo}.txt"
            fut = pool.submit(executar_parte, entrada, saida, log, i+1, dispositivo)
            futuros[fut] = (i, dispositivo)
            if dispositivo == "cpu":
                cpu_ativos += 1

        iniciar(gpu_idx, "gpu")
        while cpu_fila and cpu_ativos < 2 and ram_livre_gb() >= ram_minimo_para_nova_cpu:
            iniciar(cpu_fila.pop(0), "cpu")
        while futuros:
            feitos, _ = wait(futuros, timeout=30, return_when=FIRST_COMPLETED)
            if not feitos:
                print(f"Execucoes ativas; RAM livre={ram_livre_gb():.1f} GiB; GPU={gpu_estado()}", flush=True)
                continue
            for futuro in feitos:
                _, dispositivo = futuros.pop(futuro)
                futuro.result()
                if dispositivo == "cpu":
                    cpu_ativos -= 1
            while cpu_fila and cpu_ativos < 2 and ram_livre_gb() >= ram_minimo_para_nova_cpu:
                iniciar(cpu_fila.pop(0), "cpu")
            if cpu_fila and cpu_ativos < 2 and ram_livre_gb() < ram_minimo_para_nova_cpu:
                print(f"Aguardando RAM antes de iniciar outra parte CPU; livre={ram_livre_gb():.1f} GiB.", flush=True)
                time.sleep(30)


def juntar(corpo: nib.Nifti1Image, fatias: tuple[slice, slice, slice], janelas: list[tuple[int, int]]) -> tuple[dict[str, float], dict[str, tuple[float, float, float]]]:
    escolhida = np.full(corpo.shape[2], -1, dtype=np.int16)
    for z in range(corpo.shape[2]):
        candidatos = [i for i, (a, b) in enumerate(janelas) if a <= z < b]
        escolhida[z] = max(candidatos, key=lambda i: min(z-janelas[i][0], janelas[i][1]-1-z))
    rotulo_map = None
    merged = np.zeros(corpo.shape, dtype=np.uint8)
    for i, (z0, z1) in enumerate(janelas, 1):
        caminho = PARTES_DIR / f"saida_{i:02d}.nii.gz"
        img, label_map = load_multilabel_nifti(str(caminho))
        if rotulo_map is None:
            rotulo_map = label_map
        elif label_map != rotulo_map:
            raise ValueError(f"Mapa de rotulos da parte {i} difere das partes anteriores.")
        dados = np.asanyarray(img.dataobj)
        for z in range(z0, z1):
            if escolhida[z] == i - 1:
                merged[:, :, z] = dados[:, :, z-z0]

    original = nib.load(str(ENTRADA))
    resultado = np.zeros(original.shape, dtype=np.uint8)
    resultado[fatias] = merged
    final = nib.Nifti1Image(resultado, original.affine, original.header.copy())
    final.set_qform(original.affine, code=1)
    final.set_sform(original.affine, code=1)
    final.header.set_data_dtype(np.uint8)
    FAST_DIR.mkdir(parents=True, exist_ok=True)
    with_map = add_label_map_to_nifti(final, rotulo_map)
    nib.save(with_map, str(SAIDA_FINAL))

    voxels = np.bincount(resultado.ravel(), minlength=max(rotulo_map) + 1)
    voxel_cm3 = float(np.prod(nib.affines.voxel_sizes(original.affine)) / 1000.0)
    volumes = {nome: float(voxels[label] * voxel_cm3) for label, nome in rotulo_map.items()}
    ids = {nome: label for label, nome in rotulo_map.items()}
    centroides = {}
    for nome in ("heart", "liver"):
        pontos = np.where(resultado == ids.get(nome, -1))
        if len(pontos[0]):
            xyz = np.array([p.mean() for p in pontos] + [1.0])
            ras = original.affine @ xyz
            centroides[nome] = tuple(float(v) for v in ras[:3])
    return volumes, centroides


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparar-apenas", action="store_true", help="Cria o recorte e as entradas das partes, sem segmentar")
    args = parser.parse_args()
    if not PYTHON.is_file():
        raise FileNotFoundError(f"Ambiente TotalSegmentator ausente: {PYTHON}")
    corpo, fatias, janelas = recortar_e_partir()
    if args.preparar_apenas:
        return
    executar_em_paralelo(janelas)
    volumes, centroides = juntar(corpo, fatias, janelas)
    print(f"Saida multilabel unida: {SAIDA_FINAL}")
    print(f"Rotulos nao vazios: {sum(v > 0 for v in volumes.values())}/{len(volumes)}")
    for nome in ("femur_left", "femur_right", "hip_left", "hip_right", "sacrum",
                 "vertebrae_L1", "vertebrae_L2", "vertebrae_L3", "vertebrae_L4", "vertebrae_L5",
                 "kidney_left", "kidney_right", "liver", "heart"):
        print(f"{nome}: {volumes.get(nome, 0.0):.2f} cm3")
    pulmao_esq = sum(volumes.get(f"lung_{lobe}_left", 0.0) for lobe in ("upper_lobe", "lower_lobe"))
    pulmao_dir = sum(volumes.get(f"lung_{lobe}_right", 0.0) for lobe in ("upper_lobe", "middle_lobe", "lower_lobe"))
    print(f"pulmao_left (lobos): {pulmao_esq:.2f} cm3")
    print(f"pulmao_right (lobos): {pulmao_dir:.2f} cm3")
    for nome, ras in centroides.items():
        print(f"centroide {nome} RAS (mm): {tuple(round(v, 1) for v in ras)}")


if __name__ == "__main__":
    main()
