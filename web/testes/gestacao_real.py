"""Gestação e nascimento de ponta a ponta, SEM simulação, no app já rodando e ligado à homologação.
Uso, em web/:

    python testes/gestacao_real.py [pasta-capturas]          # APP_URL padrão: http://127.0.0.1:3020

Não sobe nem derruba servidor. Senhas lidas de supabase/.env.demo, nunca impressas.
Cada execução grava na homologação (dados fictícios, não apagados): uma gestação da Maria, se não houver uma em
curso; as condições O24.4 e O98.7 (restrita); uma criança "Bebê Fictício Etapa5", que encerra a gestação como
nascido vivo; o vínculo dela com a Pediatria; e eventos de auditoria.
"""
import json
import os
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
WEB = Path(__file__).resolve().parent.parent
APP = os.environ.get('APP_URL', 'http://127.0.0.1:3020').rstrip('/')
CAPTURAS = Path(sys.argv[1]) if len(sys.argv) > 1 else WEB / 'testes/capturas'
OBSTETRICIA, ADMIN_PEDIATRIA, PEDIATRIA = (f'{u}@saude3d.invalid' for u in ('obstetricia', 'admin-pediatria', 'pediatria'))
MARIA = '30000000-0000-4000-8000-000000000001'
BEBE = 'Bebê Fictício Etapa5'
NORMAL, RESTRITA = 'O24.4', 'O98.7'


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


def rpc(email, nome, **args):
    """rpc direto no banco, como o usuário: a referência contra a qual a tela é conferida."""
    sessao = chamar('/auth/v1/token?grant_type=password', {'email': email, 'password': senha_de(email)})
    return chamar(f'/rest/v1/rpc/{nome}', args, sessao['access_token'])


with sync_playwright() as p:
    CAPTURAS.mkdir(parents=True, exist_ok=True)
    navegador = p.chromium.launch(channel='chrome', args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'])
    console = []

    def entrar(email):
        pg = navegador.new_context(viewport={'width': 1440, 'height': 900}).new_page()
        pg.set_default_timeout(120000)
        pg.on('console', lambda m: m.type == 'error' and console.append(f'{email}: {m.text} {m.location.get("url", "")}'))
        pg.on('pageerror', lambda e: console.append(f'{email}: {e}'))
        pg.goto(f'{APP}/login')
        pg.fill('#email', email)
        try:
            pg.fill('#senha', senha_de(email))
        except Exception:
            raise AssertionError('não foi possível preencher a senha') from None  # o erro do Playwright a mostraria
        pg.click('button[type=submit]')
        pg.wait_for_url(f'{APP}/pacientes')
        return pg

    def fotos(pg, nome):
        for largura, altura in ((1440, 900), (390, 844)):
            pg.set_viewport_size({'width': largura, 'height': altura})
            pg.wait_for_timeout(800)
            assert pg.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'rolagem lateral em {largura}: {pg.url}'
            pg.screenshot(path=str(CAPTURAS / f'real-{largura}-{nome}.png'), full_page=True, caret='initial')
        pg.set_viewport_size({'width': 1440, 'height': 900})

    def aba(pg, nome, caminho):
        pg.get_by_role('navigation', name='Páginas do paciente').get_by_role('link', name=nome).click()
        pg.wait_for_url(f'{APP}{caminho}')

    # 1) obstetrícia: gestação (nova ou a em curso), duas condições e o nascimento
    pg = entrar(OBSTETRICIA)
    pg.goto(f'{APP}/pacientes/{MARIA}/gestacao')
    pg.wait_for_selector('text=Gestações')
    em_curso = pg.locator('[data-gestacao=em_curso]')
    pg.wait_for_selector('[data-gestacao=em_curso], form[aria-labelledby=titulo-nova-gestacao]')
    if em_curso.count():
        print('1) a Maria já tem gestação em curso: usada')
    else:
        pg.fill('input[name=dum]', str(date.today() - timedelta(273)))
        pg.fill('input[name=inicio_pre_natal]', str(date.today() - timedelta(210)))
        pg.get_by_role('button', name='Registrar gestação').click()
        em_curso.wait_for()
        print('1) gestação registrada')
    [gestacao] = [g for g in rpc(OBSTETRICIA, 'listar_gestacoes', p_mae=MARIA) if g['desfecho'] == 'em_curso']
    assert gestacao['dpp'] == str(date.fromisoformat(gestacao['dum']) + timedelta(280)), gestacao

    for codigo, semana in ((NORMAL, 24), (RESTRITA, 12)):
        antes = em_curso.locator('li', has_text=codigo).count()
        if not em_curso.locator('details[open]').count():
            em_curso.get_by_text('Adicionar condição').click()
        em_curso.locator('input[type=search]').fill('')
        em_curso.locator('input[type=search]').press_sequentially(codigo, delay=40)
        pg.get_by_role('list', name='Resultados do CID-10').locator('li button').filter(has_text=codigo).first.click()
        em_curso.locator('input[name=semana]').fill(str(semana))
        em_curso.get_by_role('button', name='Salvar condição').click()
        pg.wait_for_function(
            "([c, n]) => [...document.querySelectorAll('[data-gestacao=em_curso] li')].filter((l) => l.textContent.includes(c)).length > n",
            arg=[codigo, antes])
    [gestacao] = [g for g in rpc(OBSTETRICIA, 'listar_gestacoes', p_mae=MARIA) if g['desfecho'] == 'em_curso']
    sigilo = {c['cid10']: c['nivel_sigilo'] for c in gestacao['condicoes']}
    assert sigilo[NORMAL] == 'normal' and sigilo[RESTRITA] == 'restrito', sigilo
    fotos(pg, '1-gestacao')
    aba(pg, 'Prontuário', f'/pacientes/{MARIA}')
    pg.wait_for_selector('input[value=gestacional]')
    pg.check('input[value=gestacional]')
    pg.wait_for_selector('[data-motor][data-carregados~="gestacional"]')
    fotos(pg, '2-camada-gestacional')
    print(f'   condições gravadas: {NORMAL} normal, {RESTRITA} restrita; camada gestacional carregada')

    aba(pg, 'Gestação', f'/pacientes/{MARIA}/gestacao')
    pg.locator('[data-gestacao=em_curso]').get_by_role('link', name='Registrar nascimento').click()
    pg.wait_for_url(f'{APP}/pacientes/{MARIA}/nascimento?gestacao=*')
    pg.fill('input[name=nome]', BEBE)
    pg.select_option('select[name=sexo]', 'feminino')
    for campo, valor in (('data', str(date.today())), ('peso', '3150'), ('idade_gestacional', '39'), ('apgar', '9')):
        pg.fill(f'input[name={campo}]', valor)
    pg.get_by_role('button', name='Registrar nascimento').click()
    pg.wait_for_url(lambda u: u.startswith(f'{APP}/pacientes/') and MARIA not in u)
    bebe = pg.url.rsplit('/', 1)[1]
    pg.wait_for_selector('text=Gestação e nascimento')
    assert BEBE in pg.inner_text('main') and pg.locator('canvas').count() == 0
    pg.goto(f'{APP}/pacientes/{MARIA}/familia')
    atalho = pg.locator(f'a[href="/pacientes/{bebe}"]')
    atalho.wait_for()
    assert atalho.inner_text() == BEBE, atalho.inner_text()
    fotos(pg, '3-familia-mae')
    print(f'2) nascimento registrado; "{BEBE}" aparece na Família da Maria')

    # 3) pediatria: antes do vínculo não abre; o admin vincula (não há tela de admin: rpc)
    pediatra = entrar(PEDIATRIA)
    pediatra.goto(f'{APP}/pacientes/{bebe}')
    pediatra.wait_for_selector('text=Sem acesso a este paciente')
    assert rpc(ADMIN_PEDIATRIA, 'vincular_paciente', p_paciente=bebe, p_motivo='Puericultura (teste fictício)',
               p_origem='encaminhamento')
    print('3) sem vínculo a pediatria não abria; admin-pediatria vinculou por rpc vincular_paciente')

    # 4) pediatra abre a criança
    recebido, glbs = [], []

    def anotar(r):
        if ('/rest/v1/' in r.url or r.url.startswith(f'{APP}/pacientes')) and r.ok and r.request.method != 'OPTIONS':
            try:
                recebido.append((r.url, r.text()))
            except Exception:  # resposta de pré-carga descartada pelo navegador
                pass

    pediatra.on('response', anotar)
    pediatra.on('request', lambda r: r.url.endswith('.glb') and glbs.append(r.url))
    pediatra.goto(f'{APP}/pacientes/{bebe}')
    pediatra.wait_for_selector('text=Gestação e nascimento')
    pediatra.wait_for_timeout(2500)
    texto = pediatra.inner_text('main')
    for trecho in (BEBE, 'Maria Fictícia', NORMAL, 'semana 24', '39 semanas', '3.150 g', 'APGAR NO 5º MINUTO\n9',
                   'não usa corpo adulto'):
        assert trecho.lower() in texto.lower(), (trecho, texto)
    assert pediatra.locator('canvas').count() == 0 and pediatra.locator('[data-motor]').count() == 0 and not glbs, 'há corpo 3D'
    assert RESTRITA not in pediatra.content()
    linhas = rpc(PEDIATRIA, 'historico_gestacional_crianca', p_crianca=bebe)
    assert linhas and {x['cid10'] for x in linhas} >= {NORMAL} and RESTRITA not in json.dumps(linhas), linhas
    assert (linhas[0]['mae_id'], linhas[0]['idade_gestacional_sem'], linhas[0]['peso_g'], linhas[0]['apgar_5']) == (MARIA, 39, 3150, 9)
    fotos(pediatra, '4-pediatra-crianca')
    aba(pediatra, 'Família', f'/pacientes/{bebe}/familia')
    mae = pediatra.locator(f'a[href="/pacientes/{MARIA}"]')
    mae.wait_for()
    assert mae.inner_text() == 'Maria Fictícia'
    assert any(NORMAL in t for _, t in recebido), 'nenhuma resposta capturada trouxe o recorte'
    for endereco, corpo in recebido:
        assert RESTRITA not in corpo, f'condição restrita em {endereco}'
    mae.click()
    pediatra.wait_for_selector('text=Sem acesso a este paciente')
    corpo = pediatra.inner_text('body')
    assert 'Maria Fictícia' not in corpo and 'Acesso autorizado' not in corpo, corpo
    fotos(pediatra, '5-mae-sem-acesso')
    print(f'4) pediatra: sem corpo 3D; recorte com {NORMAL}, IG 39, 3.150 g, Apgar 9; sem {RESTRITA}; atalho da mãe: Sem acesso')
    navegador.close()

assert not console, 'console:\n' + '\n'.join(console)
print(f'console limpo; capturas em {CAPTURAS}\nOK')
