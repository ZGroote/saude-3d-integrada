"""Meta da Etapa 4 (SPEC §13): paciente com 200 achados abre em até 3 s (mediana de 5), em "tablet" simulado.
Uso, em web/, contra o app de produção já rodando (não sobe, não derruba e não faz build):

    python testes/desempenho.py [arquivo.json]          # APP_URL padrão: http://127.0.0.1:3020

CPU 4x mais lenta e rede "Fast 4G" (valores do DevTools), pelo CDP. Cada abertura usa um contexto novo,
só com a sessão: o cache do navegador começa vazio. Cada uma grava eventos na auditoria da homologação.
Senha lida de supabase/.env.demo, nunca impressa.

Critério: do início da navegação até a primeira tela da lista (com o total certo) E todos os marcadores na
cena, mais dois quadros. A lista completa (todas as linhas montadas) é medida e mostrada à parte.
"""
import json
import math
import os
import statistics
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
WEB = Path(__file__).resolve().parent.parent
APP = os.environ.get('APP_URL', 'http://127.0.0.1:3020').rstrip('/')
EMAIL = 'cardiologia@saude3d.invalid'
PACIENTE = 'Paciente Carga Fictícia'
ABERTURAS, META_MS, CPU = 5, 3000, 4
FAST_4G = {'offline': False, 'latency': 60 * 2.75, 'downloadThroughput': 9e6 / 8 * 0.9, 'uploadThroughput': 1.5e6 / 8 * 0.9}

# conta os marcadores (instâncias) que estão de fato na cena do three e anota quando ficou tudo visível
MEDIDOR = """(esperado) => {
  window.__cenas = [];
  window.__THREE_DEVTOOLS__ = new EventTarget();
  window.__THREE_DEVTOOLS__.addEventListener('observe', (e) => e.detail.isScene && window.__cenas.push(e.detail));
  window.__tempos = {};
  const naCena = () => {
    let n = 0;
    for (const cena of window.__cenas) cena.traverse((o) => {
      if (o.isInstancedMesh && o.geometry.type === 'SphereGeometry') n += o.count;
    });
    return n;
  };
  const depoisDeDesenhar = (nome) => requestAnimationFrame(() => requestAnimationFrame(() => { window.__tempos[nome] = performance.now(); }));
  const vistos = {};
  const olhar = () => {
    const linhas = document.querySelectorAll('button[data-achado]').length;
    if (!vistos.lista && linhas >= esperado.primeira
        && [...document.querySelectorAll('h3')].some((h) => h.textContent === `Achados (${esperado.linhas})`)) {
      vistos.lista = true; depoisDeDesenhar('lista');
    }
    if (!vistos.lista_completa && linhas === esperado.linhas) {
      vistos.lista_completa = true; depoisDeDesenhar('lista_completa');
    }
    if (!vistos.marcadores && document.querySelector('canvas')?.width && naCena() >= esperado.marcadores) {
      vistos.marcadores = true; depoisDeDesenhar('marcadores');
    }
    if (!vistos.corpo && document.querySelector('[data-motor][data-carregados~="tegumentar"]')) {
      vistos.corpo = true; depoisDeDesenhar('corpo');
    }
    if (!vistos.completo && document.querySelector('[data-motor][data-completos~="tegumentar"]')) {
      vistos.completo = true; depoisDeDesenhar('completo');
    }
    if (!(vistos.lista && vistos.lista_completa && vistos.marcadores && vistos.corpo && vistos.completo)) requestAnimationFrame(olhar);
  };
  requestAnimationFrame(olhar);
}"""

RECURSOS = """() => ({
  documento: performance.getEntriesByType('navigation')[0].toJSON(),
  recursos: performance.getEntriesByType('resource').map((r) => ({ url: r.name, de: r.startTime, ate: r.responseEnd, bytes: r.encodedBodySize })),
  tempos: window.__tempos,
})"""


def senha_de(email):
    for linha in (WEB.parent / 'supabase/.env.demo').read_text(encoding='utf-8-sig').splitlines():
        chave, separador, valor = linha.partition('=')
        if separador and chave.strip() == email:
            return valor.strip()
    raise SystemExit(f'sem senha para {email} em supabase/.env.demo')


def p95(valores):
    """Posição mais próxima: com 5 aberturas, é a pior delas."""
    return sorted(valores)[math.ceil(0.95 * len(valores)) - 1]


with sync_playwright() as p:
    navegador = p.chromium.launch(channel='chrome', args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'])
    tela = {'width': 1180, 'height': 820}  # tablet deitado

    # sem limitação: entra, acha a paciente e descobre quantos achados e marcadores esperar
    contexto = navegador.new_context(viewport=tela)
    pg = contexto.new_page()
    pg.set_default_timeout(120000)
    pg.goto(f'{APP}/login')
    pg.fill('#email', EMAIL)
    try:
        pg.fill('#senha', senha_de(EMAIL))
    except Exception:
        raise AssertionError('não foi possível preencher a senha') from None  # o erro do Playwright a mostraria
    pg.click('button[type=submit]')
    pg.wait_for_url(f'{APP}/pacientes')
    pg.goto(f'{APP}/pacientes?busca=Carga')
    link = pg.locator('ul[aria-label="Pacientes vinculados"] a', has_text=PACIENTE)
    if not link.count():
        raise SystemExit(f'"{PACIENTE}" ainda não existe (ou sem vínculo com a cardiologia) na homologação')
    prontuario = APP + link.first.get_attribute('href')
    pg.goto(prontuario)
    pg.wait_for_selector('[data-motor][data-completos~="tegumentar"]')
    pg.wait_for_timeout(1500)
    atlas = pg.get_attribute('[data-atlas]', 'data-atlas')
    total = "Number([...document.querySelectorAll('h3')].map((h) => /^Achados \\((\\d+)\\)$/.exec(h.textContent)?.[1]).find(Boolean))"
    pg.wait_for_function(f"document.querySelectorAll('button[data-achado]').length === {total}")
    contar = lambda lista: pg.locator(f'ul[aria-labelledby={lista}] button').count()
    no_corpo, sem_local = contar('achados-no-corpo'), contar('achados-sem-local')
    esperado = {'linhas': pg.evaluate(total), 'marcadores': int(pg.get_attribute('[data-motor]', 'data-marcadores')),
                'primeira': min(30, no_corpo) + min(30, sem_local)}
    print(f'{esperado["linhas"]} achados, {no_corpo} com local, {esperado["marcadores"]} marcadores no {atlas}; '
          f'primeira tela: {esperado["primeira"]} linhas')
    assert esperado['linhas'] >= 200, f'a meta é com 200 achados; há {esperado["linhas"]}'
    assert esperado['marcadores'] == no_corpo, 'há achado com local sem marcador'
    sessao = contexto.storage_state()
    contexto.close()

    medidas = []
    for n in range(1, ABERTURAS + 1):
        contexto = navegador.new_context(viewport=tela, storage_state=sessao, has_touch=True)
        pg = contexto.new_page()
        pg.set_default_timeout(120000)
        pg.add_init_script(f'({MEDIDOR})({json.dumps(esperado)})')
        erros = []
        pg.on('console', lambda m: m.type == 'error' and erros.append(m.text))
        pg.on('pageerror', lambda e: erros.append(str(e)))
        cdp = contexto.new_cdp_session(pg)
        cdp.send('Network.enable')
        cdp.send('Network.emulateNetworkConditions', FAST_4G)
        cdp.send('Emulation.setCPUThrottlingRate', {'rate': CPU})
        pg.goto(prontuario, wait_until='commit')
        pg.wait_for_function('["lista", "lista_completa", "marcadores", "corpo", "completo"].every((n) => window.__tempos?.[n])', timeout=120000)
        dados = pg.evaluate(RECURSOS)
        contexto.close()

        assert not erros, erros  # inclui diferença entre o HTML do servidor e o do navegador
        tempos, recursos, documento = dados['tempos'], dados['recursos'], dados['documento']
        visivel = max(tempos['lista'], tempos['marcadores'])
        assert not [r for r in recursos if '/rpc/listar_achados' in r['url']], 'a abertura não deveria pedir a lista de novo'
        glbs = [r for r in recursos if r['url'].endswith('.glb')]
        nomes = [r['url'].rsplit('/', 1)[1] for r in sorted(glbs, key=lambda r: r['de'])]
        assert nomes in (['tegumentar.glb'], ['tegumentar_leve.glb', 'tegumentar.glb']), f'só a pele deveria ser baixada: {nomes}'
        # o que abre o corpo (o leve, se houver); o completo vem depois e é medido à parte
        leve = min(glbs, key=lambda r: r['de'])
        # o maior arquivo JS é o do motor 3D (three, R3F e o visualizador)
        motor = max((r for r in recursos if r['url'].split('?')[0].endswith('.js')), key=lambda r: r['bytes'])
        medida = {
            'visivel': visivel, 'lista': tempos['lista'], 'marcadores': tempos['marcadores'],
            'lista_completa': tempos['lista_completa'], 'corpo': tempos['corpo'],
            'completo': tempos['completo'],
            # banco: a página só começa a responder depois de abrir_prontuario e listar_achados, no servidor
            'banco_servidor': documento['responseStart'], 'html_chegou': documento['responseEnd'],
            'html_bytes': documento['encodedBodySize'],
            'js3d_inicio': motor['de'], 'js3d_fim': motor['ate'], 'js3d_bytes': motor['bytes'],
            'glb_inicio': leve['de'], 'glb': leve['ate'] - leve['de'], 'glb_bytes': leve['bytes'],
            # render: do código 3D em mãos até os marcadores desenhados
            'render_3d': tempos['marcadores'] - motor['ate'],
        }
        medidas.append(medida)
        print(f'abertura {n}: ' + ', '.join(f'{k}={v:.0f}' for k, v in medida.items()))
    navegador.close()

resumo = {k: {'mediana': statistics.median(m[k] for m in medidas), 'p95': p95([m[k] for m in medidas])} for k in medidas[0]}
print('\n(ms; *_bytes em bytes)             mediana        p95')
for chave, valor in resumo.items():
    print(f'{chave:<28}{valor["mediana"]:>14.0f}{valor["p95"]:>11.0f}')
print('as parcelas se sobrepõem no tempo (GLB e banco correm juntos): não somam o total')
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_text(json.dumps({'esperado': esperado, 'medidas': medidas, 'resumo': resumo}, indent=2), encoding='utf-8')
mediana = resumo['visivel']['mediana']
assert mediana <= META_MS, f'REPROVADO: mediana {mediana:.0f} ms > {META_MS} ms'
print(f'OK: mediana {mediana:.0f} ms <= {META_MS} ms (corpo/pele: {resumo["corpo"]["mediana"]:.0f} ms)')
