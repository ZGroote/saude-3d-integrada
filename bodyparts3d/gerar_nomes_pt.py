import csv
import json
from pathlib import Path

PASTA = Path(__file__).resolve().parent
ENTRADA = PASTA / "catalogo_bp3d.csv"
SAIDA = PASTA / "nomes_pt.csv"
TRADUCOES = PASTA / "traducoes_pt.json"

registros = {}
with ENTRADA.open(encoding="utf-8-sig", newline="") as arquivo:
    for linha in csv.DictReader(arquivo):
        registros.setdefault(linha["fma"], linha["nome_en"])

traducoes = json.loads(TRADUCOES.read_text(encoding="utf-8")) if TRADUCOES.exists() else {}

with SAIDA.open("w", encoding="utf-8-sig", newline="") as arquivo:
    escritor = csv.DictWriter(arquivo, fieldnames=["fma", "nome_en", "nome_pt", "validacao"])
    escritor.writeheader()
    escritor.writerows(
        {"fma": fma, "nome_en": nome_en, "nome_pt": traducoes.get(nome_en, ""), "validacao": "pendente"}
        for fma, nome_en in registros.items()
    )

print(f"Geradas {len(registros)} linhas para {len(registros)} FMA distintos em {SAIDA}")
