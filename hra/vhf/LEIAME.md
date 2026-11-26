# Base VHF feminina — EXP-0015

Esta pasta contém o pipeline para montar a base anatômica feminina sobre a TC NLM, conforme o protocolo pré-registrado em `pesquisa/experimentos/EXP-0015-base-tc-nlm.md`.

## Licença da task `body`

Antes da execução, conferimos a seção **“Subtasks”** do README oficial do TotalSegmentator. O trecho aplicável é:

> Openly available for any usage (Apache-2.0 license):
>
> * body: body, body_trunc, body_extremities, skin

Fonte: [README oficial do TotalSegmentator — Subtasks](https://github.com/wasserth/TotalSegmentator#subtasks) (acesso em 2026-11-26). Portanto, a task `body` está explicitamente listada como aberta para qualquer uso sob Apache-2.0. A licença do código/modelo é distinta dos termos e créditos aplicáveis à TC NLM e aos dados de origem.

## Montagem

`montar_base.py` gera malhas STL em `atlas/hra-f/2.0-1/`, no referencial RAS em milímetros. As classes não vazias de `total` são extraídas individualmente por marching cubes, exceto os rótulos de membros inferiores substituídos pela Denver; sacro e S1 permanecem do TotalSegmentator. A superfície externa é extraída da máscara `body`. A suavização usa Taubin lambda-mu sem decimação, com correção uniforme do volume fechado. A pele é preenchida/reconstruída se necessário e verificada como fechada. Cada artefato é descrito em `manifest.json`.

Os modelos Denver selecionados pelo catálogo como ossos, músculos, cartilagens e ligamentos de membros inferiores recebem a matriz `stage_a.matrix_4x4` de `hra/alinhar/transformacoes.json`. Não se instala dependência: a montagem executada usou `C:\Python314\python.exe`, que já tinha `numpy`, `nibabel`, `scikit-image`, `scipy` e `trimesh`. O venv TotalSegmentator indicado não tinha `trimesh`.

```powershell
C:\Python314\python.exe hra/vhf/montar_base.py
C:\Python314\python.exe hra/vhf/avaliar_base.py
```

O script reaproveita `apply_matrix_to_mesh` de `hra/alinhar/alinhar.py`; não modifica esse módulo. Complementos HRA estão fora do escopo desta etapa.

## Situação

Resultados e critérios funcionais F1–F4 estão em `atlas/hra-f/2.0-1/avaliacao_F1-F4.json` e em `pesquisa/experimentos/EXP-0015-base-tc-nlm.md`. F3 permaneceu não avaliado; F5 depende de revisão humana e não pode ser inferido pelo pipeline.
