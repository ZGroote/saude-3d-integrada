"""Monta a base VHF feminina em RAS mm a partir das segmentações NLM e Denver.

Uso: C:\\Python314\\python.exe hra/vhf/montar_base.py
Dependências já disponíveis no Python: nibabel, numpy, scikit-image, scipy, trimesh.
Sem instalação de pacotes. Saída: atlas/hra-f/2.0-1/ (geometria em STL).
"""
from __future__ import annotations

import csv
import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import nibabel as nib
import numpy as np
import trimesh
from scipy import ndimage
from skimage.measure import marching_cubes

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "atlas" / "hra-f" / "2.0-1"
TOTAL = ROOT / "hra" / "nlm" / "bruto" / "saida" / "segmentacao.nii.gz"
BODY = ROOT / "hra" / "nlm" / "bruto" / "body" / "segmentacao.nii.gz"
DENVER_DIR = ROOT / "hra" / "denver" / "bruto" / "Final 3D STL Models-stl"
CATALOG = ROOT / "hra" / "denver" / "catalogo_denver.csv"
TRANSFORMS = ROOT / "hra" / "alinhar" / "transformacoes.json"
ALIGN = ROOT / "hra" / "alinhar" / "alinhar.py"
DENVER_TYPES = {"osso", "musculo", "cartilagem", "ligamento"}
DENVER_BONES = {
    "Bone Calcaneous", "Bone Cuboid", "Bone Femur", "Bone Fibula", "Bone IntermediateCuneiform",
    "Bone LateralCuneiform", "Bone MedialCuneiform", "Bone Navicular", "Bone Patella",
    "Bone Phalanges", "Bone Talus", "Bone Tibia",
}
DENVER_CARTILAGE = {
    "Cartilage FemurDistal", "Cartilage FemurHead", "Cartilage Patella", "Cartilage Talus",
    "Cartilage TibiaDistal", "Cartilage TibiaLateral", "Cartilage TibiaMedial",
}
LOWER_LABELS = {"femur_left", "femur_right", "tibia_left", "tibia_right",
                "fibula_left", "fibula_right", "patella_left", "patella_right", "femur", "tibia", "fibula", "patella"}
LOWER_PREFIXES = ("femur_", "tibia_", "fibula_", "patella_", "pelvis_", "gluteus_maximus_",
                  "gluteus_medius_", "gluteus_minimus_")
TAUBIN_LAMBDA = 0.45
TAUBIN_MU = -0.47
TAUBIN_ITERS = 10
MAX_FACE_COUNT = 10_000_000


def load_alignment():
    spec = importlib.util.spec_from_file_location("hra_align_reuse", ALIGN)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def taubin(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Taubin lambda/mu smoothing; no decimation, with measured volume drift."""
    mesh = mesh.copy()
    mesh.remove_unreferenced_vertices()
    mesh.process(validate=False)
    if not mesh.is_watertight:
        trimesh.repair.fill_holes(mesh)
    if mesh.is_watertight and mesh.volume < 0:
        mesh.invert()
    before = abs(float(mesh.volume)) if mesh.is_watertight else None
    if len(mesh.faces) <= MAX_FACE_COUNT:
        trimesh.smoothing.filter_taubin(mesh, lamb=TAUBIN_LAMBDA, nu=TAUBIN_MU,
                                        iterations=TAUBIN_ITERS)
    mesh.remove_unreferenced_vertices()
    if not mesh.is_watertight:
        trimesh.repair.fill_holes(mesh)
    if mesh.is_watertight:
        mesh.fix_normals(multibody=True)
        after = abs(float(mesh.volume))
        if before and after:
            # Uniform correction preserves shape and restores enclosed volume.
            mesh.apply_scale((before / after) ** (1.0 / 3.0))
            mesh.metadata["volume_drift_fraction"] = (abs(float(mesh.volume)) - before) / before
        else:
            mesh.metadata["volume_drift_fraction"] = None
    else:
        mesh.metadata["volume_drift_fraction"] = None
    return mesh


def mask_mesh(mask: np.ndarray, affine: np.ndarray, pad: int = 1) -> trimesh.Trimesh:
    padded = np.pad(mask.astype(np.uint8), pad)
    verts, faces, _, _ = marching_cubes(padded, 0.5)
    verts -= pad
    world = (np.c_[verts, np.ones(len(verts))] @ affine.T)[:, :3]
    return trimesh.Trimesh(vertices=world, faces=faces, process=False)


def total_labels(image):
    labels = {}
    for ext in image.header.extensions:
        try:
            root = ET.fromstring(ext.get_content())
            labels.update({int(x.attrib["Key"]): x.text.strip() for x in root.findall(".//LabelTable/Label")
                           if x.attrib.get("Key") and x.text})
        except Exception:
            continue
    if not labels:
        raise ValueError("Tabela de rótulos TotalSegmentator não encontrada no NIfTI")
    return labels


def file_stem(name: str) -> str:
    return "_".join(name.strip().lower().replace("-", "_").split())


def run():
    for p in (TOTAL, BODY, CATALOG, TRANSFORMS):
        if not p.is_file():
            raise FileNotFoundError(p)
    align = load_alignment()
    total = nib.load(str(TOTAL))
    values = np.asanyarray(total.dataobj)
    id_names = total_labels(total)
    named_ids = {name: ident for ident, name in id_names.items()}
    body = nib.load(str(BODY))
    body_values = np.asanyarray(body.dataobj)
    if body_values.shape != body.shape:
        raise ValueError("body NIfTI inconsistente")
    # A saída inclui uma malha por classe não vazia da task total, sem substituir
    # membro inferior Denver. Os labels totais são desmembrados individualmente.
    OUT.mkdir(parents=True, exist_ok=True)
    reports = []
    for name, ident in sorted(named_ids.items()):
        if name.lower() in LOWER_LABELS or name.lower().startswith(LOWER_PREFIXES):
            continue
        mask = values == ident
        if not mask.any():
            continue
        mesh = taubin(mask_mesh(mask, total.affine))
        key = f"total__{file_stem(name)}"
        mesh.export(OUT / f"{key}.stl")
        reports.append(mesh_record(key, mesh))
    # Label body=1 para a superfície externa; o rótulo inclui body_trunc/extremities
    # quando o modelo gera regiões separadas. Unimos os labels não-zero em uma pele.
    skin_mask = body_values > 0
    skin_mask = ndimage.binary_closing(skin_mask, structure=np.ones((3, 3, 3), dtype=bool))
    skin_mask = ndimage.binary_fill_holes(skin_mask)
    skin = taubin(mask_mesh(skin_mask, body.affine))
    if not skin.is_watertight:
        voxel = skin.voxelized(pitch=1.5, method="subdivide")
        voxel.fill(method="holes")
        skin = voxel.marching_cubes
        if not skin.is_watertight:
            trimesh.repair.fill_holes(skin)
        if skin.is_watertight:
            skin = taubin(skin)
    if not skin.is_watertight:
        raise RuntimeError("Não foi possível fechar a malha body da pele")
    skin.export(OUT / "body__skin.stl")
    reports.append(mesh_record("body__skin", skin))

    document = json.loads(TRANSFORMS.read_text(encoding="utf-8"))
    # Usa a transformação Etapa A já registrada; normalmente contém um modelo
    # separado por osso/lado. STL muscular/cartilaginoso recebe a transformação
    # do lado anatômico correspondente.
    stage = document.get("stage_a", document)
    default_matrix = np.asarray(stage.get("matrix_4x4"), dtype=float) if stage.get("matrix_4x4") else None
    rows = list(csv.DictReader(CATALOG.open(encoding="utf-8-sig", newline="")))
    denver_count = 0
    for row in rows:
        typ, structure = row.get("tipo", ""), row.get("estrutura", "")
        if typ not in DENVER_TYPES:
            continue
        if not (structure in DENVER_BONES or structure in DENVER_CARTILAGE or typ in {"musculo", "ligamento"}):
            continue
        rel = row.get("arquivo", "")
        path = DENVER_DIR / rel
        if not path.is_file():
            continue
        mesh = trimesh.load_mesh(path, process=False)
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
        side = row.get("lateralidade", "").lower()
        matrix = default_matrix
        if matrix is None:
            raise ValueError("Matriz global da Etapa A ausente")
        mesh = align.apply_matrix_to_mesh(mesh, matrix)
        mesh = taubin(mesh)
        key = f"denver__{file_stem(structure)}__{side or 'midline'}"
        mesh.export(OUT / f"{key}.stl")
        reports.append(mesh_record(key, mesh))
        denver_count += 1

    manifest = {"coordinate_system": "RAS", "units": "mm", "source_total": str(TOTAL.relative_to(ROOT)),
                "source_body": str(BODY.relative_to(ROOT)), "stage_a": str(TRANSFORMS.relative_to(ROOT)),
                "lower_limb_source": "Denver only; corresponding TotalSegmentator lower-limb labels omitted",
                "smoothing": {"method": "Taubin lambda-mu", "lambda": TAUBIN_LAMBDA, "mu": TAUBIN_MU,
                              "iterations": TAUBIN_ITERS, "decimation": "none"},
                "meshes": reports, "denver_mesh_count": denver_count}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Exported {len(reports)} meshes ({denver_count} Denver) to {OUT}")


def mesh_record(name: str, mesh: trimesh.Trimesh) -> dict:
    return {"name": name, "vertices": len(mesh.vertices), "faces": len(mesh.faces),
            "watertight": bool(mesh.is_watertight), "volume_mm3": float(abs(mesh.volume)) if mesh.is_watertight else None,
            "taubin_volume_drift_fraction": mesh.metadata.get("volume_drift_fraction"),
            "bounds_ras_mm": np.asarray(mesh.bounds).round(3).tolist()}


if __name__ == "__main__":
    run()
