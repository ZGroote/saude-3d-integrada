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
- **Situação:** `em execução`

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
Resultados já registrados em `hra/alinhar/RELATORIO.md` e `hra/alinhar/transformacoes.json` (Etapa A sobre `fast/segmentacao.nii.gz`):
- **Sinais vencedores:** `[1, 1, 1]`
- **Erros de ajuste (média / P95):**
  - `Femur Left`: `3.344 mm` / `6.167 mm`
  - `Femur Right`: `3.243 mm` / `5.675 mm`
  - `Pelvis Left`: `2.816 mm` / `4.926 mm`
  - `Pelvis Right`: `2.718 mm` / `4.848 mm`
- **Validação independente (`Sacrum` holdout):** média **`3.990 mm`**, P95 **`10.845 mm`**.
- **Etapa B (NLM CT → HRA):** não executada — registro em `hra/alinhar/transformacoes.json` (`stage_b.status`): `skipped: fewer than 3 paired fit structures`; `hra/alinhar/RELATORIO.md`: menos de três pares HRA/TC utilizáveis. Os artefatos `hra/alinhar/RELATORIO.md` e `transformacoes.json` ainda não estavam commitados quando este registro foi escrito.

## 9. Validação
**Reprovado** no critério pré-definido (`3.990 mm >= 3 mm`). A matriz ajustada está marcada explicitamente como diagnóstica apenas (`criterion_failed_sacrum_holdout`).

## 10. Limitações
Segmentação de entrada gerada em modo `--fast` (3 mm); experimento em andamento para investigar causas do residual e etapas seguintes.

## 11. Conclusão
- **Observado:** na Etapa A sobre `--fast`, fêmures apresentaram média ~3,3 mm, pelve ~2,7–2,8 mm e o sacro *holdout* atingiu 3,990 mm (P95 10,845 mm), reprovando no critério `< 3 mm`.
- **Interpretação:** a matriz diagnóstica da Etapa A não deve ser adotada como alinhamento aceito; a Etapa B permanece bloqueada até resolução do alinhamento A.
- **Veredito da hipótese:** `em aberto` (critério da Etapa A sobre `--fast` **rejeitado**)

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
