"""Transforma as segmentações de um caso do TotalSegmentator em um GLB por camada anatômica.

Uso: python gerar_malhas.py <pasta_segmentations> <pasta_saida>
Fonte dos dados: TotalSegmentator small subset v2.0.1 (CC BY 4.0), Wasserthal et al., University Hospital Basel.
"""
import json
import re
import sys
from pathlib import Path

import nibabel as nib
import numpy as np
import trimesh
from skimage import measure

CAMADAS = {  # ordem importa: primeira regra que casa vence
    "coracao": r"^(heart|atrial_appendage)",
    "vasos": r"(aorta|artery|vein|vena|brachiocephalic_trunk)",
    "musculos": r"^(gluteus|iliopsoas|autochthon)",
    "ossos": r"^(vertebrae|rib_|femur|hip_|sacrum|skull|clavicula|scapula|humerus|sternum|costal)",
}
CORES = {  # RGBA 0-255
    "ossos": [233, 224, 200, 255],
    "musculos": [190, 70, 60, 255],
    "coracao": [200, 30, 45, 255],
    "vasos": [60, 90, 200, 255],
    "orgaos": [210, 150, 120, 255],
}
ALVO_TRIANGULOS = 4000  # por estrutura; ponytail: fixo, ajustar por tamanho se faltar detalhe
# RAS (x direita, y frente, z cima) -> three.js (x esquerda do paciente, y cima, z frente)
RAS_PARA_THREE = np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]], dtype=float)


def camada_de(nome):
    return next((c for c, rx in CAMADAS.items() if re.search(rx, nome)), "orgaos")


def malha(caminho):
    img = nib.as_closest_canonical(nib.load(caminho))
    mascara = np.asarray(img.dataobj) > 0
    if mascara.sum() < 50:
        return None
    mascara = np.pad(mascara, 1)  # fecha a malha nas bordas do exame
    verts, faces, _, _ = measure.marching_cubes(mascara.astype(np.uint8), 0.5, step_size=1)
    verts -= 1  # desfaz o pad
    mundo = trimesh.transform_points(verts, img.affine) / 1000.0  # mm -> m
    m = trimesh.Trimesh(mundo @ RAS_PARA_THREE.T, faces, process=True)
    if len(m.faces) > ALVO_TRIANGULOS:
        m = m.simplify_quadric_decimation(face_count=ALVO_TRIANGULOS)
    trimesh.smoothing.filter_taubin(m, iterations=10)
    return m


def main():
    origem, saida = Path(sys.argv[1]), Path(sys.argv[2])
    saida.mkdir(parents=True, exist_ok=True)
    cenas = {c: trimesh.Scene() for c in CORES}
    estruturas = {}
    for arq in sorted(origem.glob("*.nii.gz")):
        nome = arq.name.removesuffix(".nii.gz")
        m = malha(arq)
        if m is None:
            print("vazio:", nome)
            continue
        camada = camada_de(nome)
        m.visual = trimesh.visual.ColorVisuals(m, face_colors=CORES[camada])
        cenas[camada].add_geometry(m, node_name=nome, geom_name=nome)
        estruturas[nome] = {"camada": camada, "triangulos": len(m.faces)}
    # centraliza todas as camadas pelo mesmo ponto, para continuarem alinhadas
    centro = np.mean([c.bounds.mean(axis=0) for c in cenas.values() if c.geometry], axis=0)
    for camada, cena in cenas.items():
        if not cena.geometry:
            continue
        cena.apply_translation(-centro)
        (saida / f"{camada}.glb").write_bytes(cena.export(file_type="glb"))
        print(camada, len(cena.geometry), "estruturas", sum(g.faces.shape[0] for g in cena.geometry.values()), "triângulos")
    (saida / "estruturas.json").write_text(json.dumps(estruturas, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
