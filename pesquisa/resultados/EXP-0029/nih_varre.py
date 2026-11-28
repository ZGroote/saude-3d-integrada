"""Varre a busca pública do NIH 3D (navegador comum, sem login) e guarda ID, título, autor e termos que acharam."""
import sys, re, json, urllib.parse
from playwright.sync_api import sync_playwright

PADRAO = re.compile(r"([^\n]+)\n\n(3DPX-\d{6})\n\nby ([^\n]+)")
saida, termos = sys.argv[1], sys.argv[2:]
res = {}
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome"); pg = b.new_page()
    for q in termos:
        pg.goto("https://3d.nih.gov/discover?q=" + urllib.parse.quote(q), wait_until="networkidle", timeout=90000)
        pg.wait_for_selector("text=Displaying", timeout=60000); pg.wait_for_timeout(1500)
        lidos, pagina = 0, 1
        while True:
            t = pg.inner_text("main")
            m = re.search(r"Displaying (\d+) to (\d+) of (\d+)", t)
            for tit, i, aut in PADRAO.findall(t):
                res.setdefault(i, {"titulo": tit.strip(), "autor": aut.strip(), "termos": []})
                if q not in res[i]["termos"]: res[i]["termos"].append(q)
                lidos += 1
            if not m or int(m.group(2)) >= int(m.group(3)): break
            prox = pg.locator("button[aria-label='Go to next page']")
            if not prox.count() or prox.first.is_disabled(): break
            antes = m.group(0); prox.first.click()
            pg.wait_for_function("t => !document.querySelector('main').innerText.includes(t)", arg=antes, timeout=30000)
            pg.wait_for_timeout(1000); pagina += 1
        print(f"{q}: total {m.group(3) if m else '?'} | lidos {lidos} | páginas {pagina}")
    b.close()
json.dump(res, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("total distintos:", len(res))
