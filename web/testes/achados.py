"""Achados no navegador com dados falsos: as rpc são simuladas aqui, nada chega ao Supabase.
Uso, em web/, com um `next dev` já rodando e o atlas em public/atlas:

    python testes/achados.py [pasta-capturas]          # APP_URL padrão: http://127.0.0.1:3010

Usa /dev/motor?achados=1 (o mesmo PainelAchados do prontuário).
"""
import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
APP = os.environ.get('APP_URL', 'http://127.0.0.1:3010').rstrip('/')
CAPTURAS = Path(sys.argv[1]) if len(sys.argv) > 1 else None
CID = {'codigo': 'I10', 'descricao': 'Hipertensão essencial (primária)'}

gravados, chamadas = [], []


def rpc(rota):
    pedido = rota.request
    cors = {'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*'}
    if pedido.method == 'OPTIONS':
        return rota.fulfill(status=204, headers=cors)
    nome = pedido.url.split('?')[0].rsplit('/', 1)[1]
    corpo = pedido.post_data_json or {}
    chamadas.append((nome, corpo))
    if nome == 'buscar_cid10':
        resposta = [CID]
    elif nome == 'registrar_achado':
        resposta = f'40000000-0000-4000-8000-{len(gravados) + 1:012d}'
        gravados.append({
            'id': resposta, **{k[2:]: v for k, v in corpo.items() if k not in ('p_paciente', 'p_cid10')},
            'cid10': corpo['p_cid10'], 'cid10_descricao': CID['descricao'], 'especialidade': 'cardiologia',
            'autor_nome': 'Profissional Fictício', 'unidade_nome': 'Unidade Fictícia', 'criado_em': '2026-11-25T12:00:00Z',
        })
    elif nome == 'listar_achados':
        resposta = gravados
    else:
        raise AssertionError(f'rpc inesperada: {nome}')
    rota.fulfill(status=200, headers=cors, content_type='application/json', body=json.dumps(resposta))


# o three avisa cada cena criada a este gancho: dá para ler onde o marcador foi de fato desenhado
GANCHO = """
window.__cenas = [];
window.__THREE_DEVTOOLS__ = new EventTarget();
window.__THREE_DEVTOOLS__.addEventListener('observe', (e) => e.detail.isScene && window.__cenas.push(e.detail));
"""
DESENHADOS = """() => {
  const achados = [];
  for (const cena of window.__cenas) cena.traverse((o) => {
    if (o.geometry?.type === 'SphereGeometry' && o.material.side !== 1)
      achados.push({ posicao: o.parent.position.toArray(), raio: o.parent.scale.x });
  });
  return achados;
}"""

with sync_playwright() as p:
    navegador = p.chromium.launch(channel='chrome', args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'])
    console = []

    def abrir(sexo, largura=1440, altura=900):
        pg = navegador.new_page(viewport={'width': largura, 'height': altura})
        pg.set_default_timeout(180000)
        pg.add_init_script(GANCHO)
        pg.route('**/rest/v1/**', rpc)
        pg.on('console', lambda m: m.type == 'error' and 'hra-f' not in m.location.get('url', '') and console.append(m.text))
        pg.on('pageerror', lambda e: console.append(str(e)))
        pg.goto(f'{APP}/dev/motor?achados=1&sexo={sexo}')
        return pg

    def carregados(pg, ids):
        pg.wait_for_selector(f'[data-motor][data-carregados="{ids}"]')
        pg.wait_for_timeout(1000)

    def foto(pg, nome):
        if CAPTURAS:
            CAPTURAS.mkdir(parents=True, exist_ok=True)
            pg.screenshot(path=str(CAPTURAS / f'achados-{nome}.png'), full_page=True)

    def clicar(pg, dx, fy):
        canvas = pg.locator('canvas')
        caixa = canvas.bounding_box()
        canvas.click(position={'x': caixa['width'] / 2 + dx, 'y': caixa['height'] * fy})

    def preencher_e_salvar(pg, categoria='doenca'):
        pg.get_by_label('CID-10').press_sequentially('hiper', delay=40)
        pg.get_by_role('list', name='Resultados do CID-10').get_by_role('button', name='I10').click()
        pg.locator('select[name=categoria]').select_option(categoria)
        pg.get_by_role('button', name='Salvar achado').click()
        pg.wait_for_selector('text=Achado registrado.')

    # 1) clique no fêmur esquerdo abre o formulário com o lado preenchido
    pg = abrir('masculino')
    carregados(pg, 'tegumentar')
    pg.wait_for_selector('text=Nenhum achado registrado')
    pg.check('input[value=esqueletico]')
    carregados(pg, 'tegumentar esqueletico')
    ponto = None
    for fy in (0.60, 0.57, 0.63):
        for passo in range(40):
            clicar(pg, passo * 4, fy)
            pg.wait_for_timeout(60)
            painel = pg.locator('[data-ancora]')
            if painel.count() and 'FMA24475' in painel.inner_text():
                ponto = (passo * 4, fy)
                break
        if ponto:
            break
    assert ponto, 'nenhum clique abriu o formulário no fêmur esquerdo'
    assert pg.locator('select[name=lado]').input_value() == 'esquerdo'
    foto(pg, '1-formulario')
    pg.get_by_role('button', name='Salvar achado').click()
    assert not gravados, 'salvou sem CID e sem categoria'
    preencher_e_salvar(pg)
    buscas = [c for n, c in chamadas if n == 'buscar_cid10']
    assert buscas == [{'p_texto': 'hiper', 'p_limite': 20}], f'debounce falhou: {buscas}'

    ancora = gravados[0]['ancora']
    assert set(ancora) == {'atlas', 'atlas_versao', 'sistema', 'estrutura', 'malha', 'posicao_local',
                           'normal_local', 'triangulo', 'baricentricas'}, ancora
    assert ancora['estrutura'] == 'FMA24475' and gravados[0]['lado'] == 'esquerdo' and gravados[0]['inicio'] is None

    def conferir_posicao(momento):
        pg.wait_for_selector('[data-motor][data-marcadores="1"]')
        pg.wait_for_timeout(800)
        [desenhado] = pg.evaluate(DESENHADOS)
        assert all(abs(a - b) < 1e-9 for a, b in zip(desenhado['posicao'], ancora['posicao_local'])), (desenhado, ancora)
        print(f'{momento}: gravada {ancora["posicao_local"]} == desenhada {desenhado["posicao"]} (raio {desenhado["raio"]})')

    conferir_posicao('após salvar')

    # 2) recarregar: o marcador volta no mesmo ponto
    pg.reload()
    carregados(pg, 'tegumentar')
    conferir_posicao('após recarregar')

    # 3) linha pelo teclado abre o cartão e liga o sistema; Esc fecha; clicar no marcador reabre
    linha = pg.locator('button[data-achado]')
    linha.focus()
    pg.keyboard.press('Enter')
    cartao = pg.locator('[data-cartao]')
    cartao.wait_for()
    for trecho in ('I10', CID['descricao'], 'Profissional Fictício', 'Unidade Fictícia', '2026', 'Esquerdo'):
        assert trecho in cartao.inner_text(), (trecho, cartao.inner_text())
        assert trecho == 'Esquerdo' or trecho in linha.inner_text(), (trecho, linha.inner_text())
    carregados(pg, 'tegumentar esqueletico')
    foto(pg, '2-cartao')
    pg.keyboard.press('Escape')
    assert cartao.count() == 0
    clicar(pg, *ponto)
    cartao.wait_for()
    assert pg.locator('[data-ancora]').count() == 0, 'clique no marcador abriu o formulário'

    # 4) sem local no corpo: âncora nula, sem marcador novo
    pg.get_by_role('button', name='Achado sem local no corpo').click()
    assert pg.locator('select[name=lado]').input_value() == 'nao_se_aplica'
    preencher_e_salvar(pg)
    assert gravados[1]['ancora'] is None
    pg.wait_for_selector('text=Achados (2)')
    assert 'sem local no corpo' in pg.locator('button[data-achado]').nth(1).inner_text()
    assert len(pg.evaluate(DESENHADOS)) == 1
    pg.close()
    print('formulário, debounce, salvar, recarregar, teclado, marcador e sem local: OK')

    # 5) feminina no corpo masculino provisório: clique não abre formulário; sem local continua
    pg = navegador.new_page()
    pg.set_default_timeout(180000)
    pg.route('**/rest/v1/**', rpc)
    pg.route('**/atlas/hra-f/**', lambda r: r.fulfill(status=404, body=''))
    pg.goto(f'{APP}/dev/motor?achados=1&sexo=feminino')
    carregados(pg, 'tegumentar')
    assert 'Não é possível marcar achados nele' in pg.inner_text('main')
    for fy in (0.30, 0.35, 0.40, 0.45):
        clicar(pg, 0, fy)
        pg.wait_for_timeout(200)
    assert pg.get_by_role('button', name='Salvar achado').count() == 0, 'corpo provisório aceitou âncora'
    pg.get_by_role('button', name='Achado sem local no corpo').click()
    preencher_e_salvar(pg)
    assert gravados[2]['ancora'] is None
    foto(pg, '3-provisorio')
    pg.close()
    print('feminino provisório: âncora bloqueada, sem local OK')

    # 6) celular sem rolagem lateral; falha ao listar aparece como erro
    pg = abrir('masculino', 390, 844)
    carregados(pg, 'tegumentar')
    pg.locator('button[data-achado]').first.click()
    pg.get_by_role('button', name='Achado sem local no corpo').click()
    assert pg.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'rolagem lateral no celular'
    foto(pg, '4-390')
    pg.close()
    assert not console, '\n'.join(console)

    pg = navegador.new_page()
    pg.set_default_timeout(180000)
    pg.route('**/rest/v1/**', lambda r: r.fulfill(status=500, headers={'access-control-allow-origin': '*'}, body='{}'))
    pg.goto(f'{APP}/dev/motor?achados=1')
    pg.wait_for_selector('text=Não foi possível carregar os achados')
    navegador.close()
    print('390 px, console limpo e erro de listagem: OK')
