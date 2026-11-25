"""Comprime sem simplificar: python bodyparts3d/comprimir_web.py.

Usa somente npx (cache externo ao projeto), quantizacao de posicoes a
16 bits por malha e meshopt. Interrompe se nomes, extras ou contagens mudarem.
O visualizador precisa configurar GLTFLoader.setMeshoptDecoder(...).
"""
import json
import shutil
import struct
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
CLI = [shutil.which('npx.cmd') or shutil.which('npx'),
       '--yes', '@gltf-transform/cli@4.5.1']


def executar(*args):
    resultado = subprocess.run(CLI + list(map(str, args)), capture_output=True,
                               text=True, encoding='utf-8', errors='replace')
    if resultado.returncode:
        raise RuntimeError(resultado.stdout + resultado.stderr)


def ler(caminho):
    with caminho.open('rb') as f:
        magic, versao, tamanho = struct.unpack('<4sII', f.read(12))
        assert magic == b'glTF' and versao == 2 and tamanho == caminho.stat().st_size
        tamanho_json, tipo = struct.unpack('<II', f.read(8))
        assert tipo == 0x4E4F534A
        return json.loads(f.read(tamanho_json))


def assinatura(doc):
    nos = doc['nodes']
    assert len({n['name'] for n in nos}) == len(nos), 'Nomes duplicados'
    resultado = {}
    for no in nos:
        faces = 0
        if 'mesh' in no:
            for p in doc['meshes'][no['mesh']]['primitives']:
                assert p.get('mode', 4) == 4
                accessor = p.get('indices', p['attributes']['POSITION'])
                quantidade = doc['accessors'][accessor]['count']
                assert quantidade % 3 == 0
                faces += quantidade // 3
        resultado[no['name']] = (no.get('extras'), faces)
    # Preserva tambem extras de malhas e cenas, incluindo a atribuicao.
    extras = {tipo: [item.get('extras') for item in doc.get(tipo, [])]
              for tipo in ('meshes', 'scenes')}
    return resultado, extras


def main():
    origem, destino = BASE / 'modelos', BASE / 'modelos_web'
    arquivos = sorted(origem.glob('*.glb'))
    assert arquivos, 'Nenhum GLB encontrado'
    indice = (origem / 'indice.json').read_bytes()
    assert {r['glb'] for r in json.loads(indice)} == {p.name for p in arquivos}
    destino.mkdir(exist_ok=True)
    total_antes = total_depois = total_faces = total_nos = 0
    for arquivo in arquivos:
        original = assinatura(ler(arquivo))
        saida = destino / arquivo.name
        # Comando solicitado: somente quantizacao + compressao meshopt.
        executar('meshopt', arquivo, saida, '--level', 'high',
                 '--quantize-position', '16', '--quantization-volume', 'mesh')
        comprimido = ler(saida)
        assert assinatura(comprimido) == original, (
            f'PARADO: {arquivo.name}: nomes, extras ou triangulos alterados')
        assert 'EXT_meshopt_compression' in comprimido['extensionsRequired']
        # inspect reabre e decodifica os buffers meshopt pelo NodeIO do CLI.
        executar('inspect', saida)
        antes, depois = arquivo.stat().st_size, saida.stat().st_size
        faces = sum(v[1] for v in original[0].values())
        total_antes += antes
        total_depois += depois
        total_faces += faces
        total_nos += len(original[0])
        print(f'{arquivo.name}: {antes / 1e6:.3f} -> {depois / 1e6:.3f} MB; '
              f'{len(original[0])} nos; {faces} triangulos; OK', flush=True)
    (destino / 'indice.json').write_bytes(indice)
    print(f'TOTAL: {total_antes / 1e6:.3f} -> {total_depois / 1e6:.3f} MB '
          f'({100 * (1 - total_depois / total_antes):.2f}% menor); '
          f'{total_nos} nos; {total_faces} triangulos. Indice copiado.', flush=True)


if __name__ == '__main__':
    main()
