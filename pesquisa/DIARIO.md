# Diário de Pesquisa

Registro cronológico reconstruído a partir do histórico de commits (`git log`) e dos relatórios do repositório.

## 2026-11-25
- **`1fec829`** — Conceito inicial, `SPEC-MVP.md` e primeiro experimento de reconstrução tomográfica a partir de TC (`teste-anatomia/`, caso `s1371` do TotalSegmentator v2.0.1) (`EXP-0001`).
- **`1e1389e`** — Inventário e classificação do BodyParts3D 4.0 (2.234 malhas em 15 sistemas) (`EXP-0002`), teste de encaixe BodyParts3D × `s1371` por similaridade (erro médio 36,5 mm) (`EXP-0003`) e inventário inicial do HRA female (`united_f_cdn_latest.glb`, 956 malhas) (`EXP-0005`).
- **`2b7f443`** — Compressão dos 15 GLBs do BodyParts3D com `meshopt` e quantização de 16 bits (`comprimir_web.py`) sem perda de nós ou triângulos (`EXP-0004`), tradução inicial dos nomes FMA para português e visualizador web.
- **`f9b7e65` / `69f778f`** — `LICENCAS.md`, confirmação da licença CC BY 4.0 do HRA (`hra/LICENCA_HRA.md`) e script `bodyparts3d/publicar_atlas.py`.
- **`a90cc45` / `8e9fe43`** — Publicação do pacote `atlas/hra-f/1.10-1` (956 malhas em 14 sistemas) com 100% dos nomes em português (`EXP-0005`).
- **`0324bc7`** — Inventário da coleção Denver (128 STLs, 28 ossos), alinhamento Denver STL→TC por intensidade (platô 98,60–100%, não validado) (`EXP-0006`), busca por bordas Otsu (macro score 19,888%, sem pico estreito, não validado) (`EXP-0007`) e preparo da TC da Denver para o TotalSegmentator (`EXP-0009`).
- **`fdb9441` / `8692651`** — Implementação do alinhamento malha a malha por ICP (`hra/alinhar/alinhar.py`) com validação sintética (`EXP-0008`).
- **`f6935e5`** — Montagem da TC original da NLM (`tc_nlm_1p5.nii.gz`, cortes 1001–2734) e segmentação em partes CPU+GPU (`hra/nlm/segmentar_partes.py`) (`EXP-0010`, em execução); início do ICP real Etapa A Denver↔TC NLM (`EXP-0011`, em execução; fêmures ~3,3 mm, pelve ~2,7 mm, sacro holdout 3,990 mm — reprovado no critério `< 3 mm`).
