# EXP-0006 — Alinhamento Denver STL→TC por intensidade

> **REGISTRO RETROSPECTIVO** — Reconstruído a partir de `hra/denver/RELATORIO.md`, `hra/denver/transformacao_stl_para_tc.json`, `hra/denver/inventario_denver.py`, `hra/denver/validar_transformacao.py` e commit `0324bc7`. Campos ausentes nas evidências são marcados como `não documentado`.

## 1. Identificação
- **ID:** `EXP-0006`
- **Título:** Alinhamento Denver STL→TC por intensidade (não validado)
- **Data:** `2026-11-25`
- **Responsável:** Joao-Guilherme-Groote (autor dos commits) — *fonte: mensagens de commit e registro do coordenador da sessão de 2026-11-25*
- **Agentes de IA:** Codex (GPT-6 Luna — execução e scripts); Claude Code (Claude Opus, coordenador: planejamento, critérios, decisões e revisão; commits com `Co-Authored-By: Claude Opus 5.5`) — *fonte: mensagens de commit e registro do coordenador da sessão de 2026-11-25*
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** `0324bc7`
- **Linha de pesquisa:** `LP01`
- **Situação:** `concluído` (resultado negativo / não validado)

## 2. Problema
Alinhar os 128 modelos STL da University of Denver (Visible Human Female) ao volume de TC DICOM da mesma coleção, cujos metadados `ImagePositionPatient` e `ImageOrientationPatient` estão ausentes.

## 3. Hipótese
A limiarização por intensidade (`valor > 200` para osso e `[-50, 150]` para músculo) permite recuperar e validar o deslocamento XY e o sinal dos eixos entre os STLs e a TC montada (`tc_alinhada.nii.gz`).

## 4. Fundamentação teórica
Amostragem de vértices de superfície em volume tomográfico NIfTI (conversão DICOM LPS→RAS e busca de deslocamento por fração de vértices acima de limiar).

## 5. Materiais e ambiente
- **Datasets e versões:** University of Denver Visible Human Female (128 STLs, 2.335.390 triângulos; 1.727 DICOMs `VHF_FullBody_CT0000.dcm`..`CT1726.dcm`).
- **Licenças:** CC BY 4.0 (`hra/denver/RELATORIO.md`).
- **Hashes:** não documentado.
- **Hardware:** não documentado.
- **Sistema operacional:** Windows.
- **Bibliotecas e versões:** Python (`numpy`, `nibabel`, `trimesh`, `pydicom` ou similar); versões exatas não documentadas.
- **Seed:** não documentado (amostragem determinística de 2.000 vértices nos fêmures).

## 6. Metodologia
- **Procedimentos e algoritmos:** montagem da TC (`673×670×1727`, espaçamento `[0.722656, 0.722656, 1.0] mm`), busca diagnóstica de sinal e origem XY, validação nos 28 STLs ósseos (`valor > 200`), 3 pares musculares (`[-50, 150]`) e teste de sensibilidade nos fêmures variando `±2, ±5, ±10 mm` em cada eixo.
- **Parâmetros:** `limiar_osso > 200`, `intervalo_musculo = [-50, 150]`, `amostra = 2000 vértices/STL` só na prova de referencial e na sensibilidade dos fêmures; na validação dos 28 ossos e dos 3 pares musculares, todos os vértices de cada STL (`hra/denver/RELATORIO.md`).
- **Comandos para reproduzir:** `python hra/denver/inventario_denver.py` e `python hra/denver/validar_transformacao.py`

## 7. Critérios de sucesso (definidos antes da execução)
Não documentado retrospectivamente (esperava-se pico estreito na curva de sensibilidade e consistência em ossos/músculos).

## 8. Resultados
- Candidato encontrado: `x' = -x + 300`, `y' = y - 700`, `z' = z` mm.
- Frações mistas nos 28 ossos (ex.: `Left_Bone_Femur 100.00%`, `Right_Bone_Fibula 47.00%`, `Right_Bone_Cuboid 37.58%`) e baixas nos músculos (`0.00%` a `40.00%`).
- Teste de sensibilidade nos fêmures permaneceu em platô: `±10 mm` manteve `98,60%–100,00%` acima do limiar.
- Auditoria DICOM mostrou `Modality=OT`, `RescaleType=US`, `PixelRepresentation=0`, slope `1`, intercept `0` (sem HU negativos), `IPP` e `IOP` ausentes.

## 9. Validação
O teste de sensibilidade reprovou a unicidade/precisão do alinhamento; registrado em `hra/denver/RELATORIO.md` e `transformacao_stl_para_tc.json` como **não validado**.

## 10. Limitações
Ausência de Unidades Hounsfield (HU) reais nos DICOMs da Denver e ausência de `ImagePositionPatient` / `ImageOrientationPatient`.

## 11. Conclusão
- **Observado:** a métrica por limiar de intensidade gera platô de 98,6–100% em `±10 mm` e falha em validar o alinhamento.
- **Interpretação:** a transformação por intensidade não pode ser usada para uso anatômico/clínico, permanecendo apenas como registro empírico negativo.
- **Veredito da hipótese:** `rejeitada`

## 12. Próximos passos
Testar registro baseado em bordas morfológicas (`EXP-0007`) e, se insuficiente, migrar para ICP sobre segmentação (`EXP-0008`).

## 13. Rastreabilidade
- **Commits:** `0324bc7`
- **Scripts:** `hra/denver/inventario_denver.py`, `hra/denver/validar_transformacao.py`
- **Logs:** não documentado
- **Resultados / artefatos:** `hra/denver/RELATORIO.md`, `hra/denver/transformacao_stl_para_tc.json`, `hra/denver/catalogo_denver.csv`

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** não documentado
- **Validação científica:** não documentado
- **Validação clínica:** não aplicável (reprovado na validação técnica)
