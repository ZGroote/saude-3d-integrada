"""Conta transcrições de sexo de tabelas dos artigos do EXP-0023.

Os CSVs são transcrições manuais de tabelas públicas, não metadados originais
baixados dos repositórios. Nenhum volume, máscara, malha ou arquivo de dados
das fontes é lido por este script.
"""

from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import csv


ROOT = Path(__file__).parent


def checksum(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> None:
    s2_path = ROOT / "S2" / "tabela1_sexo_transcricao.csv"
    with s2_path.open(encoding="utf-8", newline="") as stream:
        s2_rows = list(csv.DictReader(stream))
    s2_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in s2_rows:
        s2_counts[row["grupo"]][row["sexo_tabela"]] += 1

    s4_path = ROOT / "S4" / "coorte_sexo_agregado_transcricao.csv"
    with s4_path.open(encoding="utf-8", newline="") as stream:
        s4_rows = list(csv.DictReader(stream))

    print("S2 complete:", dict(s2_counts["completo"]))
    print("S2 additional/incomplete:", dict(s2_counts["adicional"]))
    print("S2 all table rows:", dict(s2_counts["completo"] + s2_counts["adicional"]))
    print("S4 aggregate:", {row["sexo"]: int(row["quantidade"]) for row in s4_rows})
    print("S4 case-level IDs in article table:", all(row["ids_por_caso_publicados"] == "sim" for row in s4_rows))
    for path in (s2_path, s4_path):
        print(f"SHA-256 {path.relative_to(ROOT)}: {checksum(path)}")


if __name__ == "__main__":
    main()
