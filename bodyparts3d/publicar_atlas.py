"""Monta e valida o pacote imutável BodyParts3D bp3d-m/4.0-1."""
import argparse
import csv
import hashlib
import json
import os
import shutil
import struct
import tempfile
import time
from datetime import datetime, timezone
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


def sha256_arquivo(caminho):
    h = hashlib.sha256()
    with caminho.open('rb') as arquivo:
        for bloco in iter(lambda: arquivo.read(65536), b''):
            h.update(bloco)
    return h.hexdigest()


def renomear_seguro(origem, destino, tentativas=5):
    """Renomeia com pequenas tentativas para evitar locks transitórios no Windows."""
    for i in range(tentativas):
        try:
            origem.rename(destino)
            return
        except PermissionError:
            if i == tentativas - 1:
                raise
            time.sleep(0.2)


def indexar_traducoes(nomes):
    """Indexa traduções por fma e nome_en (normalizados), falhando se houver conflito."""
    nomes_por_fma = {}
    nomes_por_en = {}
    for linha in nomes:
        fma = linha['fma'].strip()
        nome_en = linha['nome_en'].strip()
        nome_pt = linha['nome_pt'].strip()
        validacao = linha['validacao'].strip()
        registro = {'nome_pt': nome_pt, 'validacao': validacao}
        if fma:
            if fma in nomes_por_fma and nomes_por_fma[fma]['nome_pt'] != nome_pt:
                raise ValueError(
                    f"FMA duplicado com traduções diferentes: {fma} "
                    f"({nomes_por_fma[fma]['nome_pt']!r} != {nome_pt!r})")
            nomes_por_fma[fma] = registro
        if nome_en:
            if nome_en in nomes_por_en and nomes_por_en[nome_en]['nome_pt'] != nome_pt:
                raise ValueError(
                    f"nome_en duplicado com traduções diferentes: {nome_en!r} "
                    f"({nomes_por_en[nome_en]['nome_pt']!r} != {nome_pt!r})")
            nomes_por_en[nome_en] = registro
    return nomes_por_fma, nomes_por_en


def montar(reconstruir_local=False):
    if DESTINO.exists() and not reconstruir_local:
        raise FileExistsError(
            f'Versão publicada é imutável; destino já existe: {DESTINO}. '
            'Use --reconstruir-local para reconstruir.')
    if reconstruir_local:
        print('AVISO: versão publicada é imutável e não deve ser reconstruída; '
              'use --reconstruir-local apenas em ambiente local.')

    catalogo_path = Path(os.environ.get('ATLAS_CATALOGO', BASE / 'catalogo_bp3d.csv'))
    nomes_path = Path(os.environ.get('ATLAS_NOMES_PT', BASE / 'nomes_pt.csv'))
    catalogo = carregar_csv(catalogo_path)
    assert catalogo, f'Catálogo vazio: {catalogo_path}'
    total_esperado = len(catalogo)
    nomes_por_fma, nomes_por_en = indexar_traducoes(carregar_csv(nomes_path))

    modelos_dir = BASE / 'modelos_web'
    arquivos_web = {p.name for p in modelos_dir.glob('*.glb')}
    sistemas = sorted({linha['sistema'].strip() for linha in catalogo})
    glb_por_sistema = {sistema: f'{sistema}.glb' for sistema in sistemas}
    assert {f'{s}.glb' for s in sistemas} == arquivos_web, (
        'GLBs de modelos_web não correspondem aos sistemas do catálogo')

    indice = []
    estruturas_por_sistema = {sistema: 0 for sistema in sistemas}
    for linha in catalogo:
        fma = linha['fma'].strip()
        nome_en = linha['nome_en'].strip()
        sistema = linha['sistema'].strip()
        triangulos = int(linha['triangulos'].strip())
        assert triangulos > 0, f"triangulos inválido em {linha['arquivo']}: {triangulos}"
        traducao = nomes_por_fma.get(fma, {}) if fma else nomes_por_en.get(nome_en, {})
        item = {
            'malha': linha['arquivo'].strip(),
            'estrutura': fma or None,
            'nome_en': nome_en,
            'nome_pt': traducao.get('nome_pt', '').strip(),
            'validacao': traducao.get('validacao', '').strip(),
            'sistema': sistema,
            'lateralidade': linha['lateralidade'].strip() or None,
            'glb': glb_por_sistema[sistema],
            'triangulos': triangulos,
        }
        indice.append(item)
        estruturas_por_sistema[sistema] += 1

    assert len(indice) == total_esperado, (
        f'Índice contém {len(indice)} entradas; esperado {total_esperado}')
    assert sum(estruturas_por_sistema.values()) == total_esperado
    assert all(item['nome_pt'] for item in indice), 'Há nome_pt vazio no índice'

    nos_por_glb = {}
    for glb in sorted(arquivos_web):
        documento = ler_glb(modelos_dir / glb)
        extensoes = documento.get('extensionsUsed', [])
        assert 'EXT_meshopt_compression' in extensoes, (
            f'EXT_meshopt_compression ausente em extensionsUsed de {glb}')
        nos = [no.get('name') for no in documento.get('nodes', [])]
        assert all(nos), f'Nó sem nome em {glb}'
        assert len(nos) == len(set(nos)), f'Nomes de nó duplicados em {glb}'
        nos_por_glb[glb] = set(nos)
    for item in indice:
        assert item['malha'] in nos_por_glb[item['glb']], (
            f"Malha {item['malha']} ausente de {item['glb']}")

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix=f'.tmp-{DESTINO.name}-', dir=DESTINO.parent))
    backup_dir = None
    try:
        for glb in sorted(arquivos_web):
            shutil.copy2(modelos_dir / glb, tmp_dir / glb)
        (tmp_dir / 'indice.json').write_text(
            json.dumps(indice, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        arquivos_hash = {
            nome: sha256_arquivo(tmp_dir / nome)
            for nome in sorted(list(arquivos_web) + ['indice.json'])
        }
        manifesto = {
            'atlas': 'bp3d-m',
            'versao': '4.0-1',
            'gerado_em': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'fonte': FONTE,
            'licenca': LICENCA,
            'atribuicao': ATRIBUICAO,
            'unidade': 'm',
            'eixos': EIXOS,
            'arquivos': arquivos_hash,
            'sistemas': [
                {'id': sistema, 'glb': glb_por_sistema[sistema],
                 'estruturas': estruturas_por_sistema[sistema]}
                for sistema in sistemas
            ],
        }
        (tmp_dir / 'manifesto.json').write_text(
            json.dumps(manifesto, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

        if DESTINO.exists():
            backup_dir = DESTINO.parent / f'.bak-{DESTINO.name}-{os.getpid()}'
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            renomear_seguro(DESTINO, backup_dir)
        renomear_seguro(tmp_dir, DESTINO)
        if backup_dir and backup_dir.exists():
            shutil.rmtree(backup_dir, ignore_errors=True)
    except Exception:
        if backup_dir and backup_dir.exists() and not DESTINO.exists():
            renomear_seguro(backup_dir, DESTINO)
        raise
    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f'Pacote publicado: {DESTINO}')
    print(f'Índice: {len(indice)} entradas; todos os nomes_pt preenchidos.')
    print(f"Manifesto: {len(manifesto['sistemas'])} sistemas; "
          f"{sum(s['estruturas'] for s in manifesto['sistemas'])} estruturas.")
    print('Validação GLB: EXT_meshopt_compression e nós nomeados por malha. OK')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reconstruir-local', action='store_true',
                        help='reconstrói a pasta local da versão (não usar em versão já publicada)')
    args = parser.parse_args()
    montar(args.reconstruir_local)


if __name__ == '__main__':
    main()
