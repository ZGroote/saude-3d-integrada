"""Revisao humana F5 (EXP-0016): hra-f 1.10-1 x hib-f 0.1-0 lado a lado.
Uso, em web/, com um `next dev` rodando e os dois pacotes em public/ (`npm run atlas -- --rascunho`):

    python testes/f5_comparacao.py            # grava em testes/capturas/f5/ ; APP_URL padrão: http://127.0.0.1:3010

Câmera: mesma direção, mesma distância e mesmo tamanho de tela nos dois; cada corpo é centrado na caixa da
própria pele (as origens dos dois pacotes não precisam coincidir). A escala em pixels é igual.
"""
import html
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
WEB = Path(__file__).resolve().parents[2] / 'web'
APP = os.environ.get('APP_URL', 'http://127.0.0.1:3010').rstrip('/')
SAIDA = WEB / 'testes/capturas/f5-hibrido'
PACOTES = (('hra-f', '1.10-1'), ('hib-f', '0.1-0'))
VISTAS = {'frente': (0, 0, 1), 'costas': (0, 0, -1), 'lado-esquerdo': (1, 0, 0), 'lado-direito': (-1, 0, 0)}  # +x = esquerda da paciente
MODOS = {
    'a-pele': ('(a) Só pele', ['tegumentar']),
    'b-pele-esqueleto': ('(b) Pele translúcida + esqueleto', ['tegumentar', 'esqueletico']),
    'c-interno': ('(c) Esqueleto + muscular + arterial + venoso', ['esqueletico', 'muscular', 'arterial', 'venoso']),
}
FOV = 35

# a câmera do motor é trocada imediatamente antes de cada desenho (a luz presa a ela vem junto)
GANCHO = """
window.__cenas = []; window.__vista = null;
window.__THREE_DEVTOOLS__ = new EventTarget();
window.__THREE_DEVTOOLS__.addEventListener('observe', (e) => {
  const alvo = e.detail;
  if (alvo.isScene) return window.__cenas.push(alvo);
  const desenhar = alvo.render;
  alvo.render = function (cena, camera) {
    const v = window.__vista;
    if (v) { camera.position.set(...v.posicao); camera.lookAt(...v.alvo); camera.updateMatrixWorld(true); }
    return desenhar.call(this, cena, camera);
  };
});
"""
CAIXA_DA_PELE = """() => {
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (const cena of window.__cenas) cena.traverse((o) => {
    if (o.userData.sistema !== 'tegumentar') return;
    o.geometry.computeBoundingBox();
    const b = o.geometry.boundingBox;
    ['x', 'y', 'z'].forEach((e, i) => { min[i] = Math.min(min[i], b.min[e]); max[i] = Math.max(max[i], b.max[e]); });
  });
  return { min, max };
}"""


def abrir(navegador, atlas, versao, console):
    pg = navegador.new_page(viewport={'width': 1180, 'height': 1200})
    pg.set_default_timeout(240000)
    pg.add_init_script(GANCHO)
    pg.on('console', lambda m: m.type == 'error' and console.append(f'{atlas}: {m.text}'))
    pg.on('pageerror', lambda e: console.append(f'{atlas}: {e}'))
    pg.goto(f'{APP}/dev/motor?atlas={atlas}&versao={versao}')
    pg.wait_for_selector(f'[data-atlas="{atlas}"] [data-motor][data-completos="tegumentar"]')
    return pg


def mostrar(pg, sistemas):
    presentes = pg.locator('fieldset input').evaluate_all('(caixas) => caixas.map((c) => c.value)')
    ligar = [s for s in sistemas if s in presentes]
    for s in presentes:
        pg.locator(f'input[value="{s}"]').set_checked(s in ligar)
    pg.wait_for_function(
        """(esperado) => { const m = document.querySelector('[data-motor]');
             const tem = (a) => (m.dataset[a] || '').split(' ').filter(Boolean).sort().join(' ');
             return tem('carregados') === esperado && tem('completos') === esperado; }""",
        arg=' '.join(sorted(ligar)))
    pg.wait_for_timeout(1500)
    return [s for s in sistemas if s not in presentes]


def capturar():
    faltas, console, caixas = [], [], {}
    with sync_playwright() as p:
        navegador = p.chromium.launch(channel='chrome', args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'])
        paginas = {atlas: abrir(navegador, atlas, versao, console) for atlas, versao in PACOTES}
        for atlas, pg in paginas.items():
            pg.bring_to_front()
            pg.wait_for_timeout(1000)
            caixas[atlas] = pg.evaluate(CAIXA_DA_PELE)
        # uma distância só, para o corpo maior caber: os dois saem na mesma escala
        maior = max(max(c['max'][i] - c['min'][i] for c in caixas.values()) for i in range(3))
        distancia = maior * 0.56 / __import__('math').tan(__import__('math').radians(FOV / 2)) + maior * 0.1
        for modo, (titulo, sistemas) in MODOS.items():
            for atlas, pg in paginas.items():
                pg.bring_to_front()
                ausentes = mostrar(pg, sistemas)
                faltas += [f'{atlas} não tem o sistema {s} (modo {titulo})' for s in ausentes]
                centro = [(a + b) / 2 for a, b in zip(caixas[atlas]['min'], caixas[atlas]['max'])]
                for vista, direcao in VISTAS.items():
                    posicao = [c + d * distancia for c, d in zip(centro, direcao)]
                    pg.evaluate('(v) => { window.__vista = v; }', {'posicao': posicao, 'alvo': centro})
                    pg.wait_for_timeout(500)
                    pg.locator('canvas').screenshot(path=str(SAIDA / f'{modo}-{vista}-{atlas}.png'))
                print(f'{atlas} {modo}: 4 vistas')
        navegador.close()
    return caixas, faltas, console


ORDINAIS = {n: str(i) for i, n in enumerate(('first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth').split(), 1)}


def chave(entrada):
    """Compara os indices hibrido e HRA por nome em ingles e lateralidade."""
    texto = unicodedata.normalize('NFKD', entrada['nome_en']).encode('ascii', 'ignore').decode()
    texto = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', texto).lower()
    palavras = [ORDINAIS.get(w, w) for w in re.findall(r'[a-z]+|\d+', texto)]
    for regiao, letra in (('cervical', 'c'), ('thoracic', 't'), ('lumbar', 'l')):
        if regiao in palavras and any(w.startswith('vertebra') for w in palavras):
            numero = next((w for w in palavras if w.isdigit()), None)
            if numero:
                palavras = ['vertebrae', letra + numero]
    juntas = ' '.join(palavras)
    juntas = re.sub(r'\bvertebrae ([ctls]) (\d+)\b', r'vertebrae \1\2', juntas)
    ruido = {'left', 'right', 'bone', 'muscle', 'ligament', 'cartilage', 'of', 'the', 'l', 'r', 'vh', 'f'}
    nucleo = frozenset(w.rstrip('s') if len(w) > 3 else w for w in juntas.split() if w not in ruido)
    return nucleo, entrada.get('lateralidade')


def comparar():
    indices = {a: json.loads((WEB.parent / f'atlas/{a}/{v}/indice.json').read_text(encoding='utf-8')) for a, v in PACOTES}
    chaves = {a: {chave(e) for e in i} for a, i in indices.items()}
    sistemas = sorted({e['sistema'] for i in indices.values() for e in i})
    resumo = []
    for s in sistemas:
        linha = {'sistema': s}
        for atlas, outro in (('hra-f', 'hib-f'), ('hib-f', 'hra-f')):
            entradas = [e for e in indices[atlas] if e['sistema'] == s]
            # a estrutura pode estar noutro sistema no outro pacote: só falta se não estiver em nenhum
            so = defaultdict(int)
            for e in entradas:
                if chave(e) not in chaves[outro]:
                    so[e['nome_en'] + {'left': ' (E)', 'right': ' (D)'}.get(e.get('lateralidade'), '')] += 1
            linha[atlas] = {'malhas': len(entradas), 'so_aqui': sorted(so)}
        resumo.append(linha)
    return indices, resumo


def montar_html(resumo, faltas, indices):
    e = html.escape
    partes = ['''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>F5: hra-f × hib-f</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><style>
body{font:15px/1.4 system-ui,sans-serif;margin:24px;color:#14201e;background:#f6f8f7}
.par{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:0 0 18px;max-width:1500px}
figure{margin:0;background:#fff;border:1px solid #d7dedc;border-radius:8px;padding:8px}img{width:100%;display:block}
figcaption{font-weight:600;padding:2px 0 6px}table{border-collapse:collapse;background:#fff}td,th{border:1px solid #d7dedc;padding:5px 10px;text-align:left;vertical-align:top}
.aviso{background:#fff3d6;border:1px solid #e0b24a;border-radius:8px;padding:10px 14px;max-width:900px}details ul{columns:2;margin:6px 0}
</style>''',
              '<h1>Revisão humana F5 — corpo feminino</h1>',
              '<p class="aviso"><strong>hib-f 0.1-0 é rascunho, não publicado e não aceito</strong> (TC da NLM + pernas da Denver). '
              'Mesma direção de câmera, distância e escala; cada corpo é centrado na caixa da própria pele. '
              '“Lado esquerdo” é o lado esquerdo da paciente.</p>',
              '<p><a href="#indice">Ir para a diferença entre os índices</a></p>']
    if faltas:
        partes.append('<ul>' + ''.join(f'<li>{e(f)}</li>' for f in sorted(set(faltas))) + '</ul>')
    for modo, (titulo, _) in MODOS.items():
        partes.append(f'<h2>{e(titulo)}</h2>')
        for vista in VISTAS:
            nome = vista.replace('-', ' ')
            partes.append(f'<h3>{e(nome.capitalize())}</h3><div class="par">' + ''.join(
                f'<figure><figcaption>{e(a)} {e(v)}{" (rascunho)" if a == "hib-f" else ""}</figcaption>'
                f'<img loading="lazy" src="{modo}-{vista}-{a}.png" alt="{e(a)}, {e(titulo)}, {e(nome)}"></figure>' for a, v in PACOTES) + '</div>')
    partes.append('<h2 id="indice">O que existe em um e nao no outro</h2><p class="aviso">O pacote hibrido combina estruturas HRA e VHF; alguns itens nao tem ID de ontologia. A comparacao e aproximada, por nome em ingles e lado: nomes '
                  'diferentes para a mesma coisa aparecem como ausentes nos dois lados, e uma estrutura dividida em partes num pacote '
                  'nao casa com a inteira no outro.</p><table><tr><th>Sistema</th><th>hra-f: malhas</th><th>So no hra-f</th>'
                  '<th>hib-f: malhas</th><th>So no hib-f</th></tr>')
    for linha in resumo:
        celulas = ''
        for a, _ in PACOTES:
            so = linha[a]['so_aqui']
            lista = f'<details><summary>{len(so)}</summary><ul>' + ''.join(f'<li>{e(n)}</li>' for n in so) + '</ul></details>' if so else '0'
            celulas += f'<td>{linha[a]["malhas"]}</td><td>{lista}</td>'
        partes.append(f'<tr><th>{e(linha["sistema"])}</th>{celulas}</tr>')
    partes.append('</table></html>')
    (SAIDA / 'comparacao.html').write_text('\n'.join(partes), encoding='utf-8')


SAIDA.mkdir(parents=True, exist_ok=True)
indices, resumo = comparar()
if '--so-html' in sys.argv:
    caixas, faltas, console = {}, [], []
else:
    caixas, faltas, console = capturar()
montar_html(resumo, faltas, indices)
(SAIDA / 'diferencas.json').write_text(json.dumps(resumo, ensure_ascii=False, indent=1), encoding='utf-8')
print('\nsistema: malhas hra-f (só nele) | malhas hib-f (só nele)')
for linha in resumo:
    print(f'{linha["sistema"]:13} {linha["hra-f"]["malhas"]:4} ({len(linha["hra-f"]["so_aqui"])}) | {linha["hib-f"]["malhas"]:4} ({len(linha["hib-f"]["so_aqui"])})')
for atlas, c in caixas.items():
    print(atlas, 'pele (m): largura/altura/profundidade', [round(b - a, 3) for a, b in zip(c['min'], c['max'])], 'centro', [round((a + b) / 2, 3) for a, b in zip(c['min'], c['max'])])
print(*sorted(set(faltas)), sep='\n')
print('console:', *console[:10], sep='\n') if console else print('console limpo')
print(SAIDA / 'comparacao.html')
