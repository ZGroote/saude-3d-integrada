# TotalSegmentator para hra-f

Ambiente isolado: `C:\Users\respawn\venvs\totalseg` (Python 3.14.4).

## Versoes

- TotalSegmentator: 2.18.0
- PyTorch: 2.11.0+cu128; CUDA 12.8
- `torch.cuda.is_available()`: `True` (NVIDIA GeForce GTX 1650, 4 GB)

## Licenca

O README oficial lista a tarefa `total` sob a categoria aberta. Trecho literal: **"Openly available for any usage (Apache-2.0 license):"**. A tarefa padrao `total` e aberta; nao selecionar tarefas comerciais como `appendicular_bones`, `tissue_types`, `thigh_shoulder_muscles` ou `heartchambers_highres`.

Fonte: <https://github.com/wasserth/TotalSegmentator#subtasks> (README oficial, secao Subtasks).

## Preparacao da TC

A Denver foi entregue como `Modality=OT`, `RescaleType=US`, sem HU. Use Python isolado para converter e recortar:

```powershell
& 'C:\Users\respawn\venvs\totalseg\Scripts\python.exe' -I .\hra\totalseg\preparar_tc.py
```

O script estima modos do histograma, recorta o maior componente nao ar com margem de 10 mm e reamostra para 1,5 mm mantendo o referencial espacial. O histograma nao apresentou pico adiposo local destacado; o codigo registra o ajuste por trechos usado para ancorar o ombro adiposo em -90 HU, preservando ar=-1000 HU e musculo=+40 HU. Valores finais sao limitados a -1000..3000 HU. Saida: `hra/totalseg/bruto/tc_hu_1p5.nii.gz`.

## Execucao

```powershell
.\hra\totalseg\rodar_totalseg.ps1 -Nifti .\hra\totalseg\bruto\tc_hu_1p5.nii.gz -Fast -Saida bruto\fast
.\hra\totalseg\rodar_totalseg.ps1 -Nifti .\hra\totalseg\bruto\tc_hu_1p5.nii.gz -Saida bruto\saida
```

O script escolhe GPU se CUDA estiver disponivel, senao CPU. `--fast` usa modelo em 3 mm, recomendado para a GTX 1650 com 4 GB. Usa uma thread de reamostragem/salvamento e uma imagem multilabel para conter uso de memoria.