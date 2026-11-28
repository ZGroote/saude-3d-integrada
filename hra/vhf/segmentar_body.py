"""Roda TotalSegmentator task body em CPU, por partes, e recompõe o NIfTI."""
from __future__ import annotations

import ctypes
import os
import subprocess
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

import nibabel as nib
import numpy as np
from totalsegmentator.nifti_ext_header import add_label_map_to_nifti, load_multilabel_nifti


ROOT = Path(__file__).resolve().parents[2]
NLM = ROOT / "hra" / "nlm" / "bruto"
PARTS_IN = NLM / "partes"
BODY_DIR = NLM / "body"
PARTS_OUT = BODY_DIR / "partes"
CT_PATH = NLM / "tc_nlm_1p5.nii.gz"
CROP_PATH = NLM / "tc_nlm_corpo_1p5.nii.gz"
OUT_PATH = BODY_DIR / "segmentacao.nii.gz"
PYTHON = Path(r"C:\Users\respawn\venvs\totalseg\Scripts\python.exe")
THREADS = "2"
MIN_RAM_GIB = 8.0
START_RAM_GIB = 14.0


def free_ram_gib() -> float:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    status = MemoryStatus()
    status.dwLength = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError("GlobalMemoryStatusEx failed")
    return status.ullAvailPhys / (1024 ** 3)


def windows() -> list[tuple[int, int]]:
    paths = sorted(PARTS_IN.glob("entrada_*.nii.gz"))
    if len(paths) != 5:
        raise RuntimeError(f"Expected 5 prepared windows in {PARTS_IN}, found {len(paths)}")
    crop = nib.load(str(CROP_PATH))
    ranges = []
    for path in paths:
        image = nib.load(str(path))
        z0 = int(round((image.affine[2, 3] - crop.affine[2, 3]) / 1.5))
        ranges.append((z0, z0 + image.shape[2]))
    return ranges


def run_part(index: int) -> tuple[int, float]:
    source = PARTS_IN / f"entrada_{index:02d}.nii.gz"
    target = PARTS_OUT / f"saida_{index:02d}.nii.gz"
    log = PARTS_OUT / f"log_{index:02d}_cpu.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        try:
            segmented, _ = load_multilabel_nifti(str(target))
            reference = nib.load(str(source))
            if segmented.shape == reference.shape and np.allclose(segmented.affine, reference.affine, atol=1e-3):
                print(f"body CPU part {index} already complete; reusing {target}", flush=True)
                return index, 0.0
        except Exception:
            pass
        target.unlink()
    command = [str(PYTHON), "-I", "-c", "from totalsegmentator.bin.TotalSegmentator import main; main()",
               "-i", str(source), "-o", str(target), "--task", "body", "--device", "cpu",
               "--nr_thr_resamp", "1", "--nr_thr_saving", "1", "--ml"]
    env = os.environ.copy()
    for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[key] = THREADS
    start = time.monotonic()
    print(f"body CPU part {index} started; RAM free={free_ram_gib():.1f} GiB", flush=True)
    with log.open("w", encoding="utf-8", errors="replace") as stream:
        process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, env=env, cwd=ROOT)
        last_size = -1
        while process.poll() is None:
            time.sleep(30)
            size = log.stat().st_size
            ram = free_ram_gib()
            if size != last_size:
                last_size = size
            print(f"body part {index}: {(time.monotonic()-start)/60:.1f} min; log={size} bytes; RAM={ram:.1f} GiB", flush=True)
            if ram < MIN_RAM_GIB:
                print(f"RAM below {MIN_RAM_GIB:.0f} GiB; waiting for this inference to release memory.", flush=True)
    if process.returncode != 0 or not target.is_file():
        raise RuntimeError(f"body part {index} failed ({process.returncode}); see {log}")
    segmented, _ = load_multilabel_nifti(str(target))
    reference = nib.load(str(source))
    if segmented.shape != reference.shape or not np.allclose(segmented.affine, reference.affine, atol=1e-3):
        raise ValueError(f"body part {index} output geometry differs from its input")
    elapsed = time.monotonic() - start
    print(f"body part {index} complete in {elapsed/60:.1f} min", flush=True)
    return index, elapsed


def run_all_parts() -> dict[int, float]:
    if not PYTHON.is_file():
        raise FileNotFoundError(f"TotalSegmentator environment missing: {PYTHON}")
    if not CROP_PATH.is_file() or not CT_PATH.is_file():
        raise FileNotFoundError("NLM input CT or prepared body crop is missing")
    PARTS_OUT.mkdir(parents=True, exist_ok=True)
    pending = iter(index for index in range(1, 6) if not (PARTS_OUT / f"saida_{index:02d}.nii.gz").is_file())
    active = {}
    times = {}
    # TotalSegmentator downloads weights on first use; concurrent first calls race on one temp zip.
    # Run one worker at a time so only one process can initialize/download a task's weights.
    with ThreadPoolExecutor(max_workers=1) as pool:
        while True:
            while len(active) < 1 and free_ram_gib() >= START_RAM_GIB:
                try:
                    idx = next(pending)
                except StopIteration:
                    break
                active[pool.submit(run_part, idx)] = idx
            if not active:
                try:
                    idx = next(pending)
                except StopIteration:
                    break
                while free_ram_gib() < START_RAM_GIB:
                    print(f"Waiting for {START_RAM_GIB:.0f} GiB free RAM before body part {idx}; now {free_ram_gib():.1f} GiB", flush=True)
                    time.sleep(30)
                active[pool.submit(run_part, idx)] = idx
            done, _ = wait(active, timeout=30, return_when=FIRST_COMPLETED)
            if not done:
                print(f"body parts running; free RAM={free_ram_gib():.1f} GiB", flush=True)
                continue
            for future in done:
                idx, elapsed = future.result()
                times[idx] = elapsed
                active.pop(future)
    for index in range(1, 6):
        if not (PARTS_OUT / f"saida_{index:02d}.nii.gz").is_file():
            raise FileNotFoundError(f"body part {index} output missing after inference")
    return times


def combine() -> dict[str, int]:
    original = nib.load(str(CT_PATH))
    crop = nib.load(str(CROP_PATH))
    crop_start = np.rint(np.linalg.inv(original.affine) @ np.r_[crop.affine[:3, 3], 1])[:3].astype(int)
    crop_slices = tuple(slice(int(a), int(a + n)) for a, n in zip(crop_start, crop.shape))
    ranges = windows()
    owner = np.full(crop.shape[2], -1, dtype=np.int8)
    for z in range(crop.shape[2]):
        covers = [i for i, (start, stop) in enumerate(ranges) if start <= z < stop]
        if not covers:
            raise RuntimeError(f"No body window covers z={z}")
        owner[z] = max(covers, key=lambda i: min(z-ranges[i][0], ranges[i][1]-1-z))
    merged = np.zeros(crop.shape, dtype=np.uint8)
    label_map = None
    for i, (z0, z1) in enumerate(ranges, 1):
        image, current_map = load_multilabel_nifti(str(PARTS_OUT / f"saida_{i:02d}.nii.gz"))
        if label_map is None:
            label_map = current_map
        elif current_map != label_map:
            raise ValueError(f"body label map differs in part {i}")
        block = np.asanyarray(image.dataobj)
        for z in range(z0, z1):
            if owner[z] == i - 1:
                merged[:, :, z] = block[:, :, z-z0]
    full = np.zeros(original.shape, dtype=np.uint8)
    full[crop_slices] = merged
    output = nib.Nifti1Image(full, original.affine, original.header.copy())
    output.header.set_data_dtype(np.uint8)
    output.set_qform(original.affine, code=1)
    output.set_sform(original.affine, code=1)
    BODY_DIR.mkdir(parents=True, exist_ok=True)
    nib.save(add_label_map_to_nifti(output, label_map), str(OUT_PATH))
    counts = np.bincount(full.ravel(), minlength=max(label_map)+1)
    result = {name: int(counts[label]) for label, name in label_map.items()}
    print(f"Combined body segmentation: {OUT_PATH}", flush=True)
    print(f"Nonempty labels: {sum(v > 0 for v in result.values())}/{len(result)}; labels={label_map}", flush=True)
    print(f"Output affine preserved: {np.allclose(output.affine, original.affine)}; shape={output.shape}", flush=True)
    return result


if __name__ == "__main__":
    durations = run_all_parts()
    for index, seconds in sorted(durations.items()):
        print(f"BODY_PART_{index}_MIN={seconds/60:.1f}", flush=True)
    combine()
