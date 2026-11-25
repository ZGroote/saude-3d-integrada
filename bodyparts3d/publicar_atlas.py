"""Monta e valida o pacote imutável BodyParts3D bp3d-m/4.0-1."""
import argparse
import csv
import json
import shutil
import struct
from pathlib import Path


BASE = Path(__file__).resolve().parent
RAIZ = BASE.parent
DESTINO = RAIZ / 'atlas' / 'bp3d-m' / '4.0-1'
FONTE = 'BodyParts3D release 4.0 (is_a, OBJ 99%)'
LICENCA = 'CC BY 4.0'
ATRIBUICAO = ('BodyParts3D, © The Database Center for Life Science licensed '
              'under CC Attribution 4.0 International')
EIXOS = 'x esquerda do paciente, y cima, z frente'


def ler_glb(caminho):
    """Lê o chunk JSON de um GLB v2, sem decodificar os buffers binários."""
    with caminho.open('rb') as arquivo:
        cabecalho = arquivo.read(12)
        assert len(cabecalho) == 12, f'GLB truncado: {caminho.name}'
        magic, versao, tamanho = struct.unpack('<4sII', cabecalho)
        assert magic == b'glTF' and versao == 2, f'GLB inválido: {caminho.name}'
        assert tamanho == caminho.stat().st_size, f'Tamanho inválido: {caminho.name}'
        chunk = arquivo.read(8)
        assert len(chunk) == 8, f'Chunk JSON ausente: {caminho.name}'
        tamanho_json, tipo = struct.unpack('<II', chunk)
        assert tipo == 0x4E4F534A, f'Primeiro chunk não é JSON: {caminho.name}'
        dados = arquivo.read(tamanho_json)
        assert len(dados) == tamanho_json, f'Chunk JSON truncado: {caminho.name}'
    return json.loads(dados.decode('utf-8'))


def carregar_csv(caminho):
    with caminho.open(encoding='utf-8-sig', newline='') as arquivo:
        return list(csv.DictReader(arquivo))


def montar(sobrescrever=False):
    if DESTINO.exists() and not sobrescrever:
        raise FileExistsError(
            f'Versão publicada é imutável; destino já existe: {DESTINO}. '
            'Use --sobrescrever para reconstruir.')

    catalogo = carregar_csv(BASE / 'catalogo_bp3d.csv')
    nomes = carregar_csv(BASE / 'nomes_pt.csv')
    nomes_por_fma = {linha['fma']: linha for linha in nomes if linha['fma'].strip()}
    nomes_por_en = {linha['nome_en']: linha for linha in nomes}
    arquivos_web = {p.name for p in (BASE / 'modelos_web').glob('*.glb')}
    sistemas = sorted({linha['sistema'] for linha in catalogo})
    glb_por_sistema = {sistema: f'{sistema}.glb' for sistema in sistemas}
    assert {f'{s}.glb' for s in sistemas} == arquivos_web, (
        'GLBs de modelos_web não correspondem aos sistemas do catálogo')

    indice = []
    estruturas_por_sistema = {sistema: 0 for sistema in sistemas}
    for linha in catalogo:
        fma = linha['fma'].strip()
        traducao = (nomes_por_fma.get(fma, {}) if fma else
                    nomes_por_en.get(linha['nome_en'], {}))
        nome_pt = traducao.get('nome_pt', '').strip()
        item = {
            'malha': linha['arquivo'].strip(),
            'estrutura': fma or None,
            'nome_en': linha['nome_en'].strip(),
            'nome_pt': nome_pt,
            'validacao': traducao.get('validacao', '').strip(),
            'sistema': linha['sistema'].strip(),
            'lateralidade': linha['lateralidade'].strip() or None,
            'glb': glb_por_sistema[linha['sistema'].strip()],
        }
        indice.append(item)
        estruturas_por_sistema[item['sistema']] += 1

    manifesto = {
        'atlas': 'bp3d-m',
        'versao': '4.0-1',
        'fonte': FONTE,
        'licenca': LICENCA,
        'atribuicao': ATRIBUICAO,
        'unidade': 'm',
        'eixos': EIXOS,
        'sistemas': [
            {'id': sistema, 'glb': glb_por_sistema[sistema],
             'estruturas': estruturas_por_sistema[sistema]}
            for sistema in sistemas
        ],
    }

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    if DESTINO.exists() and sobrescrever:
        shutil.rmtree(DESTINO)
    DESTINO.mkdir()
    for glb in sorted(arquivos_web):
        shutil.copy2(BASE / 'modelos_web' / glb, DESTINO / glb)
    (DESTINO / 'indice.json').write_text(
        json.dumps(indice, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (DESTINO / 'manifesto.json').write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    assert len(indice) == 2234, f'Índice contém {len(indice)} entradas; esperado 2234'
    assert sum(s['estruturas'] for s in manifesto['sistemas']) == 2234
    assert all(item['nome_pt'] for item in indice), 'Há nome_pt vazio no índice'
    nos_por_glb = {}
    for glb in sorted(arquivos_web):
        documento = ler_glb(DESTINO / glb)
        nos = [no.get('name') for no in documento.get('nodes', [])]
        assert all(nos), f'Nó sem nome em {glb}'
        assert len(nos) == len(set(nos)), f'Nomes de nó duplicados em {glb}'
        nos_por_glb[glb] = set(nos)
    for item in indice:
        assert item['malha'] in nos_por_glb[item['glb']], (
            f"Malha {item['malha']} ausente de {item['glb']}")

    print(f'Pacote publicado: {DESTINO}')
    print(f'Índice: {len(indice)} entradas; todos os nomes_pt preenchidos.')
    print(f"Manifesto: {len(manifesto['sistemas'])} sistemas; "
          f"{sum(s['estruturas'] for s in manifesto['sistemas'])} estruturas.")
    print('Validação GLB: cada malha existe como nó nomeado no GLB do sistema. OK')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sobrescrever', action='store_true',
                        help='recria a pasta da versão se ela já existir')
    args = parser.parse_args()
    montar(args.sobrescrever)


if __name__ == '__main__':
    main()
