# EXP-0009 — TotalSegmentator na TC da Denver convertida por histograma

> **REGISTRO RETROSPECTIVO** — Reconstruído a partir de `hra/totalseg/LEIAME.md`, `hra/totalseg/preparar_tc.py`, `hra/totalseg/rodar_totalseg.ps1`, `hra/alinhar/alinhar.py` (linha 726) e commits `0324bc7`, `8692651`. Campos ausentes nas evidências são marcados como `não documentado`.

## 1. Identificação
- **ID:** `EXP-0009`
- **Título:** TotalSegmentator na TC da Denver convertida por histograma (ossos falharam; GPU 4 GB)
- **Data:** `2026-11-25`
- **Responsável:** Joao-Guilherme-Groote (autor dos commits) — *fonte: mensagens de commit e registro do coordenador da sessão de 2026-11-25*
- **Agentes de IA:** Codex 2 (GPT-6 Luna — instalação e execução do TotalSegmentator, `preparar_tc.py`); Claude Code (Claude Opus, coordenador: planejamento, critérios, decisões e revisão; commits com `Co-Authored-By: Claude Opus 5.5`) — *fonte: mensagens de commit e registro do coordenador da sessão de 2026-11-25*
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** `0324bc7`, `8692651`
- **Linha de pesquisa:** `LP01`
- **Situação:** `concluído` (resultado negativo / inválido)

## 2. Problema
A TC da Denver foi entregue em `Modality=OT`, `RescaleType=US`, sem Unidades Hounsfield (HU), impedindo a aplicação direta do TotalSegmentator (treinado em TC em HU). Além disso, o hardware local dispõe de GPU de apenas 4 GB.

## 3. Hipótese
A calibração por ajuste de histograma por trechos (ancorando ar em `-1000 HU`, ombro adiposo em `-90 HU` e músculo em `+40 HU`) e reamostragem para `1,5 mm` permite que o TotalSegmentator (`--fast`, 3 mm) segmente adequadamente os ossos na TC da Denver.

## 4. Fundamentação teórica
Normalização de intensidades por modas do histograma e segmentação semântica por aprendizado profundo (TotalSegmentator tarefa `total`).

## 5. Materiais e ambiente
- **Datasets e versões:** `hra/denver/bruto/tc_alinhada.nii.gz` -> `hra/totalseg/bruto/tc_hu_1p5.nii.gz`.
- **Licenças:** Denver CC BY 4.0; TotalSegmentator tarefa `total` sob Apache-2.0 (`hra/totalseg/LEIAME.md`).
- **Hashes:** não documentado.
- **Hardware:** `NVIDIA GeForce GTX 1650, 4 GB`.
- **Sistema operacional:** Windows.
- **Bibliotecas e versões:** Python `3.14.4` (`C:\Users\respawn\venvs\totalseg`), `TotalSegmentator 2.18.0`, `PyTorch 2.11.0+cu128`, `CUDA 12.8`, `nibabel`, `numpy`, `scipy`.
- **Seed:** não documentado.

## 6. Metodologia
- **Procedimentos e algoritmos:** cálculo de histograma suavizado (`gaussian_filter1d`, `sigma=2`), busca de picos (`find_peaks`), ajuste por trechos para HU (`-1000..3000 HU`), recorte do maior componente não-ar com margem de `10 mm`, reamostragem para `1,5 mm` (`preparar_tc.py`), e execução do TotalSegmentator `--fast` em saída multilabel (`rodar_totalseg.ps1`).
- **Parâmetros:** `ESPACAMENTO_ALVO = 1.5 mm`, `FAIXA_HU = (-1000.0, 3000.0)`, `--fast` (3 mm).
- **Comandos para reproduzir:**
  - `& 'C:\Users\respawn\venvs\totalseg\Scripts\python.exe' -I .\hra\totalseg\preparar_tc.py`
  - `.\hra\totalseg\rodar_totalseg.ps1 -Nifti .\hra\totalseg\bruto\tc_hu_1p5.nii.gz -Fast -Saida bruto\fast`

## 7. Critérios de sucesso (definidos antes da execução)
Segmentação óssea anatomicamente válida (fêmures, pelve, sacro e vértebras) para alimentar o ICP.

## 8. Resultados
O histograma não apresentou pico adiposo local destacado; na execução `--fast` sobre a TC da Denver convertida, a segmentação dos ossos falhou (registrado em `hra/alinhar/alinhar.py` linha 726: `# Prevent accidental use of the known-invalid Denver fast result.`). Métricas numéricas detalhadas da falha: `não documentado`.

## 9. Validação
Resultado marcado explicitamente no código como inválido (`known-invalid Denver fast result`).

## 10. Limitações
Ausência de HU reais na TC da Denver e restrição de VRAM (4 GB) da GTX 1650, que limita a resolução de execução.

## 11. Conclusão
- **Observado:** a conversão sintética de histograma da TC da Denver não recuperou contraste adequado para segmentação óssea pelo TotalSegmentator `--fast`.
- **Interpretação:** é necessário abandonar a TC reescalada da Denver e utilizar a TC original da NLM em formato GE `IMGF` com HU reais (`EXP-0010`).
- **Veredito da hipótese:** `rejeitada`

## 12. Próximos passos
Baixar, montar e segmentar a TC original do Visible Human Female da NLM (`EXP-0010`).

## 13. Rastreabilidade
- **Commits:** `0324bc7`, `8692651`, `fdb9441`
- **Scripts:** `hra/totalseg/preparar_tc.py`, `hra/totalseg/rodar_totalseg.ps1`
- **Logs:** não documentado
- **Resultados / artefatos:** `hra/totalseg/LEIAME.md`, `hra/totalseg/bruto/` (fora do git)

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** não documentado
- **Validação científica:** não documentado
- **Validação clínica:** não aplicável
