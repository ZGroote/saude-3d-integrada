"""Importação FHIR no navegador, com um Supabase FALSO (as rpc imitam supabase/migrations/0005).
Uso, em web/, com o atlas em public/atlas e SEM nenhum `next dev` rodando nesta pasta:

    python testes/importacao.py [pasta-capturas]

Não testa o banco. O falso e o `next dev` vêm de testes/gestacao.py.
"""
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright

import gestacao as base

sys.stdout.reconfigure(encoding='utf-8')
WEB = Path(__file__).resolve().parent.parent
CAPTURAS = Path(sys.argv[1]) if len(sys.argv) > 1 else None
UNIDADE = base.MATERNIDADE
ADMIN, PROFISSIONAL = 'admin@falso.invalid', 'obstetra@falso.invalid'
base.USUARIOS.clear()
base.USUARIOS.update({ADMIN: UNIDADE, PROFISSIONAL: UNIDADE})

CNS_SISTEMA = 'http://rnDS.saude.gov.br/fhir/r4/StructureDefinition/BRIndividuo-1.0'
CID = {'I10': 'Hipertensão essencial', 'M54.5': 'Dor lombar baixa', 'B24': 'HIV não especificado', 'N20.0': 'Calculose do rim'}
# como na 0005
MAPA = [{'snomed': s, 'estrutura_fma': f, 'estrutura_uberon': u, 'lado': l} for s, f, u, l in (
    ('9846003', 'FMA7204', 'UBERON:0002189', 'direito'), ('18639004', 'FMA7205', 'UBERON:0002189', 'esquerdo'),
    ('6757004', 'FMA24486', None, 'direito'))]
estado = {'admins': {ADMIN}, 'mapa': True, 'falhar': set(), 'importacoes': [], 'pacientes': {}, 'condicoes': {}, 'eventos': {}, 'chamadas': []}


def rpc(nome, p, unidade):
    estado['chamadas'].append((nome, p))
    email = estado['quem']
    pacientes = estado['pacientes']
    if nome == 'eh_admin':
        return email in estado['admins']
    if nome == 'minha_unidade':
        return unidade
    if nome == 'buscar_pacientes':
        t = p['p_texto']
        return [{'id': x['id'], 'nome': x['nome'], 'sexo': x['sexo'], 'data_nascimento': x['data_nascimento'], 'cns_final': x['cns'][-4:]}
                for x in pacientes.values() if t in x['cns'] or t.lower() in x['nome'].lower()]
    if nome == 'abrir_prontuario':
        x = pacientes.get(p['p_paciente'])
        campos = ('id', 'nome', 'cns', 'cpf_hash', 'sexo', 'data_nascimento', 'municipio_ibge')
        return {k: (x or {}).get(k) for k in campos}
    if nome == 'listar_achados':
        return [c['linha'] for c in estado['condicoes'].values() if c['paciente'] == p['p_paciente']]
    if nome == 'listar_eventos':
        return [e for e in estado['eventos'].values() if e['paciente'] == p['p_paciente']]
    if nome in ('listar_gestacoes', 'historico_gestacional_crianca', 'buscar_cid10'):
        return []
    if email not in estado['admins']:
        return None
    if nome == 'iniciar_importacao':
        assert p.get('p_sistema_origem') == 'teste-simulado', p
        estado['importacoes'].append({'arquivo': p['p_arquivo'], 'recursos': p['p_recursos'], 'erros': None})
        return f'70000000-0000-4000-8000-{len(estado["importacoes"]):012d}'
    if p.get('p_fhir_id') in estado['falhar']:
        raise ValueError('22023')
    if nome == 'importar_paciente_fhir':
        x = next((x for x in pacientes.values() if x['cns'] == p['p_cns']), None)
        if not x:
            i = f'30000000-0000-4000-8000-{len(pacientes) + 1:012d}'
            x = pacientes[i] = {'id': i, 'nome': p['p_nome'], 'cns': p['p_cns'], 'cpf_hash': None, 'sexo': p['p_sexo'],
                                'data_nascimento': p['p_nascimento'], 'municipio_ibge': None}
        return x['id']
    if nome == 'importar_condicao_fhir':
        if p['p_cid10'] not in CID:
            raise ValueError('22023')
        c = estado['condicoes'].get(p['p_fhir_id'])
        if not c:
            i = f'40000000-0000-4000-8000-{len(estado["condicoes"]) + 1:012d}'
            c = estado['condicoes'][p['p_fhir_id']] = {'paciente': p['p_paciente'], 'linha': {
                'id': i, 'ancora': p['p_ancora'], 'cid10': p['p_cid10'], 'cid10_descricao': CID[p['p_cid10']], 'categoria': 'doenca',
                'lado': 'nao_se_aplica', 'status': p['p_status'], 'inicio': p['p_inicio'], 'observacao': None, 'especialidade': None,
                'autor_nome': 'Admin Fictício', 'unidade_nome': 'Unidade Fictícia', 'unidade_id': unidade, 'substitui_id': None,
                'criado_em': '2026-11-26T12:00:00Z'}}
        return c['linha']['id']
    if nome == 'importar_evento_fhir':
        estado['eventos'].setdefault(p['p_fhir_id'], {
            'id': f'80000000-0000-4000-8000-{len(estado["eventos"]) + 1:012d}', 'paciente': p['p_paciente'], 'tipo': p['p_tipo'],
            'data': p['p_data'], 'codigo': p['p_codigo'], 'descricao': p['p_descricao'], 'valor': p['p_valor']})
        return None
    if nome == 'concluir_importacao':
        estado['importacoes'][-1]['erros'] = p['p_erros']
        return None
    raise KeyError(nome)


base.rpc = rpc
# a prévia faz 8 buscas ao mesmo tempo: com a fila padrão (5) o falso recusaria conexões de vez em quando
base.ThreadingHTTPServer.request_queue_size = 64


class Falso(base.SupabaseFalso):
    def do_POST(self):
        estado['quem'] = self.email()  # o servidor é de uma thread por pedido, mas o teste é sequencial
        super().do_POST()

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == '/rest/v1/cid10':
            pedidos = parse_qs(url.query).get('codigo', [''])[0]
            return self.responder(200, [{'codigo': c, 'descricao': d} for c, d in CID.items() if c in pedidos])
        if url.path == '/rest/v1/bodysite_estrutura':
            if not estado['mapa']:
                return self.responder(403, {'code': '42501', 'message': 'permission denied for table bodysite_estrutura'})
            return self.responder(200, MAPA)
        super().do_GET()


def montar_bundle():
    """O Bundle sintético do repositório mais os casos de borda; nomes marcados para procurar nos logs."""
    bundle = json.loads((WEB / 'testes/dados/bundle-sintetico-50.json').read_text(encoding='utf-8'))
    # as contagens deste teste não dependem dos códigos do sintético: todos viram um que o mapa falso não tem
    for entrada in bundle['entry']:
        for local in entrada['resource'].get('bodySite', []):
            local['coding'][0]['code'] = '73780009'
    paciente = lambda i, sexo, cns: {'resourceType': 'Patient', 'id': i, 'gender': sexo, 'birthDate': '1990-05-05',
                                     'name': [{'given': ['NOMESECRETO'], 'family': i.upper()}],
                                     **({'identifier': [{'system': CNS_SISTEMA, 'value': cns}]} if cns else {})}

    def condicao(i, quem, cid, local=None):
        r = {'resourceType': 'Condition', 'id': i, 'subject': {'reference': f'Patient/{quem}'},
             'code': {'coding': [{'system': 'http://hl7.org/fhir/sid/icd-10', 'code': cid}]},
             'clinicalStatus': {'coding': [{'code': 'active'}]}, 'onsetDateTime': '2025-03-01'}
        if local:
            r['bodySite'] = [{'coding': [{'system': 'http://snomed.info/sct', 'code': local}]}]
        return r

    extras = [
        paciente('pf', 'female', '999000000009991'), paciente('pm', 'male', '999000000009992'), paciente('sem-cns', 'female', None),
        condicao('rim-f', 'pf', 'N20.0', '9846003'), condicao('joelho-f', 'pf', 'M54.5', '6757004'),
        condicao('rim-m', 'pm', 'N20.0', '9846003'), condicao('cid-ruim', 'pm', 'X99.9'), condicao('sigilosa', 'pm', 'B24'),
        condicao('orfa', 'sem-cns', 'I10'),
        {'resourceType': 'Observation', 'id': 'obs-pf', 'subject': {'reference': 'Patient/pf'},
         'code': {'coding': [{'code': '29463-7', 'display': 'Peso corporal'}]}, 'effectiveDateTime': '2024-01-15T13:00:00Z',
         'valueQuantity': {'value': 70, 'unit': 'kg'}},
    ]
    bundle['entry'] += [{'resource': r} for r in extras]
    # acima do limite padrão de 1 MB das ações de servidor
    bundle['enchimento'] = 'x' * (4 * 1024 * 1024)
    return json.dumps(bundle).encode()


def chamadas(prefixo):
    return [(n, p) for n, p in estado['chamadas'] if n.startswith(prefixo)]


def testar(app):
    dados = montar_bundle()
    arquivo = {'name': 'Pacientes NOMESECRETO.json', 'mimeType': 'application/json', 'buffer': dados}
    with sync_playwright() as p:
        navegador = p.chromium.launch(channel='chrome', args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'])
        console, do_navegador = [], []

        def sessao(email):
            pg = navegador.new_context(viewport={'width': 1440, 'height': 900}).new_page()
            pg.set_default_timeout(180000)
            pg.on('console', lambda m: m.type == 'error' and console.append(f'{m.text} {m.location.get("url", "")}'))
            pg.on('pageerror', lambda e: console.append(str(e)))
            pg.on('request', lambda r: '/rest/v1/' in r.url and do_navegador.append(r.url))
            pg.goto(f'{app}/login')
            pg.fill('#email', email)
            pg.fill('#senha', 'senha-falsa')
            pg.click('button[type=submit]')
            pg.wait_for_url(f'{app}/pacientes')
            return pg

        def foto(pg, nome):
            if CAPTURAS:
                CAPTURAS.mkdir(parents=True, exist_ok=True)
                pg.screenshot(path=str(CAPTURAS / f'importacao-{nome}.png'), full_page=True, caret='initial')

        # anônimo e profissional são negados no servidor
        anonimo = navegador.new_context().new_page()
        anonimo.set_default_timeout(180000)
        anonimo.goto(f'{app}/importar')
        assert anonimo.url.split('?')[0] == f'{app}/login', anonimo.url
        pro = sessao(PROFISSIONAL)
        assert pro.get_by_role('link', name='Importar FHIR').count() == 0
        pro.goto(f'{app}/importar')
        pro.wait_for_selector('text=Acesso negado')
        assert pro.locator('input[type=file]').count() == 0
        print('anônimo vai ao login; profissional vê "Acesso negado"')

        pg = sessao(ADMIN)
        pg.get_by_role('link', name='Importar FHIR').click()
        pg.wait_for_url(f'{app}/importar')
        entrada, analisar = pg.locator('input[type=file]'), pg.get_by_role('button', name='Analisar')
        confirmar = pg.get_by_role('button', name='Confirmar importação')

        def analisar_arquivo(conteudo=arquivo):
            entrada.set_input_files([])
            entrada.set_input_files(conteudo)
            pg.get_by_label('Sistema de origem').fill('teste-simulado')
            analisar.click()

        analisar_arquivo({'name': 'ruim.json', 'mimeType': 'application/json', 'buffer': b'{nao e json'})
        pg.wait_for_selector('text=não é um JSON válido')
        entrada.set_input_files({'name': 'grande.json', 'mimeType': 'application/json', 'buffer': b' ' * (10 * 1024 * 1024 + 1)})
        pg.wait_for_selector('text=passa de 10 MB')
        assert analisar.is_disabled()

        estado['mapa'] = False
        analisar_arquivo()
        pg.wait_for_selector('text=mapeamento de bodySite não pôde ser lida')
        assert confirmar.is_disabled(), 'confirmaria sem o mapeamento'
        estado['mapa'] = True

        analisar_arquivo()
        pg.wait_for_selector('text=Prévia: nada foi gravado ainda')
        pg.wait_for_function("!document.body.textContent.includes('não pôde ser lida')")
        texto = ' '.join(pg.inner_text('main').split()).lower()
        for trecho in ('pacientes 52', 'já vinculados à sua unidade 0', 'condições com local no corpo 2', 'condições sem local 52',
                       'eventos (linha do tempo) 51', 'recursos com erro (3)', '26 condições citam',
                       'cid-ruim — cid-10 inexistente', 'sem-cns —', 'orfa —'):
            assert trecho in texto, (trecho, texto[:900])
        assert 'nomesecreto' not in texto and '999000000009991' not in texto, 'dado pessoal na prévia'
        assert not chamadas('importar_') and not chamadas('iniciar_'), 'gravou antes de confirmar'
        foto(pg, '1-previa')
        print('prévia: contagens e 3 erros, nada gravado')

        # perde o papel entre a prévia e a confirmação: a ação recusa
        estado['admins'] = set()
        confirmar.click()
        pg.wait_for_selector('text=Acesso negado')  # a ação recusa e a página volta negada
        assert not chamadas('importar_') and not chamadas('iniciar_')
        estado['admins'] = {ADMIN}
        pg.goto(f'{app}/importar')

        def importar():
            analisar_arquivo()
            pg.wait_for_selector('text=Prévia: nada foi gravado ainda')
            confirmar.click()
            pg.wait_for_selector('[data-relatorio]')
            return ' '.join(pg.inner_text('[data-relatorio]').split()).lower()

        # um paciente falha: vira erro com os recursos dele, e o resto entra
        estado['falhar'] = {'sintetico-003'}
        relatorio = importar()
        for trecho in ('pacientes (novos + já existentes) 51', 'condições (novas + já existentes) 53', 'eventos (novos + já existentes) 50', 'recursos com erro (6)',
                       'sintetico-003 — dados recusados', 'o paciente deste recurso não foi importado'):
            assert trecho in relatorio, (trecho, relatorio)
        nomes = [n for n, _ in estado['chamadas'] if n.startswith(('iniciar_', 'importar_', 'concluir_'))]
        assert nomes[0] == 'iniciar_importacao' and nomes[-1] == 'concluir_importacao', nomes[:3]
        registro = estado['importacoes'][-1]
        assert registro['arquivo'].startswith('bundle-') and 'NOMESECRETO' not in registro['arquivo'], registro['arquivo']
        assert all(set(e) == {'id', 'motivo'} for e in registro['erros']) and 'NOMESECRETO' not in json.dumps(registro['erros'])
        assert registro['recursos'] == 52 + 54 + 51 + 3, registro['recursos']
        foto(pg, '2-relatorio')

        contar = lambda: tuple(len(estado[k]) for k in ('pacientes', 'condicoes', 'eventos'))
        estado['falhar'] = set()
        assert 'pacientes (novos + já existentes) 52' in importar() and contar() == (52, 54, 51), contar()
        assert 'pacientes (novos + já existentes) 52' in importar() and contar() == (52, 54, 51), 'reimportar criou algo'
        print('confirmação: falha isolada, relatório; reimportar não cria nada; erros sem dado pessoal')

        ancoras = {k: v['linha']['ancora'] for k, v in estado['condicoes'].items()}
        assert ancoras['rim-f']['atlas'] == 'hra-f' and ancoras['rim-f']['malha'].endswith('_R') and ancoras['rim-f']['posicao_local'] is None
        assert ancoras['rim-m']['atlas'] == 'bp3d-m' and ancoras['rim-m']['malha'] == 'FJ3147', ancoras['rim-m']
        assert ancoras['joelho-f'] is None and ancoras['sigilosa'] is None and sum(a is not None for a in ancoras.values()) == 2
        print(f'âncoras pelo sexo e pelo lado: {ancoras["rim-f"]["malha"]} (hra-f), {ancoras["rim-m"]["malha"]} (bp3d-m); sem mapeamento → sem local')

        # prontuário: marcador na estrutura, "sem local" e eventos na linha do tempo
        pf = next(x['id'] for x in estado['pacientes'].values() if x['cns'] == '999000000009991')
        pg.goto(f'{app}/pacientes/{pf}')
        pg.wait_for_selector('[data-motor][data-marcadores="1"]')
        principal = ' '.join(pg.inner_text('main').split()).lower()
        for trecho in ('no corpo (1)', 'sem local no corpo (1)', 'eventos clínicos (1)'):
            assert trecho in principal, trecho
        evento = pg.locator('[data-evento=Observation]').text_content()
        assert 'Peso corporal' in evento and '70 kg' in evento and '2024' in evento, evento
        pg.fill('input[name=filtro-de]', '2025-01-01')
        pg.wait_for_selector('text=Eventos clínicos (0)')
        pg.get_by_role('button', name='Limpar filtros').click()
        pg.wait_for_selector('text=Eventos clínicos (1)')
        foto(pg, '3-prontuario')
        print('prontuário: marcador estrutural, sem local e evento filtrado pelo período')

        pg.set_viewport_size({'width': 390, 'height': 844})
        pg.goto(f'{app}/importar')
        analisar_arquivo()
        pg.wait_for_selector('text=Prévia: nada foi gravado ainda')
        assert 'já vinculados à sua unidade 52' in ' '.join(pg.inner_text('main').split()).lower()
        assert pg.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'rolagem lateral em 390'
        foto(pg, '4-390')
        assert not [u for u in do_navegador if '/importar_' in u or 'iniciar_importacao' in u or 'bodysite' in u], 'navegador falou com o banco para importar'
        console[:] = [m for m in console if 'atlas/hra-f' not in m]
        assert not console, 'console:\n' + '\n'.join(console)
        navegador.close()


if __name__ == '__main__':
    log = base.com_app(testar, Falso)
    for segredo in ('NOMESECRETO', 'PACIENTE FICTICIO', '999000000009991', '999000000000015'):
        assert segredo not in log, f'dado pessoal no log do servidor: {segredo}'
    print('log do servidor e console sem dado pessoal; 390 px sem rolagem\nOK')
