#!/usr/bin/env python3
"""Conta exames pediátricos (< 18 anos) no meta.csv local do TotalSegmentator V3 por faixa e sexo."""

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

META_CSV = Path(__file__).resolve().parents[1] / "EXP-0023" / "metadados" / "S1_totalsegmentator" / "meta.csv"


def age_band(age: float) -> str | None:
    if age < 0 or age >= 18:
        return None
    if age < 2:
        return "0-1"
    if age < 6:
        return "2-5"
    if age < 12:
        return "6-11"
    return "12-17"


def main() -> None:
    raw = META_CSV.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    print(f"meta.csv: {len(raw)} bytes | SHA-256: {sha256}")

    with META_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    print(f"Total de exames no meta.csv: {len(rows)}")

    bands = defaultdict(Counter)
    total_ped = 0
    empty_study_type = 0
    thicknesses = []

    for r in rows:
        age_s = (r.get("age") or "").strip()
        if not age_s:
            continue
        try:
            age = float(age_s)
        except ValueError:
            continue
        band = age_band(age)
        if band is None:
            continue
        total_ped += 1
        sex = (r.get("gender") or "").strip().lower() or "ausente"
        bands[band][sex] += 1
        if not (r.get("study_type") or "").strip():
            empty_study_type += 1
        st = (r.get("slice_thickness") or "").strip()
        if st:
            try:
                thicknesses.append(float(st))
            except ValueError:
                pass

    print(f"Total pediátricos (< 18 anos): {total_ped} (study_type vazio: {empty_study_type}/{total_ped})")
    for b in ["0-1", "2-5", "6-11", "12-17"]:
        c = bands[b]
        tot = sum(c.values())
        print(f"  Faixa {b:5s}: total={tot:3d} | f={c.get('f', 0):3d} | m={c.get('m', 0):3d} | ausente={c.get('ausente', 0):3d}")
    if thicknesses:
        thicknesses.sort()
        mid = thicknesses[len(thicknesses) // 2]
        print(f"slice_thickness (n={len(thicknesses)}): min={thicknesses[0]}, mediana={mid}, max={thicknesses[-1]}")


if __name__ == "__main__":
    main()
