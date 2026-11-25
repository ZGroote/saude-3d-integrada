"""Ponta a ponta no app já rodando, ligado à homologação (dados fictícios). Uso, em web/:

    python testes/ponta_a_ponta.py [pasta-capturas]          # padrão: testes/capturas
    APP_URL=http://127.0.0.1:3010 python testes/ponta_a_ponta.py

Não sobe nem derruba servidor. A senha é lida de supabase/.env.demo e nunca é impressa.
Cada execução grava eventos na auditoria da homologação (aberturas e acesso negado).
Precisa de Playwright para Python, do Chrome e do atlas em public/atlas (npm run atlas).
"""
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
WEB = Path(__file__).resolve().parent.parent
APP = os.environ.get('APP_URL', 'http://127.0.0.1:3010').rstrip('/')
EMAIL = 'cardiologia@saude3d.invalid'
JOAO = '30000000-0000-4000-8000-000000000002'
CAPTURAS = Path(sys.argv[1]) if len(sys.argv) > 1 else WEB / 'testes/capturas'


def senha_de(email):
    for linha in (WEB.parent / 'supabase/.env.demo').read_text(encoding='utf-8-sig').splitlines():
        chave, separador, valor = linha.partition('=')
        if separador and chave.strip() == email:
            return valor.strip()
    raise SystemExit(f'sem senha para {email} em supabase/.env.demo')


def entrar(pg):
    pg.goto(f'{APP}/login')
    pg.fill('#email', EMAIL)
    try:
        pg.fill('#senha', senha_de(EMAIL))
    except Exception:
        raise AssertionError('não foi possível preencher a senha') from None  # o erro do Playwright a mostraria
    pg.click('button[type=submit]')
    pg.wait_for_url(f'{APP}/pacientes')


def login_sem_javascript(navegador):
    """Como antes de a página hidratar: valores FALSOS, e a senha não pode aparecer em URL nenhuma."""
    contexto = navegador.new_context(java_script_enabled=False)
    pg = contexto.new_page()
    pg.set_default_timeout(120000)
    pedidos = []
    pg.on('request', lambda r: pedidos.append((r.method, r.url)))
    pg.goto(f'{APP}/login')
    assert pg.get_attribute('form', 'method').lower() == 'post', 'formulário sem method=post'
    pg.fill('#email', 'falso@exemplo.invalid')
    pg.fill('#senha', 'SENHA-FALSA-123')
    pg.click('button[type=submit]')
    pg.wait_for_selector('form [role=alert]')  # o servidor processou o POST e respondeu com o erro
    assert ('POST', f'{APP}/login') in pedidos, pedidos
    assert not [u for _, u in pedidos + [('', pg.url)] if 'SENHA-FALSA' in u or 'senha=' in u], 'senha na URL'
    assert pg.input_value('#email') == 'falso@exemplo.invalid' and pg.input_value('#senha') == ''
    contexto.close()
    print('login sem JavaScript: POST, senha fora da URL')


def fluxo(navegador, largura, altura):
    celular = largura < 600
    contexto = navegador.new_context(viewport={'width': largura, 'height': altura}, has_touch=celular, is_mobile=celular)
    pg = contexto.new_page()
    pg.set_default_timeout(120000)
    console = []
    pg.on('console', lambda m: m.type in ('error', 'warning')
          and console.append(f'{largura} {m.type}: {m.text} {m.location.get("url", "")}'))
    pg.on('pageerror', lambda e: console.append(f'{largura} {e}'))

    def foto(nome):
        # caret='initial': senão o Playwright injeta estilo no HTML ainda não hidratado e o React reclama
        pg.screenshot(path=str(CAPTURAS / f'{largura}-{nome}.png'), full_page=True, caret='initial')

    def sem_rolagem_lateral():
        assert pg.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'rolagem lateral em {pg.url}'

    def caminho():
        return pg.url[len(APP):].split('?')[0]

    # sem sessão, a lista manda para o login
    pg.goto(f'{APP}/pacientes')
    assert caminho() == '/login', pg.url
    foto('1-login')
    entrar(pg)

    # lista: só a Maria
    lista = pg.locator('ul[aria-label="Pacientes vinculados"] li')
    lista.first.wait_for()
    assert lista.count() == 1 and 'Maria Fictícia' in lista.first.inner_text(), lista.all_inner_texts()
    assert 'João' not in pg.inner_text('main')
    sem_rolagem_lateral()
    foto('2-pacientes')

    # prontuário: corpo feminino, na pele
    lista.first.locator('a').click()
    pg.wait_for_selector('[data-atlas="hra-f"] [data-motor][data-carregados="tegumentar"]')
    pg.wait_for_timeout(1500)
    prontuario_maria = pg.url
    texto = pg.inner_text('main')
    assert 'Maria Fictícia' in texto and 'Acesso autorizado' in texto
    assert 'em preparação' not in texto, 'caiu no corpo masculino provisório'
    assert 'Human Reference Atlas' in texto or 'HBM637' in texto, 'sem atribuição do atlas feminino'
    assert pg.locator('input[value=gestacional]').count() == 0
    canvas = pg.locator('canvas')
    canvas.scroll_into_view_if_needed()
    caixa = canvas.bounding_box()
    assert caixa['height'] >= 380 and caixa['width'] > (300 if celular else 600), caixa
    # atribuição do atlas (licença) visível e abaixo do 3D, sem cobrir os pés
    atribuicao = pg.locator('[data-motor] > small')
    base, cartao = atribuicao.bounding_box(), pg.locator('[data-motor]').bounding_box()
    assert base['y'] >= caixa['y'] + caixa['height'] - 0.5, (caixa, base)
    assert base['y'] + base['height'] <= cartao['y'] + cartao['height'] + 0.5, (cartao, base)
    sem_rolagem_lateral()
    foto('3-prontuario')

    # clique numa estrutura: tenta pontos do tronco até o painel aparecer
    painel = pg.locator('[data-ancora]')
    for fy in (0.40, 0.45, 0.35, 0.50, 0.30):
        posicao = {'x': caixa['width'] / 2, 'y': caixa['height'] * fy}
        canvas.tap(position=posicao) if celular else canvas.click(position=posicao)
        pg.wait_for_timeout(400)
        if painel.count():
            break
    assert painel.count(), 'clicar no corpo não mostrou o painel'
    dados = painel.inner_text()
    assert re.search(r'(UBERON|FMA):?\d+', dados) and re.search(r'(?i)lado\s+(Esquerdo|Direito|Não se aplica)', dados), dados
    assert 'Pele' in dados, dados
    painel.scroll_into_view_if_needed()
    foto('4-painel')
    print(f'{largura}: painel ->', ' | '.join(dados.split()))

    # sem vínculo (João) e paciente inexistente: a mesma recusa, sem cabeçalho de prontuário
    for nome, paciente in (('joao', JOAO), ('inexistente', '30000000-0000-4000-8000-0000000000ff')):
        pg.goto(f'{APP}/pacientes/{paciente}')
        pg.wait_for_selector('text=Sem acesso a este paciente')
        texto = pg.inner_text('body')
        for proibido in ('João', 'Acesso autorizado', 'CNS', 'Prontuário 3D', 'NaN'):
            assert proibido not in texto, (nome, proibido, texto)
        assert pg.locator('canvas').count() == 0
        sem_rolagem_lateral()
        if nome == 'joao':
            foto('5-sem-acesso')

    # sair a partir de um prontuário aberto encerra esta sessão, e só ela
    outro = navegador.new_context()
    outra_aba = outro.new_page()
    outra_aba.set_default_timeout(120000)
    entrar(outra_aba)
    pg.goto(prontuario_maria)
    pg.wait_for_selector('[data-motor][data-carregados="tegumentar"]')
    cookies_antes = contexto.cookies()
    pg.locator('header form button[type=submit]').click()
    pg.wait_for_url(f'{APP}/login')
    foto('6-saiu')
    pg.go_back()
    pg.wait_for_timeout(2500)
    assert 'Maria Fictícia' not in pg.inner_text('body'), '"voltar" mostrou o prontuário depois de sair'
    for rota in ('/pacientes', prontuario_maria[len(APP):]):
        pg.goto(APP + rota)
        assert caminho() == '/login', (rota, pg.url)
    # os cookies copiados antes de sair não valem mais: a sessão foi revogada no servidor
    copia = navegador.new_context()
    copia.add_cookies(cookies_antes)
    pagina_copia = copia.new_page()
    pagina_copia.goto(f'{APP}/pacientes')
    assert pagina_copia.url.split('?')[0] == f'{APP}/login', 'sessão encerrada ainda abre a lista'
    # a outra sessão do mesmo profissional continua
    outra_aba.goto(f'{APP}/pacientes')
    assert outra_aba.url == f'{APP}/pacientes' and 'Maria Fictícia' in outra_aba.inner_text('main'), outra_aba.url
    outra_aba.locator('header form button[type=submit]').click()
    outra_aba.wait_for_url(f'{APP}/login')
    copia.close()
    outro.close()

    contexto.close()
    return console


CAPTURAS.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    navegador = p.chromium.launch(channel='chrome', args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'])
    login_sem_javascript(navegador)
    erros = []
    for largura, altura in ((1440, 900), (390, 844)):
        erros += fluxo(navegador, largura, altura)
        print(f'{largura}x{altura}: login, lista, hra-f, painel, sem acesso e logout local OK')
    navegador.close()
assert not erros, 'console:\n' + '\n'.join(erros)
print(f'console limpo; capturas em {CAPTURAS}\nOK')
