# Hipóteses Científicas

| ID | Experimento | Linha | Hipótese resumida | Situação |
|---|---|---|---|---|
| H01 | `EXP-0001` | LP01 | É possível reconstruir malhas 3D leves por camada anatômica diretamente de segmentações do TotalSegmentator para visualização web. | **Sustentada** |
| H02 | `EXP-0002` | LP01 | Os 2.234 objetos do BodyParts3D 4.0 podem ser classificados nos 15 sistemas anatômicos pela árvore FMA + revisão manual. | **Sustentada** |
| H03 | `EXP-0003` | LP01 | Um ajuste global de similaridade alinha o BodyParts3D ao caso tomográfico `s1371` com precisão suficiente para fusão anatômica direta. | **Rejeitada** (erro médio 36,5 mm, máx. 86,2 mm) |
| H04 | `EXP-0004` | LP02 | Quantização de 16 bits + `EXT_meshopt_compression` reduz substancialmente o tamanho dos GLBs preservando 100% dos nós, extras e triângulos. | **Sustentada** |
| H05 | `EXP-0005` | LP01 | O conjunto HRA United Female v1.10 (956 malhas) pode ser empacotado com licença CC BY 4.0, nomes PT-BR e hashes SHA-256 no contrato de atlas. | **Sustentada** |
| H06 | `EXP-0006` | LP01 | Limiarização por intensidade na TC da Denver recupera e valida o deslocamento STL→TC. | **Rejeitada** (TC sem HU, resposta em platô) |
| H07 | `EXP-0007` | LP01 | Busca conjunta por bordas (Otsu 3 classes) encontra pico estreito de alinhamento STL→TC na Denver. | **Rejeitada** (sem pico estreito, macro 19,888%) |
| H08 | `EXP-0008` | LP01 | O pipeline de ICP (rígido, similaridade, anisotrópico) e leitor GLB recuperam transformações conhecidas em dados sintéticos. | **Sustentada** (validação sintética) |
| H09 | `EXP-0009` | LP01 | Calibração por histograma da TC da Denver permite segmentação óssea válida pelo TotalSegmentator em GPU de 4 GB. | **Rejeitada** (ossos falharam) |
| H10 | `EXP-0010` | LP01 | A TC original da NLM (com cabeçalhos GE completos) segmentada em blocos craniocaudais com `--fast` atinge os critérios anatômicos mínimos. | **Em execução** (`--fast` passou no critério) |
| H11 | `EXP-0011` | LP01 | ICP rígido nos fêmures e pelve alinha os STLs da Denver à TC da NLM com erro médio `< 3 mm` no sacro (*holdout*). | **Em execução** (Etapa A reprovou: sacro 3,990 mm / p95 10,845 mm) |
| H12 | `EXP-0012` | LP01 | A integração multimodal (TC + RM + máscaras Denver) aumenta a cobertura anatômica sem comprometer a precisão geométrica (`< 3 mm`). | **Planejada** (viabilidade avaliada: ganho limitado a `intervertebral_discs`/`brain`; priorizar Método A só TC) |
| H13 | `EXP-0013` | LP01 | Existem fontes, métodos e ferramentas abertas (compatíveis com uso comercial mediante atribuição) que podem reduzir os gargalos G1–G5. | **Planejada** (levantamento de existência/licenças concluído; eficácia em aberto até execução) |
