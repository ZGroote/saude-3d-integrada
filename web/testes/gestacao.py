"""Gestação, nascimento e família no navegador, com um Supabase FALSO (nada sai da máquina).
Uso, em web/, com o atlas em public/atlas e SEM nenhum `next dev` rodando nesta pasta:

    python testes/gestacao.py [pasta-capturas]

As páginas são do servidor, então não basta simular no navegador: o teste sobe um Supabase de mentira
(as rpc imitam supabase/migrations/0004) e um `next dev` apontado para ele. Não testa o banco.
"""
import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
WEB = Path(__file__).resolve().parent.parent
NEXT = next(n for p in (WEB, *WEB.parents) if (n := p / 'node_modules/next/dist/bin/next').exists())
CAPTURAS = Path(sys.argv[1]) if len(sys.argv) > 1 else None

MATERNIDADE, PEDIATRIA = '10000000-0000-4000-8000-0000000000a1', '10000000-0000-4000-8000-0000000000a2'
MAE, CRIANCA = '30000000-0000-4000-8000-0000000000b1', '30000000-0000-4000-8000-0000000000c1'
GEMEO = '30000000-0000-4000-8000-0000000000c2'
USUARIOS = {'obstetra@falso.invalid': MATERNIDADE, 'pediatra@falso.invalid': PEDIATRIA}
CID = {'O24.4': 'Diabetes mellitus que surge durante a gravidez', 'I10': 'Hipertensão essencial (primária)'}
SEGREDO = 'ACHADO-DA-MAE'

pacientes = {MAE: {'id': MAE, 'nome': 'Mãe Fictícia', 'cns': '700000000000009', 'cpf_hash': None, 'sexo': 'feminino',
                   'data_nascimento': '1994-05-02', 'municipio_ibge': None}}
vinculos = {(MAE, MATERNIDADE)}
achados = {MAE: [{'id': '40000000-0000-4000-8000-000000000001', 'ancora': None, 'cid10': 'I10', 'cid10_descricao': SEGREDO,
                  'categoria': 'doenca', 'lado': 'nao_se_aplica', 'status': 'ativo', 'inicio': None, 'observacao': None,
                  'especialidade': 'obstetricia', 'autor_nome': 'Profissional Fictício', 'unidade_nome': 'Maternidade Fictícia',
                  'unidade_id': MATERNIDADE, 'substitui_id': None, 'criado_em': '2026-10-01T12:00:00Z'}]}
gestacoes, chamadas = [], []


def jwt(email):
    parte = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip('=')
    return f"{parte({'alg': 'HS256', 'typ': 'JWT'})}.{parte({'sub': email, 'email': email, 'exp': int(time.time()) + 3600, 'role': 'authenticated'})}.falso"


def usuario(email):
    return {'id': email, 'aud': 'authenticated', 'role': 'authenticated', 'email': email, 'app_metadata': {}, 'user_metadata': {},
            'created_at': '2026-01-01T00:00:00Z'}


def rpc(nome, p, unidade):
    chamadas.append((nome, p))
    ve = lambda paciente: (paciente, unidade) in vinculos
    if nome == 'minha_unidade':
        return unidade
    if nome == 'buscar_pacientes':
        return [{'id': i, 'nome': x['nome'], 'sexo': x['sexo'], 'data_nascimento': x['data_nascimento'], 'cns_final': '0009'}
                for i, x in pacientes.items() if ve(i)]
    if nome == 'abrir_prontuario':
        i = p['p_paciente']
        return pacientes[i] if ve(i) else {k: None for k in pacientes[MAE]}
    if nome == 'buscar_cid10':
        return [{'codigo': c, 'descricao': d} for c, d in CID.items() if p['p_texto'].lower() in f'{c} {d}'.lower()]
    if nome == 'listar_achados':
        return achados.get(p['p_paciente'], []) if ve(p['p_paciente']) else []
    if nome == 'listar_gestacoes':
        if not ve(p['p_mae']):
            return []
        return [{**{k: g[k] for k in ('gestacao_id', 'dum', 'dpp', 'inicio_pre_natal', 'desfecho')},
                 'condicoes': [{'cid10': c['cid10'], 'semana': c['semana'], 'nivel_sigilo': 'normal'} for c in g['condicoes']],
                 'nascimentos': [{k: n[k] for k in ('crianca_id', 'data', 'peso_g')} for n in g['nascimentos']]}
                for g in gestacoes if g['mae_id'] == p['p_mae']]
    if nome == 'historico_gestacional_crianca':
        i = p['p_crianca']
        return [] if not ve(i) else [
            {'nome_mae': pacientes[g['mae_id']]['nome'], 'cid10': c and c['cid10'], 'cid10_descricao': c and CID[c['cid10']],
             'semana': c and c['semana'], **{k: n[k] for k in ('idade_gestacional_sem', 'peso_g', 'apgar_5', 'data')}}
            for g in gestacoes for n in g['nascimentos'] if n['crianca_id'] == i for c in (g['condicoes'] or [None])]
    if nome == 'registrar_gestacao':
        if not ve(p['p_mae']):
            return None
        novo = f'50000000-0000-4000-8000-{len(gestacoes) + 1:012d}'
        gestacoes.append({'gestacao_id': novo, 'mae_id': p['p_mae'], 'dum': p['p_dum'], 'inicio_pre_natal': p['p_inicio_pre_natal'],
                          'dpp': str(date.fromisoformat(p['p_dum']) + timedelta(280)), 'desfecho': 'em_curso',
                          'condicoes': [], 'nascimentos': []})
        return novo
    g = next((g for g in gestacoes if g['gestacao_id'] == p.get('p_gestacao')), None)
    if not g or not ve(g['mae_id']):
        return None
    if nome == 'registrar_condicao_gestacao':
        g['condicoes'].append({'cid10': p['p_cid10'], 'semana': p['p_semana']})
        return '60000000-0000-4000-8000-000000000001'
    if nome == 'encerrar_gestacao':
        g['desfecho'] = p['p_desfecho']
        return None
    if nome == 'registrar_nascimento':
        if not g['dum'] <= p['p_data'] <= str(date.today()):
            raise ValueError('22023')
        filho = GEMEO if g['nascimentos'] else CRIANCA
        pacientes[filho] = {**pacientes[MAE], 'id': filho, 'nome': p['p_nome'], 'sexo': p['p_sexo'], 'cns': None,
                            'data_nascimento': p['p_data']}
        vinculos.add((filho, unidade))
        g['nascimentos'].append({'crianca_id': filho, 'data': p['p_data'], 'peso_g': p['p_peso_g'],
                                 'idade_gestacional_sem': p['p_idade_gestacional_sem'], 'apgar_5': p['p_apgar_5']})
        g['desfecho'] = 'nascido_vivo'
        return filho
    raise KeyError(nome)


class SupabaseFalso(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def responder(self, status, corpo=None):
        self.send_response(status)
        for chave, valor in (('access-control-allow-origin', '*'), ('access-control-allow-headers', '*'),
                             ('access-control-allow-methods', 'GET,POST,OPTIONS'), ('content-type', 'application/json')):
            self.send_header(chave, valor)
        dados = b'' if status == 204 else json.dumps(corpo).encode()
        self.send_header('content-length', str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def email(self):
        try:
            meio = self.headers.get('authorization', '').split('.')[1]
            return json.loads(base64.urlsafe_b64decode(meio + '=' * (-len(meio) % 4)))['email']
        except (IndexError, ValueError, KeyError):
            return None

    def do_OPTIONS(self):
        self.responder(204)

    def do_GET(self):
        caminho = urlparse(self.path).path
        if caminho == '/auth/v1/user':
            return self.responder(200, usuario(self.email())) if self.email() else self.responder(401, {'message': 'sem sessão'})
        if caminho == '/rest/v1/cid10':
            return self.responder(200, [{'codigo': c, 'descricao': d} for c, d in CID.items()])
        self.responder(404, {'message': caminho})

    def do_POST(self):
        caminho = urlparse(self.path).path
        corpo = json.loads(self.rfile.read(int(self.headers.get('content-length') or 0)) or b'{}')
        if caminho == '/auth/v1/token':
            email = corpo.get('email') or corpo.get('refresh_token')
            if email not in USUARIOS:
                return self.responder(400, {'message': 'credenciais'})
            return self.responder(200, {'access_token': jwt(email), 'token_type': 'bearer', 'expires_in': 3600,
                                        'expires_at': int(time.time()) + 3600, 'refresh_token': email, 'user': usuario(email)})
        if caminho == '/auth/v1/logout':
            return self.responder(204)
        if caminho.startswith('/rest/v1/rpc/') and self.email() in USUARIOS:
            try:
                resposta = rpc(caminho.rsplit('/', 1)[1], corpo, USUARIOS[self.email()])
            except ValueError as erro:  # como o PostgREST entrega um raise com ERRCODE
                return self.responder(400, {'code': str(erro), 'message': 'entrada inválida'})
            return self.responder(204) if caminho.endswith('encerrar_gestacao') else self.responder(200, resposta)
        self.responder(401, {'message': 'sem sessão'})


def porta_livre():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def testar(app):
    with sync_playwright() as p:
        navegador = p.chromium.launch(channel='chrome', args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'])
        console = []

        def sessao(email, largura=1440, altura=900):
            pg = navegador.new_context(viewport={'width': largura, 'height': altura}).new_page()
            pg.set_default_timeout(180000)  # a primeira compilação de cada rota é lenta
            pg.on('console', lambda m: m.type == 'error' and console.append(f'{m.text} {m.location.get("url", "")}'))
            pg.on('pageerror', lambda e: console.append(str(e)))
            pg.goto(f'{app}/login')
            pg.fill('#email', email)
            pg.fill('#senha', 'senha-falsa')
            pg.click('button[type=submit]')
            pg.wait_for_url(f'{app}/pacientes')
            return pg

        def foto(pg, nome):
            if CAPTURAS:
                CAPTURAS.mkdir(parents=True, exist_ok=True)
                pg.screenshot(path=str(CAPTURAS / f'gestacao-{nome}.png'), full_page=True, caret='initial')

        def aba(pg, nome, caminho):
            pg.get_by_role('navigation', name='Páginas do paciente').get_by_role('link', name=nome).click()
            pg.wait_for_url(f'{app}{caminho}')

        def corpo_pronto(pg):
            pg.wait_for_selector('[data-motor][data-carregados~="tegumentar"]')

        pg = sessao('obstetra@falso.invalid')
        # sem gestação em curso não há camada gestacional
        pg.goto(f'{app}/pacientes/{MAE}')
        corpo_pronto(pg)
        pg.wait_for_selector('input[value=tegumentar]')
        assert pg.locator('input[value=gestacional]').count() == 0

        # registrar gestação: DPP mostrada antes de salvar; depois só pode haver uma em curso
        aba(pg, 'Gestação', f'/pacientes/{MAE}/gestacao')
        pg.wait_for_selector('text=Nenhuma gestação registrada')
        pg.fill('input[name=dum]', '2026-02-01')
        assert pg.locator('output').inner_text() == '8 de nov. de 2026', pg.locator('output').inner_text()
        pg.fill('input[name=inicio_pre_natal]', '2026-03-10')
        pg.get_by_role('button', name='Registrar gestação').click()
        pg.wait_for_selector('[data-gestacao=em_curso]')
        assert pg.get_by_role('button', name='Registrar gestação').count() == 0
        assert chamadas_de('registrar_gestacao') == [{'p_mae': MAE, 'p_dum': '2026-02-01', 'p_inicio_pre_natal': '2026-03-10'}]

        # condição com busca de CID-10 e semana (obrigatórias)
        pg.get_by_text('Adicionar condição').click()
        pg.get_by_label('CID-10').press_sequentially('diabetes', delay=30)
        pg.get_by_role('list', name='Resultados do CID-10').get_by_role('button', name='O24.4').click()
        pg.get_by_role('button', name='Salvar condição').click()
        pg.wait_for_timeout(500)
        assert not chamadas_de('registrar_condicao_gestacao'), 'salvou sem a semana'
        pg.fill('input[name=semana]', '24')
        pg.get_by_role('button', name='Salvar condição').click()
        condicoes = pg.get_by_role('list', name='Condições da gestação')
        condicoes.wait_for()
        assert 'O24.4' in condicoes.inner_text() and CID['O24.4'] in condicoes.inner_text() and 'semana 24' in condicoes.inner_text()
        assert chamadas_de('registrar_condicao_gestacao')[0]['p_semana'] == 24
        foto(pg, '1-em-curso')

        # camada gestacional no corpo da mãe
        aba(pg, 'Prontuário', f'/pacientes/{MAE}')
        corpo_pronto(pg)
        pg.check('input[value=gestacional]')
        pg.wait_for_selector('[data-motor][data-carregados~="gestacional"]')
        assert 'representação de referência' in pg.inner_text('main')
        foto(pg, '2-camada')
        print('gestação, DPP, condição e camada gestacional: OK')

        # nascimento: da gestação em curso para o prontuário da criança
        aba(pg, 'Gestação', f'/pacientes/{MAE}/gestacao')
        pg.get_by_role('link', name='Registrar nascimento').click()
        pg.wait_for_url(f'{app}/pacientes/{MAE}/nascimento?gestacao=*')
        pg.fill('input[name=nome]', 'Bebê Fictício')
        pg.select_option('select[name=sexo]', 'feminino')
        pg.fill('input[name=data]', '2026-11-05')
        pg.fill('input[name=peso]', '3200')
        pg.fill('input[name=idade_gestacional]', '39')
        pg.fill('input[name=apgar]', '11')
        pg.get_by_role('button', name='Registrar nascimento').click()
        pg.wait_for_timeout(500)
        assert not chamadas_de('registrar_nascimento'), 'aceitou Apgar 11'
        pg.fill('input[name=apgar]', '9')
        assert pg.locator('input[name=cns]').count() == 0, 'o nascimento não pede CNS'
        # data antes da DUM: o navegador barra com a mensagem clara; se passar, o banco recusa (22023) e a mensagem é a mesma
        pg.fill('input[name=data]', '2026-01-15')
        pg.get_by_role('button', name='Registrar nascimento').click()
        pg.wait_for_selector('text=tem que estar entre a DUM (1 de fev. de 2026) e hoje')
        assert not chamadas_de('registrar_nascimento')
        pg.locator('input[name=data]').evaluate("(e) => e.removeAttribute('min')")
        pg.get_by_role('button', name='Registrar nascimento').click()
        pg.wait_for_selector('text=O nascimento não foi registrado. A data do nascimento tem que estar entre a DUM')
        chamadas[:] = [c for c in chamadas if c[0] != 'registrar_nascimento']
        console[:] = [m for m in console if 'registrar_nascimento' not in m]  # o 400 esperado
        pg.fill('input[name=data]', '2026-11-05')
        pg.get_by_role('button', name='Registrar nascimento').click()
        pg.wait_for_url(f'{app}/pacientes/{CRIANCA}')
        assert chamadas_de('registrar_nascimento') == [{
            'p_gestacao': gestacoes[0]['gestacao_id'], 'p_nome': 'Bebê Fictício', 'p_sexo': 'feminino', 'p_data': '2026-11-05',
            'p_peso_g': 3200, 'p_idade_gestacional_sem': 39, 'p_apgar_5': 9}]

        def prontuario_da_crianca(pg):
            pg.wait_for_selector('text=Gestação e nascimento')
            # recarrega: o documento passa a ser só o que o servidor manda para a criança (numa troca de página no
            # navegador, sobra o HTML da primeira página aberta)
            pg.reload()
            pg.wait_for_selector('text=Gestação e nascimento')
            texto = pg.inner_text('main')
            for trecho in ('Bebê Fictício', 'Mãe Fictícia', '3.200 g', '39 semanas', 'O24.4', 'semana 24', '5 de nov. de 2026',
                           'Prontuário e linha do tempo', 'não usa corpo adulto'):
                assert trecho in texto, (trecho, texto)
            assert pg.locator('canvas').count() == 0, 'criança com corpo 3D'
            assert SEGREDO not in pg.content(), 'achado da mãe no prontuário da criança'

        prontuario_da_crianca(pg)
        foto(pg, '3-crianca')

        # família nos dois sentidos
        aba(pg, 'Família', f'/pacientes/{CRIANCA}/familia')
        pg.wait_for_selector('text=Mãe Fictícia')
        pg.reload()
        pg.wait_for_selector('text=Mãe Fictícia')
        assert SEGREDO not in pg.content()
        pg.goto(f'{app}/pacientes/{MAE}/familia')
        pg.get_by_role('list', name='Filhos').get_by_role('link').click()
        pg.wait_for_url(f'{app}/pacientes/{CRIANCA}')
        # gestação encerrada com nascido vivo: oferece o outro bebê e não oferece a camada
        pg.goto(f'{app}/pacientes/{MAE}')
        corpo_pronto(pg)
        pg.wait_for_selector('input[value=tegumentar]')
        assert pg.locator('input[value=gestacional]').count() == 0
        aba(pg, 'Gestação', f'/pacientes/{MAE}/gestacao')
        print('nascimento, recorte da criança sem corpo 3D e família: OK')

        # gêmeos: a gestação nascido_vivo continua aceitando nascimentos
        pg.get_by_role('link', name='Registrar outro recém-nascido desta gestação').click()
        pg.wait_for_url(f'{app}/pacientes/{MAE}/nascimento?gestacao=*')
        pg.wait_for_selector('text=outro recém-nascido de uma gestação que já tem nascimento')
        pg.fill('input[name=nome]', 'Gêmeo Fictício')
        pg.select_option('select[name=sexo]', 'masculino')
        for campo, valor in (('data', '2026-11-05'), ('peso', '2900'), ('idade_gestacional', '39'), ('apgar', '8')):
            pg.fill(f'input[name={campo}]', valor)
        pg.get_by_role('button', name='Registrar nascimento').click()
        pg.wait_for_url(f'{app}/pacientes/{GEMEO}')
        pg.wait_for_selector('text=2.900 g')
        pg.goto(f'{app}/pacientes/{MAE}/familia')
        pg.get_by_role('list', name='Filhos').wait_for()
        assert pg.get_by_role('list', name='Filhos').get_by_role('link').count() == 2
        assert len(gestacoes) == 1 and len(gestacoes[0]['nascimentos']) == 2
        pg.goto(f'{app}/pacientes/{MAE}/gestacao')
        pg.get_by_role('link', name='Registrar outro recém-nascido desta gestação').wait_for()
        print('gêmeos e mensagem de data fora do intervalo: OK')

        # encerrar sem nascimento: pede confirmação
        pg.fill('input[name=dum]', '2026-11-10')
        pg.get_by_role('button', name='Registrar gestação').click()
        pg.wait_for_selector('[data-gestacao=em_curso]')
        pg.get_by_role('button', name='Encerrar: aborto').click()
        assert not chamadas_de('encerrar_gestacao'), 'encerrou sem confirmar'
        pg.get_by_role('button', name='Confirmar').click()
        pg.wait_for_selector('[data-gestacao=aborto]')
        assert chamadas_de('encerrar_gestacao') == [{'p_gestacao': gestacoes[1]['gestacao_id'], 'p_desfecho': 'aborto'}]
        pg.get_by_role('button', name='Registrar gestação').wait_for()
        # sem vínculo no momento de salvar, a função devolve null: a tela avisa
        vinculos.discard((MAE, MATERNIDADE))
        pg.fill('input[name=dum]', '2026-11-20')
        pg.get_by_role('button', name='Registrar gestação').click()
        pg.wait_for_selector('text=A gestação não foi registrada')
        vinculos.add((MAE, MATERNIDADE))
        assert len(gestacoes) == 2
        print('encerramento com confirmação e falha sem vínculo: OK')

        # pediatra: vínculo só com a criança
        vinculos.add((CRIANCA, PEDIATRIA))
        pediatra = sessao('pediatra@falso.invalid', 390, 844)

        def sem_rolagem():
            assert pediatra.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'rolagem lateral em {pediatra.url}'

        pediatra.goto(f'{app}/pacientes/{CRIANCA}')
        prontuario_da_crianca(pediatra)
        sem_rolagem()
        foto(pediatra, '4-pediatra-390')
        pediatra.goto(f'{app}/pacientes/{CRIANCA}/familia')
        pediatra.wait_for_selector('text=Mãe Fictícia')
        sem_rolagem()
        antes = len(chamadas_de('listar_achados'))
        for caminho in ('', '/gestacao', '/familia', '/nascimento'):
            pediatra.goto(f'{app}/pacientes/{MAE}{caminho}')
            pediatra.wait_for_selector('text=Sem acesso a este paciente')
            assert 'Mãe Fictícia' not in pediatra.content() and SEGREDO not in pediatra.content()
        assert len(chamadas_de('listar_achados')) == antes, 'consultou dados sem vínculo'
        print('pediatra: recorte da criança; todas as páginas da mãe recusadas: OK')

        # 390 px nas páginas da mãe
        celular = sessao('obstetra@falso.invalid', 390, 844)
        for caminho in ('/gestacao', '/familia', '/nascimento'):
            celular.goto(f'{app}/pacientes/{MAE}{caminho}')
            celular.wait_for_selector('nav[aria-label="Páginas do paciente"]')
            assert celular.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'rolagem lateral em {caminho}'
        foto(celular, '5-390')
        assert not console, 'console:\n' + '\n'.join(console)
        navegador.close()
        print('390 px e console limpo\nOK')


def chamadas_de(nome):
    return [p for n, p in chamadas if n == nome]


if __name__ == '__main__':
    cache = WEB / '.next/dev'
    assert not (cache / 'lock').exists(), 'há (ou ficou) um `next dev` nesta pasta: encerre-o e apague web/.next/dev'
    falso = ThreadingHTTPServer(('127.0.0.1', porta_livre()), SupabaseFalso)
    threading.Thread(target=falso.serve_forever, daemon=True).start()
    porta = porta_livre()
    ambiente = {**os.environ, 'NEXT_PUBLIC_SUPABASE_URL': f'http://127.0.0.1:{falso.server_port}',
                'NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY': 'chave-falsa'}
    # o cache do dev guarda o endereço do Supabase dentro do código: começa e termina limpo
    shutil.rmtree(cache, ignore_errors=True)
    saida = tempfile.TemporaryFile()
    servidor = subprocess.Popen(['node', str(NEXT), 'dev', '-H', '127.0.0.1', '-p', str(porta)], cwd=WEB, env=ambiente,
                                stdout=saida, stderr=subprocess.STDOUT)
    try:
        for _ in range(300):
            assert servidor.poll() is None, (saida.seek(0), saida.read().decode('utf-8', 'replace'))[1]
            try:
                socket.create_connection(('127.0.0.1', porta), timeout=1).close()
                break
            except OSError:
                time.sleep(0.3)
        testar(f'http://127.0.0.1:{porta}')
    finally:
        if os.name == 'nt':  # o Next cria processos filhos
            subprocess.run(['taskkill', '/T', '/F', '/PID', str(servidor.pid)], capture_output=True)
        else:
            servidor.terminate()
        servidor.wait(timeout=30)
        falso.shutdown()
        shutil.rmtree(cache, ignore_errors=True)
