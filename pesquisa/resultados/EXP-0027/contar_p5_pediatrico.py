#!/usr/bin/env python3
"""Baixa metadados de pacientes do Pediatric-CT-SEG via TCIA NBIA API (<= 50 MB) e conta por faixa e sexo."""

import hashlib
import json
import re
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

API_URL = "https://services.cancerimagingarchive.net/nbia-api/services/v1/getPatientStudy?Collection=Pediatric-CT-SEG"
OUT_JSON = Path(__file__).parent / "metadados" / "P5_pediatric_ct_seg" / "nbia_patient_study.json"


def parse_age_years(age_str: str) -> float | None:
    s = (age_str or "").strip().upper()
    m = re.match(r"^(\d+)([DWMY])$", s)
    if not m:
        return None
    val, unit = int(m.group(1)), m.group(2)
    if unit == "Y":
        return float(val)
    if unit == "M":
        return val / 12.0
    if unit == "W":
        return val / 52.0
    if unit == "D":
        return val / 365.25
    return None


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
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    OUT_JSON.write_bytes(raw)
    sha256 = hashlib.sha256(raw).hexdigest()
    print(f"nbia_patient_study.json: {len(raw)} bytes | SHA-256: {sha256}")

    records = json.loads(raw.decode("utf-8"))
    print(f"Total de estudos/registros: {len(records)}")

    bands = defaultdict(Counter)
    sex_total = Counter()
    unparsed = 0
    for rec in records:
        sex = (rec.get("PatientSex") or "").strip().upper() or "AUSENTE"
        sex_total[sex] += 1
        age_y = parse_age_years(rec.get("PatientAge") or "")
        if age_y is None:
            unparsed += 1
            continue
        b = age_band(age_y)
        if b is None:
            unparsed += 1
            continue
        bands[b][sex] += 1

    print(f"Total por sexo: {dict(sex_total)} | não classificados (<18): {unparsed}")
    for b in ["0-1", "2-5", "6-11", "12-17"]:
        c = bands[b]
        tot = sum(c.values())
        print(f"  Faixa {b:5s}: total={tot:3d} | F={c.get('F', 0):3d} | M={c.get('M', 0):3d}")


if __name__ == "__main__":
    main()
