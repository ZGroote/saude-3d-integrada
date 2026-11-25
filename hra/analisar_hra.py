"""Inventário do HRA female (united, CDN latest) + comparação com o BodyParts3D.

Uso:  python hra/analisar_hra.py
Lê:   hra/bruto/united_f_cdn_latest.glb, hra/bruto/crosswalk.csv, bodyparts3d/catalogo_bp3d.csv
Gera: hra/catalogo_hra.csv e hra/RELATORIO.md
"""
import csv, json, struct
from collections import Counter
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent
GLB = RAIZ / "bruto" / "united_f_cdn_latest.glb"


def ler_glb(p):
    with open(p, "rb") as f:
        f.read(12)
        n, _ = struct.unpack("<II", f.read(8))
        j = json.loads(f.read(n))
        f.read(4); f.read(4)  # cabeçalho do chunk BIN
        return j, f.read()


j, binario = ler_glb(GLB)
nodes = j["nodes"]
pai = {c: i for i, n in enumerate(nodes) for c in n.get("children", [])}


def matriz(n):
    if "matrix" in n: return np.array(n["matrix"]).reshape(4, 4).T
    T, R, S = np.eye(4), np.eye(4), np.eye(4)
    T[:3, 3] = n.get("translation", [0, 0, 0])
    x, y, z, w = n.get("rotation", [0, 0, 0, 1])
    R[:3, :3] = [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
    S[:3, :3] = np.diag(n.get("scale", [1, 1, 1]))
    return T @ R @ S


def mundo(i):
    M = matriz(nodes[i])
    while i in pai:
        i = pai[i]; M = matriz(nodes[i]) @ M
    return M


def caminho(i):
    c = [nodes[i].get("name", "")]
    while i in pai:
        i = pai[i]; c.append(nodes[i].get("name", ""))
    return c[::-1]


def triangulos(mesh):
    t = 0
    for p in mesh["primitives"]:
        if "indices" in p: t += j["accessors"][p["indices"]]["count"] // 3
        else: t += j["accessors"][p["attributes"]["POSITION"]]["count"] // 3
    return t


def caixa(mesh, M):
    pts = []
    for p in mesh["primitives"]:
        a = j["accessors"][p["attributes"]["POSITION"]]
        lo, hi = np.array(a["min"]), np.array(a["max"])
        cantos = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        pts.append((M @ cantos.T).T[:, :3])
    pts = np.vstack(pts)
    return pts.min(0), pts.max(0)


xw = {}
with open(RAIZ / "bruto" / "crosswalk.csv", encoding="utf-8-sig") as f:
    linhas = list(csv.reader(f))
cab = next(i for i, l in enumerate(linhas) if l and l[0] == "anatomical_structure_of")
for l in linhas[cab + 1:]:
    if len(l) >= 5: xw[l[2]] = dict(label=l[3], ontologia=l[4], orgao=l[0])

linhas_out, caixas = [], []
for i, n in enumerate(nodes):
    if "mesh" not in n: continue
    M = mundo(i)
    lo, hi = caixa(j["meshes"][n["mesh"]], M)
    caixas.append((lo, hi))
    cam = caminho(i)
    nome = n.get("name", "")
    x = xw.get(nome) or next((xw[c] for c in reversed(cam) if c in xw), {})
    linhas_out.append(dict(no=nome, sistema_hra=cam[1] if len(cam) > 1 else "", orgao=cam[2] if len(cam) > 2 else "",
                           label=x.get("label", ""), ontologia=x.get("ontologia", ""), no_no_crosswalk=nome in xw,
                           triangulos=triangulos(j["meshes"][n["mesh"]])))

with open(RAIZ / "catalogo_hra.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(linhas_out[0])); w.writeheader(); w.writerows(linhas_out)

lo = np.min([c[0] for c in caixas], 0); hi = np.max([c[1] for c in caixas], 0)
ext = hi - lo
eixo_alto = int(np.argmax(ext))
por_sis = Counter(l["sistema_hra"] for l in linhas_out)
tri_sis = Counter(); [tri_sis.update({l["sistema_hra"]: l["triangulos"]}) for l in linhas_out]
ont = Counter(l["ontologia"].split(":")[0] for l in linhas_out if l["ontologia"])
total = sum(l["triangulos"] for l in linhas_out)
com_ont = sum(1 for l in linhas_out if l["ontologia"])
ont_dist = len({l["ontologia"] for l in linhas_out if l["ontologia"]})

with open(RAIZ.parent / "bodyparts3d" / "catalogo_bp3d.csv", encoding="utf-8") as f:
    bp = list(csv.DictReader(f))
fma_bp = {r["fma"] for r in bp if r["fma"]}
fma_hra = {l["ontologia"].replace("FMA:", "FMA") for l in linhas_out if l["ontologia"].startswith("FMA:")}

r = ["# HRA female (Visible Human Female) — inventário", "",
     f"Arquivo: `united_f_cdn_latest.glb` ({GLB.stat().st_size/1e6:.0f} MB), gerador: {j['asset'].get('generator','')}", "",
     f"- **{len(linhas_out)} malhas** ({len(nodes)} nós no total)",
     f"- **{total:,} triângulos**",
     f"- {com_ont} malhas com ID de ontologia ({ont_dist} IDs distintos): " + ", ".join(f"{k} {v}" for k, v in ont.most_common()),
     f"- Caixa do corpo: {np.round(ext, 3).tolist()} (eixo mais longo = {'XYZ'[eixo_alto]}, {ext[eixo_alto]:.3f} unidades → "
     + ("metros" if 1.2 < ext[eixo_alto] < 2.2 else "mm" if 1200 < ext[eixo_alto] < 2200 else "unidade a confirmar") + ")",
     f"- FMA em comum com o BodyParts3D: {len(fma_hra & fma_bp)} de {len(fma_hra)} IDs FMA do HRA (o resto do HRA usa UBERON; precisa de tabela UBERON↔FMA para comparar)", "",
     "## Por grupo (filho direto de VH_F)", "", "| Grupo | Malhas | Triângulos |", "|---|---:|---:|"]
r += [f"| {k} | {v} | {tri_sis[k]:,} |" for k, v in por_sis.most_common()]
(RAIZ / "RELATORIO.md").write_text("\n".join(r) + "\n", encoding="utf-8")
print("ok:", RAIZ / "RELATORIO.md")
