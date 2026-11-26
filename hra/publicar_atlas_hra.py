"""Gera localmente o pacote versionado HRA Female 1.10 em atlas/hra-f/1.10-1."""
import argparse
import copy
import csv
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
SOURCE = BASE / 'bruto' / 'united_f_cdn_latest.glb'
CATALOGO = BASE / 'catalogo_hra.csv'
TRADUCOES = BASE / 'nomes_pt_hra.csv'
DESTINO = ROOT / 'atlas' / 'hra-f' / '1.10-1'
ATRIBUICAO = (
    'Browne, Kristen, and Heidi Schlehlein. 2026. 3D Reference Organ Set for '
    'Female, v1.10. https://doi.org/10.48539/HBM637.DWBM.744 — CC BY 4.0. '
    'Data from the Visible Human Dataset, courtesy of the U.S. National '
    'Library of Medicine.'
)
EIXOS = 'x esquerda do paciente, y cima, z frente'

# Mapeia todos os sistemas e órgãos efetivamente presentes no catálogo HRA.
# Vasos são separados pelos termos do label; label sem artery/vein usa o nome
# anatômico do nó, e troncos/estruturas vasculares restantes entram em arterial.
SYSTEM_MAP = {
    'VH_F_integumentary_system': 'tegumentar',
    'VH_F_nervous_system': 'nervoso',
    'VH_F_muscular_system': 'muscular',
    'VH_F_reproductive_system': 'urogenital',
    'VH_F_digestive_system': 'digestorio',
    'VH_F_urinary_system': 'urogenital',
    'VH_F_circulatory_system': 'arterial',  # refinado por orgao/label abaixo
    'VH_F_respiratory_system': 'respiratorio',
    'VH_F_lymphatic_system': 'linfatico',
    'VH_F_skeletal_system': 'esqueletico',
    'VH_F_lower_limb': 'esqueletico',
}
ORGAN_MAP = {
    'VH_F_heart': 'cardiaco',
    'VH_F_eyes': 'sensorial',
    'VH_F_mammary_gland': 'tegumentar',
    'VH_F_muscles_of_eye': 'muscular',
    'VH_F_muscles_of_knee': 'muscular',
    'VH_F_placenta': 'gestacional',
    'VH_F_spleen': 'linfatico',
    'VH_F_thymus': 'linfatico',
    'Yao_lymph_node': 'linfatico',
    'VH_F_palatine_tonsil': 'linfatico',
}
SISTEMAS_BP3D = {
    'esqueletico', 'muscular', 'arterial', 'venoso', 'cardiaco', 'nervoso',
    'respiratorio', 'digestorio', 'urogenital', 'endocrino', 'linfatico',
    'sensorial', 'tegumentar', 'articular', 'fascia', 'gestacional',
}
LOD_TRIANGLES = 40_000
SYSTEM_PYTHON = Path(r'C:\Python314\python.exe')


def read_glb(path):
    with path.open('rb') as f:
        header = f.read(12)
        magic, version, length = struct.unpack('<4sII', header)
        assert magic == b'glTF' and version == 2 and length == path.stat().st_size, (
            f'GLB v2 inválido: {path}')
        json_len, json_type = struct.unpack('<II', f.read(8))
        assert json_type == 0x4E4F534A, 'Primeiro chunk GLB deve ser JSON'
        document = json.loads(f.read(json_len).decode('utf-8'))
        rest = f.read()
    assert len(rest) >= 8, 'Chunk BIN ausente'
    bin_len, bin_type = struct.unpack_from('<II', rest, 0)
    assert bin_type == 0x004E4942 and len(rest) == 8 + bin_len, (
        'Formato de chunks GLB não suportado')
    return document, rest[8:]


def write_glb(path, document, binary):
    encoded = json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    encoded += b' ' * ((-len(encoded)) % 4)
    binary += b'\0' * ((-len(binary)) % 4)
    document['buffers'][0]['byteLength'] = len(binary)
    total = 12 + 8 + len(encoded) + 8 + len(binary)
    with path.open('wb') as f:
        f.write(struct.pack('<4sII', b'glTF', 2, total))
        f.write(struct.pack('<II', len(encoded), 0x4E4F534A))
        f.write(encoded)
        f.write(struct.pack('<II', len(binary), 0x004E4942))
        f.write(binary)


def local_matrix(node):
    if 'matrix' in node:
        return np.asarray(node['matrix'], dtype=float).reshape((4, 4), order='F')
    matrix = np.eye(4)
    matrix[:3, 3] = node.get('translation', [0, 0, 0])
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    rotation = np.array([
        [1 - 2 * (y*y + z*z), 2 * (x*y - z*w), 2 * (x*z + y*w)],
        [2 * (x*y + z*w), 1 - 2 * (x*x + z*z), 2 * (y*z - x*w)],
        [2 * (x*z - y*w), 2 * (y*z + x*w), 1 - 2 * (x*x + y*y)],
    ])
    matrix[:3, :3] = rotation @ np.diag(node.get('scale', [1, 1, 1]))
    return matrix


def world_matrices(document):
    nodes = document['nodes']
    parent = {child: i for i, node in enumerate(nodes) for child in node.get('children', [])}
    result = []
    for index in range(len(nodes)):
        matrix = local_matrix(nodes[index])
        current = index
        while current in parent:
            current = parent[current]
            matrix = local_matrix(nodes[current]) @ matrix
        result.append(matrix)
    return result


def mesh_bounds(document, node, matrix):
    points = []
    for primitive in document['meshes'][node['mesh']]['primitives']:
        accessor = document['accessors'][primitive['attributes']['POSITION']]
        low, high = np.asarray(accessor['min']), np.asarray(accessor['max'])
        corners = np.array([[x, y, z, 1]
                            for x in (low[0], high[0])
                            for y in (low[1], high[1])
                            for z in (low[2], high[2])])
        points.extend((matrix @ corners.T).T[:, :3])
    points = np.asarray(points)
    return points.min(axis=0), points.max(axis=0)


def triangles(document, node):
    total = 0
    for primitive in document['meshes'][node['mesh']]['primitives']:
        assert primitive.get('mode', 4) == 4, f"Primitiva não triangular: {node.get('name')}"
        accessor = primitive.get('indices', primitive['attributes']['POSITION'])
        count = document['accessors'][accessor]['count']
        assert count % 3 == 0, f"Contagem de triângulos inválida: {node.get('name')}"
        total += count // 3
    return total


def load_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


NODE_LEFT_RE = re.compile(r'(?:^|_)(l|left)(?:_|$)', re.I)
NODE_RIGHT_RE = re.compile(r'(?:^|_)(r|right)(?:_|$)', re.I)
WORD_LEFT_RE = re.compile(r'\bleft\b', re.I)
WORD_RIGHT_RE = re.compile(r'\bright\b', re.I)
VENOUS_RE = re.compile(r'(?:^|[_\s])(vein|venous|vena|coronary[_\s]+sinus)(?:$|[_\s])', re.I)


def side(node_name, label):
    if NODE_LEFT_RE.search(node_name) or WORD_LEFT_RE.search(label):
        return 'left'
    if NODE_RIGHT_RE.search(node_name) or WORD_RIGHT_RE.search(label):
        return 'right'
    return None


def readable_node_name(node_name):
    clean = re.sub(r'^VH_F_', '', node_name.strip())
    return clean.replace('_', ' ').strip()


def map_system(row):
    organ = row['orgao'].strip()
    source_system = row['sistema_hra'].strip()
    label = row['label'].strip().lower()
    node_name = row['no'].strip().lower()
    if organ in ORGAN_MAP:
        return ORGAN_MAP[organ]
    if source_system == 'VH_F_circulatory_system':
        if VENOUS_RE.search(label) or 'vein' in label or 'venous' in label:
            return 'venoso'
        if 'artery' in label or 'arterial' in label:
            return 'arterial'
        if VENOUS_RE.search(node_name) or 'vein' in node_name or 'venous' in node_name:
            return 'venoso'
        if 'artery' in node_name or 'arterial' in node_name:
            return 'arterial'
        return 'arterial'  # trunk/vasculature sem tipo explícito no label
    if source_system == 'VH_F_lower_limb' and any(
        term in f"{label} {node_name}" for term in ('ligament', 'cartilage', 'meniscus', 'articular')
    ):
        return 'articular'
    return SYSTEM_MAP.get(source_system)


def translations_by_label():
    assert TRADUCOES.exists(), f'Arquivo de traduções ausente: {TRADUCOES}'
    result = {}
    for row in load_csv(TRADUCOES):
        label = (row.get('label') or '').strip()
        name_pt = (row.get('nome_pt') or '').strip()
        validacao = (row.get('validacao') or '').strip() or 'pendente'
        if not label:
            continue
        if label in result and result[label]['nome_pt'] != name_pt:
            raise ValueError(
                f"Label duplicado em {TRADUCOES.name} com traduções diferentes: "
                f"{label!r} ({result[label]['nome_pt']!r} != {name_pt!r})")
        result[label] = {'nome_pt': name_pt, 'validacao': validacao}
    return result


def attribution_text():
    text = (ROOT / 'LICENCAS.md').read_text(encoding='utf-8-sig')
    marker = '**HRA** (`hra-f`):'
    start = text.index(marker)
    quote_start = text.index('> ', start) + 2
    quote_end = text.index('\n', quote_start)
    return text[quote_start:quote_end].strip()


def run_gltf(command, *args):
    npx = shutil.which('npx.cmd') or shutil.which('npx')
    if not npx:
        raise RuntimeError('npx não encontrado para compressão meshopt')
    result = subprocess.run(
        [npx, '--yes', '@gltf-transform/cli@4.5.1', command, *map(str, args)],
        capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode:
        raise RuntimeError(f'gltf-transform {command} falhou:\n{result.stdout}{result.stderr}')


def simplify_tegumentar(source, destination, names, expected_triangles):
    if not SYSTEM_PYTHON.exists():
        raise FileNotFoundError(f'Python do sistema ausente: {SYSTEM_PYTHON}')
    helper = r"""
import json, sys, trimesh, numpy as np
src,dst,target=sys.argv[1],sys.argv[2],int(sys.argv[3])
scene=trimesh.load(src,force='scene',process=False); entries=[]
for node in list(scene.graph.nodes_geometry):
    transform,geom=scene.graph[node]; mesh=scene.geometry[geom]
    entries.append((node,geom,len(mesh.faces),float(mesh.area)))
minimum=200
if len(entries)*minimum>target*1.1: raise RuntimeError('Too many meshes for 200-face minimum')
areas=np.array([max(e[3],1e-12) for e in entries]); weights=areas/areas.sum()
budgets=np.maximum(minimum,np.floor(weights*target).astype(int)); budgets=np.minimum(budgets,[e[2] for e in entries])
while budgets.sum()<target:
    candidates=[i for i,e in enumerate(entries) if budgets[i]<e[2]]
    if not candidates: break
    i=max(candidates,key=lambda j:weights[j]*target-budgets[j]); budgets[i]+=1
for (node,geom,faces,area),count in zip(entries,budgets):
    if faces>count: scene.geometry[geom]=scene.geometry[geom].simplify_quadric_decimation(face_count=int(count))
open(dst,'wb').write(scene.export(file_type='glb'))
print(json.dumps([e[0] for e in entries]))
"""
    target = int(LOD_TRIANGLES * 0.9)
    result=subprocess.run([str(SYSTEM_PYTHON),'-c',helper,str(source),str(destination),str(target)],capture_output=True,text=True,encoding='utf-8',errors='replace')
    if result.returncode: raise RuntimeError(f'Simplifica??o trimesh falhou:\n{result.stdout}{result.stderr}')
    simplified,_=read_glb(destination)
    out_names=[node.get('name') for node in simplified.get('nodes',[]) if 'mesh' in node]
    if len(out_names)!=len(names) or set(out_names)!=set(names): raise AssertionError('Nomes de n? alterados no LOD')
    count=sum(triangles(simplified,node) for node in simplified['nodes'] if 'mesh' in node)
    if not LOD_TRIANGLES*0.9<=count<=LOD_TRIANGLES*1.1: raise AssertionError(f'LOD fora da toler?ncia: {count} tri?ngulos')
    return count

def surface_deviation_mm(reference_path, simplified_path, names):
    helper = r"""
import json,sys,trimesh,numpy as np
from scipy.spatial import cKDTree
def load(path):
    scene=trimesh.load(path,force='scene',process=False); out={}
    for node in scene.graph.nodes_geometry:
        transform,geom=scene.graph[node]; mesh=scene.geometry[geom].copy(); mesh.apply_transform(transform); out[node]=np.asarray(mesh.vertices)
    return out
a,b=load(sys.argv[1]),load(sys.argv[2]); names=json.loads(sys.argv[3]); ds=[]
for name in names: ds.extend((cKDTree(b[name]).query(a[name])[0],cKDTree(a[name]).query(b[name])[0]))
d=np.concatenate(ds)*1000; print(json.dumps([float(d.mean()),float(d.max())]))
"""
    result=subprocess.run([str(SYSTEM_PYTHON),'-c',helper,str(reference_path),str(simplified_path),json.dumps(names)],capture_output=True,text=True,encoding='utf-8',errors='replace')
    if result.returncode: raise RuntimeError(f'Medi??o de desvio falhou:\n{result.stdout}{result.stderr}')
    return tuple(json.loads(result.stdout.strip().splitlines()[-1]))

def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def safe_rename(source, destination):
    for attempt in range(5):
        try:
            source.rename(destination)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.2)


def publish(rebuild_local=False):
    if DESTINO.exists() and not rebuild_local:
        raise FileExistsError(
            f'Versão publicada é imutável: {DESTINO}. Use --reconstruir-local apenas para build local.')
    if rebuild_local:
        print('AVISO: --reconstruir-local pode substituir somente a cópia local deste pacote.')

    original, binary = read_glb(SOURCE)
    catalog = load_csv(CATALOGO)
    assert len(catalog) == 956, f'Catálogo contém {len(catalog)} malhas; esperado 956'
    source_nodes = original['nodes']
    node_indices = {node.get('name'): i for i, node in enumerate(source_nodes) if 'mesh' in node}
    assert None not in node_indices and len(node_indices) == sum('mesh' in n for n in source_nodes), (
        'Nomes de nó ausentes ou duplicados no GLB HRA')
    assert {row['no'].strip() for row in catalog} == set(node_indices), (
        'Nós com malha no GLB não correspondem ao catálogo HRA')

    matrices = world_matrices(original)
    bounds = {}
    for name, index in node_indices.items():
        bounds[name] = mesh_bounds(original, source_nodes[index], matrices[index])
    global_low = np.min([item[0] for item in bounds.values()], axis=0)
    global_high = np.max([item[1] for item in bounds.values()], axis=0)
    extent = global_high - global_low
    center = (global_low + global_high) / 2
    assert 1.2 < extent[1] < 2.2 and extent[1] == max(extent), (
        f'Orientação/unidade inesperada: extensão da caixa {extent.tolist()}')

    by_name = {row['no'].strip(): row for row in catalog}
    groups = defaultdict(list)
    unmapped = []
    for row in catalog:
        system = map_system(row)
        if not system:
            unmapped.append(row['no'])
        elif system not in SISTEMAS_BP3D:
            raise ValueError(f'Sistema fora do contrato: {system}')
        else:
            groups[system].append(row['no'].strip())
    assert not unmapped, f'Malhas sem sistema: {unmapped}'
    assert sum(map(len, groups.values())) == 956

    # Provas anatômicas do referencial original. HRA já está em metros e com
    # X esquerdo, Y superior e Z anterior; só é necessário centralizar a caixa.
    def mean_center(predicate):
        selected = [((bounds[name][0] + bounds[name][1]) / 2)
                    for name, row in by_name.items() if predicate(name, row)]
        if not selected:
            raise ValueError('Landmark anatômico ausente')
        return np.mean(selected, axis=0)

    landmarks = {
        'heart': mean_center(lambda n, r: r['orgao'].strip() == 'VH_F_heart'),
        'left_leg': mean_center(lambda n, r: 'tibia_l' in n.lower()),
        'right_leg': mean_center(lambda n, r: 'tibia_r' in n.lower()),
        'eyes': mean_center(lambda n, r: r['orgao'].strip() == 'VH_F_eyes'),
        'breast': mean_center(lambda n, r: r['orgao'].strip() == 'VH_F_mammary_gland'),
        'spine': mean_center(lambda n, r: 'vertebra' in n.lower()),
        'lowest_tibia_fibula': mean_center(lambda n, r: 'tibia' in n.lower() or 'fibula' in n.lower()),
    }
    assert landmarks['left_leg'][0] > 0 > landmarks['right_leg'][0]
    assert landmarks['breast'][2] > landmarks['spine'][2]
    assert landmarks['eyes'][1] > landmarks['lowest_tibia_fibula'][1]

    target_low, target_high = global_low - center, global_high - center
    translation = np.eye(4)
    translation[:3, 3] = -center
    translations = translations_by_label()
    index = []
    triangle_counts = defaultdict(int)
    for row in catalog:
        name = row['no'].strip()
        system = map_system(row)
        count = triangles(original, source_nodes[node_indices[name]])
        expected = int(row['triangulos'])
        assert count == expected, f'Triângulos divergentes em {name}: {count} != {expected}'
        triangle_counts[system] += count
        ontology = row['ontologia'].strip()
        estrutura = ontology if ontology and ontology != '-' else None
        raw_label = row['label'].strip()
        has_valid_label = bool(raw_label and raw_label != '-')
        nome_en = raw_label if has_valid_label else readable_node_name(name)
        assert nome_en and nome_en != '-', f'nome_en inválido para {name}'
        trad = translations.get(nome_en)
        assert trad and trad['nome_pt'], (
            f'Malha sem nome_pt em {TRADUCOES.name}: {name} ({nome_en!r})')
        nome_pt = trad['nome_pt']
        validacao = trad['validacao']
        item = {
            'malha': name,
            'estrutura': estrutura,
            'nome_en': nome_en,
            'nome_pt': nome_pt,
            'validacao': validacao,
            'sistema': system,
            'lateralidade': side(name, raw_label),
            'glb': f'{system}.glb',
            'triangulos': count,
        }
        if estrutura is None:
            item['sem_ontologia'] = True
        index.append(item)

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.tmp-hra-f-1.10-1-', dir=DESTINO.parent))
    backup = None
    try:
        working = stage
        for system, names in sorted(groups.items()):
            selected_nodes = []
            for name in names:
                original_node = source_nodes[node_indices[name]]
                node = copy.deepcopy(original_node)
                node.pop('children', None)
                node.pop('translation', None)
                node.pop('rotation', None)
                node.pop('scale', None)
                node['matrix'] = (translation @ matrices[node_indices[name]]).flatten(order='F').tolist()
                selected_nodes.append(node)
            document = copy.deepcopy(original)
            document['nodes'] = selected_nodes
            document['scenes'] = [{'nodes': list(range(len(selected_nodes)))}]
            document['scene'] = 0
            document.pop('animations', None)
            document.pop('skins', None)
            document.pop('cameras', None)
            # Nós e índices glTF usam dados ainda não compactados nesta etapa.
            document['buffers'] = [{'byteLength': len(binary)}]
            raw = working / f'{system}-raw.glb'
            pruned = working / f'{system}-pruned.glb'
            output = stage / f'{system}.glb'
            write_glb(raw, document, binary)
            run_gltf('prune', raw, pruned)
            if system == 'tegumentar':
                leve_raw = working / 'tegumentar-leve-raw.glb'
                leve_pruned = working / 'tegumentar-leve-pruned.glb'
                leve_output = stage / 'tegumentar_leve.glb'
                leve_triangles = simplify_tegumentar(
                    pruned, leve_raw, names, triangle_counts[system])
                run_gltf('prune', leve_raw, leve_pruned)
                run_gltf('meshopt', leve_pruned, leve_output, '--level', 'high',
                         '--quantize-position', '16', '--quantization-volume', 'mesh')
                run_gltf('inspect', leve_output)
                leve_doc, _ = read_glb(leve_output)
                if 'EXT_meshopt_compression' not in leve_doc.get('extensionsRequired', []):
                    raise AssertionError('Meshopt não obrigatório em tegumentar_leve.glb')
                if {n.get('name') for n in leve_doc['nodes'] if 'mesh' in n} != set(names):
                    raise AssertionError('Meshopt alterou nós de tegumentar_leve.glb')
                leve_output_raw = working / 'tegumentar-leve-validacao.glb'
                run_gltf('dequantize', leve_output, leve_output_raw)
                leve_decoded, _ = read_glb(leve_output_raw)
                distances = surface_deviation_mm(pruned, leve_output_raw, names)
                print(f'tegumentar_leve.glb: {leve_output.stat().st_size / 1e6:.3f} MB; '
                      f'{leve_triangles} triângulos; desvio médio={distances[0]:.3f} mm; '
                      f'máximo={distances[1]:.3f} mm', flush=True)
                leve_output_raw.unlink()
                leve_raw.unlink()
                leve_pruned.unlink()
            run_gltf('meshopt', pruned, output, '--level', 'high',
                     '--quantize-position', '16', '--quantization-volume', 'mesh')
            run_gltf('inspect', output)

            compressed, _ = read_glb(output)
            assert 'EXT_meshopt_compression' in compressed.get('extensionsRequired', []), (
                f'Meshopt não obrigatório em {system}.glb')
            out_names = [n.get('name') for n in compressed.get('nodes', [])]
            assert len(out_names) == len(set(out_names)) and set(out_names) == set(names), (
                f'Nós alterados em {system}.glb')
            out_triangles = sum(triangles(compressed, n) for n in compressed['nodes'])
            assert out_triangles == triangle_counts[system], (
                f'Triângulos alterados em {system}.glb')
            raw.unlink()
            pruned.unlink()

        (stage / 'indice.json').write_text(
            json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        hashes = {path.name: sha256(path) for path in sorted(stage.iterdir()) if path.is_file()}
        manifest = {
            'atlas': 'hra-f',
            'versao': '1.10-1',
            'fonte': 'Human Reference Atlas, 3D Reference Organ Set for Female, v1.10',
            'licenca': 'CC BY 4.0',
            'atribuicao': attribution_text(),
            'unidade': 'm',
            'eixos': EIXOS,
            'orientacao_fonte': {
                'rotacao_aplicada_graus_xyz': [0, 0, 0],
                'escala_para_metros': 1.0,
                'translacao_centralizacao_m': (-center).tolist(),
                'caixa_origem_m': {'min': global_low.tolist(), 'max': global_high.tolist(),
                                   'extensao': extent.tolist(), 'centro': center.tolist()},
                'caixa_publicada_m': {'min': target_low.tolist(), 'max': target_high.tolist()},
                'landmarks_origem_m': {key: value.tolist() for key, value in landmarks.items()},
                'evidencia': (
                    'Y tem a maior extensão e olhos ficam acima de tíbias/fíbulas; '
                    'tíbia_L tem X positivo e tíbia_R X negativo; mamas têm Z maior '
                    'que vértebras (anterior). Os arquivos de pés não existem neste catálogo.'
                ),
            },
            'sha256': hashes,
            'sistemas': [
                {'id': system, 'glb': f'{system}.glb',
                 **({'glb_leve': 'tegumentar_leve.glb'} if system == 'tegumentar' else {}),
                 'estruturas': len(names), 'triangulos': triangle_counts[system]}
                for system, names in sorted(groups.items())
            ],
            'gerado_em': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        }
        (stage / 'manifesto.json').write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

        # Validação integrada antes de publicar o diretório.
        assert len(index) == 956 and sum(s['estruturas'] for s in manifest['sistemas']) == 956
        assert len({item['malha'] for item in index}) == 956
        for system in groups:
            doc, _ = read_glb(stage / f'{system}.glb')
            names = {node.get('name') for node in doc.get('nodes', [])}
            assert all(item['malha'] in names for item in index if item['sistema'] == system)
        assert all(sha256(stage / filename) == digest for filename, digest in hashes.items())

        if DESTINO.exists():
            backup = DESTINO.parent / f'.bak-hra-f-1.10-1-{os.getpid()}'
            safe_rename(DESTINO, backup)
        safe_rename(stage, DESTINO)
        if backup and backup.exists():
            shutil.rmtree(backup, ignore_errors=True)
    except Exception:
        if backup and backup.exists() and not DESTINO.exists():
            safe_rename(backup, DESTINO)
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)

    total_bytes = sum((DESTINO / f'{system}.glb').stat().st_size for system in groups)
    print(f'Pacote publicado: {DESTINO}')
    print(f'Orientação: extensão XYZ={np.round(extent, 6).tolist()} m; '
          f'centro={np.round(center, 6).tolist()} m; transformação aplicada: '
          f'identidade + translação {np.round(-center, 6).tolist()} m.')
    print('Landmarks (origem, m): ' + json.dumps(
        {key: np.round(value, 4).tolist() for key, value in landmarks.items()}, ensure_ascii=False))
    print(f'Mapeamento: {len(catalog)} malhas; sem sistema: {len(unmapped)}.')
    for system in sorted(groups):
        size = (DESTINO / f'{system}.glb').stat().st_size / 1e6
        print(f'{system}.glb: {size:.3f} MB; {len(groups[system])} malhas; '
              f'{triangle_counts[system]} triângulos; meshopt OK')
    side_counts = {
        'left': sum(1 for item in index if item['lateralidade'] == 'left'),
        'right': sum(1 for item in index if item['lateralidade'] == 'right'),
        'null': sum(1 for item in index if item['lateralidade'] is None),
    }
    print(f"Lateralidade: left={side_counts['left']}, right={side_counts['right']}, null={side_counts['null']}")
    for vascular in ('arterial', 'venoso'):
        items = [f"{item['malha']} ({item['nome_en']})" for item in index if item['sistema'] == vascular]
        print(f"Vascular [{vascular}] ({len(items)}): " + '; '.join(items))
    print(f'TOTAL: {total_bytes / 1e6:.3f} MB; {len(index)} malhas; '
          f'{sum(triangle_counts.values())} triângulos. SHA-256 validado.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reconstruir-local', action='store_true',
                        help='substitui somente a cópia local do pacote versionado')
    args = parser.parse_args()
    publish(args.reconstruir_local)


if __name__ == '__main__':
    main()
