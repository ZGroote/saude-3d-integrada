"""Lê a janela "Source Data Details" de entradas do NIH 3D (modalidade, sexo/idade quando informados, instituição)."""
import sys, re
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome"); pg = b.new_page()
    for i in sys.argv[1:]:
        pg.goto(f"https://3d.nih.gov/entries/{i}", wait_until="networkidle", timeout=90000); pg.wait_for_timeout(2000)
        el = pg.get_by_text("Source Data Details", exact=True)
        txt = "(sem botão)"
        if el.count():
            el.first.click(); pg.wait_for_timeout(1200)
            d = pg.query_selector("[role=dialog]")
            txt = d.inner_text() if d else "(sem janela)"
        print("=====", i, "|", re.sub(r"\s*\n\s*", " / ", txt)[:700])
    b.close()
