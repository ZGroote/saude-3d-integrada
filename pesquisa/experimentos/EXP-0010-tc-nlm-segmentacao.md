# EXP-0010 — TC original da NLM montada e segmentada em partes CPU+GPU

> **REGISTRO RETROSPECTIVO** — Reconstruído a partir de `hra/nlm/montar_tc.py`, `hra/nlm/segmentar_partes.py`, `hra/nlm/verificar_segmentacao.py`, `hra/alinhar/RELATORIO.md`, `hra/alinhar/transformacoes.json` e commit `f6935e5`. Campos ausentes nas evidências são marcados como `não documentado`.

## 1. Identificação
- **ID:** `EXP-0010`
- **Título:** TC original da NLM montada e segmentada em partes CPU+GPU (`--fast` passou no critério)
- **Data:** `2026-11-25`
- **Responsável:** não documentado
- **Agentes de IA:** não documentado
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** `f6935e5`
- **Linha de pesquisa:** `LP01`
- **Situação:** `em execução`

## 2. Problema
A TC da Denver falhou por não conter Unidades Hounsfield (HU) reais (`EXP-0009`). Além disso, o volume de corpo inteiro da NLM excede a capacidade de memória/VRAM da GTX 1650 (4 GB) se segmentado de uma só vez.

## 3. Hipótese
Montando a TC original da NLM (`c_vf1001..2734.fre.Z`, GE `IMGF`) em NIfTI RAS de `1,5 mm` com HU calibradas (`OFFSET_HU = -1024`) e executando o TotalSegmentator em blocos craniocaudais sobrepostos (CPU+GPU), é possível obter segmentação multilabel anatomicamente válida.

## 4. Fundamentação teórica
Reconstrução volumétrica a partir de cabeçalhos GE `IMGF` e `c_vf*.txt`, seguida de segmentação em janelas craniocaudais com sobreposição e recomposição sem emendas visíveis.

## 5. Materiais e ambiente
- **Datasets e versões:** NLM Visible Human Female CT (`normalCT/c_vf1001.fre.Z`..`c_vf2734.fre.Z` e `headers/c_vf1001.txt`..`c_vf2734.txt`).
- **Licenças:** Termos e Condições da NLM (sem licença desde 2019; exige crédito NLM).
- **Hashes:** não documentado.
- **Hardware:** `NVIDIA GeForce GTX 1650, 4 GB` + CPU (`hra/totalseg/LEIAME.md`, `hra/nlm/segmentar_partes.py`).
- **Sistema operacional:** Windows.
- **Bibliotecas e versões:** Python `3.14.4` (`C:\Users\respawn\venvs\totalseg`), `TotalSegmentator 2.18.0`, `PyTorch 2.11.0+cu128`, `CUDA 12.8`, `nibabel`, `numpy`, `scipy`, `gzip`.
- **Seed:** não documentado.

## 6. Metodologia
- **Procedimentos e algoritmos:** leitura dos 1.734 cortes GE `IMGF` (`HEADER_BYTES = 3416`, `512×512`), verificação de `FOV`, `Center R/A/S`, reamostragem para grade RAS de `1,5 mm` (`FOV_COMUM_MM = 480.0`, `N_PLANO = 320`), geração de `tc_nlm_1p5.nii.gz` (`montar_tc.py`); recorte corporal (`LIMIAR_AR_HU = -500.0`, `MARGEM_MM = 10.0`), divisão em blocos craniocaudais (`COMPRIMENTO_MAX_MM = 400.0`, `SOBREPOSICAO_MM = 60.0`), execução do TotalSegmentator `--fast` em partes e fusão em `hra/nlm/bruto/fast/segmentacao.nii.gz` (`segmentar_partes.py`); checagem em `verificar_segmentacao.py`.
- **Parâmetros:** `ALVO_MM = 1.5`, `OFFSET_HU = -1024`, `COMPRIMENTO_MAX_MM = 400.0`, `SOBREPOSICAO_MM = 60.0`.
- **Comandos para reproduzir:** `python hra/nlm/montar_tc.py` → `python hra/nlm/segmentar_partes.py` → `python hra/nlm/verificar_segmentacao.py`

## 7. Critérios de sucesso (definidos antes da execução)
Definidos em `hra/nlm/verificar_segmentacao.py`:
- `femur_left > 150 cm³` e `femur_right > 150 cm³`
- `hip_left > 200 cm³` e `hip_right > 200 cm³`
- `vertebrae_L1`..`vertebrae_L5 > 0 cm³`

## 8. Resultados
Até o momento nos arquivos versionados (`hra/alinhar/transformacoes.json` e `hra/alinhar/RELATORIO.md`):
- Volume multilabel `--fast` gerado em `hra/nlm/bruto/fast/segmentacao.nii.gz` com `shape_ijk = [320, 320, 1156]`, voxel `1,5 mm` isotrópico (`affine_ijk_to_world_mm` origem `[-239.25, -239.25, -1771.0]`), `117` rótulos no cabeçalho e **`114` rótulos não vazios** (incluindo fêmures, quadris, sacro, L1–L5, T1–T12, C1–C7, fígado, rins, coração, aorta e pulmões).
- Execução `--fast` reportada como aprovada no critério anatômico; segmentação em alta resolução / etapas adicionais seguem em andamento.

## 9. Validação
Verificação automatizada via `hra/nlm/verificar_segmentacao.py` (`criterio_anatomico=PASSOU` para `--fast`).

## 10. Limitações
Execução atual documentada em modo `--fast` (3 mm) devido ao limite de 4 GB de VRAM da GTX 1650.

## 11. Conclusão
- **Observado:** a TC original da NLM foi montada em 1,5 mm e segmentada em 114 rótulos não vazios no modo `--fast`.
- **Interpretação:** a segmentação `--fast` sobre a TC da NLM viabilizou o início do alinhamento real por ICP (`EXP-0011`); o experimento permanece em execução para etapas de maior resolução.
- **Veredito da hipótese:** `em aberto` (`--fast` sustentada parcialmente)

## 12. Próximos passos
Concluir segmentação em alta resolução (se aplicável) e prosseguir com o alinhamento real em `EXP-0011`.

## 13. Rastreabilidade
- **Commits:** `f6935e5`
- **Scripts:** `hra/nlm/montar_tc.py`, `hra/nlm/segmentar_partes.py`, `hra/nlm/verificar_segmentacao.py`
- **Logs:** não documentado
- **Resultados / artefatos:** `hra/nlm/bruto/fast/segmentacao.nii.gz` (fora do git), metadados em `hra/alinhar/transformacoes.json`

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** não documentado
- **Validação científica:** não documentado
- **Validação clínica:** não aplicável
