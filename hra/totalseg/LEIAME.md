# TotalSegmentator para hra-f

Ambiente isolado: `C:\Users\respawn\venvs\totalseg` (Python 3.14.4).

## Versões instaladas

- TotalSegmentator: 2.18.0
- PyTorch: 2.11.0+cu128
- CUDA: 12.8; `torch.cuda.is_available()` = `True` (NVIDIA GeForce GTX 1650)

## Licença da tarefa usada

A tarefa `total` está incluída na categoria aberta do README oficial do projeto. Trecho literal: **“Openly available for any usage (Apache-2.0 license):”**. O item seguinte identifica `total` como a tarefa padrão. Essa autorização é da tarefa `total`; não selecionar tarefas com termos comerciais diferentes (incluindo `appendicular_bones`, `tissue_types`, `thigh_shoulder_muscles` ou `heartchambers_highres`).

Fonte: <https://github.com/wasserth/TotalSegmentator#subtasks> (README oficial, seção “Subtasks”).

## Execução

```powershell
.\hra\totalseg\rodar_totalseg.ps1 -Nifti .\hra\denver\bruto\tc_alinhada.nii.gz
```

O script seleciona `gpu` quando `torch.cuda.is_available()` for verdadeiro e `cpu` caso contrário. Se a GPU ficar sem memória, repetir com `-Fast`, que acrescenta `--fast` (modelo de 3 mm com menor uso de memória):

```powershell
.\hra\totalseg\rodar_totalseg.ps1 -Nifti .\hra\denver\bruto\tc_alinhada.nii.gz -Fast
```

As máscaras serão gravadas em `hra/totalseg/bruto/saida/`.
