# EXP-0017 — Desempenho de abertura do prontuário 3D (Etapas 4, 5 e 7)

> **REGISTRO RETROSPECTIVO** — Não houve hipótese nem critério pré-registrado no formato de `pesquisa/` antes da execução; os critérios abaixo foram tirados de `SPEC-MVP.md` (§10/§13) na data `2026-11-26`. Reconstruído a partir dos commits `867e279`, `8447a20`, `1dc037a`, `df98dd5`, `832f26e`, `3e6c960` e `web/testes/resultados/desempenho-etapa4.json`.

## 1. Identificação
- **ID:** `EXP-0017`
- **Título:** Desempenho de abertura do prontuário 3D (lista + marcadores sob CPU 4x e Fast 4G)
- **Data:** `2026-11-26` (registro retrospectivo)
- **Responsável:** não documentado
- **Agentes de IA:** não documentado
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** `867e279`, `8447a20`, `1dc037a`, `df98dd5`, `832f26e`, `3e6c960`
- **Linha de pesquisa:** `LP02`
- **Situação:** `concluído`

## 2. Problema
Avaliar se o prontuário 3D abre com lista de achados e marcadores 3D visíveis dentro do limite operacional em cenário de carga (200 achados distribuídos em 14 sistemas) sob rede restrita (Fast 4G) e CPU reduzida (4x).

## 3. Hipótese
Não houve hipótese pré-registrada antes da execução (registro retrospectivo).

## 4. Fundamentação teórica
Carregamento progressivo (`glb_leve` seguido do GLB completo em segundo plano), renderização de lista no servidor (`listar_achados`), preload do chunk 3D e montagem incremental da lista por viewport (`content-visibility: auto`).

## 5. Materiais e ambiente
- **Datasets e versões:** paciente de carga fictícia com `200` achados em `14` sistemas (`desempenho-etapa4.json`), atlas `bp3d-m/4.0-1`.
- **Licenças:** `CC BY 4.0` (BodyParts3D).
- **Hashes:** `não documentado` para a execução.
- **Hardware:** `não documentado` (emulação Playwright CPU `4x` + rede `Fast 4G`).
- **Sistema operacional:** Windows.
- **Bibliotecas e versões:** Next.js / React Three Fiber (`web/package.json`), Playwright.
- **Seed:** não aplicável.

## 6. Metodologia
- **Procedimentos e algoritmos:** build de produção servido localmente, abertura do prontuário do paciente de carga em 5 execuções consecutivas sob throttling `CPU 4x` e `Fast 4G`, medindo `lista` (primeira tela), `marcadores` / `visivel`, `lista_completa`, `corpo` (GLB leve) e `completo`.
- **Parâmetros:** `linhas = 200`, `marcadores = 200`, `primeira = 30`, CPU `4x`, `Fast 4G`.
- **Comandos para reproduzir:** `web/testes/desempenho.py` (conforme commit `1dc037a` / `867e279`).

## 7. Critérios de sucesso (tirados da SPEC na data `2026-11-26`)
Não houve critério pré-registrado no formato de `pesquisa/`; critério tirado de `SPEC-MVP.md` (§10/§13): abertura do prontuário (lista + marcadores visíveis) em **mediana `< 3 s`**.

## 8. Resultados
- **Etapa 4 (`df98dd5`, `desempenho-etapa4.json`):** mediana **`2,77 s`**, P95 **`2,98 s`** (todas as 5 aberturas `< 3 s`); primeira tela da lista `0,89 s`, lista completa `3,25 s`, corpo `3,67 s` (antes `16,9 s`), completo `~13,56 s`.
- **Etapa 5 (`832f26e`):** mediana **`2,38 s`**, P95 **`2,50 s`**.
- **Etapa 7 (`3e6c960`, servidor `3020`):** mediana **`2,68 s`**.

## 9. Validação
Todas as três rodadas registradas (`df98dd5`, `832f26e`, `3e6c960`) ficaram abaixo do limite de `3 s` (`2,77 s → 2,38 s → 2,68 s`).

## 10. Limitações
Folga pequena em relação ao limite de 3 s (`226 ms` na Etapa 4; `320 ms` na Etapa 7); clique no corpo na primeira abertura aguarda o carregamento da pele completa (`~13,6–14 s`); medições em ambiente local/homologação sob emulação de rede.

## 11. Conclusão
- **Observado:** as medianas medidas nas Etapas 4, 5 e 7 foram `2,77 s`, `2,38 s` e `2,68 s`, respectivamente, todas `< 3 s`.
- **Interpretação:** o carregamento progressivo e a renderização no servidor mantiveram o tempo de abertura dentro da meta da SPEC até a Etapa 7.
- **Veredito da hipótese:** `não aplicável` (registro retrospectivo sem hipótese prévia; critério da SPEC atendido)

## 12. Próximos passos
Repetir o benchmark a cada alteração relevante no motor 3D ou na página de prontuário.

## 13. Rastreabilidade
- **Commits:** `867e279`, `8447a20`, `1dc037a`, `df98dd5`, `832f26e`, `3e6c960`
- **Scripts:** `web/testes/desempenho.py`
- **Logs:** não documentado em arquivo separado
- **Resultados / artefatos:** `web/testes/resultados/desempenho-etapa4.json`

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** não documentado
- **Validação científica:** não documentado
- **Validação clínica:** não aplicável
