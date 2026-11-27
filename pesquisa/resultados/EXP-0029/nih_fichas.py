"""Abre a página pública de cada entrada do NIH 3D e guarda o texto (descrição, licença, arquivos)."""
import sys, json
from playwright.sync_api import sync_playwright

saida, ids = sys.argv[1], sys.argv[2:]
fichas = {}
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome"); pg = b.new_page()
    for i in ids:
        pg.goto(f"https://3d.nih.gov/entries/{i}", wait_until="networkidle", timeout=90000)
        pg.wait_for_timeout(2500)
        t = pg.inner_text("main") if pg.query_selector("main") else pg.inner_text("body")
        lic = pg.eval_on_selector_all("a", "els => els.map(e => e.href).filter(h => /creativecommons|gnu.org|opensource.org|license/i.test(h))")
        fichas[i] = {"texto": t, "licencas": sorted(set(lic))}
        print(f"===== {i} ({len(t)} chars)")
    b.close()
json.dump(fichas, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
