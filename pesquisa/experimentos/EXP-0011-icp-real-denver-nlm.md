# EXP-0011 — ICP real Denver↔TC NLM (Etapa A)

> **REGISTRO RETROSPECTIVO** — Reconstruído a partir de `hra/alinhar/RELATORIO.md`, `hra/alinhar/transformacoes.json`, `hra/alinhar/alinhar.py` e commits `fdb9441`, `8692651`, `f6935e5`. Campos ausentes nas evidências são marcados como `não documentado`.

## 1. Identificação
- **ID:** `EXP-0011`
- **Título:** ICP real Denver↔TC NLM Etapa A
- **Data:** `2026-11-25`
- **Responsável:** Joao-Guilherme-Groote (autor dos commits) — *fonte: mensagens de commit e registro do coordenador da sessão de 2026-11-25*
- **Agentes de IA:** Codex (GPT-6 Luna — execução do ICP); Claude Code (Claude Opus, coordenador: planejamento, critérios, decisões e revisão; commits com `Co-Authored-By: Claude Opus 5.5`) — *fonte: mensagens de commit e registro do coordenador da sessão de 2026-11-25*
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** `fdb9441`, `8692651`, `f6935e5`
- **Linha de pesquisa:** `LP01`
- **Situação:** `concluído — reprovado no critério de 3 mm`

## 2. Problema
Alinhar os modelos ósseos STL da University of Denver às superfícies segmentadas da TC original da NLM (Etapa A) e, posteriormente, a TC da NLM ao atlas HRA Female `1.10-1` (Etapa B).

## 3. Hipótese
O ICP rígido ajustado sobre quatro estruturas de treino (`femur_left`, `femur_right`, `hip_left`, `hip_right`) alinha os STLs da Denver à TC da NLM com erro médio `< 3 mm` na estrutura independente de *holdout* (`sacrum`).

## 4. Fundamentação teórica
ICP rígido com busca dos 8 sinais de eixos, extração de superfícies das máscaras NIfTI via *marching cubes* e avaliação por erro simétrico de superfície em estrutura *holdout* independente (`sacrum`).

## 5. Materiais e ambiente
- **Datasets e versões:** STLs da Denver (`hra/denver/bruto/Final 3D STL Models-stl/`), segmentação multilabel `hra/nlm/bruto/fast/segmentacao.nii.gz` (`EXP-0010`) e `atlas/hra-f/1.10-1/`.
- **Licenças:** CC BY 4.0 (Denver / HRA) + termos NLM.
- **Hashes:** não documentado para os arquivos de entrada da Etapa A.
- **Hardware:** não documentado.
- **Sistema operacional:** Windows.
- **Bibliotecas e versões:** Python (`nibabel`, `numpy`, `trimesh`, `scikit-image`); Node.js (`decoder_glb.mjs`). Versões exatas não documentadas.
- **Seed:** `seed=1` em `sample_mesh` / `point_union` (`hra/alinhar/alinhar.py`).

## 6. Metodologia
- **Procedimentos e algoritmos:** extração de malhas por *marching cubes* de `hra/nlm/bruto/fast/segmentacao.nii.gz`, busca nos 8 sinais de eixos para ICP rígido (`iterations=20`) nas 4 estruturas de ajuste (`Femur Left`, `Femur Right`, `Pelvis Left`, `Pelvis Right`) e validação independente no `Sacrum` (*holdout*). Etapa B bloqueada automaticamente caso o critério do sacro falhe.
- **Parâmetros:** `iterations = 20`, ajuste `rigid`, 4 estruturas de fit + 1 *holdout*.
- **Comandos para reproduzir:** `python hra/alinhar/alinhar.py --multilabel hra/nlm/bruto/fast/segmentacao.nii.gz`

## 7. Critérios de sucesso (definidos antes da execução)
Erro médio simétrico de superfície no `Sacrum` (*holdout*) **`< 3 mm`**.

## 8. Resultados
- **Rodada 1 (`--fast`, `hra/nlm/bruto/fast/segmentacao.nii.gz`, 2026-11-25):** sinais vencedores `[1, 1, 1]`; `Femur Left` `3,344 mm` (P95 `6,167 mm`), `Femur Right` `3,243 mm` (P95 `5,675 mm`), `Pelvis Left` `2,816 mm` (P95 `4,926 mm`), `Pelvis Right` `2,718 mm` (P95 `4,848 mm`), **`Sacrum` (holdout) `3,990 mm` (P95 `10,845 mm`)**. Etapa B não executada (`skipped: fewer than 3 paired fit structures` em `transformacoes.json`).
- **Rodada 2 (resolução normal `1,5 mm`, `hra/nlm/bruto/saida/segmentacao.nii.gz`, commit `5ec1c34`, 2026-11-26):** sinais vencedores `[1, 1, 1]`; `Femur Left` `3,006 mm` (P95 `5,717 mm`), `Femur Right` `3,234 mm` (P95 `6,155 mm`), `Pelvis Left` `3,027 mm` (P95 `4,771 mm`), `Pelvis Right` `2,707 mm` (P95 `4,743 mm`), **`Sacrum NLM vs Denver Sacrum + Coccyx` (holdout) `3,785 mm` (P95 `9,602 mm`)**. *Mudança de método entre rodadas:* na Rodada 2 o comparador do holdout passou de `Sacrum` Denver para a união `Sacrum + Coccyx` Denver (o cóccix é separado nos STLs da Denver e incluído na máscara `sacrum` do TotalSegmentator); o limite `< 3 mm` não foi alterado.

## 9. Validação
**Reprovado** no critério pré-definido (`< 3 mm`) em ambas as rodadas (`3,990 mm` na Rodada 1 `--fast` e `3,785 mm` na Rodada 2 em resolução normal). A matriz ajustada permanece marcada como diagnóstica apenas (`EXP-0011` não alterado retroativamente após o `EXP-0014`).

## 10. Limitações
Diferenças anatômicas/de segmentação residuais no sacro entre os STLs da Denver e a máscara do TotalSegmentator mantiveram o erro médio em ~3,8–4,0 mm.

## 11. Conclusão
- **Observado:** tanto sobre `--fast` (`3,990 mm`) quanto sobre resolução normal (`3,785 mm`), o sacro *holdout* permaneceu acima do limite `< 3 mm`.
- **Interpretação:** a hipótese de alinhamento rígido `< 3 mm` foi rejeitada sob esse critério; a avaliação de aceitação por finalidade passou a ser conduzida separadamente no `EXP-0014` (mantendo o `EXP-0011` reprovado).
- **Veredito da hipótese:** `rejeitada` (critério `< 3 mm` não atingido)

## 12. Próximos passos
Investigar origem do erro residual no sacro (ex.: resolução `--fast` de 3 mm vs. resolução completa, ou segmentação/diferença anatômica local).

## 13. Rastreabilidade
- **Commits:** `fdb9441`, `8692651`, `f6935e5`
- **Scripts:** `hra/alinhar/alinhar.py`, `hra/alinhar/decoder_glb.mjs`
- **Logs:** não documentado
- **Resultados / artefatos:** `hra/alinhar/RELATORIO.md`, `hra/alinhar/transformacoes.json`

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** não documentado
- **Validação científica:** não documentado
- **Validação clínica:** não aplicável
