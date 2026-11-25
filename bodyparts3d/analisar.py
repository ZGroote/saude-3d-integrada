"""Inventário do BodyParts3D (is_a, OBJ 99%; 2234 malhas) + teste de encaixe com o caso s1371.

Uso:  python -I bodyparts3d/analisar.py
Lê:   bodyparts3d/bruto/  (OBJs + listas oficiais)   e   teste-anatomia/modelos/*.glb
Gera: bodyparts3d/catalogo_bp3d.csv  e  bodyparts3d/RELATORIO.md
"""
import csv, re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import trimesh

RAIZ = Path(__file__).resolve().parent
BRUTO = RAIZ / "bruto"
OBJS = BRUTO / "isa_BP3D_4.0_obj_99"  # superconjunto das malhas do part_of
GLBS = RAIZ.parent / "teste-anatomia" / "modelos"


def tsv(nome):
    with open(BRUTO / nome, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


# ---------- árvores part_of + is_a: ancestrais de cada conceito ----------
pais = defaultdict(set)
for arq in ("partof_inclusion_relation_list.txt", "isa_inclusion_relation_list.txt"):
    for r in tsv(arq):
        pais[r["child id"]].add(r["parent id"])


def ancestrais(c, vistos=None):
    vistos = set() if vistos is None else vistos
    for p in pais[c]:
        if p not in vistos:
            vistos.add(p)
            ancestrais(p, vistos)
    return vistos


# ordem importa: a primeira regra que bate vence. (sistema, raízes FMA, regex no nome)
REGRAS = [
    ("muscular", {"FMA5022", "FMA9721"}, r"trapezius|muscle|tendon|aponeuro|sphincter|diaphragm|rectus|oblique|levator|pectoralis|serratus|rhomboid|piriformis|psoas|obturator internus|anconeus|brachialis|coracobrachialis|subclavius|transversus"),
    ("sensorial", set(), r"eyeball|cornea|sclera|choroid|iris|lens|vitreous|lacrimal|nasolacrimal|cochlea|ossicle|tympanic|auricle of|semicircular"),
    ("cardiaco", {"FMA7088"}, r"\bheart|atrium|atrial|ventricle of heart|(left|right) ventricle|valve|papillary|chorda|myocard"),
    ("venoso", {"FMA50723"}, r"\bvein|vena\b|\bvenous|sinus of dura|coronary sinus"),
    ("arterial", {"FMA50720", "FMA7161", "FMA228642", "FMA3710"}, r"arter|aorta|pulmonary trunk|arterial"),
    ("nervoso", {"FMA7157", "FMA65132", "FMA5865", "FMA61284", "FMA55676"}, r"nerve|brain|cerebr|gyrus|spinal cord|ganglion|plexus|medulla oblongata|pons|thalamus|hippocamp"),
    ("respiratorio", {"FMA7158"}, r"bronch|lung|trachea|larynx"),
    ("digestorio", {"FMA7152", "FMA12516"}, r"hepatovenous|tooth|stomach|colon|intestin|liver|pancrea|esophag|duoden|jejun|ileum|cecum|rectum|gallbladder|tongue"),
    ("urogenital", {"FMA7159", "FMA7160"}, r"kidney|ureter|bladder|urethra|prostate|testis|ovary|uterus|penis"),
    ("endocrino", {"FMA9668"}, r"thyroid|adrenal|pituitary|parathyroid|thymus"),
    ("tegumentar", {"FMA74657", "FMA72979", "FMA7163"}, r"\bskin|hair"),
    ("articular", {"FMA55107"}, r"ligament|cartilage|dis[ck]\b|menisc|capsule|labrum|symphysis|retinaculum"),
    ("esqueletico", {"FMA23881", "FMA5018", "FMA10483"}, r"bone|vertebra|\brib\b|skull|femur|\btibia|fibula|humerus|radius|ulna|phalan|metacarp|metatars|carpal|tarsal|patella|sternum|manubrium|xiphoid|sacrum|coccyx|clavicle|scapula|mandible|maxilla|hyoid|calcaneus|talus|atlas|axis|capitate|hamate|lunate|pisiform|scaphoid|trapezium|trapezoid|triquetral|cuboid|cuneiform|navicular"),
    ("fascia", set(), r"fascia|iliotibial tract"),
]
REGRAS = [(s, r, re.compile(x, re.I)) for s, r, x in REGRAS]


def sistema(conceito, nome):
    anc = ancestrais(conceito) | {conceito}
    for s, raizes, rx in REGRAS:  # nome primeiro: a árvore FMA tem vários pais e erra mais
        if rx.search(nome): return s
    for s, raizes, rx in REGRAS:
        if raizes & anc: return s
    return "outros"


# autoteste: casos que já classificamos errado uma vez (regex pega pedaço de palavra)
for _nome, _esperado in [("Descending part of left trapezius", "muscular"), ("Left trapezium", "esqueletico"),
                         ("Right iliotibial tract", "fascia"), ("Hepatovenous segment II", "digestorio"),
                         ("Dorsal venous network of left hand", "venoso"), ("Left tibia", "esqueletico"),
                         ("Right anterior tibial artery", "arterial"), ("Left femur", "esqueletico")]:
    assert sistema("", _nome) == _esperado, (_nome, sistema("", _nome), _esperado)


# ---------- inventário dos OBJ ----------
HDR = re.compile(r"# (Concept ID|English name|Bounds\(mm\))\s*:\s*(.*)")
linhas, bounds_el = [], {}
for p in sorted(OBJS.glob("*.obj")):
    meta, nv, nf = {}, 0, 0
    with open(p, encoding="utf-8", errors="replace") as f:
        for l in f:
            if l.startswith("v "): nv += 1
            elif l.startswith("f "): nf += 1
            elif l.startswith("#"):
                m = HDR.match(l.strip())
                if m: meta[m[1]] = m[2]
    b = [float(x) for x in re.findall(r"-?\d+\.\d+", meta.get("Bounds(mm)", ""))]
    nome = meta.get("English name", "")
    lado = "left" if re.search(r"\bleft\b", nome, re.I) else "right" if re.search(r"\bright\b", nome, re.I) else ""
    bounds_el[p.stem] = np.array(b).reshape(2, 3)
    linhas.append(dict(arquivo=p.stem, fma=meta.get("Concept ID", ""), nome_en=nome, sistema=sistema(meta.get("Concept ID", ""), nome),
                       lateralidade=lado, vertices=nv, triangulos=nf))

# revisão manual dos 'outros' (revisao_outros.csv) vence a regra automática; também preenche nomes vazios no OBJ
if (RAIZ / "revisao_outros.csv").exists():
    with open(RAIZ / "revisao_outros.csv", encoding="utf-8") as f:
        rev = {r["arquivo"]: r for r in csv.DictReader(f)}
    for l in linhas:
        if l["arquivo"] in rev:
            l["sistema"] = rev[l["arquivo"]]["sistema_sugerido"]
            l["nome_en"] = l["nome_en"] or rev[l["arquivo"]]["nome_en"]

with open(RAIZ / "catalogo_bp3d.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(linhas[0]))
    w.writeheader(); w.writerows(linhas)

# ---------- bounds de conceitos compostos (união dos elementos) ----------
elementos = defaultdict(list)
for r in tsv("partof_element_parts.txt") + tsv("isa_element_parts.txt"):
    elementos[r["name"].lower()].append(r["element file id"])


def caixa_bp3d(nome):
    els = [bounds_el[e] for e in elementos.get(nome, []) if e in bounds_el]
    if not els: return None
    a = np.array(els)
    return np.array([a[:, 0].min(0), a[:, 1].max(0)])


# ---------- caixas do s1371 (m -> mm; coordenadas RAS do CT, centralizadas) ----------
caixa_ts = {}
for g in GLBS.glob("*.glb"):
    cena = trimesh.load(g, force="scene")
    for nome, geo in cena.geometry.items():
        caixa_ts[nome] = geo.bounds * 1000.0

PARES = {  # s1371 -> BP3D (estruturas que cabem inteiras no CT)
    "liver": "liver", "kidney_left": "left kidney", "kidney_right": "right kidney", "stomach": "stomach",
    "pancreas": "pancreas", "gallbladder": "gallbladder", "urinary_bladder": "urinary bladder", "sacrum": "sacrum",
    "hip_left": "left hip bone", "hip_right": "right hip bone", "vertebrae_L1": "first lumbar vertebra",
    "vertebrae_L3": "third lumbar vertebra", "vertebrae_L5": "fifth lumbar vertebra", "vertebrae_T6": "sixth thoracic vertebra",
    "vertebrae_T12": "twelfth thoracic vertebra", "heart": "heart", "trachea": "trachea", "esophagus": "esophagus",
    "lung_upper_lobe_left": "upper lobe of left lung", "lung_upper_lobe_right": "upper lobe of right lung",
    "lung_lower_lobe_left": "lower lobe of left lung", "lung_lower_lobe_right": "lower lobe of right lung",
    "spleen": "spleen", "thyroid_gland": "thyroid gland", "sternum": "sternum",
    "scapula_left": "left scapula", "scapula_right": "right scapula",
    "clavicula_left": "left clavicle", "clavicula_right": "right clavicle",
}
pares = [(t, b, caixa_ts[t], caixa_bp3d(b)) for t, b in PARES.items() if t in caixa_ts and caixa_bp3d(b) is not None]
A = np.array([cb.mean(0) for *_, cb in pares])  # BP3D
B = np.array([ct.mean(0) for _, _, ct, _ in pares])  # s1371


def umeyama(X, Y):
    """Similaridade (escala s, rotação R, translação t) que leva X a Y por mínimos quadrados."""
    mx, my = X.mean(0), Y.mean(0)
    Xc, Yc = X - mx, Y - my
    U, S, Vt = np.linalg.svd(Yc.T @ Xc / len(X))
    D = np.eye(3); D[2, 2] = np.sign(np.linalg.det(U @ Vt))
    R = U @ D @ Vt
    s = np.trace(np.diag(S) @ D) / Xc.var(0).sum()
    return s, R, my - s * R @ mx


s, R, t = umeyama(A, B)
res = np.linalg.norm((s * (R @ A.T)).T + t - B, axis=1)

# checagem do próprio Umeyama: transformação conhecida tem que ser recuperada
_R = trimesh.transformations.rotation_matrix(0.7, [1, 2, 3])[:3, :3]
_s, _Rr, _t = umeyama(A, 1.3 * (_R @ A.T).T + 5)
assert abs(_s - 1.3) < 1e-9 and np.allclose(_Rr, _R), "umeyama quebrado"

# ---------- relatório ----------
cont = Counter(l["sistema"] for l in linhas)
tri = Counter(); [tri.update({l["sistema"]: l["triangulos"]}) for l in linhas]
corpo = np.array([bounds_el[e] for e in bounds_el])
alt = corpo[:, 1, 2].max() - corpo[:, 0, 2].min()
total_tri = sum(l["triangulos"] for l in linhas)

r = ["# BodyParts3D — inventário e teste de encaixe", "",
     "Fonte: BodyParts3D release 4.0 (2013), árvore is_a (contém todas as do part_of), malhas com 99% de redução. ",
     "Licença atual no site: CC BY 4.0 (página atualizada em 27/02/2025). O cabeçalho dos OBJ ainda diz CC BY-SA 2.1 JP (texto antigo).",
     "Atribuição exigida: \"BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International\".", "",
     f"- **{len(linhas)} malhas** (cada uma é uma estrutura folha com ID FMA)",
     f"- **{len(set(l['fma'] for l in linhas))} conceitos FMA distintos**, {len(elementos)} conceitos nomeados contando agrupamentos",
     f"- **{total_tri:,} triângulos** no total (média {total_tri // len(linhas):,} por estrutura)",
     f"- Altura do corpo: {alt:.0f} mm · unidades em mm · Z para cima", "",
     "## Por sistema", "", "| Sistema | Estruturas | Triângulos |", "|---|---:|---:|"]
r += [f"| {k} | {v} | {tri[k]:,} |" for k, v in cont.most_common()]
r += ["", "Classificação automática (árvore FMA + palavras-chave). Ver `catalogo_bp3d.csv`; os casos ambíguos foram revisados em `revisao_outros.csv`.", "",
      "## Lacunas conhecidas do BodyParts3D", "",
      "- Carótida: falta o trecho entre a carótida comum (termina a ~1373 mm) e a interna (começa a ~1434 mm), incluindo a bifurcação; não há carótida externa.",
      "- Um único corpo masculino adulto (2013). Sem anatomia feminina. Nomes em português (`nomes_pt.csv`) ainda sem revisão médica.", "",
      "## Encaixe com o caso s1371 (TotalSegmentator)", "",
      f"Ajuste de similaridade (escala + rotação + translação) sobre os centros de {len(pares)} estruturas comuns.", "",
      f"- Escala BP3D→s1371: **{s:.3f}**",
      f"- Erro médio após o ajuste: **{res.mean():.1f} mm** (máximo {res.max():.1f} mm)",
      "- Rotação encontrada (deveria ser quase identidade ou só troca de eixos):", "```", np.array2string(R, precision=2, suppress_small=True), "```", "",
      "| s1371 | BP3D | erro (mm) | tamanho s1371 (mm) | tamanho BP3D×escala (mm) |", "|---|---|---:|---|---|"]
for (tn, bn, ct, cb), e in sorted(zip(pares, res), key=lambda x: -x[1]):
    r.append(f"| {tn} | {bn} | {e:.0f} | {np.round(np.sort(ct[1]-ct[0])).astype(int).tolist()} | {np.round(np.sort((cb[1]-cb[0])*s)).astype(int).tolist()} |")
(RAIZ / "RELATORIO.md").write_text("\n".join(r) + "\n", encoding="utf-8")
print("ok:", RAIZ / "RELATORIO.md")
