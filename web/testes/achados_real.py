"""Achados de ponta a ponta, SEM simulação, no app já rodando e ligado à homologação (dados fictícios).
Uso, em web/:

    python testes/achados_real.py [pasta-capturas]          # padrão: testes/capturas
    APP_URL=http://127.0.0.1:3010 python testes/achados_real.py

Não sobe nem derruba servidor. As senhas são lidas de supabase/.env.demo e nunca impressas.
Cada execução grava DOIS achados na paciente fictícia (um I10 e um F32.9 restrito) e eventos na auditoria;
achados não são apagados. Precisa de Playwright para Python, do Chrome e do atlas servido pelo app.
"""
import json
import os
import random
import sys
import urllib.request
from pathlib import Path

# o banco (0008) grava a lateralidade do catálogo; o cliente a omite quando é nula
def catalogada(ancora):
    return {**ancora, 'lateralidade': ancora.get('lateralidade')}

from playwright.sync_api import TimeoutError as TempoEsgotado, sync_playwright
from sessao_atividade import registrar_atividade

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
    if (!o.isInstancedMesh || o.geometry.type !== 'SphereGeometry') return;
    for (let i = 0; i < o.count; i++) {
      const m = o.instanceMatrix.array.subarray(i * 16, i * 16 + 16);
      posicoes.push([m[12], m[13], m[14]]);
    }
  });
  return posicoes;
}"""


def desenhado_em(pg, posicao):
    # as matrizes das instâncias são float32: tolerância de 1 micrômetro
    return any(all(abs(a - b) < 1e-6 for a, b in zip(d, posicao)) for d in pg.evaluate(DESENHADOS))


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
        return json.load(resposta)


def listar(email):
    """listar_achados direto no banco, como o profissional: a referência contra a qual a tela é conferida."""
    sessao = chamar('/auth/v1/token?grant_type=password', {'email': email, 'password': senha_de(email)})
    registrar_atividade(sessao['access_token'])
    return chamar('/rest/v1/rpc/listar_achados', {'p_paciente': MARIA}, sessao['access_token'])


def carregar(pg, acao, email):
    """Executa a navegação e espera o corpo com todos os marcadores; a tela tem de bater com o banco."""
    acao()
    pg.wait_for_url(f'{APP}/pacientes/{MARIA}')
    linhas = listar(email)
    no_corpo = [a for a in linhas if a['ancora'] and a['ancora']['atlas'] == 'hra-f']
    # com a pele completa na tela, o clique no corpo responde na hora
    pg.wait_for_selector('[data-atlas="hra-f"] [data-motor][data-completos="tegumentar"]')
    pg.wait_for_selector(f'[data-motor][data-marcadores="{len(no_corpo)}"]')
    pg.wait_for_selector(f'text=Achados ({len(linhas)})')
    # com mais de 30 linhas, a lista termina de ser montada depois dos marcadores
    pg.wait_for_function(f"document.querySelectorAll('button[data-achado]').length === {len(linhas)}")
    pg.wait_for_timeout(1500)
    ids = pg.locator('button[data-achado]').evaluate_all('(b) => b.map((e) => e.dataset.achado)')
    assert sorted(ids) == sorted(a['id'] for a in linhas), 'lista da tela diferente do banco'
    assert len(pg.evaluate(DESENHADOS)) == len(no_corpo), 'marcadores desenhados diferentes da lista'
    return linhas


def abrir_maria(pg, email):
    return carregar(pg, lambda: pg.locator(f'a[href="/pacientes/{MARIA}"]').click(), email)


def registrar(pg, cid):
    """Clica no corpo, preenche o formulário e salva. Devolve (id, âncora do clique)."""
    canvas = pg.locator('canvas')
    formulario = pg.locator('form[aria-labelledby="titulo-novo-achado"]')
    cartao = pg.locator('[data-cartao]')
    # os achados de execuções anteriores continuam no corpo, e um clique num marcador abre o cartão dele:
    # pontos sorteados pelo corpo inteiro (cabeça, tronco, coxas, pernas) até cair em pele livre
    pontos = [(dx, fy) for fy in (0.12, 0.28, 0.33, 0.38, 0.43, 0.48, 0.58, 0.63, 0.68, 0.74, 0.80)
              for dx in range(-45, 46, 3)]
    random.shuffle(pontos)
    marcadores = fora = 0
    for dx, fy in pontos[:120]:
        if cartao.count():
            cartao.get_by_role('button', name='Fechar').click()
        canvas.scroll_into_view_if_needed()
        caixa = canvas.bounding_box()
        canvas.click(position={'x': caixa['width'] / 2 + dx, 'y': caixa['height'] * fy})
        try:
            pg.wait_for_selector('form[aria-labelledby="titulo-novo-achado"], [data-cartao]', timeout=1500)
        except TempoEsgotado:
            fora += 1  # fora do corpo
            continue
        if formulario.count():
            break
        marcadores += 1
    assert formulario.count() and formulario.locator('[data-ancora]').count(), (
        f'clique no corpo não abriu o formulário ({marcadores} cliques caíram em marcadores, {fora} fora do corpo)')
    formulario.get_by_role('searchbox').press_sequentially(cid, delay=40)
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
    texto = pg.locator(f'button[data-achado="{achado["id"]}"]').text_content()
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
    abrir_maria(pg, CARDIO)
    normal, clique = registrar(pg, 'I10')
    linhas = carregar(pg, pg.reload, CARDIO)
    [i10] = [a for a in linhas if a['id'] == normal]
    assert i10['cid10'] == 'I10' and i10['nivel_sigilo'] == 'normal', i10
    assert i10['ancora'] == catalogada(clique), (i10['ancora'], clique)
    assert desenhado_em(pg, clique['posicao_local']), pg.evaluate(DESENHADOS)
    conferir_linha(pg, i10, problemas)
    print(f'1) I10: clique {clique["posicao_local"]} == listar_achados {i10["ancora"]["posicao_local"]} == marcador desenhado')

    # 2) restrito, também com âncora
    restrito, ancora_restrita = registrar(pg, 'F32.9')
    linhas_cardio = carregar(pg, pg.reload, CARDIO)
    [f32] = [a for a in linhas_cardio if a['id'] == restrito]
    assert f32['nivel_sigilo'] == 'restrito' and f32['ancora'] == catalogada(ancora_restrita), f32
    assert ancora_restrita['posicao_local'] != clique['posicao_local']
    fotos(pg, '1-cardiologia-registrou', normal)
    print('2) F32.9 gravado como restrito e visível para a cardiologia')
    sair(pg)

    # 3) obstetrícia: vê o I10, e nada do restrito (resposta, linha, contagem, marcador, HTML)
    recebido = []
    # tudo o que leva dado do prontuário: a página (HTML e dados do React) e as chamadas ao banco
    def anotar(r):
        if ('/rest/v1/' in r.url or r.url.startswith(f'{APP}/pacientes')) and r.ok and r.request.method != 'OPTIONS':
            try:
                recebido.append((r.url, r.text()))
            except Exception:  # resposta de pré-carga descartada pelo navegador
                pass

    entrar(pg, OBSTETRICIA)
    pg.on('response', anotar)
    linhas_obst = abrir_maria(pg, OBSTETRICIA)
    carregar(pg, pg.reload, OBSTETRICIA)  # a página inteira, com os achados no HTML
    ocultos = {a['id'] for a in linhas_cardio
               if a['nivel_sigilo'] == 'restrito' and a['unidade_nome'] == i10['unidade_nome']}
    visiveis = {a['id'] for a in linhas_obst}
    assert restrito in ocultos and not ocultos & visiveis, ocultos & visiveis
    assert visiveis == {a['id'] for a in linhas_cardio} - ocultos, 'contagem não bate com a lista sem os restritos'
    [visto] = [a for a in linhas_obst if a['id'] == normal]
    assert visto['ancora'] == catalogada(clique) and 'Cardiologia' in visto['autor_nome'] and 'Cardiologia' in visto['unidade_nome'], visto
    conferir_linha(pg, visto, problemas)
    assert not desenhado_em(pg, ancora_restrita['posicao_local']), 'marcador do restrito desenhado'
    assert any(normal in texto for _, texto in recebido), 'nenhuma resposta capturada trouxe o I10'
    for endereco, texto in recebido:
        assert restrito not in texto and 'F32' not in texto, endereco
    html = pg.content()
    assert restrito not in html and 'F32' not in html, 'rastro do restrito na página'
    fotos(pg, '2-obstetricia', normal)
    pg.remove_listener('response', anotar)
    print(f'3) obstetrícia: {len(linhas_obst)} achados (cardiologia: {len(linhas_cardio)}); I10 com autor '
          f'"{visto["autor_nome"]}" / "{visto["unidade_nome"]}"; sem rastro do F32.9')
    sair(pg)

    # 4) cardiologia de novo vê os dois
    entrar(pg, CARDIO)
    linhas = abrir_maria(pg, CARDIO)
    assert {normal, restrito} <= {a['id'] for a in linhas}
    for achado in (i10, f32):
        conferir_linha(pg, achado, problemas)
    assert desenhado_em(pg, ancora_restrita['posicao_local'])
    fotos(pg, '3-cardiologia-de-novo', restrito)
    print(f'4) cardiologia: {len(linhas)} achados, I10 e F32.9 presentes')
    sair(pg)
    navegador.close()

assert not console, 'console:\n' + '\n'.join(console)
assert not problemas, 'FALHOU:\n' + '\n'.join(dict.fromkeys(problemas))
print(f'console limpo; capturas em {CAPTURAS}\nOK')
