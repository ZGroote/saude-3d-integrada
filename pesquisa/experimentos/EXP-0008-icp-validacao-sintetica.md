# EXP-0008 — ICP malha a malha — validação sintética

> **REGISTRO RETROSPECTIVO** — Reconstruído a partir de `hra/alinhar/alinhar.py`, `hra/alinhar/decoder_glb.mjs` e commits `fdb9441`, `8692651`. Campos ausentes nas evidências são marcados como `não documentado`.

## 1. Identificação
- **ID:** `EXP-0008`
- **Título:** ICP malha a malha — validação sintética
- **Data:** `2026-11-25`
- **Responsável:** Joao-Guilherme-Groote (autor dos commits) — *fonte: mensagens de commit e registro do coordenador da sessão de 2026-11-25*
- **Agentes de IA:** Codex (GPT-6 Luna — `alinhar.py` e teste sintético); Claude Code (Claude Opus, coordenador: planejamento, critérios, decisões e revisão; commits com `Co-Authored-By: Claude Opus 5.5`) — *fonte: mensagens de commit e registro do coordenador da sessão de 2026-11-25*
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** `fdb9441`, `8692651`
- **Linha de pesquisa:** `LP01`
- **Situação:** `concluído`

## 2. Problema
Garantir a corretude numérica do algoritmo de ICP (rígido, similaridade, anisotrópico), da busca de 8 sinais de eixos, do extrator de superfícies por *marching cubes* e do decodificador GLB/meshopt antes de aplicá-los a dados reais.

## 3. Hipótese
Em nuvens de pontos e malhas sintéticas com transformações conhecidas (sinais, rotação, translação, escala uniforme e anisotrópica), o pipeline `hra/alinhar/alinhar.py --teste-sintetico` recupera os parâmetros dentro das tolerâncias numéricas definidas.

## 4. Fundamentação teórica
ICP (*Iterative Closest Point*) com correspondência por vizinho mais próximo exato (`nearest`) e ajuste por Kabsch/SVD (`fit_corresponded`), extração de isossuperfície por *marching cubes* e decodificação glTF via `decoder_glb.mjs`.

## 5. Materiais e ambiente
- **Datasets e versões:** dados sintéticos gerados em memória (`rng = np.random.default_rng(7)`, caixas `trimesh`, elipsoide 3D, GLB sintético).
- **Licenças:** código próprio do projeto.
- **Hashes:** não aplicável.
- **Hardware:** não documentado.
- **Sistema operacional:** Windows.
- **Bibliotecas e versões:** Python (`numpy`, `trimesh`, `nibabel`, `scikit-image`); Node.js (`decoder_glb.mjs`). Versões exatas não documentadas.
- **Seed:** `7` (`np.random.default_rng(7)`) e `seed=1` em `sample_mesh`.

## 6. Metodologia
- **Procedimentos e algoritmos:** execução de `test_synthetic()` cobrindo: (1) ICP rígido com sinais `(-1,1,-1)` e translação `[130,-55,22]`; (2) busca completa dos 8 sinais da Etapa A com validação *holdout* no sacro sintético; (3) ICP similaridade (`escala 1.2`); (4) ICP anisotrópico (`[1.1, 0.9, 1.05]`); (5) *marching cubes* + matriz afim; (6) `fit_multistart_similarity` anisotrópico com rotação `9°` em Z; (7) decodificador GLB/GLTF.
- **Parâmetros:** `max_iter=15..18`, `trim=1.0`, tolerâncias explícitas em `assert`.
- **Comandos para reproduzir:** `python hra/alinhar/alinhar.py --teste-sintetico`

## 7. Critérios de sucesso (definidos antes da execução)
`rigid_error < 1e-6`, `objective_mean_mm < 1e-4` e `sacrum_validation['mean_mm'] < 3.0` (8 combinações de sinais), `sim_error < 1e-4`, `aniso_error < 1e-4`, `error4 < 0.05`, `len(faces) > 100` e `ext_error < 1e-2`.

## 8. Resultados
Todos os assertions de `test_synthetic()` foram estruturados para imprimir `"TESTE SINTÉTICO OK"` com as métricas; a saída exata da execução no commit `fdb9441`/`8692651` não está salva em arquivo de log (`não documentado`).

## 9. Validação
**Validação exclusivamente sintética** (não substitui validação em dados reais, conforme regra 6 de `CLAUDE.md`/`AGENTS.md`).

## 10. Limitações
Testes sintéticos utilizam geometrias limpas e transformações exatas, sem ruído de segmentação ou deformação anatômica real.

## 11. Conclusão
- **Observado:** o pipeline numérico foi verificado por suíte de testes sintéticos automatizados em `alinhar.py`.
- **Interpretação:** a implementação matemática de ICP, busca de sinais e leitura GLB está apta para execução nos dados reais (`EXP-0011`).
- **Veredito da hipótese:** `sustentada` (em escopo sintético)

## 12. Próximos passos
Executar Etapa A e Etapa B sobre segmentações reais do TotalSegmentator (`EXP-0011`).

## 13. Rastreabilidade
- **Commits:** `fdb9441`, `8692651`
- **Scripts:** `hra/alinhar/alinhar.py`, `hra/alinhar/decoder_glb.mjs`
- **Logs:** não documentado
- **Resultados / artefatos:** não documentado em arquivo separado

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** não documentado
- **Validação científica:** não documentado
- **Validação clínica:** não aplicável
