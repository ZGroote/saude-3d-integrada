"""Achados de ponta a ponta, SEM simulação, no app já rodando e ligado à homologação (dados fictícios).
Uso, em web/:

    python testes/achados_real.py [pasta-capturas]          # padrão: testes/capturas
    APP_URL=http://127.0.0.1:3010 python testes/achados_real.py

Não sobe nem derruba servidor. As senhas são lidas de supabase/.env.demo e nunca impressas.
Cada execução grava DOIS achados na paciente fictícia (um I10 e um F32.9 restrito) e eventos na auditoria;
achados não são apagados. Precisa de Playwright para Python, do Chrome e do atlas servido pelo app.
"""
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
WEB = Path(__file__).resolve().parent.parent
APP = os.environ.get('APP_URL', 'http://127.0.0.1:3020').rstrip('/')
CARDIO, OBSTETRICIA = 'cardiologia@saude3d.invalid', 'obstetricia@saude3d.invalid'
MARIA = '30000000-0000-4000-8000-000000000001'
CAPTURAS = Path(sys.argv[1]) if len(sys.argv) > 1 else WEB / 'testes/capturas'

# o three avisa cada cena criada a este gancho: dá para ler onde os marcadores foram de fato desenhados
GANCHO = """
window.__cenas = [];
window.__THREE_DEVTOOLS__ = new EventTarget();
window.__THREE_DEVTOOLS__.addEventListener('observe', (e) => e.detail.isScene && window.__cenas.push(e.detail));
"""
DESENHADOS = """() => {
  const posicoes = [];
  for (const cena of window.__cenas) cena.traverse((o) => {
    if (o.geometry?.type === 'SphereGeometry' && o.material.side !== 1) posicoes.push(o.parent.position.toArray());
  });
  return posicoes;
}"""


def senha_de(email):
    for linha in (WEB.parent / 'supabase/.env.demo').read_text(encoding='utf-8-sig').splitlines():
        chave, separador, valor = linha.partition('=')
        if separador and chave.strip() == email:
            return valor.strip()
    raise SystemExit(f'sem senha para {email} em supabase/.env.demo')


def entrar(pg, email):
    pg.goto(f'{APP}/login')
    pg.fill('#email', email)
    try:
        pg.fill('#senha', senha_de(email))
    except Exception:
        raise AssertionError('não foi possível preencher a senha') from None  # o erro do Playwright a mostraria
    pg.click('button[type=submit]')
    pg.wait_for_url(f'{APP}/pacientes')


def sair(pg):
    pg.locator('header form button[type=submit]').click()
    pg.wait_for_url(f'{APP}/login')


def carregar(pg, acao):
    """Executa a navegação, espera a resposta real de listar_achados e o corpo com todos os marcadores."""
    with pg.expect_response(lambda r: '/rpc/listar_achados' in r.url and r.request.method == 'POST') as espera:
        acao()
    resposta = espera.value
    assert resposta.ok, f'listar_achados: {resposta.status} {resposta.text()}'
    linhas = resposta.json()
    no_corpo = [a for a in linhas if a['ancora'] and a['ancora']['atlas'] == 'hra-f']
    pg.wait_for_selector('[data-atlas="hra-f"] [data-motor][data-carregados="tegumentar"]')
    pg.wait_for_selector(f'[data-motor][data-marcadores="{len(no_corpo)}"]')
    pg.wait_for_selector(f'text=Achados ({len(linhas)})')
    pg.wait_for_timeout(1500)
    assert pg.locator('button[data-achado]').count() == len(linhas)
    assert len(pg.evaluate(DESENHADOS)) == len(no_corpo), 'marcadores desenhados diferentes da lista'
    return linhas


def abrir_maria(pg):
    return carregar(pg, lambda: pg.locator(f'a[href="/pacientes/{MARIA}"]').click())


def registrar(pg, cid, alturas):
    """Clica no corpo, preenche o formulário e salva. Devolve (id, âncora do clique)."""
    canvas = pg.locator('canvas')
    formulario = pg.locator('form[aria-labelledby="titulo-novo-achado"]')
    for fy in alturas:
        canvas.scroll_into_view_if_needed()
        caixa = canvas.bounding_box()
        canvas.click(position={'x': caixa['width'] / 2 + 6, 'y': caixa['height'] * fy})
        pg.wait_for_timeout(500)
        if formulario.count():
            break
    assert formulario.count() and formulario.locator('[data-ancora]').count(), 'clique no corpo não abriu o formulário'
    formulario.locator('input[type=search]').press_sequentially(cid, delay=40)
    pg.get_by_role('list', name='Resultados do CID-10').locator('li button').filter(has_text=cid).first.click()
    assert formulario.locator('[data-cid-escolhido] strong').inner_text() == cid
    formulario.locator('select[name=categoria]').select_option('doenca')
    formulario.locator('textarea[name=observacao]').fill('Teste de ponta a ponta (dado fictício)')
    with pg.expect_response(lambda r: '/rpc/registrar_achado' in r.url and r.request.method == 'POST') as espera, \
            pg.expect_response(lambda r: '/rpc/listar_achados' in r.url and r.request.method == 'POST'):
        formulario.get_by_role('button', name='Salvar achado').click()
    resposta = espera.value
    assert resposta.ok and resposta.json(), f'registrar_achado: {resposta.status} {resposta.text()}'
    pg.wait_for_selector(f'button[data-achado="{resposta.json()}"]')
    return resposta.json(), resposta.request.post_data_json['p_ancora']


def fotos(pg, nome, achado=None):
    if achado:
        pg.locator(f'button[data-achado="{achado}"]').click()
        pg.wait_for_selector(f'[data-cartao="{achado}"]')
    for largura, altura in ((1440, 900), (390, 844)):
        pg.set_viewport_size({'width': largura, 'height': altura})
        pg.wait_for_timeout(1200)
        assert pg.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'rolagem lateral em {largura}'
        pg.screenshot(path=str(CAPTURAS / f'real-{largura}-{nome}.png'), full_page=True, caret='initial')
    pg.set_viewport_size({'width': 1440, 'height': 900})
    pg.wait_for_timeout(800)


def conferir_linha(pg, achado, problemas):
    texto = pg.locator(f'button[data-achado="{achado["id"]}"]').inner_text()
    for campo in ('cid10', 'autor_nome', 'unidade_nome', 'cid10_descricao'):
        if achado[campo] not in texto:
            # a descrição não impede o resto do teste; reprova no fim
            if campo == 'cid10_descricao':
                problemas.append(f'a tela não mostra a descrição do {achado["cid10"]}: {texto!r}')
            else:
                raise AssertionError((campo, achado[campo], texto))


CAPTURAS.mkdir(parents=True, exist_ok=True)
problemas = []
with sync_playwright() as p:
    navegador = p.chromium.launch(channel='chrome', args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'])
    pg = navegador.new_page(viewport={'width': 1440, 'height': 900})
    pg.set_default_timeout(120000)
    pg.add_init_script(GANCHO)
    console = []
    pg.on('console', lambda m: m.type == 'error' and console.append(f'{m.text} {m.location.get("url", "")}'))
    pg.on('pageerror', lambda e: console.append(str(e)))

    # 1) cardiologia registra o I10 clicando no corpo; recarrega
    entrar(pg, CARDIO)
    abrir_maria(pg)
    normal, clique = registrar(pg, 'I10', (0.35, 0.40, 0.30))
    linhas = carregar(pg, pg.reload)
    [i10] = [a for a in linhas if a['id'] == normal]
    assert i10['cid10'] == 'I10' and i10['nivel_sigilo'] == 'normal', i10
    assert i10['ancora'] == clique, (i10['ancora'], clique)
    desenhados = pg.evaluate(DESENHADOS)
    assert any(all(abs(a - b) < 1e-9 for a, b in zip(d, clique['posicao_local'])) for d in desenhados), desenhados
    conferir_linha(pg, i10, problemas)
    print(f'1) I10: clique {clique["posicao_local"]} == listar_achados {i10["ancora"]["posicao_local"]} == marcador desenhado')

    # 2) restrito, também com âncora
    restrito, ancora_restrita = registrar(pg, 'F32.9', (0.50, 0.55, 0.45))
    linhas_cardio = carregar(pg, pg.reload)
    [f32] = [a for a in linhas_cardio if a['id'] == restrito]
    assert f32['nivel_sigilo'] == 'restrito' and f32['ancora'] == ancora_restrita, f32
    assert ancora_restrita['posicao_local'] != clique['posicao_local']
    fotos(pg, '1-cardiologia-registrou', normal)
    print('2) F32.9 gravado como restrito e visível para a cardiologia')
    sair(pg)

    # 3) obstetrícia: vê o I10, e nada do restrito (resposta, linha, contagem, marcador, HTML)
    recebido = []
    anotar = lambda r: '/rest/v1/' in r.url and r.request.method == 'POST' and recebido.append(r)
    entrar(pg, OBSTETRICIA)
    pg.on('response', anotar)
    linhas_obst = abrir_maria(pg)
    ocultos = {a['id'] for a in linhas_cardio
               if a['nivel_sigilo'] == 'restrito' and a['unidade_nome'] == i10['unidade_nome']}
    visiveis = {a['id'] for a in linhas_obst}
    assert restrito in ocultos and not ocultos & visiveis, ocultos & visiveis
    assert visiveis == {a['id'] for a in linhas_cardio} - ocultos, 'contagem não bate com a lista sem os restritos'
    [visto] = [a for a in linhas_obst if a['id'] == normal]
    assert visto['ancora'] == clique and 'Cardiologia' in visto['autor_nome'] and 'Cardiologia' in visto['unidade_nome'], visto
    conferir_linha(pg, visto, problemas)
    assert ancora_restrita['posicao_local'] not in pg.evaluate(DESENHADOS), 'marcador do restrito desenhado'
    for resposta in recebido:
        assert restrito not in resposta.text() and 'F32' not in resposta.text(), resposta.url
    html = pg.content()
    assert restrito not in html and 'F32' not in html, 'rastro do restrito na página'
    fotos(pg, '2-obstetricia', normal)
    pg.remove_listener('response', anotar)
    print(f'3) obstetrícia: {len(linhas_obst)} achados (cardiologia: {len(linhas_cardio)}); I10 com autor '
          f'"{visto["autor_nome"]}" / "{visto["unidade_nome"]}"; sem rastro do F32.9')
    sair(pg)

    # 4) cardiologia de novo vê os dois
    entrar(pg, CARDIO)
    linhas = abrir_maria(pg)
    assert {normal, restrito} <= {a['id'] for a in linhas}
    for achado in (i10, f32):
        conferir_linha(pg, achado, problemas)
    assert ancora_restrita['posicao_local'] in pg.evaluate(DESENHADOS)
    fotos(pg, '3-cardiologia-de-novo', restrito)
    print(f'4) cardiologia: {len(linhas)} achados, I10 e F32.9 presentes')
    sair(pg)
    navegador.close()

assert not console, 'console:\n' + '\n'.join(console)
assert not problemas, 'FALHOU:\n' + '\n'.join(dict.fromkeys(problemas))
print(f'console limpo; capturas em {CAPTURAS}\nOK')
