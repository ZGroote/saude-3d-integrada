"""Conta mulheres no meta.csv do TotalSegmentator V3 (extraído por extrair_meta_s1.py) e o subconjunto conservador para piloto de pelve."""
import csv, collections as C
from pathlib import Path
r = list(csv.DictReader(open(Path(__file__).parent / "metadados/S1_totalsegmentator/meta.csv", encoding="utf-8-sig"), delimiter=";"))
print("imagens:", len(r), "| sexo:", dict(C.Counter(x["gender"] or "vazio" for x in r)))
f = [x for x in r if x["gender"] == "f" and x["age"] and float(x["age"]) >= 18]
print("imagens de mulheres adultas (>=18):", len(f))
regiao = lambda x: any(k in x["study_type"] for k in ("pelvis", "lower limb", "leg", "polytrauma"))
def fino(x):
    try: return float(x["slice_thickness"]) <= 2
    except ValueError: return False
p = [x for x in f if regiao(x)]
print("  com pelve/membro inferior no tipo de estudo (inclui polytrauma):", len(p))
print("  idem, corte nativo <= 2 mm:", len([x for x in p if fino(x)]))
print("  idem, corte <= 2 mm e pathology == no_pathology:", len([x for x in p if fino(x) and x["pathology"] == "no_pathology"]))
