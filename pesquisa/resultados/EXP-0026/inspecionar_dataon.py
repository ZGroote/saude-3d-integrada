#!/usr/bin/env python3
"""Inspeciona metadados públicos das páginas DataON 1472 e 1473 (sem login) e verifica bloqueio de download."""

import json
import re
import subprocess
import sys
from pathlib import Path

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
OUT_EXT = Path(__file__).resolve().parents[3] / "hra" / "externo" / "kisti"
OUT_EXT.mkdir(parents=True, exist_ok=True)


def fetch_html(key: str) -> str:
    url = f"https://dataon.kisti.re.kr/dr/doi/?key=10.22711/idr/{key}"
    p = subprocess.run(["curl.exe", "-sL", "-A", UA, url], capture_output=True, text=True, timeout=30)
    return p.stdout


def parse_record(key: str, html: str) -> dict:
    files = []
    m = re.search(r"source:\s*\$\.parseJSON\('(\[.*?\])'\)", html)
    if m:
        files = json.loads(m.group(1))
    svc_m = re.search(r'"svc_id"\s*:\s*"([^"]+)"', html)
    svc_id = svc_m.group(1) if svc_m else None

    txt = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", html, flags=re.S)
    txt = re.sub(r"\s+", " ", txt).strip()
    lic_matches = re.findall(r"(?:CC\s*BY[^\s,;]*|Creative Commons[^.]{0,80}|저작권[^.]{0,80}|라이선스[^.]{0,80})", txt, re.I)

    return {
        "key": key,
        "svc_id": svc_id,
        "requires_login_js": 'location.href="/user/userLogin.do"' in html,
        "license_snippets": lic_matches[:10],
        "files": [
            {
                "title": f.get("title"),
                "file_name": f.get("file_name"),
                "file_sz": f.get("file_sz"),
                "file_sz_ori": f.get("file_sz_ori"),
                "sha256": f.get("hashCode"),
                "file_id": f.get("file_id"),
            }
            for f in files
        ],
    }


def main() -> None:
    print(f"Python: {sys.version.split()[0]}")
    records = {}
    for key in ["1472", "1473"]:
        html = fetch_html(key)
        records[key] = parse_record(key, html)
        print(f"=== DataON 10.22711/idr/{key} ===")
        print("  svc_id:", records[key]["svc_id"])
        print("  requires_login_js:", records[key]["requires_login_js"])
        print("  license_snippets:", records[key]["license_snippets"])
        for f in records[key]["files"]:
            print(f"  - {f['title']} ({f['file_sz']}, {f['file_sz_ori']} B, sha256={f['sha256']})")

    out_json = OUT_EXT / "metadados_dataon_1472_1473.json"
    out_json.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Salvo em: {out_json}")


if __name__ == "__main__":
    main()
