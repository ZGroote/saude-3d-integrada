"""Build EXP-0016 hybrid GLBs from HRA v1.10 and source RAS-mm STLs."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
HRA = ROOT / "web" / "public" / "atlas" / "hra-f" / "1.10-1"
VHF = ROOT / "web" / "public" / "atlas" / "vhf-f" / "0.1-0"
STL_BASE = ROOT / "atlas" / "hra-f" / "2.0-1"
TRANSFORMS = ROOT / "hra" / "alinhar" / "transformacoes.json"
NPM = shutil.which("npx.cmd") or shutil.which("npx")
APP_TO_RAS = np.array([[-1000., 0, 0, 0], [0, 0, 1000, 0], [0, 1000, 0, 0], [0, 0, 0, 1]])
RAS_TO_APP = np.linalg.inv(APP_TO_RAS)
REGION_BY_NAME = {
    "head_neck": ("vertebrae_c", "skull", "mandible", "hyoid"),
    "thorax": ("vertebrae_t", "rib_", "sternum", "costal_cartilage", "clavicula", "scapula", "humerus", "ulna", "radius", "hand", "carpal", "metacarpal"),
    "abdomen_pelvis": ("vertebrae_l", "sacrum", "coccyx", "hip_", "pelvis", "femur", "patella", "tibia", "fibula", "talus", "calcaneous", "calcaneus", "cuboid", "cuneiform", "navicular", "metatarsal", "phalanges"),
}

align_spec = importlib.util.spec_from_file_location("exp16_align", ROOT / "hra" / "alinhar" / "alinhar.py")
align = importlib.util.module_from_spec(align_spec)
assert align_spec and align_spec.loader
align_spec.loader.exec_module(align)
pack_spec = importlib.util.spec_from_file_location("exp16_vhf_pack", ROOT / "hra" / "vhf" / "gerar_pacote_revisao.py")
pack = importlib.util.module_from_spec(pack_spec)
assert pack_spec and pack_spec.loader
pack_spec.loader.exec_module(pack)
SYSTEMS = sorted(pack.SYSTEMS)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def region_for(name: str) -> str:
    if name.lower().startswith("denver__ligament_"):
        return "abdomen_pelvis"
    for region, tokens in REGION_BY_NAME.items():
        if any(token in name.lower() for token in tokens):
            return region
    raise ValueError(f"Estrutura sem região pré-registrada: {name}")


def run_meshopt(raw: Path, output: Path) -> None:
    if not NPM:
        raise RuntimeError("npx não encontrado")
    command = [NPM, "--yes", "@gltf-transform/cli@4.5.1", "meshopt", str(raw), str(output),
               "--level", "high", "--quantize-position", "16", "--quantization-volume", "mesh"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(f"meshopt falhou: {result.stdout}\n{result.stderr}")


def export_system(meshes: list[tuple[str, trimesh.Trimesh]], output: Path, stage: Path) -> None:
    if not meshes:
        # Preserve the HRA empty system GLB byte-for-byte when there are no entries.
        source = output.parent / ".empty-source.glb"
        source.write_bytes(b"")
        return
    scene = trimesh.Scene()
    for name, mesh in meshes:
        scene.add_geometry(mesh, geom_name=name, node_name=name)
    raw = stage / f".{output.stem}.raw.glb"
    raw.write_bytes(scene.export(file_type="glb"))
    run_meshopt(raw, output)
    raw.unlink(missing_ok=True)


def build(variant: str, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(f"Destino já existe: {destination}")
    hra_index = json.loads((HRA / "indice.json").read_text(encoding="utf-8"))
    vhf_index = json.loads((VHF / "indice.json").read_text(encoding="utf-8"))
    hra_manifest = json.loads((HRA / "manifesto.json").read_text(encoding="utf-8"))
    vhf_manifest = json.loads((VHF / "manifesto.json").read_text(encoding="utf-8"))
    systems_meta = {row["id"]: row for row in hra_manifest["sistemas"]}
    matrices = json.loads(TRANSFORMS.read_text(encoding="utf-8"))["stage_b"]
    if variant == "A":
        similarity = np.asarray(matrices["similarity"]["matrix_4x4"], dtype=float)
        transforms = {key: similarity for key in ("head_neck", "thorax", "abdomen_pelvis")}
    else:
        transforms = {key: np.asarray(value, dtype=float)
                      for key, value in matrices["regional_registration"]["matrices_4x4"].items()}

    hra_kept = [row for row in hra_index if row["sistema"] not in {"esqueletico", "articular"}]
    vhf_rows = [row for row in vhf_index if row["sistema"] in {"esqueletico", "articular"}]
    if len(vhf_rows) != 109:
        raise AssertionError(f"Esperadas 109 estruturas VHF; encontradas {len(vhf_rows)}")
    rows_by_system: dict[str, list[dict]] = {key: [] for key in SYSTEMS}
    meshes_by_system: dict[str, list[tuple[str, trimesh.Trimesh]]] = {key: [] for key in SYSTEMS}
    input_hashes = {}
    manifest_rows = {row["name"]: row for row in json.loads((STL_BASE / "manifest.json").read_text(encoding="utf-8"))["meshes"]}

    for row in vhf_rows:
        name, system = row["malha"], row["sistema"]
        source = STL_BASE / f"{name}.stl"
        source_meta = manifest_rows.get(name)
        if not source.is_file() or source_meta is None:
            raise FileNotFoundError(f"STL fonte/manifesto ausente: {name}")
        mesh = trimesh.load_mesh(source, process=True)
        if len(mesh.faces) != int(source_meta["faces"]):
            raise AssertionError(f"Triângulos fonte divergentes: {name}")
        region = region_for(name)
        matrix = transforms[region]
        mesh.apply_transform(matrix)
        mesh.apply_transform(RAS_TO_APP)
        meshes_by_system[system].append((name, mesh))
        entry = {**row, "glb": f"{system}.glb", "fonte": "vhf-f",
                 "transformacao": "stage_b.similarity" if variant == "A" else f"stage_b.regional_registration.matrices_4x4.{region}"}
        rows_by_system[system].append(entry)
        input_hashes[f"atlas/hra-f/2.0-1/{name}.stl"] = sha256(source)

    for row in hra_kept:
        system = row["sistema"]
        rows_by_system[system].append({**row, "glb": f"{system}.glb", "fonte": "hra-f"})
    for row in hra_kept:
        source = HRA / systems_meta[row["sistema"]]["glb"]
        input_hashes.setdefault(f"hra-f/1.10-1/{source.name}", sha256(source))

    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = destination.parent / f".hib-f-{variant.lower()}-stage"
    stage.mkdir(parents=True, exist_ok=False)
    try:
        for system in SYSTEMS:
            if system in {"esqueletico", "articular"}:
                export_system(meshes_by_system[system], stage / f"{system}.glb", stage)
            elif system not in systems_meta:
                pack.write_empty_glb(stage / f"{system}.glb")
            else:
                shutil.copy2(HRA / systems_meta[system]["glb"], stage / f"{system}.glb")
        skin_meta = systems_meta["tegumentar"]
        shutil.copy2(HRA / skin_meta["glb_leve"], stage / skin_meta["glb_leve"])

        index = [entry for system in SYSTEMS for entry in rows_by_system[system]]
        if len(index) != len(hra_kept) + len(vhf_rows):
            raise AssertionError("Contagem do índice híbrido divergiu")
        (stage / "indice.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        system_rows = []
        for system in SYSTEMS:
            entries = rows_by_system[system]
            sysrow = {"id": system, "glb": f"{system}.glb", "estruturas": len(entries),
                      "triangulos": sum(int(row["triangulos"]) for row in entries)}
            if system == "tegumentar":
                sysrow.update({"glb_leve": skin_meta["glb_leve"], "triangulos_leve": skin_meta.get("triangulos_leve")})
            system_rows.append(sysrow)
        files = sorted(path for path in stage.iterdir() if path.is_file())
        hashes = {path.name: sha256(path) for path in files}
        manifest = {
            "atlas": "hib-f", "versao": "0.1-0", "status": "rascunho, nao publicado, nao aceito",
            "publicado": False, "aceito": False, "variante": variant,
            "fonte": "HRA v1.10-1 para pele e sistemas nao esqueleticos; STLs RAS de vhf-f 0.1-0 para esqueletico/articular",
            "unidade": "m", "eixos": "x esquerda do paciente, y cima, z frente",
            "transformacao_de_RAS_m": RAS_TO_APP.tolist(),
            "transformacao_stage_b": {key: value.tolist() for key, value in transforms.items()},
            "sha256": hashes, "fontes_sha256": input_hashes, "sistemas": system_rows,
            "observacao": "Pacote local de revisao F5; rascunho, nao publicado, nao aceito. GLBs HRA nao esqueleticos e LOD tegumentar copiados sem recodificacao."
        }
        (stage / "manifesto.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if any(sha256(stage / name) != digest for name, digest in hashes.items()):
            raise AssertionError("Falha ao verificar sha256 do pacote")
        stage.rename(destination)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    total = sum(path.stat().st_size for path in destination.iterdir() if path.is_file())
    print(f"{destination}: variante {variant}, {len(index)} estruturas, {total / 1e6:.3f} MB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--variante", choices=("A", "B"), required=True)
    parser.add_argument("--destino", type=Path, required=True)
    args = parser.parse_args()
    build(args.variante, args.destino.resolve())
