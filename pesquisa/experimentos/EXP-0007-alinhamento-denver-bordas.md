# EXP-0007 — Alinhamento Denver STL→TC por bordas (Otsu multinível)

> **REGISTRO RETROSPECTIVO** — Reconstruído a partir de `hra/denver/RELATORIO.md`, `hra/denver/validar_bordas.py`, `hra/denver/transformacao_stl_para_tc.json` e commit `0324bc7`. Campos ausentes nas evidências são marcados como `não documentado`.

## 1. Identificação
- **ID:** `EXP-0007`
- **Título:** Alinhamento Denver STL→TC por bordas (não validado: sem pico estreito)
- **Data:** `2026-11-25`
- **Responsável:** Joao-Guilherme-Groote (autor dos commits) — *fonte: mensagens de commit e registro do coordenador da sessão de 2026-11-25*
- **Agentes de IA:** Codex (GPT-6 Luna — execução e scripts); Claude Code (Claude Opus, coordenador: planejamento, critérios, decisões e revisão; commits com `Co-Authored-By: Claude Opus 5.5`) — *fonte: mensagens de commit e registro do coordenador da sessão de 2026-11-25*
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** `0324bc7`
- **Linha de pesquisa:** `LP01`
- **Situação:** `concluído` (resultado negativo / não validado)

## 2. Problema
Superar o platô observado na métrica por limiar de intensidade (`EXP-0006`) buscando o alinhamento STL→TC por coincidência com a casca de borda óssea da TC da Denver.

## 3. Hipótese
A limiarização de Otsu em 3 classes combinada com extração de borda morfológica (`máscara XOR erosão 3×3×3`) produz um pico estreito e robusto na busca conjunta por fêmures e pelve.

## 4. Fundamentação teórica
Segmentação por limiar de Otsu multinível, morfologia matemática 3D (erosão/dilatação 3×3×3, 26-conectividade) e otimização *coarse-to-fine*.

## 5. Materiais e ambiente
- **Datasets e versões:** `hra/denver/bruto/tc_alinhada.nii.gz` e 28 STLs ósseos da Denver.
- **Licenças:** CC BY 4.0.
- **Hashes:** não documentado.
- **Hardware:** não documentado.
- **Sistema operacional:** Windows.
- **Bibliotecas e versões:** Python (`numpy`, `scipy`/`skimage`, `nibabel`, `trimesh`); versões exatas não documentadas.
- **Seed:** `20261125` (amostra uniforme de 1.500.000 voxels para Otsu).

## 6. Metodologia
- **Procedimentos e algoritmos:** Otsu de 3 classes (`228.889` ar/fundo→tecido mole; `726.434` tecido mole→osso); borda `valor > 726.434` XOR erosão 3×3×3 dilatada por 3×3×3; busca coarse (`X -1200..800`, `Y -1200..0`, `Z -400..1200`, passo 40 mm, 500 vértices/estrutura em 4 estruturas: `Femur Left/Right`, `Pelvis Left/Right`) testando sinais X `-1` e `+1`; refinamento usando todos os vértices; curva de sensibilidade eixo a eixo (`±2, ±5, ±10, ±20 mm`); validação nos 28 ossos.
- **Parâmetros:** `seed=20261125`, `n_voxels=1_500_000`, `limiar_osso=726.434`, passo coarse `40 mm`.
- **Comandos para reproduzir:** `python hra/denver/validar_bordas.py`

## 7. Critérios de sucesso (definidos antes da execução)
Presença de pico estreito e consistente na curva de sensibilidade por eixo e alta fração de vértices na casca de borda nos 28 ossos.

## 8. Resultados
- Melhor candidato: sinal `X = -1`, offset `(290, -690, 430)` mm (`x' = -x + 290, y' = y - 690, z' = z + 430`), com **macro score de 19,888%** em todos os vértices (`Femur Left 12.186%`, `Pelvis Left 28.466%`, `Femur Right 6.847%`, `Pelvis Right 32.053%`), contra `0.264%` da transformação anterior do `EXP-0006`.
- Curva eixo a eixo irregular: deslocamentos vizinhos pontuaram acima do centro (ex.: `Femur Left` X `-20 mm` = `16.056%` vs `12.186%`; `Femur Right` Z `+20 mm` = `9.495%` vs `6.847%`).
- Nos 28 ossos, várias estruturas tiveram `0.000%` na borda (`Left_Bone_Cuboid`, `Left_Bone_Fibula`, `Right_Bone_Tibia`, etc.).

## 9. Validação
Reprovado na análise de sensibilidade e na validação nos 28 ossos; marcado no JSON como **não validado**.

## 10. Limitações
Intensidades reescaladas sem HU na TC da Denver, ausência de IPP/IOP e sensibilidade de borda afetada por artefatos/ruído.

## 11. Conclusão
- **Observado:** o macro score atingiu apenas 19,888%, sem pico estreito e com vários ossos em 0,000% na casca de borda.
- **Interpretação:** registro por bordas diretamente sobre a TC sem HU não é robusto; é necessário passar para segmentação semântica (TotalSegmentator) + ICP malha a malha.
- **Veredito da hipótese:** `rejeitada`

## 12. Próximos passos
Implementar pipeline de ICP malha a malha (`EXP-0008`) e segmentar TC com TotalSegmentator (`EXP-0009` / `EXP-0010`).

## 13. Rastreabilidade
- **Commits:** `0324bc7`
- **Scripts:** `hra/denver/validar_bordas.py`
- **Logs:** não documentado
- **Resultados / artefatos:** `hra/denver/RELATORIO.md`, `hra/denver/transformacao_stl_para_tc.json`

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** não documentado
- **Validação científica:** não documentado
- **Validação clínica:** não aplicável
