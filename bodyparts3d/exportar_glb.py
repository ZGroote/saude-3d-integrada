"""Exporta BodyParts3D para three.js. Execute: python exportar_glb.py.

Coordenadas em metros: (X, Z, -Y)/1000, menos o centro global.
Os caminhos glb do indice.json sao relativos ao proprio indice.
"""
import csv
import json
import struct
from pathlib import Path

import numpy as np
import trimesh

BASE = Path(__file__).resolve().parent
CAMPOS = ('fma', 'nome_en', 'sistema', 'lateralidade')


def main():
    with (BASE / 'catalogo_bp3d.csv').open(encoding='utf-8-sig', newline='') as f:
        linhas = list(csv.DictReader(f))
    assert len({r['arquivo'] for r in linhas}) == len(linhas)
    malhas = {}
    for r in linhas:
        malha = trimesh.load_mesh(
            BASE / 'bruto/isa_BP3D_4.0_obj_99' / (r['arquivo'] + '.obj'),
            process=False)
        assert isinstance(malha, trimesh.Trimesh) and len(malha.faces)
        assert len(malha.faces) == int(r['triangulos']), r['arquivo']
        malhas[r['arquivo']] = malha
    limites = np.array([m.bounds for m in malhas.values()])
    centro = (limites[:, 0].min(axis=0) + limites[:, 1].max(axis=0)) / 2
    transformacao = np.eye(4)
    transformacao[:3, :3] = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]]) / 1000
    transformacao[:3, 3] = -transformacao[:3, :3] @ centro
    for m in malhas.values():
        m.apply_transform(transformacao)

    femur = next(r for r in linhas if r['nome_en'].lower() == 'left femur')
    esterno = next(r for r in linhas if r['nome_en'].lower() == 'body of sternum')
    vertebras = [r for r in linhas if r['sistema'] == 'esqueletico'
                and 'thoracic vertebra' in r['nome_en'].lower()]
    fx = malhas[femur['arquivo']].bounds.mean(axis=0)[0]
    sz = malhas[esterno['arquivo']].bounds.mean(axis=0)[2]
    vz = [malhas[r['arquivo']].bounds.mean(axis=0)[2] for r in vertebras]
    assert fx > 0 and vz and sz > max(vz), 'Orientacao anatomica incorreta'
    print(f'Centro global BP3D (mm): {centro.tolist()}', flush=True)
    print(f'Centros (m): femur esquerdo x={fx:.6f}; esterno z={sz:.6f}; '
          f'vertebras toracicas z=[{min(vz):.6f}, {max(vz):.6f}]', flush=True)

    saida = BASE / 'modelos'
    saida.mkdir(exist_ok=True)
    indice = []
    for sistema in sorted({r['sistema'] for r in linhas}):
        assert sistema and Path(sistema).name == sistema
        grupo = [r for r in linhas if r['sistema'] == sistema]
        cena = trimesh.Scene()
        cena.metadata['copyright'] = ('BodyParts3D, © The Database Center for Life Science '
                                      'licensed under CC Attribution 4.0 International')
        for r in grupo:
            nome = r['arquivo']
            cena.add_geometry(malhas[nome], node_name=nome, geom_name=nome,
                              metadata={k: r[k] for k in CAMPOS})
            indice.append({k: r[k] for k in ('arquivo', *CAMPOS)} |
                          {'glb': sistema + '.glb'})
        destino = saida / (sistema + '.glb')
        destino.write_bytes(trimesh.exchange.gltf.export_glb(cena))

        # Confere os extras nos nos glTF, alem de reabrir a geometria exportada.
        with destino.open('rb') as f:
            assert f.read(4) == b'glTF'
            f.seek(12)
            tamanho, tipo = struct.unpack('<II', f.read(8))
            assert tipo == 0x4E4F534A
            gltf = json.loads(f.read(tamanho))
        nos = {n['name']: n for n in gltf['nodes'] if 'mesh' in n}
        assert set(nos) == {r['arquivo'] for r in grupo}
        for r in grupo:
            assert nos[r['arquivo']]['extras'] == {k: r[k] for k in CAMPOS}
        reaberta = trimesh.load_scene(destino, process=False)
        assert len(reaberta.graph.nodes_geometry) == len(grupo)
        triangulos = sum(len(m.faces) for m in reaberta.geometry.values())
        assert triangulos == sum(int(r['triangulos']) for r in grupo)
        if sistema == femur['sistema']:
            matriz, geometria = reaberta.graph[femur['arquivo']]
            pontos = trimesh.transform_points(reaberta.geometry[geometria].vertices, matriz)
            assert (pontos.min(axis=0)[0] + pontos.max(axis=0)[0]) / 2 > 0
        print(f'{destino.name}: {destino.stat().st_size / 1_000_000:.3f} MB | '
              f'{triangulos:,} triangulos | {len(grupo)} estruturas', flush=True)
    (saida / 'indice.json').write_text(
        json.dumps(indice, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'OK: {len(indice)} estruturas; indice.json gravado.', flush=True)


if __name__ == '__main__':
    main()
