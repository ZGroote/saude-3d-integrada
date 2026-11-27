"""Verifica consistência, links, encoding e seções obrigatórias da documentação científica."""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PESQUISA = ROOT / 'pesquisa'
EXPERIMENTS_DIR = PESQUISA / 'experimentos'
INDEX_PATH = PESQUISA / 'INDICE_EXPERIMENTOS.md'

REQUIRED_SECTIONS = (
    'problema',
    'hipotese',
    'metodologia',
    'criterios',
    'resultados',
    'conclusao',
)

MOJIBAKE_RE = re.compile(r'Ã[\x80-\xbf]|Â[\x80-\xbf]|\ufffd')
BROKEN_Q_RE = re.compile(r'[A-Za-zÀ-ÿ]\?[A-Za-zÀ-ÿ]|[A-Za-zÀ-ÿ]\?\?[A-Za-zÀ-ÿ]')
EXP_ID_RE = re.compile(r'\bEXP-\d{4}\b')
MD_LINK_RE = re.compile(r'\[[^\]]+\]\(([^)]+)\)')


def norm(text: str) -> str:
    table = str.maketrans('áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ', 'aaaaeeioooucAAAAEEIOOOUC')
    return text.translate(table).lower()


def main() -> int:
    errors: list[str] = []

    exp_files = {
        m.group(0): p
        for p in sorted(EXPERIMENTS_DIR.glob('EXP-*.md'))
        if (m := re.match(r'EXP-\d{4}', p.name))
    }

    # Parse INDICE_EXPERIMENTOS.md
    index_status: dict[str, str] = {}
    if not INDEX_PATH.exists():
        errors.append('INDICE_EXPERIMENTOS.md ausente')
    else:
        for line in INDEX_PATH.read_text(encoding='utf-8').splitlines():
            if not line.startswith('| ['):
                continue
            cols = [c.strip() for c in line.strip('|').split('|')]
            if len(cols) < 4:
                continue
            m = EXP_ID_RE.search(cols[0])
            if m:
                index_status[m.group(0)] = cols[3]

    # (a) Todo EXP-XXXX citado existe em pesquisa/experimentos e no índice
    cited_exps: set[str] = set()
    md_files = sorted(PESQUISA.rglob('*.md')) + [
        p for p in (ROOT / 'SPEC-MVP.md', ROOT / 'CLAUDE.md', ROOT / 'AGENTS.md', ROOT / 'docs/lgpd/RIPD-rascunho.md')
        if p.exists()
    ]
    for md in md_files:
        if md.name == 'EXPERIMENTO.md':
            continue
        raw = md.read_bytes()
        # (d) ausência de mojibake / BOM / ? quebrado
        if raw.startswith(b'\xef\xbb\xbf'):
            errors.append(f'BOM UTF-8 encontrado em {md.relative_to(ROOT)}')
        txt = raw.decode('utf-8', errors='replace')
        if MOJIBAKE_RE.search(txt):
            errors.append(f'Mojibake encontrado em {md.relative_to(ROOT)}')
        if BROKEN_Q_RE.search(re.sub(r'https?://\S+', '', txt)):  # '?' de query string em URL não é encoding quebrado
            errors.append(f'Caractere ? suspeito de encoding em {md.relative_to(ROOT)}')

        # (c) links relativos de .md apontam para arquivos existentes
        for target in MD_LINK_RE.findall(txt):
            if target.startswith(('http://', 'https://', 'mailto:', '#')):
                continue
            rel = target.split('#', 1)[0].strip()
            if not rel:
                continue
            resolved = (md.parent / rel).resolve()
            if not resolved.exists():
                errors.append(f'Link quebrado em {md.relative_to(ROOT)}: {target}')

        if md.is_relative_to(PESQUISA):
            for exp_id in EXP_ID_RE.findall(txt):
                if exp_id == 'EXP-XXXX':
                    continue
                cited_exps.add(exp_id)

    for exp_id in sorted(cited_exps | set(exp_files)):
        if exp_id not in exp_files:
            errors.append(f'{exp_id} citado na documentação, mas arquivo não existe em pesquisa/experimentos/')
        if exp_id not in index_status:
            errors.append(f'{exp_id} ausente de pesquisa/INDICE_EXPERIMENTOS.md')

    # (b) situação no índice == situação no arquivo do EXP + (e) seções obrigatórias
    for exp_id, path in sorted(exp_files.items()):
        txt = path.read_text(encoding='utf-8')
        m_sit = re.search(r'^-\s+\*\*Situação:\*\*\s*(.+)$', txt, re.M)
        if not m_sit:
            errors.append(f'{exp_id}: campo Situação ausente')
        else:
            file_sit = m_sit.group(1).strip()
            idx_sit = index_status.get(exp_id)
            if idx_sit is not None and file_sit != idx_sit:
                errors.append(f'{exp_id}: situação diverge (arquivo={file_sit!r} vs índice={idx_sit!r})')

        headings = [norm(h) for h in re.findall(r'^##+\s+(.+)$', txt, re.M)]
        for req in REQUIRED_SECTIONS:
            if not any(req in h for h in headings):
                errors.append(f'{exp_id}: seção obrigatória ausente ({req})')

    if errors:
        print(f'FALHOU: {len(errors)} inconsistência(s):')
        for e in errors:
            print(f' - {e}')
        return 1

    print(f'OK: {len(exp_files)} experimentos verificados, {len(md_files)} arquivos .md sem mojibake/BOM ou links quebrados.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
