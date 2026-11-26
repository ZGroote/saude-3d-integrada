"""Importação FHIR de ponta a ponta, SEM simulação, no app já rodando e ligado à homologação.
Uso, em web/:

    python testes/importacao_real.py [pasta-capturas]          # APP_URL padrão: http://127.0.0.1:3020
    SERVIDOR_LOG=saida.log APP_URL=... python testes/importacao_real.py    # confere também a saída do servidor

Não sobe nem derruba servidor. Senhas lidas de supabase/.env.demo, nunca impressas.
Grava na homologação (dados fictícios, não apagados): os 50 pacientes do Bundle sintético e 1 do Bundle com
recursos inválidos, vinculados à UBS, mais registros de importação e auditoria. Repetir não cria nada novo.
Cada item é julgado sozinho: PASSOU ou REPROVOU.
"""
import json
import os
import re
import sys
import traceback
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
WEB = Path(__file__).resolve().parent.parent
APP = os.environ.get('APP_URL', 'http://127.0.0.1:3020').rstrip('/')
CAPTURAS = Path(sys.argv[1]) if len(sys.argv) > 1 else WEB / 'testes/capturas'
ADMIN_UBS, PROFISSIONAL_UBS = 'admin@saude3d.invalid', 'ortopedia@saude3d.invalid'
SINTETICO = WEB / 'testes/dados/bundle-sintetico-50.json'
CNS = 'http://rnDS.saude.gov.br/fhir/r4/StructureDefinition/BRIndividuo-1.0'
MAPEADOS, FORA = ('52612000', '80891009', '9846003'), '73780009'
LOMBAR = '52612000'

recursos = [e['resource'] for e in json.loads(SINTETICO.read_text(encoding='utf-8'))['entry']]
PACIENTES = {r['id']: r for r in recursos if r['resourceType'] == 'Patient'}
CONDICOES = [r for r in recursos if r['resourceType'] == 'Condition']
local_de = lambda c: next((x['code'] for s in c.get('bodySite', []) for x in s.get('coding', [])), None)
dono = lambda c: PACIENTES[c['subject']['reference'].split('/')[1]]
nome_de = lambda p: p['name'][0]['text']
# com local = código mapeado E sexo que define o atlas (indeterminado não tem corpo)
COM_LOCAL = sum(local_de(c) in MAPEADOS and dono(c).get('gender') in ('male', 'female') for c in CONDICOES)
NOME_INVALIDOS = 'PACIENTE FICTICIO INVALIDOS'
CNS_INVALIDOS = '999000000008101'
SEGREDOS = ['FICTICIO', CNS_INVALIDOS] + [p['identifier'][0]['value'] for p in PACIENTES.values()]


def senha_de(email):
    for linha in (WEB.parent / 'supabase/.env.demo').read_text(encoding='utf-8-sig').splitlines():
        chave, separador, valor = linha.partition('=')
        if separador and chave.strip() == email:
            return valor.strip()
    raise SystemExit(f'sem senha para {email} em supabase/.env.demo')


def ajustes():
    linhas = (WEB / '.env.local').read_text(encoding='utf-8-sig').splitlines()
    return {k.strip(): v.strip().strip('"') for k, s, v in (linha.partition('=') for linha in linhas) if s}


def chamar(caminho, corpo, token=None):
    env = ajustes()
    chave = env['NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY']
    cabecalhos = {'apikey': chave, 'content-type': 'application/json'}
    if token:
        cabecalhos['authorization'] = f'Bearer {token}'
    pedido = urllib.request.Request(env['NEXT_PUBLIC_SUPABASE_URL'].rstrip('/') + caminho,
                                    data=json.dumps(corpo).encode(), headers=cabecalhos)
    with urllib.request.urlopen(pedido, timeout=60) as resposta:
        return json.loads(resposta.read() or b'null')


def foto_do_banco():
    """O que o admin da UBS enxerga direto no banco: pacientes fictícios e os ids de achados e eventos de cada um."""
    token = chamar('/auth/v1/token?grant_type=password', {'email': ADMIN_UBS, 'password': senha_de(ADMIN_UBS)})['access_token']
    rpc = lambda nome, **a: chamar(f'/rest/v1/rpc/{nome}', a, token)
    achados = {}
    for p in rpc('buscar_pacientes', p_texto='PACIENTE FICTICIO'):
        achados[p['id']] = {'nome': p['nome'],
                            'achados': {a['id']: a for a in rpc('listar_achados', p_paciente=p['id'])},
                            'eventos': {e['id'] for e in rpc('listar_eventos', p_paciente=p['id'])}}
    return achados


def contagem(banco, nomes):
    meus = [x for x in banco.values() if x['nome'] in nomes]
    return len(meus), sum(len(x['achados']) for x in meus), sum(len(x['eventos']) for x in meus)


resultados, console = {}, []


def item(numero, titulo):
    def decorar(funcao):
        def executar(*args):
            try:
                detalhe = funcao(*args)
                resultados[numero] = f'{numero}) PASSOU — {titulo}: {detalhe}'
            except Exception as erro:
                resultados[numero] = f'{numero}) REPROVOU — {titulo}: {type(erro).__name__}: {str(erro)[:600]}'
                traceback.print_exc()
            print(resultados[numero])
        return executar
    return decorar


with sync_playwright() as p:
    CAPTURAS.mkdir(parents=True, exist_ok=True)
    navegador = p.chromium.launch(channel='chrome', args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'])

    def nova_pagina():
        pg = navegador.new_context(viewport={'width': 1440, 'height': 900}).new_page()
        pg.set_default_timeout(600000)  # a importação grava um recurso de cada vez
        pg.on('console', lambda m: console.append((m.type, m.text)))
        pg.on('pageerror', lambda e: console.append(('pageerror', str(e))))
        return pg

    def entrar(email):
        pg = nova_pagina()
        pg.goto(f'{APP}/login')
        pg.fill('#email', email)
        try:
            pg.fill('#senha', senha_de(email))
        except Exception:
            raise AssertionError('não foi possível preencher a senha') from None  # o erro do Playwright a mostraria
        pg.click('button[type=submit]')
        pg.wait_for_url(f'{APP}/pacientes')
        return pg

    def foto(pg, nome):
        pg.screenshot(path=str(CAPTURAS / f'importacao-real-{nome}.png'), full_page=True, caret='initial')

    admin = entrar(ADMIN_UBS)

    def importar(arquivo):
        admin.goto(f'{APP}/importar')
        admin.locator('input[type=file]').set_input_files(arquivo)
        admin.get_by_role('button', name='Analisar').click()
        admin.wait_for_selector('text=Prévia: nada foi gravado ainda')
        previa = ' '.join(admin.inner_text('main').split()).lower()
        antes = foto_do_banco()
        confirmar = admin.get_by_role('button', name='Confirmar importação')
        assert confirmar.is_enabled(), previa
        foto(admin, 'previa')
        confirmar.click()
        admin.wait_for_selector('[data-relatorio]')
        foto(admin, 'relatorio')
        return previa, antes, ' '.join(admin.inner_text('[data-relatorio]').split()).lower()

    def numeros(relatorio):
        # o rótulo do build antigo era "aceitos"; o novo diz que inclui os já existentes
        return tuple(int(re.search(rf'{nome} (?:aceit[oa]s|\(nov[oa]s \+ já existentes\)) (\d+)', relatorio)[1])
                     for nome in ('pacientes', 'condições', 'eventos'))

    nomes = {nome_de(x) for x in PACIENTES.values()}
    inicial = foto_do_banco()

    @item(1, 'importar o Bundle sintético')
    def primeiro():
        previa, _, relatorio = importar(str(SINTETICO))
        for trecho in ('pacientes 50', f'condições com local no corpo {COM_LOCAL}', f'condições sem local {50 - COM_LOCAL}',
                       'eventos (linha do tempo) 50', 'nenhum erro'):
            assert trecho in previa, (trecho, previa)
        assert numeros(relatorio) == (50, 50, 50) and 'nenhum erro' in relatorio and 'recursos com erro' not in relatorio, relatorio
        depois = foto_do_banco()
        assert contagem(depois, nomes) == (50, 50, 50), contagem(depois, nomes)
        return (f'prévia sem erro ({COM_LOCAL} com local, {50 - COM_LOCAL} sem); relatório 50/50/50, 0 erros; banco 50/50/50 '
                f'(antes desta execução: {contagem(inicial, nomes)})')

    @item(2, 'reimportar o mesmo arquivo')
    def segundo():
        _, antes, relatorio = importar(str(SINTETICO))
        depois = foto_do_banco()
        ids = lambda b: {i: (sorted(x['achados']), sorted(x['eventos'])) for i, x in b.items()}
        assert ids(antes) == ids(depois), 'ids diferentes depois de reimportar'
        assert contagem(depois, nomes) == (50, 50, 50) and numeros(relatorio) == (50, 50, 50), (contagem(depois, nomes), relatorio)
        return f'mesmos pacientes e mesmos ids de achados e eventos antes e depois ({len(depois)} pacientes fictícios visíveis)'

    @item(3, 'Bundle com 3 recursos inválidos')
    def terceiro():
        paciente = {'resourceType': 'Patient', 'id': 'web-e6-ubs', 'gender': 'female', 'birthDate': '1990-01-01',
                    'name': [{'text': NOME_INVALIDOS}], 'identifier': [{'system': CNS, 'value': CNS_INVALIDOS}]}

        def condicao(i, cid):
            return {'resourceType': 'Condition', 'id': i, 'subject': {'reference': 'Patient/web-e6-ubs'},
                    'code': {'coding': [{'system': 'http://hl7.org/fhir/sid/icd-10', 'code': cid}]},
                    'clinicalStatus': {'coding': [{'code': 'active'}]}, 'onsetDateTime': '2025-05-01'}

        def observacao(i, quem):
            return {'resourceType': 'Observation', 'id': i, 'subject': {'reference': f'Patient/{quem}'},
                    'code': {'coding': [{'code': '8867-4', 'display': 'Frequência cardíaca'}]},
                    'effectiveDateTime': '2026-03-01T10:00:00Z', 'valueQuantity': {'value': 70, 'unit': 'bpm'}}

        lista = [paciente, condicao('web-e6-ubs-ok', 'I10'), observacao('web-e6-ubs-obs', 'web-e6-ubs'),
                 {'resourceType': 'Patient', 'id': 'invalido-sem-cns', 'name': [{'text': 'PACIENTE FICTICIO SEM CNS'}]},
                 condicao('invalido-cid', 'X99.99'), observacao('invalido-orfa', 'nao-existe')]
        previa, _, relatorio = importar({'name': 'invalidos.json', 'mimeType': 'application/json', 'buffer': json.dumps(
            {'resourceType': 'Bundle', 'type': 'collection', 'entry': [{'resource': r} for r in lista]}).encode()})
        esperados = ('invalido-sem-cns — patient inválido ou sem cns', 'invalido-cid — cid-10 inexistente',
                     'invalido-orfa — referência patient ausente')
        for texto in (previa, relatorio):
            assert 'recursos com erro (3)' in texto and all(e in texto for e in esperados), texto
        assert numeros(relatorio) == (1, 1, 1), relatorio
        depois = foto_do_banco()
        assert contagem(depois, {NOME_INVALIDOS}) == (1, 1, 1) and contagem(depois, {'PACIENTE FICTICIO SEM CNS'}) == (0, 0, 0)
        return 'válidos gravados (1/1/1); os 3 inválidos listados com motivo na prévia e no relatório; o sem CNS não foi criado'

    @item(4, 'só admin importa')
    def quarto():
        profissional = entrar(PROFISSIONAL_UBS)
        assert profissional.get_by_role('link', name='Importar FHIR').count() == 0
        profissional.goto(f'{APP}/importar')
        profissional.wait_for_selector('text=Acesso negado')
        assert profissional.locator('input[type=file]').count() == 0
        foto(profissional, 'negado')
        anonimo = nova_pagina()
        anonimo.goto(f'{APP}/importar')
        assert anonimo.url.split('?')[0] == f'{APP}/login' and anonimo.locator('input[type=file]').count() == 0, anonimo.url
        return 'profissional da UBS vê "Acesso negado" (sem campo de arquivo nem link); anônimo vai para o login'

    @item(5, 'prontuário do importado')
    def quinto():
        banco = foto_do_banco()
        por_nome = {x['nome']: i for i, x in banco.items()}

        def abrir(condicao, marcadores):
            i = por_nome[nome_de(dono(condicao))]
            [achado] = [a for a in banco[i]['achados'].values()]
            admin.goto(f'{APP}/pacientes/{i}')
            admin.wait_for_selector(f'[data-motor][data-marcadores="{marcadores}"]')
            admin.wait_for_selector('text=Eventos clínicos (1)')
            texto = ' '.join(admin.inner_text('main').split()).lower()
            assert f'no corpo ({marcadores})' in texto and f'sem local no corpo ({1 - marcadores})' in texto, texto[:900]
            assert 'bpm' in admin.locator('[data-evento=Observation]').text_content()
            return achado

        lombar = next(c for c in CONDICOES if local_de(c) == LOMBAR and dono(c).get('gender') in ('male', 'female'))
        admin.add_init_script("""
window.__cenas = []; window.__THREE_DEVTOOLS__ = new EventTarget();
window.__THREE_DEVTOOLS__.addEventListener('observe', (e) => e.detail.isScene && window.__cenas.push(e.detail));""")
        achado = abrir(lombar, 1)
        ancora = achado['ancora']
        assert ancora['posicao_local'] is None and ancora['estrutura'] in ('UBERON:0004617', 'FMA13072'), ancora
        # selecionar liga o sistema da vértebra: o marcador tem de estar no centro da caixa da malha
        admin.locator(f'button[data-achado="{achado["id"]}"]').click()
        admin.wait_for_selector(f'[data-motor][data-completos~="{ancora["sistema"]}"]')
        admin.wait_for_timeout(1500)
        medida = admin.evaluate("""(malha) => { let centro, marcador;
  for (const cena of window.__cenas) cena.traverse((o) => {
    if (o.name === malha && o.userData.sistema) { o.geometry.computeBoundingBox(); const b = o.geometry.boundingBox;
      centro = ['x', 'y', 'z'].map((e) => (b.min[e] + b.max[e]) / 2); }
    if (o.isInstancedMesh && o.geometry.type === 'SphereGeometry') marcador = [...o.instanceMatrix.array.slice(12, 15)];
  });
  return { centro, marcador }; }""", ancora['malha'])
        assert medida['centro'] and medida['marcador'] and all(abs(a - b) < 1e-5 for a, b in zip(medida['centro'], medida['marcador'])), medida
        foto(admin, 'lombar')
        sem = next(c for c in CONDICOES if local_de(c) == FORA and dono(c).get('gender') in ('male', 'female'))
        assert abrir(sem, 0)['ancora'] is None
        foto(admin, 'sem-local')
        return (f'lombar ({dono(lombar)["gender"]}): marcador no centro de {ancora["malha"]} ({ancora["estrutura"]}); '
                f'{FORA}: "sem local no corpo", sem marcador; evento na linha do tempo nos dois')

    primeiro()
    segundo()
    terceiro()
    quarto()
    quinto()
    navegador.close()


@item(6, 'sem dado pessoal em console e saída do servidor')
def sexto():
    vazou = [(tipo, texto[:120]) for tipo, texto in console if any(s in texto for s in SEGREDOS)]
    assert not vazou, vazou
    erros = [t for tipo, t in console if tipo in ('error', 'pageerror')]
    caminho = os.environ.get('SERVIDOR_LOG')
    servidor = 'saída do servidor NÃO conferida (defina SERVIDOR_LOG)'
    if caminho:
        saida = Path(caminho).read_text(encoding='utf-8', errors='replace')
        assert not [s for s in SEGREDOS if s in saida], 'dado pessoal na saída do servidor'
        servidor = f'saída do servidor ({len(saida)} caracteres) sem nome nem CNS'
    return f'console do navegador ({len(console)} mensagens, {len(erros)} erros) sem nome nem CNS; {servidor}'


sexto()
print('\n=== RESUMO', APP)
print(*(resultados[n] for n in sorted(resultados)), sep='\n')
sys.exit(any('REPROVOU' in r for r in resultados.values()))
