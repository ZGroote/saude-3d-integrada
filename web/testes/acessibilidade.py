"""Etapa 7: acessibilidade e usabilidade em 1440, 820 e 390 px, contra a homologação (dados fictícios).
Uso, em web/, contra um app já rodando (não sobe nem derruba servidor):

    APP_URL=http://127.0.0.1:3040 python testes/acessibilidade.py [pasta-capturas] [--sem-gravar]

Para um servidor próprio sem mexer no `.next` de outro:
    NEXT_DIST_DIR=.next-etapa7 npx next build && NEXT_DIST_DIR=.next-etapa7 npx next start -p 3040

Confere, tela a tela: axe-core (reprova serious/critical), rolagem horizontal, sobreposição de controles e, em
390 px, alvos de toque >= 44 px. Depois (a menos de --sem-gravar): registrar e abrir um achado só pelo teclado
e a demonstração de referência (SPEC §14) em 390 px. Essas duas GRAVAM na homologação, a cada execução:
um achado sem local e um com local (teclado), três achados da demonstração e, se não houver, uma gestação em curso da Maria.
Senhas lidas de supabase/.env.demo, nunca impressas. Resultado em <pasta>/resultado.json.
"""
import json
import os
import re
import sys
import traceback
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
WEB = Path(__file__).resolve().parent.parent
APP = os.environ.get('APP_URL', 'http://127.0.0.1:3040').rstrip('/')
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
SAIDA = Path(ARGS[0]) if ARGS else WEB / 'testes/capturas/etapa7'
GRAVAR = '--sem-gravar' not in sys.argv
AXE = next(c for p in (WEB, *WEB.parents) if (c := p / 'node_modules/axe-core/axe.min.js').exists())
LARGURAS = ((1440, 900), (820, 1180), (390, 844))
MARIA = '30000000-0000-4000-8000-000000000001'
MARCA_TESTE = 'Teste de teclado (dado fictício)'
BEBE = 'Bebê Fictício Etapa5'
U = {n: f'{n}@saude3d.invalid' for n in ('cardiologia', 'ortopedia', 'obstetricia', 'pediatria', 'admin')}

SOBREPOSTOS = """() => {
  const visiveis = [...document.querySelectorAll('a[href], button, input:not([type=hidden]), select, textarea, summary')]
    .filter((e) => e.checkVisibility({ visibilityProperty: true, contentVisibilityAuto: true }))
    .map((e) => {
      // dentro de uma área com rolagem, só conta o pedaço que aparece
      let { left, top, right, bottom } = e.getBoundingClientRect();
      for (let p = e.parentElement; p; p = p.parentElement) {
        const s = getComputedStyle(p);
        if (s.overflowY !== 'visible' || s.overflowX !== 'visible') {
          const r = p.getBoundingClientRect();
          left = Math.max(left, r.left); top = Math.max(top, r.top); right = Math.min(right, r.right); bottom = Math.min(bottom, r.bottom);
        }
      }
      return { e, left, top, right, bottom };
    }).filter((r) => r.right - r.left > 2 && r.bottom - r.top > 2);
  const nome = (e) => (e.getAttribute('aria-label') || e.textContent || e.name || e.tagName).trim().replace(/\\s+/g, ' ').slice(0, 40);
  const pares = [];
  for (let i = 0; i < visiveis.length; i++) for (let j = i + 1; j < visiveis.length; j++) {
    const a = visiveis[i], b = visiveis[j];
    if (a.e.contains(b.e) || b.e.contains(a.e)) continue;
    const x = Math.min(a.right, b.right) - Math.max(a.left, b.left), y = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (x > 2 && y > 2) pares.push(`${nome(a.e)} × ${nome(b.e)}`);
  }
  return pares;
}"""

# a área de toque de uma caixa de marcar é o rótulo que a envolve
PEQUENOS = """() => {
  const ruins = [];
  for (const e of document.querySelectorAll('a[href], button, input:not([type=hidden]), select, textarea, summary, [role=button], [role=option]')) {
    if (!e.checkVisibility({ visibilityProperty: true })) continue;
    const alvo = (e.type === 'checkbox' || e.type === 'radio') && e.closest('label') ? e.closest('label') : e;
    const r = alvo.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    if (r.width < 43.5 || r.height < 43.5) {
      const nome = (e.getAttribute('aria-label') || e.closest('label')?.textContent || e.textContent || e.name || '').trim().replace(/\\s+/g, ' ').slice(0, 40);
      ruins.push(`${e.tagName.toLowerCase()}${e.type && e.tagName === 'INPUT' ? '[' + e.type + ']' : ''} "${nome}" ${Math.round(r.width)}x${Math.round(r.height)}`);
    }
  }
  return ruins;
}"""

falhas = defaultdict(list)  # categoria -> descrições
console = []


def senha_de(email):
    for linha in (WEB.parent / 'supabase/.env.demo').read_text(encoding='utf-8-sig').splitlines():
        chave, separador, valor = linha.partition('=')
        if separador and chave.strip() == email:
            return valor.strip()
    raise SystemExit(f'sem senha para {email} em supabase/.env.demo')


def anotar(categoria, texto):
    falhas[categoria].append(texto)


with sync_playwright() as p:
    SAIDA.mkdir(parents=True, exist_ok=True)
    navegador = p.chromium.launch(channel='chrome', args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'])
    sessoes = {}

    def pagina(usuario=None, largura=1440, altura=900):
        celular = largura < 600
        contexto = navegador.new_context(viewport={'width': largura, 'height': altura}, has_touch=celular, is_mobile=celular,
                                         storage_state=sessoes.get(usuario))
        pg = contexto.new_page()
        pg.set_default_timeout(60000)
        pg.on('console', lambda m: m.type == 'error' and console.append(f'{m.text} {m.location.get("url", "")}'))
        pg.on('pageerror', lambda e: console.append(str(e)))
        return pg

    def entrar(nome):
        pg = pagina()
        pg.goto(f'{APP}/login')
        pg.fill('#email', U[nome])
        try:
            pg.fill('#senha', senha_de(U[nome]))
        except Exception:
            raise AssertionError('não foi possível preencher a senha') from None  # o erro do Playwright a mostraria
        pg.click('button[type=submit]')
        pg.wait_for_url(f'{APP}/pacientes')
        sessoes[nome] = pg.context.storage_state()
        pg.context.close()

    for nome in U:
        entrar(nome)

    pg = pagina('pediatria')
    pg.goto(f'{APP}/pacientes?busca=Etapa5')
    bebe = pg.locator('ul[aria-label="Pacientes vinculados"] a', has_text=BEBE).first.get_attribute('href')
    pg.context.close()
    pg = pagina('obstetricia')
    pg.goto(f'{APP}/pacientes/{MARIA}/gestacao')
    pg.wait_for_selector('nav[aria-label="Páginas do paciente"]')
    pg.wait_for_timeout(1500)
    links = pg.locator('a[href*="/nascimento?gestacao="]')
    nascimento = links.first.get_attribute('href') if links.count() else f'/pacientes/{MARIA}/nascimento'
    pg.context.close()

    def corpo_pronto(pg):
        pg.wait_for_selector('[data-motor][data-completos~="tegumentar"]', timeout=90000)
        pg.wait_for_timeout(800)

    def prontuario_adulto(pg):
        corpo_pronto(pg)
        pg.wait_for_function("!document.querySelector('ul[aria-busy=true]')")

    def com_formulario_e_cartao(pg):
        prontuario_adulto(pg)
        pg.locator('button[data-achado]').first.click()
        pg.wait_for_selector('[data-cartao]')

    def com_formulario(pg):
        prontuario_adulto(pg)
        pg.get_by_role('button', name='Achado sem local no corpo').click()
        pg.get_by_label('CID-10').press_sequentially('I10', delay=30)
        pg.get_by_role('list', name='Resultados do CID-10').wait_for()

    def com_estruturas(pg):
        prontuario_adulto(pg)
        pg.get_by_role('button', name='Achado com local no corpo').click()
        pg.get_by_role('combobox', name='Buscar estrutura do corpo').press_sequentially('vertebra', delay=30)
        pg.get_by_role('listbox').wait_for()

    def com_condicao(pg):
        pg.wait_for_selector('nav[aria-label="Páginas do paciente"]')
        pg.wait_for_timeout(1000)
        if pg.locator('summary').count():
            pg.locator('summary').first.click()

    def com_previa(pg):
        pg.locator('input[type=file]').set_input_files(str(WEB / 'testes/dados/bundle-sintetico-50.json'))
        pg.get_by_label('Sistema de origem').fill('teste-homologacao')
        pg.get_by_role('button', name='Analisar').click()
        pg.wait_for_selector('text=Prévia: nada foi gravado ainda')

    def simples(pg):
        pg.locator('main h1').first.wait_for()
        pg.wait_for_timeout(800)

    # (nome, quem, caminho, preparo)
    TELAS = (
        ('login', None, '/login', simples),
        ('pacientes', 'cardiologia', '/pacientes', simples),
        ('prontuario-adulto', 'cardiologia', f'/pacientes/{MARIA}', prontuario_adulto),
        ('prontuario-cartao', 'cardiologia', f'/pacientes/{MARIA}', com_formulario_e_cartao),
        ('prontuario-formulario', 'cardiologia', f'/pacientes/{MARIA}', com_formulario),
        ('prontuario-estruturas', 'cardiologia', f'/pacientes/{MARIA}', com_estruturas),
        ('prontuario-crianca', 'pediatria', bebe, simples),
        ('gestacao', 'obstetricia', f'/pacientes/{MARIA}/gestacao', com_condicao),
        ('nascimento', 'obstetricia', nascimento, simples),
        ('familia', 'obstetricia', f'/pacientes/{MARIA}/familia', simples),
        ('familia-crianca', 'pediatria', f'{bebe}/familia', simples),
        ('importar', 'admin', '/importar', simples),
        ('importar-previa', 'admin', '/importar', com_previa),
    )

    for largura, altura in LARGURAS:
        for nome, quem, caminho, preparo in TELAS:
            onde = f'{nome} {largura}'
            pg = pagina(quem, largura, altura)
            try:
                pg.goto(APP + caminho)
                preparo(pg)
                # as linhas fora da tela usam content-visibility: sem isto o axe as pula e a captura sai em branco
                pg.add_style_tag(content='li { content-visibility: visible !important; }')
                pg.add_script_tag(path=str(AXE))
                violacoes = pg.evaluate("""async () => (await axe.run(document, { resultTypes: ['violations'] })).violations.map((v) =>
                    ({ id: v.id, impacto: v.impact, ajuda: v.help, nos: v.nodes.slice(0, 4).map((n) => n.target.join(' ')), total: v.nodes.length }))""")
                for v in violacoes:
                    if v['impacto'] in ('serious', 'critical'):
                        anotar('axe', f'{onde}: {v["id"]} ({v["impacto"]}, {v["total"]} nós) {v["ajuda"]} | {"; ".join(v["nos"])[:220]}')
                    else:
                        anotar('axe menor (não reprova)', f'{onde}: {v["id"]} ({v["impacto"]}, {v["total"]})')
                sobra = pg.evaluate('document.documentElement.scrollWidth - innerWidth')
                if sobra > 0:
                    anotar('rolagem horizontal', f'{onde}: {sobra} px')
                for par in pg.evaluate(SOBREPOSTOS):
                    anotar('sobreposição', f'{onde}: {par}')
                if largura == 390:
                    for alvo in pg.evaluate(PEQUENOS):
                        anotar('alvo < 44 px', f'{onde}: {alvo}')
                # o que está no corpo também está na lista
                if pg.locator('[data-motor]').count() and nome == 'prontuario-adulto':
                    marcadores = int(pg.get_attribute('[data-motor]', 'data-marcadores'))
                    na_lista = pg.locator('ul[aria-labelledby=achados-no-corpo] button').count()
                    if marcadores > na_lista:
                        anotar('3D fora da lista', f'{onde}: {marcadores} marcadores, {na_lista} na lista')
                pg.screenshot(path=str(SAIDA / f'{largura}-{nome}.png'), full_page=True, caret='initial')
                print('ok', onde)
            except Exception as erro:
                anotar('tela não conferida', f'{onde}: {type(erro).__name__}: {str(erro)[:200]}')
                print('ERRO', onde, str(erro)[:200])
            pg.context.close()

    def tabular(pg, condicao, descricao, limite=400, voltar=False):
        """Tab até o foco satisfazer `condicao` (expressão sobre `e`). Anota focos sem indicação visível."""
        for _ in range(limite):
            pg.keyboard.press('Shift+Tab' if voltar else 'Tab')
            estado = pg.evaluate("""(c) => { const e = document.activeElement; if (!e || e === document.body) return null;
                const s = getComputedStyle(e);
                return { achou: !!eval(c), visivel: s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0 || s.boxShadow !== 'none',
                         nome: e.tagName + ' ' + (e.getAttribute('aria-label') || e.textContent || e.name || '').trim().slice(0, 30) }; }""", condicao)
            if not estado:
                continue
            if not estado['visivel']:
                aviso = f'{estado["nome"]}'
                if aviso not in falhas['foco sem indicação']:
                    anotar('foco sem indicação', aviso)
            if estado['achou']:
                return
        raise AssertionError(f'o teclado não alcançou: {descricao}')

    def teclado():
        pg = pagina('cardiologia')
        pg.goto(f'{APP}/pacientes/{MARIA}')
        prontuario_adulto(pg)
        tabular(pg, "e.textContent.trim() === 'Achado sem local no corpo'", 'botão de achado sem local')
        pg.keyboard.press('Enter')
        pg.wait_for_selector('text=Novo achado')
        tabular(pg, "e.type === 'search'", 'busca de CID-10')
        pg.keyboard.type('I10', delay=40)
        pg.get_by_role('list', name='Resultados do CID-10').wait_for()
        tabular(pg, "e.closest('[aria-label=\"Resultados do CID-10\"]') && e.textContent.startsWith('I10')", 'resultado do CID-10')
        pg.keyboard.press('Enter')
        pg.wait_for_selector('[data-cid-escolhido]')
        tabular(pg, "e.name === 'categoria'", 'categoria')
        pg.keyboard.type('Doen')  # num select, digitar escolhe a opção
        assert pg.locator('select[name=categoria]').input_value() == 'doenca'
        tabular(pg, "e.name === 'observacao'", 'observação')
        pg.keyboard.type(MARCA_TESTE)  # supabase/limpar_testes_homologacao.py apaga pela marca
        tabular(pg, "e.type === 'submit' && e.textContent.includes('Salvar')", 'salvar')
        with pg.expect_response(lambda r: '/rpc/registrar_achado' in r.url and r.request.method == 'POST') as espera:
            pg.keyboard.press('Enter')
        novo = espera.value.json()
        pg.wait_for_selector(f'[data-cartao="{novo}"]')
        assert pg.evaluate('!!document.activeElement.closest("[data-cartao]")'), 'o foco não foi para o cartão salvo'
        pg.keyboard.press('Escape')
        pg.wait_for_selector('[data-cartao]', state='detached')
        pg.reload()
        prontuario_adulto(pg)
        tabular(pg, f"e.dataset.achado === '{novo}'", 'linha do achado na lista')
        pg.keyboard.press('Enter')
        pg.wait_for_selector(f'[data-cartao="{novo}"]')
        pg.screenshot(path=str(SAIDA / 'teclado-cartao.png'), caret='initial')
        pg.context.close()
        return 'achado registrado e aberto só pelo teclado'

    def teclado_com_local():
        """Achado COM local registrado pela busca de estrutura e aberto pela lista, sem ponteiro."""
        pg = pagina('cardiologia')
        pg.add_init_script("""
window.__cenas = []; window.__THREE_DEVTOOLS__ = new EventTarget();
window.__THREE_DEVTOOLS__.addEventListener('observe', (e) => e.detail.isScene && window.__cenas.push(e.detail));""")
        pg.goto(f'{APP}/pacientes/{MARIA}')
        prontuario_adulto(pg)
        antes = int(pg.get_attribute('[data-motor]', 'data-marcadores'))
        tabular(pg, "e.textContent.trim() === 'Achado com local no corpo'", 'botão de achado com local')
        pg.keyboard.press('Enter')
        campo = pg.get_by_role('combobox', name='Buscar estrutura do corpo')
        campo.wait_for()
        pg.wait_for_function("document.activeElement?.getAttribute('role') === 'combobox'")
        pg.keyboard.type('vertebra lombar', delay=30)
        pg.get_by_role('option').first.wait_for()
        opcoes = pg.get_by_role('option').all_inner_texts()
        pg.keyboard.press('ArrowDown')
        pg.keyboard.press('ArrowUp')
        assert pg.get_by_role('option').first.get_attribute('aria-selected') == 'true'
        pg.keyboard.press('Escape')
        assert campo.get_attribute('aria-expanded') == 'false'
        pg.keyboard.press('ArrowDown')  # reabre
        pg.keyboard.press('Enter')
        escolhida = pg.locator('form[aria-labelledby="titulo-novo-achado"] [data-ancora] strong').inner_text()
        assert opcoes[0].startswith(escolhida), (escolhida, opcoes[:3])
        assert pg.evaluate("document.activeElement?.getAttribute('role')") == 'combobox', 'a escolha tirou o foco do campo'
        tabular(pg, "e.type === 'search'", 'busca de CID-10')
        pg.keyboard.type('M54.5', delay=40)
        pg.get_by_role('list', name='Resultados do CID-10').wait_for()
        tabular(pg, "e.closest('[aria-label=\"Resultados do CID-10\"]') && e.textContent.startsWith('M54.5')", 'resultado do CID-10')
        pg.keyboard.press('Enter')
        pg.wait_for_selector('[data-cid-escolhido]')
        tabular(pg, "e.name === 'categoria'", 'categoria')
        pg.keyboard.type('Sint')
        tabular(pg, "e.name === 'observacao'", 'observação')
        pg.keyboard.type(MARCA_TESTE)
        tabular(pg, "e.type === 'submit' && e.textContent.includes('Salvar')", 'salvar')
        with pg.expect_response(lambda r: '/rpc/registrar_achado' in r.url and r.request.method == 'POST') as espera:
            pg.keyboard.press('Enter')
        novo, ancora = espera.value.json(), espera.value.request.post_data_json['p_ancora']
        assert novo and ancora['posicao_local'] is None and ancora['malha'] and ancora['atlas'] == 'hra-f', ancora
        pg.wait_for_selector(f'[data-cartao="{novo}"]')
        pg.wait_for_selector(f'[data-motor][data-marcadores="{antes + 1}"]', timeout=90000)
        pg.reload()
        prontuario_adulto(pg)
        tabular(pg, f"e.dataset.achado === '{novo}'", 'linha do achado na lista')
        assert 'não exibido' not in pg.locator(f'button[data-achado="{novo}"]').text_content()
        pg.keyboard.press('Enter')
        pg.wait_for_selector(f'[data-cartao="{novo}"]')
        pg.wait_for_selector(f'[data-motor][data-completos~="{ancora["sistema"]}"]', timeout=90000)
        pg.wait_for_timeout(1500)
        # o marcador está no centro da caixa da malha escolhida
        desvio = pg.evaluate("""(malha) => { let centro; const pontos = [];
  for (const cena of window.__cenas) cena.traverse((o) => {
    if (o.name === malha && o.userData.sistema) { o.geometry.computeBoundingBox(); const b = o.geometry.boundingBox;
      centro = ['x', 'y', 'z'].map((e) => (b.min[e] + b.max[e]) / 2); }
    if (o.isInstancedMesh && o.geometry.type === 'SphereGeometry')
      for (let i = 0; i < o.count; i++) pontos.push([...o.instanceMatrix.array.slice(i * 16 + 12, i * 16 + 15)]);
  });
  return centro ? Math.min(...pontos.map((p) => Math.hypot(...p.map((v, i) => v - centro[i])))) : null; }""", ancora['malha'])
        assert desvio is not None and desvio < 1e-5, desvio
        pg.screenshot(path=str(SAIDA / 'teclado-com-local.png'), caret='initial')
        pg.context.close()
        return f'"{escolhida}" ({ancora["malha"]}) registrado e aberto só pelo teclado; marcador no centro da malha'

    def registrar(pg, cid, categoria):
        formulario = pg.locator('form[aria-labelledby="titulo-novo-achado"]')
        formulario.locator('input[type=search]').press_sequentially(cid, delay=40)
        pg.get_by_role('list', name='Resultados do CID-10').locator('li button').filter(has_text=cid).first.tap()
        formulario.locator('select[name=categoria]').select_option(categoria)
        formulario.locator('textarea[name=observacao]').fill('Demonstração §14 (dado fictício)')
        with pg.expect_response(lambda r: '/rpc/registrar_achado' in r.url and r.request.method == 'POST') as espera:
            formulario.get_by_role('button', name='Salvar achado').tap()
        novo = espera.value.json()
        assert novo, 'o banco não devolveu o id'
        pg.wait_for_selector(f'[data-cartao="{novo}"]')
        return novo

    def tocar_ate(pg, nome, sistema, alturas, desvios):
        """Liga o sistema e toca no corpo até o formulário abrir numa estrutura cujo nome casa com `nome`."""
        pg.locator(f'input[value={sistema}]').check()
        pg.wait_for_selector(f'[data-motor][data-completos~="{sistema}"]', timeout=90000)
        pg.wait_for_timeout(1000)
        canvas, vistos = pg.locator('canvas'), set()
        formulario = pg.locator('form[aria-labelledby="titulo-novo-achado"]')
        for fy in alturas:
            for dx in desvios:
                canvas.scroll_into_view_if_needed()
                caixa = canvas.bounding_box()
                canvas.tap(position={'x': caixa['width'] / 2 + dx, 'y': caixa['height'] * fy})
                pg.wait_for_timeout(250)
                if formulario.locator('[data-ancora] strong').count():
                    achado = formulario.locator('[data-ancora] strong').inner_text()
                    vistos.add(achado)
                    if re.search(nome, achado, re.I):
                        return achado
        raise AssertionError(f'nenhum toque caiu em /{nome}/; vistos: {sorted(vistos)}')

    def demonstracao():
        ids, detalhes = {}, []

        def abrir(quem):
            pg = pagina(quem, 390, 844)
            pg.goto(f'{APP}/pacientes?busca=Maria')
            pg.locator(f'a[href="/pacientes/{MARIA}"]').tap()
            prontuario_adulto(pg)
            return pg

        pg = abrir('cardiologia')
        pg.get_by_role('button', name='Achado sem local no corpo').tap()
        ids['I10'] = registrar(pg, 'I10', 'doenca')
        pg.context.close()
        pg = abrir('ortopedia')
        local = tocar_ate(pg, 'lombar', 'esqueletico', (0.42, 0.40, 0.44, 0.38, 0.46, 0.36), (0, 5, -5, 10, -10))
        ids['M54.5'] = registrar(pg, 'M54.5', 'sintoma')
        detalhes.append(f'M54.5 em "{local}"')
        pg.context.close()
        pg = abrir('obstetricia')
        pg.get_by_role('navigation', name='Páginas do paciente').get_by_role('link', name='Gestação').tap()
        pg.wait_for_selector('[data-gestacao=em_curso], form[aria-labelledby=titulo-nova-gestacao]')
        if not pg.locator('[data-gestacao=em_curso]').count():
            pg.fill('input[name=dum]', str(date.today() - timedelta(140)))
            pg.fill('input[name=inicio_pre_natal]', str(date.today() - timedelta(90)))
            pg.get_by_role('button', name='Registrar gestação').tap()
            pg.wait_for_selector('[data-gestacao=em_curso]')
        assert 'pré-natal desde' in pg.locator('[data-gestacao=em_curso]').inner_text()
        pg.screenshot(path=str(SAIDA / '390-demo-gestacao.png'), full_page=True, caret='initial')
        pg.get_by_role('navigation', name='Páginas do paciente').get_by_role('link', name='Prontuário').tap()
        prontuario_adulto(pg)
        local = tocar_ate(pg, r'\bútero\b', 'urogenital', (0.50, 0.52, 0.48, 0.54, 0.46, 0.56, 0.49, 0.51, 0.47, 0.53), (0, 4, -4, 8, -8, 12, -12))
        ids['Z34'] = registrar(pg, 'Z34', 'sintoma')
        detalhes.append(f'Z34 em "{local}"')
        pg.context.close()
        for quem in ('cardiologia', 'ortopedia', 'obstetricia'):
            pg = abrir(quem)
            for codigo, i in ids.items():
                linha = pg.locator(f'button[data-achado="{i}"]')
                assert linha.count() == 1, f'{quem} não vê o {codigo}'
            linha = pg.locator(f'button[data-achado="{ids["M54.5"]}"]')
            linha.tap()
            pg.wait_for_selector(f'[data-cartao="{ids["M54.5"]}"]')
            assert pg.evaluate('document.documentElement.scrollWidth <= innerWidth')
            pg.add_style_tag(content='li { content-visibility: visible !important; }')
            pg.screenshot(path=str(SAIDA / f'390-demo-{quem}.png'), full_page=True, caret='initial')
            pg.context.close()
        return f'três unidades registraram e veem os três; {"; ".join(detalhes)}; gestação com pré-natal'

    fluxos = {}
    if GRAVAR:
        for nome, fluxo in (('teclado sem local', teclado), ('teclado com local', teclado_com_local), ('demonstração §14 em 390', demonstracao)):
            try:
                fluxos[nome] = 'PASSOU: ' + fluxo()
            except Exception as erro:
                traceback.print_exc()
                fluxos[nome] = f'REPROVOU: {type(erro).__name__}: {str(erro)[:400]}'
            print(nome, '->', fluxos[nome])
    navegador.close()

for texto in dict.fromkeys(console):
    anotar('erro no console', texto[:200])
(SAIDA / 'resultado.json').write_text(json.dumps({'fluxos': fluxos, 'falhas': falhas}, ensure_ascii=False, indent=1), encoding='utf-8')
print('\n=== RESUMO')
for categoria, itens in sorted(falhas.items()):
    print(f'\n## {categoria}: {len(itens)}')
    # o mesmo problema aparece em várias telas: agrupa pelo texto sem a tela
    grupos = defaultdict(list)
    for item in itens:
        tela, _, resto = item.partition(': ')
        grupos[resto or item].append(tela if resto else '')
    for resto, telas in list(grupos.items())[:60]:
        print(f'  {resto}  [{len(telas)}x: {", ".join(telas[:3])}]')
for nome, texto in fluxos.items():
    print(f'{nome}: {texto}')
reprova = [c for c in falhas if c != 'axe menor (não reprova)'] + [n for n, t in fluxos.items() if t.startswith('REPROVOU')]
print('\nREPROVADO: ' + ', '.join(reprova) if reprova else '\nOK')
sys.exit(bool(reprova))
