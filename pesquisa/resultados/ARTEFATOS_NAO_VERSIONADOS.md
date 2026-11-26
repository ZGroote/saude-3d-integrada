# Artefatos Não Versionados Referenciados na Documentação

Levantamento via `git ls-files` e `git check-ignore` em `2026-11-26`.

## Existem localmente e estão no `.gitignore`
- `atlas/bp3d-m/4.0-1/` (`manifesto.json`, `indice.json`, 15 GLBs) — pacote publicado local do `bp3d-m`.
- `atlas/hra-f/1.10-1/` (`manifesto.json`, `indice.json`, 14 GLBs) — pacote publicado local do `hra-f` (mantido no MVP).
- `atlas/hra-f/2.0-1/` (`avaliacao_F1-F4.json`, `proveniencia_sha256.json`, STLs) — saída intermediária do `EXP-0015`.
- `atlas/vhf-f/0.1-0/` — rascunho local não publicado/não aceito (`EXP-0015`).
- `atlas/hib-f/0.1-0/` — rascunho local não publicado/não aceito (`EXP-0016`).
- `bodyparts3d/bruto/` — dados brutos do BodyParts3D 4.0.
- `hra/bruto/united_f_cdn_latest.glb` — GLB bruto do HRA v1.10 (375 MB).
- `hra/denver/bruto/` (`MetaData/README.txt`, `tc_alinhada.nii.gz`, `Aligned CT-DICOM/`, `Final 3D STL Models-stl/`) — dados brutos da University of Denver.
- `hra/nlm/bruto/` (`tc_nlm_1p5.nii.gz`, `fast/segmentacao.nii.gz`, `saida/segmentacao.nii.gz`) — TC original da NLM e segmentações TotalSegmentator.
- `hra/totalseg/bruto/` (`tc_hu_1p5.nii.gz`) — TC da Denver convertida (`EXP-0009`).
- `supabase/dados/bruto/` (`CID10CSV.zip` e CSVs ISO-8859-1) — tabelas brutas DATASUS.
- `web/public/atlas/hra-f/1.10-1/tegumentar.glb` — cópia servida pelo app web.
- `web/testes/capturas/` (`f5/`, `f5-hibrido/`) — capturas de revisão visual.

## Faltam localmente (não estão no git nem no disco atual)
- `bodyparts3d/modelos/*.glb` — GLBs pré-compressão do `EXP-0004` (substituídos por `bodyparts3d/modelos_web/*.glb` no pacote final; `modelos_web/` existe localmente e está versionado no commit `2b7f443`).
- `web/public/atlas/vhf-f/0.1-0/indice.json` — referência histórica do `EXP-0016` ao rascunho em `web/public/atlas/` (o rascunho permanece em `atlas/vhf-f/0.1-0/`).
