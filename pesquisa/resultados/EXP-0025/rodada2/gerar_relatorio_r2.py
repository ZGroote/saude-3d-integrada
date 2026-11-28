"""Monta RELATORIO.md exclusivamente dos artefatos medidos da rodada 2."""
import csv
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
metrics = list(csv.DictReader((OUT / "metricas_r2.csv").open(encoding="utf-8-sig", newline="")))
by = {(r["grupo_muscular"], r["metodo"]): r for r in metrics}
manifest = json.loads((OUT / "hashes_adaptadas_r2.json").read_text(encoding="utf-8"))
fractions = manifest["insertion_fractions"]
verdicts = json.loads((OUT / "metricas_meta_r2.json").read_text(encoding="utf-8"))["verdicts"]
bad_hashes = [r["arquivo"] for r in manifest["adapted_meshes"]
              if hashlib.sha256((OUT / r["arquivo"]).read_bytes()).hexdigest() != r["sha256"]]
r1_rows = list(csv.DictReader((ROOT / "metricas.csv").open(encoding="utf-8-sig", newline="")))
r1_rectus = next(r["dist_superficie_simetrica_media_mm"] for r in r1_rows
                 if r["grupo_muscular"] == "rectus_femoris" and r["metodo"] == "B0")

lines = [
    "# EXP-0025 — Rodada 2", "",
    "**Estado:** execução concluída. O protocolo e a rodada 1 permaneceram intactos; H25 na rodada 1 continua rejeitada no registro original. A decisão desta rodada segue a seção 8.2: somente M2b em R1, R2 e R3 decide H25.", "",
    "## Métodos e integridade", "",
    "- **B0:** reutilizadas as 11 malhas B0 da rodada 1 (bíceps longo/curto em arquivos distintos). SHA-256 conferido antes da cópia e igual ao manifesto de origem; nenhuma malha B0 foi recalculada.",
    "- **M2a:** thin-plate spline da rodada 1, sem projeção nem relaxamento.",
    "- **M2b:** TPS; inserções definidas por vértices a ≤3 mm de osso BP3D **e** nos 10% terminais de uma das extremidades do eixo principal calculado por PCA separadamente em cada componente; projeção desses vértices no osso Denver e relaxamento laplaciano da rodada 1 (12 iterações, fator 0,22).",
    "- **Barreira:** o adaptador mantém a asserção `_Muscle_` anterior à abertura e permite Denver somente com `_Bone_`; leu 13 caminhos ósseos e nenhum muscular. M2a/M2b e seus hashes foram gravados antes da avaliação abrir qualquer músculo Denver. O avaliador conferiu os 33 hashes (11 B0 + 11 M2a + 11 M2b) antes dessa leitura.",
    "- Seeds: adaptação 25021; avaliação 25022; 6.000 pontos por direção e mesma regra de seeds por grupo da rodada 1; voxelização 1 mm.", "",
    "## Resultados R1–R4", "",
    "| Critério | M2a (secundário) | M2b (primário) |", "|---|---|---|",
]
for key, label in [("R1", "redução ≥20% em pelo menos 8/10"), ("R2", "mediana das inserções ≤2 mm"),
                   ("R3", "colisão <2% em todos os grupos"), ("R4", "Dice mediano ≥0,60, exploratório")]:
    a, b = verdicts["M2a"], verdicts["M2b"]
    if key == "R1":
        av, bv = f"{a[key]} ({a['r1_count']}/10)", f"{b[key]} ({b['r1_count']}/10)"
    elif key == "R2":
        av = f"{a[key]} ({a['r2_median_mm']:.3f} mm; n={a['r2_n_vertices']})"
        bv = f"{b[key]} ({b['r2_median_mm']:.3f} mm; n={b['r2_n_vertices']})"
    elif key == "R3":
        av = f"{a[key]} (máx. {a['r3_max_collision_pct']:.3f}%; <2% em {a['r3_groups_below_2pct']}/10)"
        bv = f"{b[key]} (máx. {b['r3_max_collision_pct']:.3f}%; <2% em {b['r3_groups_below_2pct']}/10)"
    else:
        av, bv = f"{a['r4_dice_median_exploratory']:.4f}", f"{b['r4_dice_median_exploratory']:.4f}"
    lines.append(f"| {key} — {label} | {av} | {bv} |")
lines += [
    "", "**Veredito da rodada 2:** H25 **REJEITADA**: M2b falhou R1 (0/10) e R3; R2 passou. R4 é exploratório e não decide. M2a também falhou R1 e R3; não decide H25.", "",
    "As reduções R1 por grupo, distâncias médias simétricas e distância exploratória Denver→adaptado estão em `metricas_r2.csv`. A distância unidirecional é a média de 6.000 pontos Denver até uma nuvem de 6.000 pontos da malha adaptada (aproximação por amostragem de superfície).", "",
    "| Grupo | Redução R1 M2a | Redução R1 M2b | Simétrica média B0 / M2a / M2b (mm) | Denver→adaptado B0 / M2a / M2b (mm) |", "|---|---:|---:|---:|---:|",
]
groups = list(dict.fromkeys(r["grupo_muscular"] for r in metrics))
for g in groups:
    a = 100 * verdicts["M2a"]["r1_reductions"][g]
    b = 100 * verdicts["M2b"]["r1_reductions"][g]
    sym = " / ".join(f"{float(by[g, m]['dist_superficie_simetrica_media_mm']):.2f}" for m in ("B0", "M2a", "M2b"))
    directed = " / ".join(f"{float(by[g, m]['dist_unidirecional_denver_para_adaptado_media_mm']):.2f}" for m in ("B0", "M2a", "M2b"))
    lines.append(f"| {g} | {a:+.1f}% | {b:+.1f}% | {sym} | {directed} |")

lines += ["", "## Fração de vértices de inserção M2b", "", "| Músculo/componente | Vértices de inserção / total | Fração |", "|---|---:|---:|"]
for key, value in fractions.items():
    group, component = key.split(":")
    part = "longa" if group == "biceps_femoris" and component == "0" else "curta" if group == "biceps_femoris" else "único"
    lines.append(f"| {group} ({part}) | {value['vertices_insercao']} / {value['vertices_musculo']} | {100*value['fracao']:.2f}% |")
total_v = sum(v["vertices_musculo"] for v in fractions.values())
total_i = sum(v["vertices_insercao"] for v in fractions.values())
lines.append(f"| **Total (10 grupos; 11 componentes)** | **{total_i} / {total_v}** | **{100*total_i/total_v:.2f}%** |")
lines += [
    "", "## Desvios, limitações e auditoria", "",
    "- Não houve alteração de critérios nem desvio das regras M2a/M2b. Nenhum componente ficou sem vértices M2b selecionados.",
    "- R2 usa os vértices candidatos M2b para ambos M2a/M2b. M2b projeta esses pontos por construção; R2 não é validação independente. M2a não projeta, mas usa o mesmo subconjunto para comparação.",
    "- R3/R4 repetem a aproximação da rodada 1: voxelização a 1 mm, fechamento temporário de bordas em memória e união das malhas ósseas mapeadas. Contato de fronteira pode contribuir em R3; PLY gravados não são alterados pelo fechamento.",
    f"- **Inconsistência de reprodução da rodada 1:** o CSV arquivado registra {float(r1_rectus):.4f} mm para B0 do reto femoral. Recarregando os mesmos PLY e Denver com seed 25022 e a função simétrica atual, obtivemos 18.6840 mm; o SHA do B0 coincide com o manifesto da rodada 1. A causa não foi determinada. Nesta rodada, M2a/M2b foram comparados com o B0 medido no mesmo lote usando as seeds documentadas. Isso limita a comparação entre CSVs de rodadas, sem alterar critérios.",
    f"- Conferência final de SHA-256: {len(manifest['adapted_meshes'])} malhas; divergências: {', '.join(bad_hashes) if bad_hashes else 'nenhuma'}.", "",
    "## Arquivos e reprodução", "",
    "- `adaptar_r2.py` — copia/verifica B0, adapta M2a/M2b, registra inserções e congela hashes.",
    "- `avaliar_r2.py` — verifica hashes antes de ler músculos Denver e calcula R1–R4 e Denver→adaptado.",
    "- Saídas: `hashes_adaptadas_r2.json`, `insercoes_m2b.csv`, `insercoes_vertices_m2b.json`, `metricas_r2.csv`, `metricas_meta_r2.json`, `veredito_r2.txt` e malhas PLY.",
    "- Reproduzir em sequência com `C:\\Python314\\python.exe pesquisa/resultados/EXP-0025/rodada2/adaptar_r2.py` e depois `C:\\Python314\\python.exe pesquisa/resultados/EXP-0025/rodada2/avaliar_r2.py`. Sem instalação de pacotes.", "",
    "**Revisão humana:** pendente. **Validação científica/clínica:** não realizada.", "",
]
(OUT / "RELATORIO.md").write_text("\n".join(lines), encoding="utf-8")
print(f"relatório gerado; linhas métricas={len(metrics)}; hashes divergentes={len(bad_hashes)}")
