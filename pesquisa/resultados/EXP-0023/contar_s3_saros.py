#!/usr/bin/env python3
"""Conta mulheres/homens e regiões anatômicas nos metadados públicos do SAROS (S3)."""

import csv
from collections import Counter, defaultdict
from pathlib import Path

CSV_PATH = Path(__file__).parent / "metadados" / "S3_saros" / "Segmentation-Info_09-29-2023.csv"


def main() -> None:
    with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    print(f"Total de séries (linhas): {len(rows)}")

    series_by_gender = Counter(r["gender"].strip().lower() for r in rows)
    print("Séries por sexo:", dict(series_by_gender))

    patients_by_gender: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        patients_by_gender[r["gender"].strip().lower()].add(r["tcia_case_id"].strip())

    all_patients = {r["tcia_case_id"].strip() for r in rows}
    print(f"Pacientes únicos (tcia_case_id): {len(all_patients)}")
    for g, pset in sorted(patients_by_gender.items()):
        print(f"  Pacientes {g}: {len(pset)}")

    female_regions = Counter(
        r["anatomic_region"].strip().lower()
        for r in rows
        if r["gender"].strip().lower() == "female"
    )
    print("Regiões anatômicas (séries femininas):", dict(female_regions))

    implants = Counter(r["has_breast_implant"].strip().upper() for r in rows)
    print("Implante mamário (todas as séries):", dict(implants))


if __name__ == "__main__":
    main()
