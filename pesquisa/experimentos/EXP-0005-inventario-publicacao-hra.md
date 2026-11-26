# EXP-0005 — Inventário do HRA female (956 malhas) e publicação hra-f 1.10-1

> **REGISTRO RETROSPECTIVO** — Reconstruído a partir de `hra/RELATORIO.md`, `hra/LICENCA_HRA.md`, `hra/publicar_atlas_hra.py`, `atlas/hra-f/1.10-1/manifesto.json` e commits `1e1389e`, `69f778f`, `a90cc45`, `8e9fe43`. Campos ausentes nas evidências são marcados como `não documentado`.

## 1. Identificação
- **ID:** `EXP-0005`
- **Título:** Inventário do HRA female (956 malhas) e publicação `hra-f 1.10-1`
- **Data:** `2026-11-25`
- **Responsável:** não documentado
- **Agentes de IA:** não documentado
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** `1e1389e`, `69f778f`, `a90cc45`, `8e9fe43`
- **Linha de pesquisa:** `LP01`
- **Situação:** `concluído`

## 2. Problema
Avaliar o modelo `united-female` do Human Reference Atlas (HRA), confirmar sua licença e publicar o pacote versionado `hra-f/1.10-1` compatível com o contrato do motor anatômico (`SPEC-MVP.md` §5.3).

## 3. Hipótese
O arquivo `united_f_cdn_latest.glb` (v1.10) pode ser particionado em sistemas anatômicos compatíveis com o contrato do `bp3d-m` (incluindo camada `gestacional`), comprimido com `meshopt`, traduzido para PT-BR e validado com hashes SHA-256.

## 4. Fundamentação teórica
Contrato de pacote de atlas (`SPEC-MVP.md` §5.3), ontologias UBERON/FMA e compressão glTF `EXT_meshopt_compression`.

## 5. Materiais e ambiente
- **Datasets e versões:** HRA 3D Reference Organ Set for United, Female `v1.10` (`3d-vh-f-united.glb`, 375 MB bruto, publicado em `2026-06-15`, DOI `10.48539/HBM637.DWBM.744`).
- **Licenças:** CC BY 4.0 + termos NLM Visible Human Dataset (`hra/LICENCA_HRA.md`).
- **Hashes:** SHA-256 dos 14 GLBs e `indice.json` em `atlas/hra-f/1.10-1/manifesto.json` (`gerado_em: 2026-11-25T21:27:15+00:00`).
- **Hardware:** não documentado.
- **Sistema operacional:** Windows.
- **Bibliotecas e versões:** Python (`numpy`), `@gltf-transform/cli@4.5.1` via `npx`.
- **Seed:** não aplicável.

## 6. Metodologia
- **Procedimentos e algoritmos:** inventário de nós/ontologias (`hra/analisar_hra.py`); confirmação documental de licença (`hra/LICENCA_HRA.md`); tradução anatômica (`hra/nomes_pt_hra.csv`, 721 entradas incluindo 210 malhas sem ontologia); verificação de orientação/escala por landmarks anatômicos (`heart`, `left_leg`/`right_leg`, `eyes`, `breast`, `spine`, `lowest_tibia_fibula`); centralização pela caixa global; particionamento em 14 sistemas; `prune` + `meshopt` (`--level high --quantize-position 16 --quantization-volume mesh`) + `inspect`; geração atômica em diretório temporário e gravação de `indice.json` e `manifesto.json` (`hra/publicar_atlas_hra.py`).
- **Parâmetros:** `rotacao = [0,0,0]`, `escala = 1.0`, `translacao = [0.006095, -0.036276, -0.006798] m`.
- **Comandos para reproduzir:** `python hra/publicar_atlas_hra.py --reconstruir-local`

## 7. Critérios de sucesso (definidos antes da execução)
Preservação das 956 malhas e 7.756.626 triângulos, 0 `nome_pt` nulos, aprovação nas provas de landmarks, `EXT_meshopt_compression` obrigatório e integridade SHA-256.

## 8. Resultados
- **956 malhas**, **7.756.626 triângulos**, **67.996 MB** totais em **14 sistemas** (`arterial`: 55, `articular`: 16, `cardiaco`: 14, `digestorio`: 82, `esqueletico`: 117, `gestacional`: 8, `linfatico`: 16, `muscular`: 16, `nervoso`: 316, `respiratorio`: 70, `sensorial`: 46, `tegumentar`: 20, `urogenital`: 125, `venoso`: 55).
- Lateralidade: `left=349`, `right=336`, `null=271`. `nome_pt` nulos: `0`.

## 9. Validação
Provas de landmarks anatômicos (`left_leg[0] > 0 > right_leg[0]`, `breast[2] > spine[2]`, `eyes[1] > lowest_tibia_fibula[1]`), checagem de triângulos por sistema, `gltf-transform inspect` e conferência SHA-256.

## 10. Limitações
Esqueleto, músculos e vasos parciais (sem arquivos de pés no catálogo); 210 malhas sem ID de ontologia (`sem_ontologia: true`); nomes PT-BR pendentes de revisão médica.

## 11. Conclusão
- **Observado:** o pacote `hra-f/1.10-1` foi gerado com 956 malhas validadas geometricamente e em hashes, reduzido de 375 MB para 67,996 MB.
- **Interpretação:** `hra-f/1.10-1` atende ao contrato de dados do MVP, demandando complementação futura das estruturas esqueléticas/musculares ausentes.
- **Veredito da hipótese:** `sustentada`

## 12. Próximos passos
Investigar integração de malhas esqueléticas/musculares da coleção University of Denver ao referencial da TC/HRA (`EXP-0006` em diante).

## 13. Rastreabilidade
- **Commits:** `1e1389e`, `69f778f`, `a90cc45`, `8e9fe43`
- **Scripts:** `hra/analisar_hra.py`, `hra/publicar_atlas_hra.py`
- **Logs:** não documentado
- **Resultados / artefatos:** `hra/RELATORIO.md`, `hra/LICENCA_HRA.md`, `hra/catalogo_hra.csv`, `hra/nomes_pt_hra.csv`, `atlas/hra-f/1.10-1/`

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** pendente para revisão médica dos nomes PT-BR
- **Validação científica:** não documentado
- **Validação clínica:** não realizada
