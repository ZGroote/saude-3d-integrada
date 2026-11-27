# EXP-0021 — Inventário comparativo bp3d-m × hra-f e levantamento de fontes para o Atlas Feminino V3

## 1. Identificação
- **ID:** `EXP-0021`
- **Título:** Inventário anatômico comparativo (lacunas femininas) e levantamento de fontes externas
- **Data:** `2026-11-27`
- **Responsável:** usuário (decisão de reabrir a linha), Claude Code (protocolo)
- **Agentes de IA:** Claude Code (protocolo e revisão), Codex (Frente A), Antigravity (Frente B); plano de origem redigido com apoio do ChatGPT
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** a preencher
- **Linha de pesquisa:** `LP01`
- **Situação:** `planejado`

## 2. Problema
O atlas feminino do MVP (`hra-f/1.10-1`, 956 malhas) tem cobertura menor que o masculino (`bp3d-m/4.0-1`, 2.234 malhas). Os EXP-0014, 0015 e 0016 tentaram completar o corpo feminino com transformações globais/regionais e não foram aceitos. Antes de qualquer nova reconstrução, falta saber **exatamente quais estruturas faltam** no feminino e **quais fontes externas existem de fato**, com licença compatível.

## 3. Hipótese
H21: as lacunas do `hra-f` em relação ao `bp3d-m` (excluídas as estruturas exclusivamente masculinas) concentram-se em ossos e músculos do membro superior, vasos dos membros e nervos periféricos — como registrado de forma não quantitativa no estado do projeto em 2026-11-25.

## 4. Fundamentação teórica
O `bp3d-m` identifica malhas por FMA e o `hra-f` por UBERON. O UBERON publica referências cruzadas (`xref: FMA:…`) que permitem o cruzamento por ontologia; correspondência por nome e revisão manual cobrem o restante.

## 5. Materiais e ambiente
- **Datasets e versões:** `bodyparts3d/catalogo_bp3d.csv` (2.234 linhas, FMA), `hra/catalogo_hra.csv` (956 linhas, UBERON), `supabase/dados/bodysite_snomed.csv` (âncoras SNOMED→FMA/UBERON); UBERON `uberon-basic.obo` (versão e SHA-256 a registrar na execução).
- **Licenças:** BodyParts3D CC BY 4.0; HRA CC BY 4.0; UBERON CC BY 3.0.
- **Hardware / SO / bibliotecas:** a registrar na execução.

## 6. Metodologia

### Frente A — Inventário (Codex)
1. Para cada malha do `bp3d-m`, procurar a correspondente no `hra-f`, nesta ordem: (a) UBERON do HRA cujo `xref` aponta para o FMA da malha; (b) nome normalizado igual; (c) revisão manual. Registrar o método usado em cada linha.
2. Classificar cada malha do `bp3d-m` em exatamente uma categoria: `presente` (mesma estrutura e lado), `parcial` (estrutura pai/filha ou agrupamento diferente), `ausente`, `exclusivo_masculino`, `nao_mapeavel` (sem FMA ou sem correspondência decidível).
3. Classificar cada malha do `hra-f` como `presente_no_bp3d`, `exclusivo_feminino` ou `so_no_hra`.
4. Prioridade clínica: **P1** = estrutura referenciada em `bodysite_snomed.csv`; **P2** = demais ossos e órgãos; **P3** = o restante.
5. Matriz de cobertura por sistema × prioridade (contagens e porcentagens).

### Frente B — Fontes externas (Antigravity, só pesquisa)
Para cada fonte — Female Atlas (GitHub HiMahendraBeniwal/female-atlas), Visible Korean Female, Chinese Visible Human, HRA-VCCF, University of Denver (máscaras e exames), Visible Human Female da NLM (RM e criossecções) — registrar, **com URL da página que comprova cada item**: disponibilidade real para download, formato, quantidade de estruturas, origem dos dados, licença (uso, modificação, redistribuição, uso comercial), resolução, referencial e método de reconstrução. Item não comprovado = `não verificado`. Proibido contornar proteção contra robôs, preencher formulários de cadastro ou baixar conjuntos grandes.

## 7. Critérios de sucesso (definidos antes da execução)
- **A1:** 100% das 2.234 malhas do `bp3d-m` e das 956 do `hra-f` classificadas em exatamente uma categoria, com método registrado.
- **A2:** revisão por Claude Code de uma amostra aleatória de 50 classificações automáticas (seed registrada); concordância `≥ 90%`. Abaixo disso, o método de cruzamento é revisto e a falha é registrada.
- **A3:** H21 é considerada **sustentada** se as quatro categorias citadas (ossos do membro superior, músculos do membro superior, vasos dos membros, nervos periféricos) somarem `≥ 50%` das malhas `ausente` do `bp3d-m`; senão, **rejeitada**.
- **B1:** as 6 fontes têm todos os campos preenchidos com valor comprovado por URL ou `não verificado`.

Este experimento é descritivo: ele não aprova nem reprova nenhum atlas.

## 8. Resultados

### Rodada 1 (2026-11-27, Codex) — A2 reprovado
- UBERON `releases/2026-11-05`, SHA-256 `1F119822…1810A397` (`uberon_origem.txt`).
- **A1 atendido:** 2.234 malhas BP3D e 956 malhas HRA classificadas. BP3D: 250 `presente`, 13 `parcial`, 1.936 `ausente`, 18 `exclusivo_masculino` e 17 `nao_mapeavel`. HRA: 184 `presente_no_bp3d`, 58 `exclusivo_feminino` e 714 `so_no_hra`.
- **A2 reprovado: 43/50 = 86% (< 90%)** na revisão de Claude Code (`revisao_A2_rodada1.csv`). As 7 divergências têm três causas:
  - (a) os nomes dos nós do HRA (`VH_F_intervertebral_disk_of_third_lumbar_vertebra`, `Allen_fornix_L`) foram ignorados. Há 50 malhas com o rótulo genérico `skeletal system` e 210 sem rótulo;
  - (b) a relação parte/todo não foi usada (árvore brônquica segmentar × brônquio segmentar, giro do cíngulo × partes, ramo × veia porta);
  - (c) a lateralidade dos nós `Allen_*_L/_R` não foi lida.
- **A3 calculado, mas sem valor de conclusão:** 257/1.936 = 13,27%. Como o denominador vem de uma classificação reprovada em A2, H21 **não** é julgada nesta rodada.

### Rodada 2 — método revisto (registrado antes de executar)
Pela regra de A2, o cruzamento é refeito. Os critérios A1–A3 e B1 **não mudam**. Mudanças no método:
1. Usar também o nome do nó do HRA: sem o prefixo `VH_F_`/`Allen_`, com `_` trocado por espaço, e com `_L`/`_R` convertidos em lado.
2. A relação pai/filha (`part_of`/`is_a`) do UBERON e as xrefs FMA dos ancestrais definem a categoria `parcial`.
3. A revisão A2 usa uma nova amostra de 50 classificações automáticas (`random.seed(22)`).

## 9. Validação
_A preencher._

## 10. Limitações
- Correspondência por ontologia não garante equivalência geométrica (uma malha pode ser `presente` mas incompleta).
- A prioridade P1 reflete as âncoras já mapeadas, não uma priorização clínica validada.

## 11. Conclusão
_A preencher._

## 12. Próximos passos
O resultado define se o EXP-0022 (auditoria do Female Atlas) e uma comparação regional (pelve e membro inferior) seguem adiante. A reconstrução integral não começa antes disto.

## 13. Rastreabilidade
- **Scripts:** `pesquisa/resultados/EXP-0021/` (a criar)
- **Resultados / artefatos:** a preencher

## 14. Revisão
- **Revisor:** Claude Code (amostra A2)
- **Revisão humana:** pendente
- **Validação científica:** não se aplica (inventário)
