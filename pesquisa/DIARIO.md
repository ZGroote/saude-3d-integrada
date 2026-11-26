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
- **`f6935e5`** — Montagem da TC original da NLM (`tc_nlm_1p5.nii.gz`, cortes 1001–2734) e segmentação em partes CPU+GPU (`hra/nlm/segmentar_partes.py`) (`EXP-0010`, em execução); scripts commitados neste commit. Depois dele (artefatos ainda não commitados em `hra/alinhar/`): ICP real Etapa A Denver↔TC NLM (`EXP-0011`, em execução; fêmures ~3,3 mm, pelve ~2,7 mm, sacro holdout 3,990 mm — reprovado no critério `< 3 mm`).
- **23:47 (`EXP-0014`, sem commit)** — Registrado o protocolo pré-execução de aceitação por finalidade (`EXP-0014-protocolo-aceitacao-atlas.md`, `planejado`) **antes** da rodada com segmentação em resolução normal. Conforme a **Regra 15**, a mudança de critério foi documentada explicitamente (critérios geométricos por classe + funcionais F1–F5, Plano B regional e regra de fonte única), mantendo o **`EXP-0011` REPROVADO** no critério original de `< 3 mm`.

## 2026-11-26
- **`5ec1c34` (`EXP-0014`)** — Rodada real em resolução normal avaliada pelo protocolo `EXP-0014`: **NÃO ACEITO** (hipótese rejeitada para a base HRA). Joelho `23–25 mm`, cabeça do fêmur à pelve HRA `17–21 mm`, F1 `32/164`, F3 `28/164` (pele HRA aberta, ~79% normais para fora), `L1–L5` e rim esquerdo reprovados; cervical/torácica passaram; F4 `160/160`; F5 pendente.
- **`01:45` (`EXP-0015`, sem commit)** — Registrado protocolo pré-execução `EXP-0015-base-tc-nlm.md` (`planejado`): inversão do corpo base para a TC NLM (`TotalSegmentator 'total' + 'body'`, com checagem prévia da licença de `'body'`) + pernas da Denver + apenas complementos locais do HRA, mantendo os mesmos critérios do `EXP-0014` e teto de 5 dias úteis.
- **`EXP-0015`, rodada-base (sem commit)** — README oficial confirmou task `body` aberta sob Apache-2.0 (`hra/vhf/LEIAME.md`). O montador marching cubes + Taubin exportou 229 malhas, incluindo 122 Denver; 227/229 fechadas, pele fechada, deriva volumétrica máxima `2,46e-15`. F1 `97,78%` (falha); F2 quadril proxy `19,418/17,911 mm` falha, joelho E `5,693 mm` falha/D `4,948 mm` passa, costelas–vértebras `1/24` ≤5 mm falha, crânio–C1 `3,350 mm` passa; F3 não avaliado; F4 `178/178` passa; F5 pendente. Hipótese não aceita nesta rodada; sem validação clínica.
