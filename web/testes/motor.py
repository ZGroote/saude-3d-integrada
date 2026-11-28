"""Teste do 3D no app, sem Supabase. Uso, em web/:  npm run atlas && npm run build && python testes/motor.py [pasta-capturas]
(com APP_URL=http://... usa um `next dev` já rodando)

1) `next dev`: /dev/motor (mesmo componente do prontuário) no Chrome headless.
2) `next start` sobre o build: /dev/motor tem de dar 404 e o atlas tem de ser servido.
Precisa de Playwright para Python e do Chrome.
"""
import json
import math
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
WEB = Path(__file__).resolve().parent.parent
NEXT = next(n for p in (WEB, *WEB.parents) if (n := p / 'node_modules/next/dist/bin/next').exists())
ATLAS = WEB / 'public/atlas'
CAPTURAS = Path(sys.argv[1]) if len(sys.argv) > 1 else None
assert (ATLAS / 'bp3d-m/4.0-1/manifesto.json').exists(), 'rode antes: npm run atlas'
SOLO_NAVEGADOR = os.environ.get('MOTOR_SOLO_NAVEGADOR') == '1'
if SOLO_NAVEGADOR:
    assert os.environ.get('APP_URL'), 'MOTOR_SOLO_NAVEGADOR=1 exige APP_URL de um servidor já iniciado'
else:
    assert (WEB / '.next/BUILD_ID').exists(), 'rode antes: npm run build'
FEMININO_REAL = (ATLAS / 'hra-f/1.10-1/manifesto.json').exists()


def pedir(url):
    try:
        with urllib.request.urlopen(url, timeout=180) as r:
            return r.status
    except urllib.error.HTTPError as erro:
        return erro.code


class Servidor:
    def __init__(self, modo):
        self.modo = modo

    def __enter__(self):
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
            porta = s.getsockname()[1]
        self.saida = tempfile.TemporaryFile()
        self.processo = subprocess.Popen(
            ['node', str(NEXT), self.modo, '-H', '127.0.0.1', '-p', str(porta)], cwd=WEB,
            stdout=self.saida, stderr=subprocess.STDOUT, start_new_session=os.name != 'nt')
        url = f'http://127.0.0.1:{porta}'
        for _ in range(200):
            assert self.processo.poll() is None, self.log()
            try:
                socket.create_connection(('127.0.0.1', porta), timeout=1).close()
                return url
            except OSError:
                time.sleep(0.3)
        raise AssertionError('servidor não subiu:\n' + self.log())

    def log(self):
        self.saida.seek(0)
        return self.saida.read().decode('utf-8', 'replace')

    def __exit__(self, *_):
        # o Next cria processos filhos: encerrar só o pai deixaria o servidor (e a trava) para trás
        if os.name == 'nt':
            subprocess.run(['taskkill', '/T', '/F', '/PID', str(self.processo.pid)], capture_output=True)
        else:
            os.killpg(self.processo.pid, signal.SIGTERM)
        self.processo.wait(timeout=30)


def desenvolvimento(url):
    with sync_playwright() as p:
        navegador = p.chromium.launch(channel='chrome', args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'])
        console, glbs = [], []

        def abrir(sexo, largura=1440, altura=900):
            pg = navegador.new_page(viewport={'width': largura, 'height': altura})
            pg.set_default_timeout(180000)  # a primeira compilação do dev é lenta

            def anotar(m):
                # o HEAD que descobre que o atlas feminino não existe aparece como 404 no console
                if m.type in ('error', 'warning') and 'hra-f' not in m.location.get('url', ''):
                    console.append(f'{m.type}: {m.text} {m.location.get("url", "")}')

            pg.on('console', anotar)
            pg.on('pageerror', lambda e: console.append(str(e)))
            pg.on('request', lambda r: r.url.endswith('.glb') and glbs.append(r.url.split('/atlas/')[1]))
            pg.goto(f'{url}/dev/motor?sexo={sexo}')
            return pg

        def carregados(pg, ids):
            pg.wait_for_selector(f'[data-motor][data-carregados="{ids}"]')
            pg.wait_for_timeout(800)

        def foto(pg, nome):
            if CAPTURAS:
                pg.screenshot(path=str(CAPTURAS / f'web-{nome}.png'), full_page=True)

        def clicar_ate(pg, esperado, alturas):
            caixa = pg.locator('canvas').bounding_box()
            for fy in alturas:
                for passo in range(0, 40):
                    pg.mouse.click(caixa['x'] + caixa['width'] / 2 + passo * 4, caixa['y'] + caixa['height'] * fy)
                    pg.wait_for_timeout(40)
                    if pg.locator('[data-ancora]').count() and esperado in pg.inner_text('[data-ancora]'):
                        return pg.inner_text('[data-ancora]')
            raise AssertionError(f'nenhum clique mostrou {esperado}')

        # masculino: abre na pele
        pg = abrir('masculino')
        carregados(pg, 'tegumentar')
        assert pg.get_attribute('[data-atlas]', 'data-atlas') == 'bp3d-m'
        assert set(glbs) == {'bp3d-m/4.0-1/tegumentar.glb'}, glbs
        assert pg.get_attribute('[data-motor]', 'data-pele') == 'opaca'
        # estilos do Tailwind aplicados: corpo alto, com o painel ao lado
        caixa, painel = pg.locator('canvas').bounding_box(), pg.get_by_role('group', name='Sistemas').bounding_box()
        assert caixa['height'] >= 600 and painel['x'] > caixa['x'] + caixa['width'], (caixa, painel)
        assert 'BodyParts3D' in pg.inner_text('[data-motor]')
        assert pg.is_checked('input[value=tegumentar]') and pg.locator('fieldset input').count() == 15
        assert 'Clique no corpo' in pg.inner_text('body')
        pele = clicar_ate(pg, 'Pele', (0.35,))
        assert 'tradução não revisada' in pele, pele
        pg.check('input[value=esqueletico]')
        carregados(pg, 'tegumentar esqueletico')
        assert pg.get_attribute('[data-motor]', 'data-pele') == 'translucida'
        femur = clicar_ate(pg, 'FMA24475', (0.60, 0.57, 0.63))
        for trecho in ('Fêmur esquerdo', 'tradução não revisada', 'Esquerdo', 'Esquelético'):
            assert trecho in femur, (trecho, femur)
        print('masculino: pele, seletor e painel ok ->', ' | '.join(femur.split('\n')))
        foto(pg, '1440-femur')
        pg.get_by_role('button', name='Vista posterior').click()
        pg.wait_for_function("document.querySelector('[data-motor]')?.getAttribute('data-vista') === 'posterior'")
        pg.get_by_role('button', name='Vista superior').click()
        pg.wait_for_function("document.querySelector('[data-motor]')?.getAttribute('data-vista') === 'superior'")
        camera_antes = json.loads(pg.get_attribute('[data-motor]', 'data-camera'))
        assert camera_antes['up'] == [0, 0, 1], camera_antes
        area_canvas = pg.locator('canvas').bounding_box()
        x, y = area_canvas['x'] + area_canvas['width'] / 2, area_canvas['y'] + area_canvas['height'] / 2
        pg.mouse.move(x, y)
        pg.mouse.down()
        pg.mouse.move(x + 55, y + 30, steps=6)
        pg.mouse.up()
        pg.wait_for_function("""antes => {
          const bruto = document.querySelector('[data-motor]')?.getAttribute('data-camera');
          if (!bruto) return false;
          const atual = JSON.parse(bruto);
          return atual.posicao.some((v, i) => v !== antes.posicao[i])
            || atual.alvo.some((v, i) => v !== antes.alvo[i]);
        }""", arg=camera_antes)
        camera_depois = json.loads(pg.get_attribute('[data-motor]', 'data-camera'))
        assert camera_depois['up'] == [0, 0, 1], camera_depois
        assert all(math.isfinite(v) for v in camera_depois['posicao'] + camera_depois['alvo'] + camera_depois['up']), camera_depois
        pg.get_by_role('button', name='Isolar estrutura').click()
        pg.wait_for_function("document.querySelector('[data-motor]')?.getAttribute('data-isoladas') === '1'")
        pg.get_by_role('button', name='Mostrar tudo').click()
        pg.wait_for_function("document.querySelector('[data-motor]')?.getAttribute('data-isoladas') === '0'")
        pg.check('input[value=muscular]')
        carregados(pg, 'tegumentar esqueletico muscular')
        pg.wait_for_function("Number(document.querySelector('[data-motor]')?.getAttribute('data-camadas-total')) > 0")
        assert 'Camadas musculares aproximadas' in pg.inner_text('[aria-label="Ferramentas do corpo"]')
        print('vistas superior/posterior, órbita sem NaN, isolamento/restauração e camadas musculares ok')
        ciclos_gpu = []
        for ciclo in range(1, 9):
            pg.uncheck('input[value=muscular]')
            carregados(pg, 'tegumentar esqueletico')
            pg.check('input[value=muscular]')
            carregados(pg, 'tegumentar esqueletico muscular')
            pg.wait_for_function("""() => {
              const m = document.querySelector('[data-motor]');
              return !!m?.getAttribute('data-gpu') && !!m?.getAttribute('data-visuais');
            }""")
            geometrias, texturas = map(int, pg.get_attribute('[data-motor]', 'data-gpu').split('/'))
            visuais = int(pg.get_attribute('[data-motor]', 'data-visuais'))
            ciclos_gpu.append((geometrias, texturas, visuais))
            print(f'GPU ciclo {ciclo}: geometrias={geometrias} texturas={texturas} visuais={visuais}')
        baseline_gpu = ciclos_gpu[1]
        assert all(g <= baseline_gpu[0] and v <= baseline_gpu[2] for g, _, v in ciclos_gpu[2:]), ciclos_gpu
        print(f'GPU estável após ciclo 2: baseline={baseline_gpu}; ciclos={ciclos_gpu}')
        pg.close()

        # feminino sem atlas publicado (404 forçado para valer mesmo quando ele existir)
        pg = navegador.new_page()
        pg.set_default_timeout(180000)
        pg.route('**/atlas/hra-f/**', lambda r: r.fulfill(status=404, body=''))
        pg.goto(f'{url}/dev/motor?sexo=feminino')
        carregados(pg, 'tegumentar')
        assert 'Atlas feminino em preparação' in pg.inner_text('main')
        assert pg.get_attribute('[data-atlas]', 'data-atlas') == 'bp3d-m'
        foto(pg, 'feminino-provisorio')
        pg.close()

        # feminino publicado: simulado servindo o pacote masculino com identidade hra-f
        def hra_simulado(rota):
            nome = rota.request.url.rsplit('/', 1)[1]
            dados = (ATLAS / 'bp3d-m/4.0-1' / nome).read_bytes()
            if nome == 'manifesto.json':
                manifesto = json.loads(dados)
                manifesto['sistemas'].append({'id': 'gestacional', 'glb': 'fascia.glb', 'estruturas': 1})
                dados = json.dumps({**manifesto, 'atlas': 'hra-f', 'versao': '1.10-1'}).encode()
            tipo = 'application/json' if nome.endswith('.json') else 'model/gltf-binary'
            rota.fulfill(status=200, body=dados, content_type=tipo)

        pg = navegador.new_page()
        pg.set_default_timeout(180000)
        pg.route('**/atlas/hra-f/1.10-1/*', hra_simulado)
        pg.goto(f'{url}/dev/motor?sexo=feminino')
        carregados(pg, 'tegumentar')
        assert pg.get_attribute('[data-atlas]', 'data-atlas') == 'hra-f'
        assert 'em preparação' not in pg.inner_text('main')
        pg.wait_for_selector('input[value=tegumentar]')
        assert pg.locator('input[value=gestacional]').count() == 0, 'camada gestacional fora do contexto de gestação'
        pg.close()
        print('feminino: sem atlas cai no masculino com aviso; publicado (simulado) usa hra-f')

        if FEMININO_REAL:
            pg = abrir('feminino')
            pg.wait_for_selector('[data-atlas="hra-f"] [data-motor][data-carregados="tegumentar"]')
            pg.wait_for_selector('text=Faltam neste corpo: Púbis, Ísquio, Acetábulo.')
            foto(pg, 'feminino-real')
            pg.close()
            print('atlas hra-f real abre na pele')

            def rpc_hra_vazia(route):
                pedido = route.request
                cors = {'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*'}
                if pedido.method == 'OPTIONS':
                    return route.fulfill(status=204, headers=cors)
                nome = pedido.url.split('?')[0].rsplit('/', 1)[1]
                if nome == 'listar_achados':
                    dados = []
                elif nome == 'minha_unidade':
                    dados = None
                else:
                    raise AssertionError(f'rpc inesperada no diagnóstico das lacunas: {nome}')
                return route.fulfill(status=200, headers=cors, content_type='application/json', body=json.dumps(dados))

            pg = navegador.new_page(viewport={'width': 1440, 'height': 900})
            pg.set_default_timeout(180000)
            pg.route('**/rest/v1/rpc/**', rpc_hra_vazia)
            pg.goto(f'{url}/dev/motor?achados=1&sexo=feminino')
            pg.wait_for_selector('[data-atlas="hra-f"] [data-motor][data-carregados="tegumentar"]')
            pg.get_by_role('button', name='Achado com local no corpo').click()
            busca_lacuna = pg.get_by_role('combobox', name='Buscar estrutura do corpo')
            busca_lacuna.fill('isq')
            nota_isquio = pg.locator('p[role="note"]').filter(has_text='Ísquio não existe neste corpo')
            nota_isquio.wait_for()
            assert 'Registre o achado sem local' in nota_isquio.inner_text()
            busca_lacuna.fill('ilio')
            opcao_ilio = pg.get_by_role('option').filter(has_text='Ílio (osso compacto)').first
            opcao_ilio.wait_for()
            assert 'lado' in opcao_ilio.inner_text().lower(), opcao_ilio.inner_text()
            assert 'Faltam neste corpo: Púbis, Ísquio, Acetábulo.' in pg.inner_text('main')
            print('lacunas HRA: isq mostra nota; ilio mostra Ílio (osso compacto) com lado; aviso visível')
            pg.close()

        # indeterminado: só mostra corpo depois da escolha
        pg = abrir('indeterminado')
        pg.wait_for_selector('select')
        assert pg.locator('canvas').count() == 0
        pg.select_option('select', 'bp3d-m')
        carregados(pg, 'tegumentar')
        pg.check('input[value=esqueletico]')
        pg.select_option('select', 'hra-f')
        if not FEMININO_REAL:
            pg.wait_for_selector('text=Atlas feminino em preparação')
            carregados(pg, 'tegumentar')
            assert not pg.is_checked('input[value=esqueletico]') or FEMININO_REAL
        pg.close()
        print('indeterminado: seletor ok')

        for largura, altura in ((820, 1180), (390, 844)):
            pg = abrir('masculino', largura, altura)
            carregados(pg, 'tegumentar')
            sobra = pg.evaluate('document.documentElement.scrollWidth - innerWidth')
            caixa = pg.locator('canvas').bounding_box()
            assert sobra <= 0 and caixa['width'] > largura * 0.8 and caixa['height'] >= 380, (largura, sobra, caixa)
            centro_coberto = pg.locator('canvas').evaluate("""canvas => {
              const r = canvas.getBoundingClientRect();
              return document.elementFromPoint(r.left + r.width / 2, r.top + r.height * 0.42) !== canvas;
            }""")
            assert not centro_coberto, f'barra/elemento cobre o centro do canvas em {largura}px'
            foto(pg, str(largura))
            pg.close()
        print('820 e 390 px: sem rolagem lateral')

        assert not console, '\n'.join(console)
        print('console limpo')
        navegador.close()


if os.environ.get('APP_URL'):  # um `next dev` já rodando nesta pasta (o Next não permite um segundo)
    desenvolvimento(os.environ['APP_URL'].rstrip('/'))
else:
    with Servidor('dev') as url:
        desenvolvimento(url)

if not SOLO_NAVEGADOR:
    with Servidor('start') as url:
        assert pedir(f'{url}/dev/motor') == 404, '/dev/motor existe em produção'
        assert pedir(f'{url}/atlas/bp3d-m/4.0-1/manifesto.json') == 200
    rotas = json.loads((WEB / '.next/app-path-routes-manifest.json').read_text(encoding='utf-8'))
    assert not [r for r in rotas if 'dev' in r], rotas
    print('produção: /dev/motor = 404 e fora do build; atlas servido\nOK')
else:
    print('teste de navegador isolado: servidor externo preservado; produção não iniciada')
