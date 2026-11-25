# Teste: anatomia 3D a partir de tomografia

- `visualizador.html`: abra com dois cliques (precisa de internet só para carregar o three.js).
- `modelos/*.glb`: uma malha por camada; cada estrutura é um nó com nome fixo (`aorta`, `femur_left`...).
- `scripts/`: `baixar_caso.py` (baixa um caso só) → `gerar_malhas.py` → `gerar_visualizador.py`.

Fonte dos dados (crédito exigido pela licença CC BY 4.0):
Wasserthal J. et al., "TotalSegmentator: Robust Segmentation of 104 Anatomic Structures in CT Images",
Radiology: Artificial Intelligence, 2023. Dataset "Small subset of TotalSegmentator Dataset" v2.0.1,
University Hospital Basel — https://zenodo.org/records/10047263 — caso s1371.
