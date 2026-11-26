"""Confere volumes, centroides RAS e criterio anatomico da saida multilabel."""
from pathlib import Path

import nibabel as nib
import numpy as np
from totalsegmentator.nifti_ext_header import load_multilabel_nifti


ARQUIVO = Path(__file__).resolve().parent / "bruto" / "fast" / "segmentacao.nii.gz"
img, mapa = load_multilabel_nifti(str(ARQUIVO))
dados = np.asanyarray(img.dataobj)
ids = {nome: indice for indice, nome in mapa.items()}
voxel_cm3 = float(np.prod(nib.affines.voxel_sizes(img.affine)) / 1000)
print(f"shape={img.shape}; axcodes={nib.aff2axcodes(img.affine)}; affine_origem={img.affine[:3, 3].tolist()}")


def medida(nome: str) -> tuple[float, tuple[float, float, float] | None]:
    indice = ids.get(nome)
    if indice is None:
        return 0.0, None
    coords = np.where(dados == indice)
    if not len(coords[0]):
        return 0.0, None
    centro_voxel = np.array([*[float(c.mean()) for c in coords], 1.0])
    centro = img.affine @ centro_voxel
    return len(coords[0]) * voxel_cm3, tuple(float(x) for x in centro[:3])


nomes = ["femur_left", "femur_right", "hip_left", "hip_right", "sacrum",
         "vertebrae_L1", "vertebrae_L2", "vertebrae_L3", "vertebrae_L4", "vertebrae_L5",
         "kidney_left", "kidney_right", "liver", "spleen", "heart", "aorta"]
volumes = {}
for nome in nomes:
    volume, centro = medida(nome)
    volumes[nome] = volume
    sufixo = f"; centroide RAS={tuple(round(x, 1) for x in centro)} mm" if centro else ""
    print(f"{nome}: {volume:.2f} cm3{sufixo}")

pulmao_esq = sum(medida(f"lung_{lobo}_left")[0] for lobo in ("upper_lobe", "lower_lobe"))
pulmao_dir = sum(medida(f"lung_{lobo}_right")[0] for lobo in ("upper_lobe", "middle_lobe", "lower_lobe"))
print(f"pulmao esquerdo: {pulmao_esq:.2f} cm3; direito: {pulmao_dir:.2f} cm3")
criterio = all(volumes[n] > 150 for n in ("femur_left", "femur_right"))
criterio &= all(volumes[n] > 200 for n in ("hip_left", "hip_right"))
criterio &= all(volumes[n] > 0 for n in ("vertebrae_L1", "vertebrae_L2", "vertebrae_L3", "vertebrae_L4", "vertebrae_L5"))
print(f"criterio_anatomico={'PASSOU' if criterio else 'FALHOU'}")
