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
    if nome == 'unidades':
        linha = {'nome': 'Unidade Fictícia'}
        um = 'pgrst.object' in pedido.headers.get('accept', '')
        return rota.fulfill(status=200, headers=cors, content_type='application/json', body=json.dumps(linha if um else [linha]))
    corpo = pedido.post_data_json or {}
    chamadas.append((nome, corpo))
    if nome == 'buscar_cid10':
        resposta = [CID]
    elif nome == 'registrar_achado':
        resposta = f'40000000-0000-4000-8000-{len(gravados) + 1:012d}'
        gravados.append({
            'id': resposta, **{k[2:]: v for k, v in corpo.items() if k not in ('p_paciente', 'p_cid10', 'p_substitui')},
            'substitui_id': corpo.get('p_substitui'),
            'cid10': corpo['p_cid10'], 'cid10_descricao': CID['descricao'], 'especialidade': 'cardiologia',
            'autor_nome': 'Profissional Fictício', 'unidade_nome': 'Unidade Fictícia', 'criado_em': '2026-11-25T12:00:00Z',
        })
    elif nome == 'listar_achados':
        substituidos = {a['substitui_id'] for a in gravados}
        resposta = [a for a in gravados if a['id'] not in substituidos]
    elif nome == 'minha_unidade':
        resposta = '10000000-0000-4000-8000-0000000000aa'
    elif nome == 'historico_achado':
        por_id = {a['id']: a for a in gravados}
        resposta, atual = [], corpo['p_achado']
        while atual:
            resposta.insert(0, por_id[atual])
            atual = por_id[atual]['substitui_id']
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
    if (!o.isInstancedMesh || o.geometry.type !== 'SphereGeometry') return;
    for (let i = 0; i < o.count; i++) {
      const m = o.instanceMatrix.array.subarray(i * 16, i * 16 + 16);
      achados.push({ posicao: [m[12], m[13], m[14]], raio: m[0] });
    }
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
        assert all(abs(a - b) < 1e-6 for a, b in zip(desenhado['posicao'], ancora['posicao_local'])), (desenhado, ancora)
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
    print('formulário, debounce, salvar, recarregar, teclado, marcador e sem local: OK')

    # 4b) filtros e linha do tempo agem ao mesmo tempo no corpo e nas listas
    antigo = {**gravados[0], 'id': '40000000-0000-4000-8000-0000000000bb', 'especialidade': 'ortopedia', 'status': 'resolvido',
              'inicio': '2020-05-01', 'autor_nome': 'Outro Profissional',
              'unidade_id': '10000000-0000-4000-8000-0000000000cc'}  # mesmo nome, outro id: vale o id
    gravados.append(antigo)
    pg.reload()
    carregados(pg, 'tegumentar')
    linhas = pg.locator('button[data-achado]')

    def conferir(total_linhas, marcadores, titulo):
        pg.wait_for_selector(f'text={titulo}')
        pg.wait_for_selector(f'[data-motor][data-marcadores="{marcadores}"]')
        pg.wait_for_timeout(500)
        assert linhas.count() == total_linhas and len(pg.evaluate(DESENHADOS)) == marcadores, (titulo, linhas.count())

    conferir(3, 2, 'Achados (3)')
    dias = pg.locator('ul[aria-labelledby=achados-no-corpo] button').evaluate_all('(b) => b.map((e) => e.dataset.dia)')
    assert dias == sorted(dias) and dias[0] == '2020-05-01', dias
    assert pg.locator('ul[aria-labelledby=achados-sem-local] button').count() == 1
    pg.select_option('select[name=filtro-especialidade]', 'ortopedia')
    conferir(1, 1, 'Achados (1 de 3)')
    pg.select_option('select[name=filtro-status]', 'ativo')
    conferir(0, 0, 'Achados (0 de 3)')
    pg.get_by_role('button', name='Limpar filtros').click()
    pg.fill('input[name=filtro-ate]', '2021-01-01')
    conferir(1, 1, 'Achados (1 de 3)')
    pg.fill('input[name=filtro-ate]', '')
    pg.fill('input[name=filtro-de]', '2021-01-01')
    conferir(2, 1, 'Achados (2 de 3)')
    pg.get_by_role('button', name='Limpar filtros').click()
    pg.locator('input[name=intervalo-fim]').focus()
    pg.keyboard.press('Home')  # deslizante pelo teclado: fim do intervalo no primeiro dia
    conferir(1, 1, 'Achados (1 de 3)')
    assert pg.input_value('input[name=filtro-ate]') == '2020-05-01'
    foto(pg, '5-linha-do-tempo')
    pg.get_by_role('button', name='Limpar filtros').click()
    print('filtros combinados, período digitado e deslizante: OK')

    # 4c) corrigir: só na própria unidade; grava com p_substitui, mantém o local e mostra o histórico
    pg.locator(f'button[data-achado="{antigo["id"]}"]').click()
    assert pg.get_by_role('button', name='Corrigir').count() == 0, 'corrigir em achado de outra unidade'
    original = gravados[0]
    pg.locator(f'button[data-achado="{original["id"]}"]').click()
    assert 'não foi corrigido' in cartao.inner_text()
    pg.get_by_role('button', name='Corrigir').click()
    assert pg.locator('select[name=categoria]').input_value() == 'doenca'
    assert pg.locator('select[name=lado]').input_value() == 'esquerdo'
    assert pg.locator('[data-cid-escolhido] strong').inner_text() == 'I10'
    pg.locator('select[name=status]').select_option('resolvido')
    pg.get_by_role('button', name='Salvar correção').click()
    pg.wait_for_selector('text=Correção registrada.')
    envio = [c for n, c in chamadas if n == 'registrar_achado'][-1]
    assert envio['p_substitui'] == original['id'] and envio['p_ancora'] == original['ancora'], envio
    versoes = pg.locator('[data-cartao] ol[aria-label="Versões do achado"] li')
    versoes.nth(1).wait_for()
    assert versoes.count() == 2 and '(atual)' in versoes.nth(1).inner_text() and 'Ativo' in versoes.nth(0).inner_text()
    assert pg.locator(f'button[data-achado="{original["id"]}"]').count() == 0
    conferir(3, 2, 'Achados (3)')
    foto(pg, '6-historico')
    pg.close()
    print('corrigir e histórico: OK')

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
    assert gravados[-1]['ancora'] is None
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
