#!/usr/bin/env python3
"""Reproduces Frente A of EXP-0021 offline using only Python's standard library.

Run from any directory: python pesquisa/resultados/EXP-0021/inventario.py
The ontology file is downloaded separately from the official PURL; this script
does not access the network. Manual decisions must include a justification.
"""
from __future__ import annotations

import csv
import hashlib
import random
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BP3D_CSV = ROOT / "bodyparts3d" / "catalogo_bp3d.csv"
HRA_CSV = ROOT / "hra" / "catalogo_hra.csv"
BODYSITE_CSV = ROOT / "supabase" / "dados" / "bodysite_snomed.csv"
UBERON_OBO = ROOT / "hra" / "externo" / "uberon" / "basic.obo"
FMA_OWL = ROOT / "hra" / "externo" / "fma" / "fma.owl"
EXPECTED_UBERON_SHA256 = "1F119822DC2DFD7ACF973FA1534E692D971064CAECAE6B7701D3221F1810A397"
EXPECTED_UBERON_DATA_VERSION = "uberon/releases/2026-11-05/uberon-basic.owl"
EXPECTED_FMA_SHA256 = "BEB3DC47979AD5434EF70FD02AF4307F147F2023F7D8C2C57103B995191194C3"
EXPECTED_FMA_VERSION = "5.1.0"
MANUAL_CSV = OUT / "decisoes_manuais.csv"

RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
OWL = "{http://www.w3.org/2002/07/owl#}"
RDFS = "{http://www.w3.org/2000/01/rdf-schema#}"
FMA_NS = "{http://purl.org/sig/ont/fma/}"
FMA_PART_RELATIONS = {"part_of", "regional_part_of", "constitutional_part_of", "branch_of", "tributary_of"}
MAX_FMA_ANCESTOR_DEPTH = 6

BP3D_CATEGORIES = {"presente", "parcial", "ausente", "exclusivo_masculino", "nao_mapeavel"}
HRA_CATEGORIES = {"presente_no_bp3d", "exclusivo_feminino", "so_no_hra"}

# Explicit vocabulary: a term match classifies a BodyParts3D mesh as male-only.
MALE_ONLY_TERMS = (
    "prostate", "prostate gland", "próstata", "testis", "testicle", "testículo", "testículos",
    "epididymis", "epidídimo", "seminal gland", "seminal vesicle", "glândula seminal",
    "ductus deferens", "vas deferens", "ducto deferente", "penis", "pênis", "scrotum", "escroto",
    "spermatic cord", "funículo espermático", "male reproductive", "masculine reproductive",
)

FEMALE_ONLY_TERMS = (
    "uterus", "uterine", "ovary", "ovaries", "ovarian", "fallopian tube", "uterine tube",
    "oviduct", "cervix of uterus", "uterine cervix", "vagina", "vaginal", "vulva",
    "female reproductive", "mammary gland", "breast gland",
)

# These terms explicitly define the H21 groups. Only meshes classified `ausente`
# receive one of these values. Matching ignores case, accents and punctuation.
UPPER_LIMB_TERMS = (
    "upper limb", "upper extremity", "shoulder", "clavicle", "collarbone", "scapula", "humerus",
    "arm", "elbow", "radius", "ulna", "carpus", "carpal", "wrist", "metacarp", "hand",
    "phalanx", "phalanges", "finger", "thumb", "digit of hand", "axilla",
)
UPPER_LIMB_VASCULAR_TERMS = (
    "upper limb", "upper extremity", "shoulder", "axillary", "subclavian", "brachial", "radial",
    "ulnar", "interosseous", "palmar", "carpal", "metacarpal", "digital artery", "digital vein",
    "cephalic vein", "basilic vein", "median cubital", "arm", "forearm", "hand",
)
VESSEL_TERMS = ("artery", "arterial", "vein", "venous", "vascular", "blood vessel", "arteriole", "venule")
NERVE_TERMS = ("nerve", "nervous", "neural", "plexus")
CENTRAL_NERVOUS_TERMS = ("brain", "spinal cord", "central nervous system", "cerebrum", "cerebellum")
ORGAN_TERMS = (
    "heart", "lung", "liver", "kidney", "stomach", "intestine", "spleen", "pancreas",
    "thyroid gland", "adrenal gland", "urinary bladder", "esophagus", "gallbladder", "uterus", "ovary", "prostate",
)
SIDE_TERMS = {"left", "right", "bilateral", "bilaterally", "esquerdo", "esquerda", "direito", "direita"}
NAME_STOPWORDS = {"of", "the", "a", "an", "and", "in", "on", "to", "structure", "part"}
GENERIC_HRA_LABELS = {"", "-", "skeletal system", "nervous system", "muscular system", "circulatory system", "respiratory system", "digestive system"}
PART_WHOLE_QUALIFIERS = {
    "part", "tree", "branch", "segment", "segmental", "anterior", "posterior", "superior", "inferior",
    "lateral", "medial", "rostral", "caudal", "proximal", "distal", "hepatic", "right", "left", "of",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def ascii_fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()


def normalize_name(value: str) -> str:
    words = re.findall(r"[a-z0-9]+", ascii_fold(value.replace("_", " ")))
    words = [word for word in words if word not in SIDE_TERMS and word not in NAME_STOPWORDS]
    words = ["brain" if word == "forebrain" else word for word in words]
    return " ".join(words)


def fma_id(value: str) -> str | None:
    match = re.search(r"\bFMA\s*:?\s*(\d+)\b", value, re.IGNORECASE)
    return f"FMA{match.group(1)}" if match else None


def fma_ids(value: str) -> set[str]:
    return {f"FMA{number}" for number in re.findall(r"\bFMA\s*:?\s*(\d+)\b", value, re.IGNORECASE)}


def uberon_id(value: str) -> str | None:
    match = re.search(r"\bUBERON\s*:?\s*(\d+)\b", value, re.IGNORECASE)
    return f"UBERON:{match.group(1)}" if match else None


def side_of(value: str) -> str | None:
    text = ascii_fold(value.replace("_", " "))
    if re.search(r"\b(left|esquerdo|esquerda)\b|(?:^|\s)l$", text):
        return "left"
    if re.search(r"\b(right|direito|direita)\b|(?:^|\s)r$", text):
        return "right"
    if re.search(r"\b(bilateral|bilaterally)\b", text):
        return "bilateral"
    return None


def side_relation(left: str | None, right: str | None) -> str:
    if left == right:
        return "same"
    if left and right and left != "bilateral" and right != "bilateral":
        return "opposite"
    return "granularity"


def hra_node_name(value: str) -> tuple[str, str | None]:
    """Derive a descriptive HRA name and side from the node id, including Allen nodes."""
    node = value.strip()
    node = re.sub(r"^(?:VH_F_|Allen_)", "", node)
    side = None
    if node.endswith("_L"):
        node, side = node[:-2], "left"
    elif node.endswith("_R"):
        node, side = node[:-2], "right"
    return node.replace("_", " ").strip(), side


def part_whole_core(value: str) -> str:
    words = normalize_name(value).split()
    words = [word for word in words if word not in PART_WHOLE_QUALIFIERS]
    words = ["brain" if word == "forebrain" else "bronchus" if word == "bronchial" else word for word in words]
    return " ".join(words)


def textual_part_whole(left: str, right: str) -> bool:
    """Conservative lexical parent/child/grouping signal used after ontology and exact-name stages."""
    left_core, right_core = part_whole_core(left), part_whole_core(right)
    return bool(left_core and left_core == right_core and normalize_name(left) != normalize_name(right))


def contains_phrase(text: str, phrase: str) -> bool:
    haystack = normalize_name(text)
    needle = normalize_name(phrase)
    return bool(needle and f" {needle} " in f" {haystack} ")


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    folded = ascii_fold(text.replace("_", " "))
    return any(ascii_fold(term) in folded for term in terms)


def parse_obo(path: Path) -> tuple[str, dict[str, dict[str, object]], dict[str, set[str]]]:
    terms: dict[str, dict[str, object]] = {}
    current: dict[str, object] | None = None
    data_version = ""
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("data-version:"):
                data_version = line.split(":", 1)[1].strip()
            elif line.startswith("[Term]"):
                if current and current.get("id") and current.get("name"):
                    terms[str(current["id"])] = current
                current = {"xref": set(), "parents": set(), "synonyms_exact": set(), "synonyms_related": set()}
            elif line.startswith("["):
                if current and current.get("id") and current.get("name"):
                    terms[str(current["id"])] = current
                current = None
            elif current is not None:
                if line.startswith("id:"):
                    current["id"] = line.split(":", 1)[1].strip()
                elif line.startswith("name:"):
                    current["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("xref:"):
                    value = line.split(":", 1)[1].strip().split(" !", 1)[0]
                    found = fma_id(value)
                    if found:
                        current["xref"].add(found)  # type: ignore[union-attr]
                elif line.startswith("is_a:"):
                    parent = line.split(":", 1)[1].strip().split()[0]
                    current["parents"].add(parent)  # type: ignore[union-attr]
                elif line.startswith("relationship: part_of "):
                    parent = line.split()[-1]
                    current["parents"].add(parent)  # type: ignore[union-attr]
                elif line.startswith("synonym:"):
                    match = re.match(r'^synonym:\s+"(.*?)"\s+(EXACT|RELATED|BROAD|NARROW)\b', line)
                    if match:
                        group = "synonyms_exact" if match.group(2) == "EXACT" else "synonyms_related"
                        current[group].add(match.group(1))  # type: ignore[union-attr]
        if current and current.get("id") and current.get("name"):
            terms[str(current["id"])] = current

    fma_to_uberon: dict[str, set[str]] = defaultdict(set)
    for term_id, term in terms.items():
        for fma in term["xref"]:  # type: ignore[union-attr]
            fma_to_uberon[str(fma)].add(term_id)
    return data_version, terms, fma_to_uberon


def fma_resource_id(resource: str) -> str | None:
    match = re.search(r"/fma0*(\d+)$", resource, re.IGNORECASE)
    return f"FMA{int(match.group(1))}" if match else None


def parse_fma(path: Path) -> tuple[str, dict[str, dict[str, object]]]:
    """Read the official FMA RDF/XML, retaining is_a and explicit part relations."""
    version = ""
    with path.open("rb") as stream:
        head = stream.read(32_768).decode("utf-8", errors="replace")
    version_match = re.search(r"<owl:versionInfo[^>]*>\s*([^<]+)", head)
    if version_match:
        version = version_match.group(1).strip()

    terms: dict[str, dict[str, object]] = {}
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag != OWL + "Class":
            continue
        about = element.attrib.get(RDF + "about", "")
        term_id = fma_resource_id(about)
        if not term_id:
            element.clear()
            continue
        names: set[str] = set()
        parents: set[str] = set()
        for child in element:
            if child.tag in {RDFS + "label", FMA_NS + "preferred_name", FMA_NS + "synonym"}:
                if child.text and child.text.strip():
                    names.add(child.text.strip())
            elif child.tag == RDFS + "subClassOf":
                direct_parent = fma_resource_id(child.attrib.get(RDF + "resource", ""))
                if direct_parent:
                    parents.add(direct_parent)
                    continue
                prop = ""
                target = ""
                for restriction_child in child.iter():
                    if restriction_child.tag == OWL + "onProperty":
                        prop_uri = restriction_child.attrib.get(RDF + "resource", "")
                        prop = prop_uri.rsplit("/", 1)[-1].rsplit("#", 1)[-1].casefold()
                    elif restriction_child.tag in {OWL + "someValuesFrom", OWL + "allValuesFrom"}:
                        target = restriction_child.attrib.get(RDF + "resource", "")
                parent_id = fma_resource_id(target)
                if prop in FMA_PART_RELATIONS and parent_id:
                    parents.add(parent_id)
        terms[term_id] = {"names": names, "parents": parents}
        element.clear()
    return version, terms


def fma_ancestors(term_id: str, terms: dict[str, dict[str, object]], cache: dict[str, set[str]]) -> set[str]:
    if term_id not in cache:
        found: set[str] = set()
        frontier = {term_id}
        for _ in range(MAX_FMA_ANCESTOR_DEPTH):
            next_frontier = {
                str(parent)
                for current in frontier
                for parent in terms.get(current, {}).get("parents", set())
                if str(parent) not in found and str(parent) != term_id
            }
            if not next_frontier:
                break
            found.update(next_frontier)
            frontier = next_frontier
        cache[term_id] = found
    return cache[term_id]


def bp_name_aliases(
    row: dict[str, str], fma_terms: dict[str, dict[str, object]],
    fma_to_uberon: dict[str, set[str]], uberon_terms: dict[str, dict[str, object]],
) -> tuple[set[str], set[str]]:
    exact = {row.get("nome_en", "")}
    related: set[str] = set()
    for fma in fma_ids(row.get("fma", "")):
        exact.update(str(value) for value in fma_terms.get(fma, {}).get("names", set()))
        for uberon in fma_to_uberon.get(fma, set()):
            term = uberon_terms.get(uberon, {})
            if term.get("name"):
                exact.add(str(term["name"]))
            exact.update(str(value) for value in term.get("synonyms_exact", set()))
            related.update(str(value) for value in term.get("synonyms_related", set()))
    exact_norms = {normalize_name(value) for value in exact if normalize_name(value)}
    related_norms = {normalize_name(value) for value in related if normalize_name(value)}
    return exact_norms, related_norms


def ancestors(term_id: str, terms: dict[str, dict[str, object]]) -> set[str]:
    seen: set[str] = set()
    pending = list(terms.get(term_id, {}).get("parents", set()))
    while pending:
        parent = pending.pop()
        if parent in seen:
            continue
        seen.add(parent)
        pending.extend(terms.get(parent, {}).get("parents", set()))
    return seen


def fmas_in_ancestry(term_id: str, terms: dict[str, dict[str, object]], ancestor_cache: dict[str, set[str]]) -> set[str]:
    if term_id not in ancestor_cache:
        ancestor_cache[term_id] = ancestors(term_id, terms)
    return {str(fma) for uberon in ancestor_cache[term_id] for fma in terms.get(uberon, {}).get("xref", set())}


def related_terms(left: str, right: str, terms: dict[str, dict[str, object]], ancestor_cache: dict[str, set[str]]) -> bool:
    if left == right:
        return True
    if left not in ancestor_cache:
        ancestor_cache[left] = ancestors(left, terms)
    if right not in ancestor_cache:
        ancestor_cache[right] = ancestors(right, terms)
    return left in ancestor_cache[right] or right in ancestor_cache[left]


def load_manual() -> dict[tuple[str, str], dict[str, str]]:
    if not MANUAL_CSV.exists():
        write_csv(MANUAL_CSV, ["dataset", "chave", "categoria", "malha_correspondente", "justificativa"], [])
        return {}
    decisions: dict[tuple[str, str], dict[str, str]] = {}
    for row_number, row in enumerate(read_csv(MANUAL_CSV), start=2):
        dataset = row.get("dataset", "").strip().upper()
        key = row.get("chave", "").strip()
        category = row.get("categoria", "").strip()
        corresponding_mesh = row.get("malha_correspondente", "").strip()
        rationale = row.get("justificativa", "").strip()
        if not any((dataset, key, category, corresponding_mesh, rationale)):
            continue
        allowed = BP3D_CATEGORIES if dataset == "BP3D" else HRA_CATEGORIES if dataset == "HRA" else set()
        if not allowed or not key or category not in allowed or not rationale:
            raise ValueError(f"decisoes_manuais.csv:{row_number}: dataset/chave/categoria/justificativa inválido(a).")
        decision_key = (dataset, key)
        if decision_key in decisions:
            raise ValueError(f"decisoes_manuais.csv:{row_number}: decisão duplicada para {dataset}:{key}.")
        decisions[decision_key] = {"categoria": category, "malha_correspondente": corresponding_mesh, "justificativa": rationale}
    return decisions


def prepare_hra(
    rows: list[dict[str, str]], fma_to_uberon: dict[str, set[str]],
    uberon_terms: dict[str, dict[str, object]], fma_terms: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    output = []
    for row in rows:
        ontology = row.get("ontologia", "").strip()
        uberon = uberon_id(ontology)
        fma_direct = fma_ids(ontology)
        fmas: set[str] = set()
        if uberon:
            for fma, uberons in fma_to_uberon.items():
                if uberon in uberons:
                    fmas.add(fma)
        node_name, node_side = hra_node_name(row.get("no", ""))
        label = row.get("label", "").strip()
        label_norm = normalize_name(label)
        usable_label = label_norm not in GENERIC_HRA_LABELS
        exact_names = [label if usable_label else "", node_name]
        related_names: list[str] = []
        uberon_term = uberon_terms.get(uberon or "", {})
        if uberon_term.get("name"):
            exact_names.append(str(uberon_term["name"]))
        exact_names.extend(str(value) for value in uberon_term.get("synonyms_exact", set()))
        related_names.extend(str(value) for value in uberon_term.get("synonyms_related", set()))
        for fma in fmas | fma_direct:
            exact_names.extend(str(value) for value in fma_terms.get(fma, {}).get("names", set()))
        exact_names = list(dict.fromkeys(value for value in exact_names if normalize_name(value)))
        related_names = list(dict.fromkeys(value for value in related_names if normalize_name(value)))
        name_candidates = list(dict.fromkeys(exact_names + related_names))
        display_name = label if usable_label else node_name
        terms = " ".join((label, row.get("orgao", ""), node_name))
        output.append({
            "no": row.get("no", ""), "sistema": row.get("sistema_hra", ""), "node_name": node_name,
            "orgao": row.get("orgao", ""), "nome": display_name, "ontology": ontology,
            "uberon": uberon, "fmas": fmas, "fma_direct": fma_direct, "termos": terms,
            "lado": node_side or side_of(label) or side_of(node_name) or side_of(row.get("orgao", "")),
            "nome_candidates": name_candidates, "nome_norms": [normalize_name(value) for value in name_candidates],
            "nome_cores": [part_whole_core(value) for value in name_candidates if part_whole_core(value)],
            "nome_exact_norms": [normalize_name(value) for value in exact_names],
            "nome_related_norms": [normalize_name(value) for value in related_names],
        })
    return output


def group_missing(row: dict[str, str]) -> str:
    """Assign the H21 group using the explicit term lists defined above."""
    text = " ".join((row.get("nome_en", ""), row.get("sistema", "")))
    system = ascii_fold(row.get("sistema", ""))
    if system == "esqueletico" and contains_any(text, UPPER_LIMB_TERMS):
        return "osso_membro_superior"
    if system == "muscular" and contains_any(text, UPPER_LIMB_TERMS):
        return "musculo_membro_superior"
    if system in {"arterial", "venoso"} and contains_any(text, VESSEL_TERMS) and contains_any(text, UPPER_LIMB_VASCULAR_TERMS):
        return "vaso_membro"
    if system == "nervoso" and contains_any(text, NERVE_TERMS) and not contains_any(text, CENTRAL_NERVOUS_TERMS):
        return "nervo_periferico"
    return "outro"


def priority_for(row: dict[str, str], p1_fmas: set[str]) -> str:
    if fma_ids(row.get("fma", "")).intersection(p1_fmas):
        return "P1"
    system = ascii_fold(row.get("sistema", row.get("sistema_hra", "")))
    name = row.get("nome_en", row.get("label", ""))
    if system == "esqueletico" or system.endswith("skeletal_system") or any(contains_phrase(name, term) for term in ORGAN_TERMS):
        return "P2"
    return "P3"


def classify_bp3d(
    bp: dict[str, str], hra: list[dict[str, object]], hra_by_fma: dict[str, list[dict[str, object]]],
    hra_by_direct_fma: dict[str, list[dict[str, object]]], hra_by_name: dict[str, list[dict[str, object]]],
    fma_to_uberon: dict[str, set[str]], uberon_by_name: dict[str, list[str]],
    terms: dict[str, dict[str, object]], ancestor_cache: dict[str, set[str]],
    hra_by_related_uberon: dict[str, list[dict[str, object]]],
    hra_by_ancestral_fma: dict[str, list[dict[str, object]]],
    hra_by_core: dict[str, list[dict[str, object]]],
    hra_by_catalog_fma: dict[str, list[dict[str, object]]],
    hra_by_fma_ancestors: dict[str, list[dict[str, object]]],
    hra_by_related_name: dict[str, list[dict[str, object]]],
    source_name_aliases: tuple[set[str], set[str]],
    fma_terms: dict[str, dict[str, object]], fma_ancestor_cache: dict[str, set[str]],
) -> tuple[str, str, str]:
    fma = fma_id(bp.get("fma", ""))
    source_side = side_of(bp.get("lateralidade", "")) or side_of(bp.get("nome_en", ""))
    name_norm = normalize_name(bp.get("nome_en", ""))

    # A fixed sex-specific anatomy list takes precedence over coincidental crosswalks.
    if contains_any(bp.get("nome_en", ""), MALE_ONLY_TERMS):
        return "exclusivo_masculino", "termo_exclusivo_masculino", ""

    # Stage 1: the UBERON basic.obo xref: FMA mapping.
    if fma:
        uberons = fma_to_uberon.get(fma, set())
        candidates = hra_by_fma.get(fma, [])
        exact_matches = [entry for entry in candidates if side_relation(source_side, entry["lado"]) == "same"]
        if exact_matches:
            return "presente", "xref_uberon_fma", ";".join(sorted(str(entry["no"]) for entry in exact_matches))
        granularity_matches = [entry for entry in candidates if side_relation(source_side, entry["lado"]) == "granularity"]
        if granularity_matches:
            return "parcial", "xref_lateralidade_agrupamento", ";".join(sorted(str(entry["no"]) for entry in granularity_matches))
        related_matches = list({str(entry["no"]): entry for target_id in uberons
                                for entry in hra_by_related_uberon.get(target_id, [])
                                if side_relation(source_side, entry["lado"]) != "opposite"}.values())
        if related_matches:
            return "parcial", "xref_uberon_fma_parent_child", ";".join(sorted(str(entry["no"]) for entry in related_matches))

        ancestor_matches = [entry for entry in hra_by_ancestral_fma.get(fma, [])
                            if side_relation(source_side, entry["lado"]) != "opposite" and fma not in entry["fmas"]]
        if ancestor_matches:
            return "parcial", "xref_fma_ancestral", ";".join(sorted(str(entry["no"]) for entry in ancestor_matches))

        # Stage 1b: the HRA catalog also carries direct FMA identifiers on some nodes.
        # Keep this distinguishable from the UBERON xref route.
        direct_matches = hra_by_direct_fma.get(fma, [])
        direct_same = [entry for entry in direct_matches if side_relation(source_side, entry["lado"]) == "same"]
        direct_partial = [entry for entry in direct_matches if side_relation(source_side, entry["lado"]) != "opposite"
                          and any(textual_part_whole(bp.get("nome_en", ""), str(name)) for name in entry["nome_candidates"])]
        if direct_partial:
            return "parcial", "fma_direto_catalogo_parte_todo", ";".join(sorted(str(entry["no"]) for entry in direct_partial))
        if direct_same:
            discordant = [entry for entry in direct_same if entry["nome_norms"]
                          and normalize_name(bp.get("nome_en", "")) not in entry["nome_norms"]]
            method = "fma_direto_catalogo_nome_discordante" if discordant else "fma_direto_catalogo"
            return "presente", method, ";".join(sorted(str(entry["no"]) for entry in direct_same))

        # FMA is_a and part_of hierarchy, limited to six ancestor levels.
        fma_hierarchy_matches = list({str(entry["no"]): entry for parent in fma_ancestors(fma, fma_terms, fma_ancestor_cache)
                                      for entry in hra_by_catalog_fma.get(parent, [])
                                      if side_relation(source_side, entry["lado"]) != "opposite"}.values())
        fma_hierarchy_matches.extend(entry for entry in hra_by_fma_ancestors.get(fma, [])
                                     if side_relation(source_side, entry["lado"]) != "opposite")
        fma_hierarchy_matches = list({str(entry["no"]): entry for entry in fma_hierarchy_matches}.values())
        if fma_hierarchy_matches:
            return "parcial", "fma_is_a_part_of_ate_6_niveis", ";".join(sorted(str(entry["no"]) for entry in fma_hierarchy_matches))

    # Stage 2: exact normalized names from the HRA label or node id.
    source_exact_names, source_related_names = source_name_aliases
    if source_exact_names:
        base_name_matches = [entry for entry in hra_by_name.get(name_norm, [])
                             if side_relation(source_side, entry["lado"]) == "same"]
        if base_name_matches:
            return "presente", "nome_normalizado", ";".join(sorted(str(entry["no"]) for entry in base_name_matches))
        exact_name_matches = list({str(entry["no"]): entry for alias in source_exact_names
                                   if alias != name_norm
                                   for entry in hra_by_name.get(alias, [])
                                   if side_relation(source_side, entry["lado"]) == "same"}.values())
        if exact_name_matches:
            return "presente", "sinonimo_uberon_fma_exato", ";".join(sorted(str(entry["no"]) for entry in exact_name_matches))

        related_name_matches = list({str(entry["no"]): entry for alias in source_exact_names
                                     for entry in hra_by_related_name.get(alias, [])
                                     if side_relation(source_side, entry["lado"]) != "opposite"}.values())
        related_name_matches.extend(entry for alias in source_related_names for entry in hra_by_name.get(alias, [])
                                    if side_relation(source_side, entry["lado"]) != "opposite")
        related_name_matches = list({str(entry["no"]): entry for entry in related_name_matches}.values())
        if related_name_matches:
            return "parcial", "sinonimo_uberon_relacionado", ";".join(sorted(str(entry["no"]) for entry in related_name_matches))

    if name_norm:
        name_matches = hra_by_name.get(name_norm, [])
        same_side = [entry for entry in name_matches if side_relation(source_side, entry["lado"]) == "same"]
        if same_side:
            return "presente", "nome_normalizado", ";".join(sorted(str(entry["no"]) for entry in same_side))
        granularity_side = [entry for entry in name_matches if side_relation(source_side, entry["lado"]) == "granularity"]
        if granularity_side:
            return "parcial", "nome_normalizado_lateralidade_agrupamento", ";".join(sorted(str(entry["no"]) for entry in granularity_side))

        # If the BP3D label resolves to a UBERON term whose HRA counterpart is a
        # parent/child, use the ontology graph rather than calling it absent.
        source_uberons = set(fma_to_uberon.get(fma or "", set()))
        source_uberons.update(uberon_by_name.get(name_norm, []))
        related_matches = []
        for entry in hra:
            target = entry.get("uberon")
            if not target or side_relation(source_side, entry["lado"]) == "opposite":
                continue
            if any(str(target) != source and related_terms(str(target), source, terms, ancestor_cache) for source in source_uberons):
                related_matches.append(entry)
        if related_matches:
            return "parcial", "uberon_is_a_part_of", ";".join(sorted(str(entry["no"]) for entry in related_matches))

        # The HRA node may be a segment/branch/tree that is not explicitly
        # cross-referenced in basic.obo; preserve the detected parent/group relation.
        textual_matches = list({str(entry["no"]): entry for entry in hra_by_core.get(part_whole_core(bp.get("nome_en", "")), [])
                                if side_relation(source_side, entry["lado"]) != "opposite"
                                and any(textual_part_whole(bp.get("nome_en", ""), str(name)) for name in entry["nome_candidates"])}.values())
        if textual_matches:
            return "parcial", "nome_no_parte_todo", ";".join(sorted(str(entry["no"]) for entry in textual_matches))
    if not fma:
        return "nao_mapeavel", "sem_fma", ""
    return "ausente", "sem_correspondencia", ""


def classify_hra(
    item: dict[str, object], bp_by_fma: dict[str, list[dict[str, str]]], bp_by_name: dict[str, list[dict[str, str]]],
    bp_by_name_rows: list[dict[str, str]], bp_by_core: dict[str, list[dict[str, str]]],
    bp_by_related_name: dict[str, list[dict[str, str]]], bp_by_fma_ancestors: dict[str, list[dict[str, str]]],
    bp_aliases: dict[str, tuple[set[str], set[str]]], fma_terms: dict[str, dict[str, object]],
    fma_ancestor_cache: dict[str, set[str]],
) -> tuple[str, str, str]:
    # HRA has UBERON identifiers and, for some catalog rows, FMA identifiers.
    candidates = []
    for fma in item["fmas"]:
        candidates.extend(bp_by_fma.get(str(fma), []))
    candidates = [row for row in candidates if side_relation(item["lado"], side_of(row.get("lateralidade", "")) or side_of(row.get("nome_en", ""))) == "same"]
    if candidates:
        return "presente_no_bp3d", "xref_uberon_fma", ";".join(sorted({row["arquivo"] for row in candidates}))
    direct_candidates = []
    for fma in item["fma_direct"]:
        direct_candidates.extend(bp_by_fma.get(str(fma), []))
    direct_candidates = [row for row in direct_candidates if side_relation(item["lado"], side_of(row.get("lateralidade", "")) or side_of(row.get("nome_en", ""))) == "same"]
    if direct_candidates:
        return "presente_no_bp3d", "fma_direto_catalogo_hra", ";".join(sorted({row["arquivo"] for row in direct_candidates}))
    # FMA ancestor/descendant relationships in either direction imply a partial counterpart.
    hra_fmas = {str(value) for value in item["fmas"] | item["fma_direct"]}
    hierarchy_candidates: dict[str, dict[str, str]] = {}
    for fma in hra_fmas:
        for ancestor_id in fma_ancestors(fma, fma_terms, fma_ancestor_cache):
            for row in bp_by_fma.get(ancestor_id, []):
                hierarchy_candidates[row["arquivo"]] = row
        for row in bp_by_fma_ancestors.get(fma, []):
            hierarchy_candidates[row["arquivo"]] = row
    if hierarchy_candidates:
        return "presente_no_bp3d", "fma_is_a_part_of_ate_6_niveis", ";".join(sorted(hierarchy_candidates))
    for name in item["nome_exact_norms"]:
        name_matches = [row for row in bp_by_name.get(str(name), []) if side_relation(item["lado"], side_of(row.get("lateralidade", "")) or side_of(row.get("nome_en", ""))) == "same"]
        if name_matches:
            method = "nome_normalizado" if name in [normalize_name(item["nome"])] else "sinonimo_uberon_fma_exato"
            return "presente_no_bp3d", method, ";".join(sorted({row["arquivo"] for row in name_matches}))
    related_matches: dict[str, dict[str, str]] = {}
    for name in item["nome_exact_norms"]:
        for row in bp_by_related_name.get(str(name), []):
            if side_relation(item["lado"], side_of(row.get("lateralidade", "")) or side_of(row.get("nome_en", ""))) != "opposite":
                related_matches[row["arquivo"]] = row
    for name in item["nome_related_norms"]:
        for row in bp_by_name.get(str(name), []):
            if side_relation(item["lado"], side_of(row.get("lateralidade", "")) or side_of(row.get("nome_en", ""))) != "opposite":
                related_matches[row["arquivo"]] = row
    if related_matches:
        return "presente_no_bp3d", "sinonimo_uberon_relacionado", ";".join(sorted(related_matches))
    textual_matches = list({row["arquivo"]: row for core in item["nome_cores"] for row in bp_by_core.get(str(core), [])
                            if side_relation(item["lado"], side_of(row.get("lateralidade", "")) or side_of(row.get("nome_en", ""))) != "opposite"
                            and any(textual_part_whole(str(name), row.get("nome_en", "")) for name in item["nome_candidates"])}.values())
    if textual_matches:
        return "presente_no_bp3d", "nome_no_parte_todo", ";".join(sorted({row["arquivo"] for row in textual_matches}))
    if contains_any(str(item["termos"]), FEMALE_ONLY_TERMS):
        return "exclusivo_feminino", "termo_exclusivo_feminino", ""
    return "so_no_hra", "sem_correspondencia", ""


def main() -> None:
    for required in (BP3D_CSV, HRA_CSV, BODYSITE_CSV, UBERON_OBO, FMA_OWL):
        if not required.is_file():
            raise FileNotFoundError(f"entrada ausente: {required.relative_to(ROOT)}")
    version, ontology, fma_to_uberon = parse_obo(UBERON_OBO)
    digest = hashlib.sha256(UBERON_OBO.read_bytes()).hexdigest().upper()
    if version != EXPECTED_UBERON_DATA_VERSION or digest != EXPECTED_UBERON_SHA256:
        raise ValueError("UBERON basic.obo não corresponde à versão/hash registrados; revise as constantes antes de executar.")

    fma_version, fma_terms = parse_fma(FMA_OWL)
    fma_digest = hashlib.sha256(FMA_OWL.read_bytes()).hexdigest().upper()
    if fma_version != EXPECTED_FMA_VERSION or fma_digest != EXPECTED_FMA_SHA256:
        raise ValueError("FMA fma.owl does not match the registered version/hash; review constants before running.")

    bp_rows = read_csv(BP3D_CSV)
    hra_raw = read_csv(HRA_CSV)
    bodysite_rows = read_csv(BODYSITE_CSV)
    hra_rows = prepare_hra(hra_raw, fma_to_uberon, ontology, fma_terms)
    hra_by_fma: dict[str, list[dict[str, object]]] = defaultdict(list)
    hra_by_direct_fma: dict[str, list[dict[str, object]]] = defaultdict(list)
    hra_by_name: dict[str, list[dict[str, object]]] = defaultdict(list)
    hra_by_related_name: dict[str, list[dict[str, object]]] = defaultdict(list)
    hra_by_related_uberon: dict[str, list[dict[str, object]]] = defaultdict(list)
    hra_by_ancestral_fma: dict[str, list[dict[str, object]]] = defaultdict(list)
    hra_by_core: dict[str, list[dict[str, object]]] = defaultdict(list)
    hra_by_catalog_fma: dict[str, list[dict[str, object]]] = defaultdict(list)
    hra_by_fma_ancestors: dict[str, list[dict[str, object]]] = defaultdict(list)
    ancestor_cache: dict[str, set[str]] = {}
    fma_ancestor_cache: dict[str, set[str]] = {}
    children: dict[str, set[str]] = defaultdict(set)
    for child_id, term in ontology.items():
        for parent_id in term.get("parents", set()):
            children[str(parent_id)].add(str(child_id))
    descendants_cache: dict[str, set[str]] = {}
    for item in hra_rows:
        for fma in item["fmas"]:
            hra_by_fma[str(fma)].append(item)
            hra_by_catalog_fma[str(fma)].append(item)
        for fma in item["fma_direct"]:
            hra_by_direct_fma[str(fma)].append(item)
            hra_by_catalog_fma[str(fma)].append(item)
        for fma in item["fmas"] | item["fma_direct"]:
            for ancestor_id in fma_ancestors(str(fma), fma_terms, fma_ancestor_cache):
                hra_by_fma_ancestors[ancestor_id].append(item)
        for name in item["nome_exact_norms"]:
            hra_by_name[str(name)].append(item)
        for name in item["nome_related_norms"]:
            hra_by_related_name[str(name)].append(item)
        for core in item["nome_cores"]:
            hra_by_core[str(core)].append(item)
        target = item.get("uberon")
        if target:
            target_id = str(target)
            if target_id not in descendants_cache:
                descendants: set[str] = set()
                pending = list(children.get(target_id, set()))
                while pending:
                    child_id = pending.pop()
                    if child_id in descendants:
                        continue
                    descendants.add(child_id)
                    pending.extend(children.get(child_id, set()))
                descendants_cache[target_id] = descendants
            related_ids = {target_id, *ancestors(target_id, ontology), *descendants_cache[target_id]}
            for source_id in related_ids:
                hra_by_related_uberon[source_id].append(item)
            for fma in fmas_in_ancestry(target_id, ontology, ancestor_cache):
                hra_by_ancestral_fma[fma].append(item)

    uberon_by_name: dict[str, list[str]] = defaultdict(list)
    for term_id, term in ontology.items():
        name = normalize_name(str(term.get("name", "")))
        if name:
            uberon_by_name[name].append(term_id)

    bp_by_fma: dict[str, list[dict[str, str]]] = defaultdict(list)
    bp_by_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    bp_by_related_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    bp_by_fma_ancestors: dict[str, list[dict[str, str]]] = defaultdict(list)
    bp_by_core: dict[str, list[dict[str, str]]] = defaultdict(list)
    bp_aliases_by_file: dict[str, tuple[set[str], set[str]]] = {}
    for row in bp_rows:
        fma = fma_id(row.get("fma", ""))
        if fma:
            bp_by_fma[fma].append(row)
            for ancestor_id in fma_ancestors(fma, fma_terms, fma_ancestor_cache):
                bp_by_fma_ancestors[ancestor_id].append(row)
        exact_aliases, related_aliases = bp_name_aliases(row, fma_terms, fma_to_uberon, ontology)
        bp_aliases_by_file[row.get("arquivo", "")] = (exact_aliases, related_aliases)
        for name in exact_aliases:
            bp_by_name[name].append(row)
        for name in related_aliases:
            bp_by_related_name[name].append(row)
        core = part_whole_core(row.get("nome_en", ""))
        if core:
            bp_by_core[core].append(row)

    p1_fmas = set()
    for row in bodysite_rows:
        p1_fmas.update(fma_ids(row.get("estrutura_fma", "")))
    manual = load_manual()
    bp_output: list[dict[str, object]] = []
    automatic_rows: list[dict[str, object]] = []
    for row in bp_rows:
        category, method, mesh = classify_bp3d(
            row, hra_rows, hra_by_fma, hra_by_direct_fma, hra_by_name, fma_to_uberon,
            uberon_by_name, ontology, ancestor_cache, hra_by_related_uberon, hra_by_ancestral_fma, hra_by_core,
            hra_by_catalog_fma, hra_by_fma_ancestors, hra_by_related_name,
            bp_aliases_by_file[row.get("arquivo", "")], fma_terms, fma_ancestor_cache,
        )
        decision = manual.get(("BP3D", row.get("arquivo", "")))
        if decision:
            category, method = decision["categoria"], "manual"
            mesh = decision["malha_correspondente"] or mesh
            if mesh and any(part not in {str(item["no"]) for item in hra_rows} for part in mesh.split(";")):
                raise ValueError(f"decisao BP3D:{row['arquivo']} cita malha HRA inexistente.")
        output = {
            "arquivo": row.get("arquivo", ""), "fma": row.get("fma", ""), "nome": row.get("nome_en", ""),
            "sistema": row.get("sistema", ""), "lado": row.get("lateralidade", ""), "categoria": category,
            "metodo": method, "malha_hra": mesh, "prioridade": priority_for(row, p1_fmas),
            "grupo_h21": group_missing(row) if category == "ausente" else "",
        }
        bp_output.append(output)
        if method != "manual":
            automatic_rows.append({"dataset": "BP3D", "arquivo": output["arquivo"], "fma": output["fma"], "nome": output["nome"],
                                   "sistema": output["sistema"], "lado": output["lado"], "categoria": category, "metodo": method,
                                   "malha_correspondente": mesh})

    if len(bp_output) != len(bp_rows) or any(row["categoria"] not in BP3D_CATEGORIES or not row["metodo"] for row in bp_output):
        raise AssertionError("A1: cada linha BP3D precisa de exatamente uma categoria e um método.")

    hra_output: list[dict[str, object]] = []
    for item in hra_rows:
        category, method, mesh = classify_hra(
            item, bp_by_fma, bp_by_name, bp_rows, bp_by_core, bp_by_related_name,
            bp_by_fma_ancestors, bp_aliases_by_file, fma_terms, fma_ancestor_cache,
        )
        decision = manual.get(("HRA", str(item["no"])))
        if decision:
            category, method = decision["categoria"], "manual"
            mesh = decision["malha_correspondente"] or mesh
            if mesh and any(part not in {row.get("arquivo", "") for row in bp_rows} for part in mesh.split(";")):
                raise ValueError(f"decisao HRA:{item['no']} cita malha BP3D inexistente.")
        fmas = sorted({str(value) for value in item["fmas"] | item["fma_direct"]})
        priority_row = {"fma": fmas[0] if fmas else "", "sistema_hra": item["sistema"], "label": item["nome"]}
        hra_output.append({
            "arquivo": item["no"], "fma": ";".join(fmas), "nome": item["nome"], "sistema": item["sistema"],
            "lado": item["lado"] or "", "categoria": category, "metodo": method, "malha_bp3d": mesh,
            "prioridade": priority_for(priority_row, p1_fmas), "ontologia": item["ontology"],
        })
        if method != "manual":
            automatic_rows.append({"dataset": "HRA", "arquivo": item["no"], "fma": ";".join(fmas), "nome": item["nome"],
                                   "sistema": item["sistema"], "lado": item["lado"] or "", "categoria": category,
                                   "metodo": method, "malha_correspondente": mesh})

    if len(hra_output) != len(hra_rows) or any(row["categoria"] not in HRA_CATEGORIES or not row["metodo"] for row in hra_output):
        raise AssertionError("A1: cada linha HRA precisa de exatamente uma categoria e um método.")

    write_csv(OUT / "inventario_bp3d.csv",
              ["arquivo", "fma", "nome", "sistema", "lado", "categoria", "metodo", "malha_hra", "prioridade", "grupo_h21"], bp_output)
    write_csv(OUT / "inventario_hra.csv",
              ["arquivo", "fma", "nome", "sistema", "lado", "categoria", "metodo", "malha_bp3d", "prioridade", "ontologia"], hra_output)

    matrix_lines = [
        "# EXP-0021 — Matriz de cobertura BP3D × HRA",
        "",
        f"UBERON: `{version}`; SHA-256: `{digest}`.",
        f"FMA: versão `{fma_version}`; SHA-256: `{fma_digest}`.",
        "Percentuais de categorias usam todas as malhas daquela combinação sistema × prioridade como denominador. "
        "`cobertura_total_%` = (presente + parcial) / (total − exclusivo_masculino − nao_mapeavel).",
        "",
        "| Sistema | Prioridade | Total | Presente n (%) | Parcial n (%) | Ausente n (%) | Exclusivo masc. n (%) | Não mapeável n (%) | Cobertura total (%) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    matrix_groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in bp_output:
        matrix_groups[(str(row["sistema"]), str(row["prioridade"]))].append(row)
    for (system, priority), rows in sorted(matrix_groups.items()):
        total = len(rows)
        counts = Counter(str(row["categoria"]) for row in rows)
        percentages = {category: (counts[category] / total * 100 if total else 0.0) for category in BP3D_CATEGORIES}
        eligible = total - counts["exclusivo_masculino"] - counts["nao_mapeavel"]
        coverage = ((counts["presente"] + counts["parcial"]) / eligible * 100) if eligible else 0.0
        matrix_lines.append(
            f"| {system} | {priority} | {total} | {counts['presente']} ({percentages['presente']:.1f}%) | "
            f"{counts['parcial']} ({percentages['parcial']:.1f}%) | {counts['ausente']} ({percentages['ausente']:.1f}%) | "
            f"{counts['exclusivo_masculino']} ({percentages['exclusivo_masculino']:.1f}%) | "
            f"{counts['nao_mapeavel']} ({percentages['nao_mapeavel']:.1f}%) | {coverage:.1f}% |"
        )
    (OUT / "matriz_cobertura.md").write_text("\n".join(matrix_lines) + "\n", encoding="utf-8")

    random.seed(23)
    sample = random.sample(automatic_rows, min(50, len(automatic_rows)))
    write_csv(OUT / "amostra_revisao.csv",
              ["dataset", "arquivo", "fma", "nome", "sistema", "lado", "categoria", "metodo", "malha_correspondente"], sample)

    category_counts = Counter(str(row["categoria"]) for row in bp_output)
    missing = [row for row in bp_output if row["categoria"] == "ausente"]
    groups = Counter(str(row["grupo_h21"]) for row in missing)
    h21_groups = ("osso_membro_superior", "musculo_membro_superior", "vaso_membro", "nervo_periferico")
    numerator = sum(groups[group] for group in h21_groups)
    percentage = numerator / len(missing) * 100 if missing else 0.0
    provisional = "limiar atingido" if missing and percentage >= 50 else "abaixo do limiar"
    h21_lines = [
        "EXP-0021 — Critério A3 (H21)",
        f"UBERON data-version: {version}",
        f"UBERON SHA-256: {digest}",
        f"FMA version: {fma_version}",
        f"FMA SHA-256: {fma_digest}",
        f"Total de malhas BP3D lidas: {len(bp_output)}",
        f"Categoria ausente (denominador A3): {len(missing)}",
        "Grupos H21 incluídos no numerador: " + ", ".join(f"{group}={groups[group]}" for group in h21_groups),
        f"Numerador A3: {numerator}",
        f"Cálculo: {numerator}/{len(missing)} = {percentage:.2f}%" if missing else "Cálculo: sem malhas ausentes (denominador zero).",
        "Limite pré-registrado: ≥ 50% das malhas `ausente`.",
        f"Estimativa A3: {provisional}; H21 não julgada enquanto a revisão A2 da Rodada 3 estiver pendente.",
        "Grupo `outro` não integra o numerador; nenhuma categoria exclusiva_masculino ou nao_mapeavel integra o denominador.",
        f"Decisões manuais aplicadas: BP3D={sum(1 for k in manual if k[0] == 'BP3D')}; HRA={sum(1 for k in manual if k[0] == 'HRA')}",
    ]
    (OUT / "resultado_h21.txt").write_text("\n".join(h21_lines) + "\n", encoding="utf-8")

    (OUT / "fma_origem.txt").write_text(
        "Fonte solicitada: http://purl.obolibrary.org/obo/fma.owl\n"
        f"versão: {fma_version}\nSHA-256: {fma_digest}\n"
        "Cópia: hra/externo/fma/fma.owl (fora do git).\n",
        encoding="utf-8",
    )

    pending_lines = [
        "EXP-0021 Frente A — situação dos critérios mensuráveis",
        f"A1: classificação automática executada para {len(bp_output)}/{len(bp_rows)} malhas BP3D e {len(hra_output)}/{len(hra_rows)} malhas HRA; cada linha tem exatamente uma categoria válida e método registrado.",
        f"A2: nova amostra de {len(sample)} classificações automáticas gerada em amostra_revisao.csv com random.seed(23); revisão pendente.",
        f"A3: {numerator}/{len(missing)} = {percentage:.2f}%; limite pré-registrado ≥50%; H21 não julgada até a revisão A2.",
        "As seções 8–11 do protocolo não foram alteradas.",
    ]
    (OUT / "criterios_pendentes.txt").write_text("\n".join(pending_lines) + "\n", encoding="utf-8")

    (OUT / "uberon_origem.txt").write_text(
        "Fonte solicitada: http://purl.obolibrary.org/obo/uberon/basic.obo\n"
        f"data-version: {version}\nSHA-256: {digest}\n" 
        "A cópia básica está em hra/externo/uberon/basic.obo (fora do git).\n",
        encoding="utf-8",
    )

    print(f"UBERON {version}; SHA-256 {digest}")
    print(f"FMA {fma_version}; SHA-256 {fma_digest}")
    print(f"BP3D {len(bp_output)}: {dict(category_counts)}")
    print(f"HRA {len(hra_output)}: {dict(Counter(str(row['categoria']) for row in hra_output))}")
    print(f"Amostra revisão: {len(sample)} (seed 23; {len(manual)} manual decisions excluded); A3: {numerator}/{len(missing)} = {percentage:.2f}% ({provisional}; H21 não julgada até A2)")


if __name__ == "__main__":
    main()
