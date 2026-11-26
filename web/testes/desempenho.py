"""Meta da Etapa 4 (SPEC §13): paciente com 200 achados abre em até 3 s (mediana de 5), em "tablet" simulado.
Uso, em web/, contra o app de produção já rodando (não sobe, não derruba e não faz build):

    python testes/desempenho.py [arquivo.json]          # APP_URL padrão: http://127.0.0.1:3020

CPU 4x mais lenta e rede "Fast 4G" (valores do DevTools), pelo CDP. Cada abertura usa um contexto novo,
só com a sessão: o cache do navegador começa vazio. Cada uma grava eventos na auditoria da homologação.
Senha lida de supabase/.env.demo, nunca impressa.

Tempo medido: do início da navegação até lista completa e todos os marcadores na cena, mais dois quadros.
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
    if (!vistos.lista && document.querySelectorAll('button[data-achado]').length === esperado.linhas) {
      vistos.lista = true; depoisDeDesenhar('lista');
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
    if (!(vistos.lista && vistos.marcadores && vistos.corpo && vistos.completo)) requestAnimationFrame(olhar);
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
    with pg.expect_response(lambda r: '/rpc/listar_achados' in r.url and r.request.method == 'POST') as espera:
        pg.goto(prontuario)
    linhas = espera.value.json()
    pg.wait_for_selector('[data-atlas]')
    atlas = pg.get_attribute('[data-atlas]', 'data-atlas')
    no_corpo = [a for a in linhas if a['ancora'] and a['ancora']['atlas'] == atlas]
    esperado = {'linhas': len(linhas), 'marcadores': len(no_corpo)}
    sistemas = sorted({a['ancora']['sistema'] for a in no_corpo})
    sem_ponto = sum(not a['ancora']['posicao_local'] for a in no_corpo)
    print(f'{len(linhas)} achados, {len(no_corpo)} marcadores no {atlas}, sistemas {sistemas}, {sem_ponto} sem posicao_local')
    assert len(linhas) >= 200, f'a meta é com 200 achados; há {len(linhas)}'
    sessao = contexto.storage_state()
    contexto.close()

    medidas = []
    for n in range(1, ABERTURAS + 1):
        contexto = navegador.new_context(viewport=tela, storage_state=sessao, has_touch=True)
        pg = contexto.new_page()
        pg.set_default_timeout(120000)
        pg.add_init_script(f'({MEDIDOR})({json.dumps(esperado)})')
        cdp = contexto.new_cdp_session(pg)
        cdp.send('Network.enable')
        cdp.send('Network.emulateNetworkConditions', FAST_4G)
        cdp.send('Emulation.setCPUThrottlingRate', {'rate': CPU})
        pg.goto(prontuario, wait_until='commit')
        pg.wait_for_function('["lista", "marcadores", "corpo", "completo"].every((n) => window.__tempos?.[n])', timeout=120000)
        dados = pg.evaluate(RECURSOS)
        contexto.close()

        tempos, recursos = dados['tempos'], dados['recursos']
        visivel = max(tempos['lista'], tempos['marcadores'])
        [listar] = [r for r in recursos if '/rpc/listar_achados' in r['url']][:1]
        atlas_baixado = [r for r in recursos if '/atlas/' in r['url']]
        glbs = [r for r in atlas_baixado if r['url'].endswith('.glb')]
        nomes = [r['url'].rsplit('/', 1)[1] for r in sorted(glbs, key=lambda r: r['de'])]
        assert nomes in (['tegumentar.glb'], ['tegumentar_leve.glb', 'tegumentar.glb']), f'só a pele deveria ser baixada: {nomes}'
        if n == 1:
            print(f'GLBs baixados: {nomes}')
        # o que abre o corpo (o leve, se houver); o completo vem depois e é medido à parte
        glbs = [min(glbs, key=lambda r: r['de'])]
        medida = {
            'visivel': visivel, 'lista': tempos['lista'], 'marcadores': tempos['marcadores'], 'corpo': tempos['corpo'], 'completo': tempos['completo'],
            # banco: página (login + abrir_prontuario no servidor) e a lista (pedida pelo navegador)
            'banco_documento': dados['documento']['responseStart'],
            'banco_listar': listar['ate'] - listar['de'], 'listar_chegou': listar['ate'],
            'glb': max(r['ate'] for r in glbs) - min(r['de'] for r in glbs),
            'glb_bytes': sum(r['bytes'] for r in glbs),
            'glb_inicio': min(r['de'] for r in glbs),
            # render: dos dados em mãos até estar desenhado
            'render': visivel - listar['ate'],
        }
        medidas.append(medida)
        print(f'abertura {n}: ' + ', '.join(f'{k}={v:.0f}' for k, v in medida.items()))
    navegador.close()

resumo = {k: {'mediana': statistics.median(m[k] for m in medidas), 'p95': p95([m[k] for m in medidas])} for k in medidas[0]}
print('\n(ms; glb_bytes em bytes)           mediana        p95')
for chave, valor in resumo.items():
    print(f'{chave:<28}{valor["mediana"]:>14.0f}{valor["p95"]:>11.0f}')
print('as parcelas se sobrepõem no tempo (GLB e banco correm juntos): não somam o total')
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_text(json.dumps({'esperado': esperado, 'medidas': medidas, 'resumo': resumo}, indent=2), encoding='utf-8')
mediana = resumo['visivel']['mediana']
assert mediana <= META_MS, f'REPROVADO: mediana {mediana:.0f} ms > {META_MS} ms'
print(f'OK: mediana {mediana:.0f} ms <= {META_MS} ms (corpo/pele: {resumo["corpo"]["mediana"]:.0f} ms)')
