"""Aceite no navegador: sobe a demo (Vite) e clica no corpo. Uso: python testes/navegador.py [captura.png]

Precisa de Playwright para Python, do Chrome instalado e do atlas em atlas/bp3d-m/4.0-1/.
"""
import json
import math
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
PACOTE = Path(__file__).resolve().parent.parent

with socket.socket() as s:
    s.bind(('127.0.0.1', 0))
    porta = s.getsockname()[1]
url = f'http://127.0.0.1:{porta}/'
# com workspaces o npm instala o Vite na raiz do repositório, não dentro do pacote
VITE = next(v for p in (PACOTE, *PACOTE.parents) if (v := p / 'node_modules/vite/bin/vite.js').exists())
servidor = subprocess.Popen(
    ['node', str(VITE), '--host', '127.0.0.1', '--port', str(porta), '--strictPort'],
    cwd=PACOTE, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
try:
    for _ in range(100):
        try:
            urllib.request.urlopen(url, timeout=1)
            break
        except OSError:
            time.sleep(0.3)
    with sync_playwright() as p:
        navegador = p.chromium.launch(channel='chrome', args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'])
        pg = navegador.new_page(viewport={'width': 1200, 'height': 800})
        console, glbs = [], []
        pg.on('console', lambda m: m.type in ('error', 'warning') and console.append(f'{m.type}: {m.text}'))
        pg.on('pageerror', lambda e: console.append(str(e)))
        pg.on('request', lambda r: r.url.endswith('.glb') and glbs.append(r.url.rsplit('/', 1)[1]))

        def carregados(*ids):
            pg.wait_for_function(
                "ids => document.querySelector('[data-motor]')?.dataset.carregados === ids", arg=' '.join(ids), timeout=120000)
            pg.wait_for_timeout(800)

        texto = lambda seletor: pg.locator(seletor).text_content()
        ancora = lambda: json.loads(texto('#ancora') or 'null')
        total = lambda: int(texto('#total'))

        inicio = time.time()
        pg.goto(url)
        carregados('esqueletico')
        print(f'esqueleto pronto em {time.time() - inicio:.1f}s; GLBs baixados: {sorted(set(glbs))}')
        assert set(glbs) == {'esqueletico.glb'}, glbs
        assert 'BodyParts3D' in pg.locator('[data-motor]').inner_text()

        # arrastar gira a câmera e não escolhe ponto
        tela = pg.locator('canvas').bounding_box()
        cx, cy = tela['x'] + tela['width'] / 2, tela['y'] + tela['height'] / 2
        pg.mouse.move(cx, cy); pg.mouse.down(); pg.mouse.move(cx + 120, cy, steps=6); pg.mouse.up()
        pg.wait_for_timeout(300)
        assert total() == 0 and ancora() is None, 'arrasto gerou âncora'
        pg.reload(); carregados('esqueletico')

        # ACEITE: fêmur esquerdo (+x do paciente = direita da tela), na coxa
        femur = None
        for fy in (0.60, 0.57, 0.63):
            for passo in range(1, 40):
                x, y = cx + passo * 4, tela['y'] + tela['height'] * fy
                pg.mouse.click(x, y); pg.wait_for_timeout(30)
                a = ancora()
                if a and a['estrutura'] == 'FMA24475' and texto('#selecionado') == f'm{total()}':
                    femur = (x, y, a)
                    break
                pg.click('text=Limpar marcadores')
            if femur:
                break
        assert femur, 'nenhum clique devolveu FMA24475'
        x, y, a = femur
        print('âncora:', json.dumps(a))
        assert set(a) == {'atlas', 'atlas_versao', 'sistema', 'estrutura', 'malha', 'posicao_local', 'normal_local', 'triangulo', 'baricentricas'}
        assert (a['atlas'], a['atlas_versao'], a['sistema'], a['malha']) == ('bp3d-m', '4.0-1', 'esqueletico', 'FJ3259'), a
        px, py, pz = a['posicao_local']
        assert 0.01 < px < 0.2 and -0.5 < py < 0.1 and abs(pz) < 0.15, 'posicao_local fora do fêmur (metros)'
        assert math.isclose(math.hypot(*a['normal_local']), 1, abs_tol=1e-4) and a['normal_local'][2] > 0
        assert math.isclose(sum(a['baricentricas']), 1, abs_tol=1e-4) and min(a['baricentricas']) > -1e-4
        assert isinstance(a['triangulo'], int) and a['triangulo'] >= 0
        assert 'Fêmur esquerdo' in texto('#nome')
        pg.wait_for_function("document.querySelector('[data-motor]').dataset.marcadores === '1'")

        # o mesmo ponto agora tem um marcador: clicar nele seleciona, sem criar outro
        pg.mouse.click(x, y - 150); pg.wait_for_timeout(200)  # outro ponto, para a seleção mudar
        antes = total()
        pg.mouse.click(x, y); pg.wait_for_timeout(300)
        assert texto('#selecionado') == 'm1' and total() == antes, (texto('#selecionado'), total(), antes)
        pg.wait_for_timeout(500)
        if len(sys.argv) > 1:
            pg.screenshot(path=sys.argv[1])

        # sistemas sob demanda; camada desligada não recebe clique
        pg.check('input[value=arterial]'); carregados('esqueletico', 'arterial')
        assert set(glbs) == {'esqueletico.glb', 'arterial.glb'}, glbs
        pg.uncheck('input[value=esqueletico]'); carregados('arterial')
        pg.click('text=Limpar marcadores')
        pg.mouse.click(x, y); pg.wait_for_timeout(300)
        assert (ancora() or {}).get('estrutura') != 'FMA24475', 'camada oculta recebeu o clique'
        baixados = len(glbs)
        pg.check('input[value=esqueletico]'); carregados('arterial', 'esqueletico')
        assert len(glbs) == baixados, 'religar baixou de novo'

        # todos os sistemas
        inicio = time.time()
        for caixa in pg.locator('aside input').all():
            caixa.check()
        pg.wait_for_function(
            "document.querySelector('[data-motor]').dataset.carregados.split(' ').length === 15", timeout=180000)
        print(f'15 sistemas em {time.time() - inicio:.1f}s')
        fps = pg.evaluate("""() => new Promise(r => { let n = 0; const t = performance.now();
            (function f() { if (++n < 60 && performance.now() - t < 5000) requestAnimationFrame(f);
              else r(n / (performance.now() - t) * 1000) })() })""")
        print(f'fps com tudo ligado: {fps:.0f}')

        # âncora de outra versão, 3 cm fora da superfície e com outro nome de malha: o motor acha pela estrutura e reprojeta
        def abrir_gravada(**mudancas):
            antiga = {**a, 'atlas_versao': '4.0-0', 'malha': 'NOME-ANTIGO',
                      'posicao_local': [p + 0.03 * n for p, n in zip(a['posicao_local'], a['normal_local'])], **mudancas}
            pg.goto(url + '?ancora=' + urllib.parse.quote(json.dumps(antiga))); carregados('esqueletico')
            return int(pg.get_attribute('[data-motor]', 'data-marcadores'))
        assert abrir_gravada() == 1
        pg.mouse.click(x, y); pg.wait_for_timeout(300)
        assert texto('#selecionado') == 'gravada' and total() == 1, (texto('#selecionado'), total())
        assert ancora()['atlas_versao'] == '4.0-0' and ancora()['malha'] == 'NOME-ANTIGO', 'âncora original foi reescrita'
        assert abrir_gravada(atlas='hra-f') == 0, 'âncora de outro atlas foi desenhada'

        # só estrutural (FHIR): desenhada no centro da caixa do fêmur e clicável mesmo estando dentro do osso
        sem_geometria = dict.fromkeys(['posicao_local', 'normal_local', 'triangulo', 'baricentricas'])
        assert abrir_gravada(atlas_versao='4.0-1', malha='FJ3259', **sem_geometria) == 1
        if len(sys.argv) > 1:
            pg.screenshot(path=str(Path(sys.argv[1]).with_name('estrutural.png')))
        # procura o marcador a partir do ponto do clique no fêmur, do mais perto ao mais longe
        vizinhos = sorted(((dx, dy) for dx in range(-60, 61, 6) for dy in range(-90, 91, 6)), key=lambda d: math.hypot(*d))
        for dx, dy in vizinhos:
            pg.mouse.click(x + dx, y + dy)
            pg.wait_for_timeout(20)
            if texto('#selecionado') == 'gravada':
                break
        assert texto('#selecionado') == 'gravada', 'marcador estrutural não é clicável'
        assert ancora()['posicao_local'] is None
        print(f'marcador estrutural clicado a ({dx}, {dy}) px do ponto no fêmur')

        # marcadores de sistema desligado: o motor baixa sem mostrar, posiciona e avisa o que não deu
        indice = json.loads((PACOTE.parent.parent / 'atlas/bp3d-m/4.0-1/indice.json').read_text(encoding='utf-8'))
        arco = next(e for e in indice if e['estrutura'] == 'FMA3768')
        do_arco = dict(sistema=arco['sistema'], estrutura=arco['estrutura'], malha=arco['malha'])
        estrutural = {**a, **sem_geometria}

        def endereco(**mudancas):
            return url + '?ancora=' + urllib.parse.quote(json.dumps({**estrutural, **mudancas}))

        def marcador_gravado(marcadores, sem_posicao, **mudancas):
            glbs.clear()
            pg.goto(endereco(**mudancas)); carregados('esqueletico')
            pg.wait_for_selector(f'[data-motor][data-marcadores="{marcadores}"]', timeout=60000)
            pg.wait_for_selector(f'#sem-posicao:text-is("{sem_posicao}")', timeout=60000)
            return set(glbs)

        assert marcador_gravado(1, 'nenhum', **do_arco) == {'esqueletico.glb', 'arterial.glb'}
        assert pg.get_attribute('[data-motor]', 'data-carregados') == 'esqueletico', 'sistema do marcador apareceu'
        assert 'Carregando' not in pg.inner_text('[data-motor] [role=status]')
        # outra versão, com ponto, também baixa o sistema escondido
        assert 'arterial.glb' in marcador_gravado(
            1, 'nenhum', **do_arco, atlas_versao='4.0-0', posicao_local=[0.0, 0.45, 0.0],
            normal_local=[0.0, 0.0, 1.0], triangulo=0, baricentricas=[1.0, 0.0, 0.0])
        assert marcador_gravado(0, 'gravada', estrutura='FMA0', malha='NAO-EXISTE') == {'esqueletico.glb'}
        marcador_gravado(0, 'gravada', atlas='hra-f')
        # GLB do marcador falha: avisa; ligar o sistema tenta de novo
        pg3 = navegador.new_page()
        falha_arterial = [True]
        pg3.route('**/arterial.glb', lambda r: r.abort() if falha_arterial and falha_arterial.pop() else r.continue_())
        pg3.goto(endereco(**do_arco))
        pg3.wait_for_selector('#sem-posicao:text-is("gravada")', timeout=60000)
        pg3.check('input[value=arterial]')
        pg3.wait_for_selector('#sem-posicao:text-is("nenhum")', timeout=60000)
        pg3.wait_for_selector('[data-motor][data-marcadores="1"]')
        pg3.close()
        print('marcadores de sistema desligado e sem posição: ok')

        # pele: opaca sozinha; com sistema interno fica translúcida e o clique atravessa
        pg.goto(url); carregados('esqueletico')
        pg.check('input[value=tegumentar]'); carregados('esqueletico', 'tegumentar')
        assert pg.get_attribute('[data-motor]', 'data-pele') == 'translucida'
        if len(sys.argv) > 1:
            pg.screenshot(path=str(Path(sys.argv[1]).with_name('pele-translucida.png')))
        pg.mouse.click(x, y); pg.wait_for_timeout(300)
        assert ancora()['estrutura'] == 'FMA24475', ancora()
        pg.click('text=Limpar marcadores')
        pg.uncheck('input[value=esqueletico]'); carregados('tegumentar')
        assert pg.get_attribute('[data-motor]', 'data-pele') == 'opaca'
        if len(sys.argv) > 1:
            pg.screenshot(path=str(Path(sys.argv[1]).with_name('pele-opaca.png')))
        pg.mouse.click(x, y); pg.wait_for_timeout(300)
        assert ancora()['sistema'] == 'tegumentar', ancora()
        print('pele translúcida e clique através dela: ok')

        # tela de celular
        pg.set_viewport_size({'width': 390, 'height': 844}); pg.reload(); carregados('esqueletico')
        if len(sys.argv) > 1:
            pg.screenshot(path=str(Path(sys.argv[1]).with_name('celular.png')))

        assert not console, console
        print('console limpo')

        # falhas (aqui o erro no console é esperado): GLB que cai uma vez e atlas inexistente
        pg2 = navegador.new_page()
        falhar = [True]
        pg2.route('**/fascia.glb', lambda rota: rota.abort() if falhar and falhar.pop() else rota.continue_())
        pg2.goto(url)
        pg2.wait_for_selector('[data-motor][data-carregados="esqueletico"]', timeout=120000)
        pg2.check('input[value=fascia]')
        pg2.wait_for_selector('[role=status]:has-text("Falha ao carregar fascia")')
        pg2.uncheck('input[value=fascia]')
        pg2.check('input[value=fascia]')
        pg2.wait_for_selector('[data-motor][data-carregados="esqueletico fascia"]', timeout=60000)
        assert 'Falha' not in pg2.inner_text('[role=status]')
        pg2.route('**/manifesto.json', lambda rota: rota.fulfill(status=404, body=''))
        pg2.reload()
        pg2.wait_for_selector('[role=status]:has-text("Não foi possível abrir o atlas")')
        print('falha de GLB, nova tentativa e atlas ausente: ok')
        print('OK')
        navegador.close()
finally:
    servidor.terminate()
