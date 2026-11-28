# EXP-0023 — Investigação de referências anatômicas femininas independentes por região

## 1. Identificação
- **ID:** `EXP-0023`
- **Título:** Viabilidade de bases regionais de exames segmentados como referência feminina independente da Visible Human Female
- **Data:** `2026-11-27`
- **Responsável:** usuário (decisão), Claude Code (protocolo e revisão)
- **Agentes de IA:** Claude Code (protocolo e revisão), Antigravity e Codex (levantamento); fontes candidatas sugeridas pelo ChatGPT, não conferidas por ele
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** a preencher
- **Linha de pesquisa:** `LP01`
- **Situação:** `concluído — H23a sustentada (ossos); H23b não sustentada (músculos)`

## 2. Problema
O EXP-0021 (Frente B) mostrou que todos os dados femininos 3D abertos já levantados (HRA, Denver, NLM) vêm da mesma doadora, a Visible Human Female (VHF), e que as doadoras coreana e chinesa dependem de contrato. Sem uma referência feminina independente, qualquer adaptação de estruturas (Método A do plano V3) seria ajustada e validada contra a mesma mulher. O EXP-0021 buscou atlas completos; não buscou bases de exames clínicos já segmentados, que podem ter dezenas de mulheres diferentes.

## 3. Hipótese
- **H23a:** existe pelo menos uma base aberta com segmentação volumétrica dos **ossos da pelve e do membro inferior** de `≥ 10` mulheres distintas da VHF que serve como referência de validação regional.
- **H23b:** existe pelo menos uma base aberta com segmentação **individual de músculos do membro inferior** de `≥ 10` mulheres distintas da VHF.

H23b é a mais incerta: as bases de TC clínica costumam segmentar poucos músculos, ou nenhum individualmente.

## 4. Fundamentação teórica
Um atlas genérico não precisa coincidir com uma mulher específica. Precisa ficar dentro da variabilidade observada. Uma coorte de várias mulheres permite medir essa variabilidade (por exemplo, distância de superfície ou medidas pélvicas clássicas) e verificar se uma estrutura adaptada cai dentro dela. A Denver e a NLM continuam como referência de **ajuste**; a coorte serve só de referência de **validação**, o que pode exigir apenas licença de pesquisa, sem uso comercial.

## 5. Materiais e ambiente
Fontes candidatas (URLs fornecidas pelo usuário; a existência e o conteúdo de cada uma ainda precisam ser confirmados):

| # | Fonte | URL |
|---|---|---|
| S1 | TotalSegmentator Dataset V3 | https://zenodo.org/records/22688904 |
| S2 | VSDFullBodyBoneReconstruction | https://zenodo.org/records/8302449 |
| S3 | SAROS | https://www.nature.com/articles/s41597-024-03337-6 |
| S4 | Musculoskeletal CT Segmentation Dataset of Lower Limbs (artigo) | https://doi.org/10.1038/s41597-026-08630-0 |
| S4a | Dados associados — original | https://doi.org/10.22711/idr/1473 |
| S4b | Dados associados — preparado para IA | https://doi.org/10.22711/idr/1472 |

Outras fontes encontradas no caminho podem ser registradas em seção à parte, sem entrar no veredito.

**Restrições (pré-registradas):**
- Baixar só páginas, documentação e arquivos de metadados com `≤ 50 MB` cada. Nenhum volume de imagem, máscara ou malha.
- Não executar código das fontes. Não treinar redes. Não reconstruir.
- Não preencher campo sem URL comprobatória; o que não puder ser comprovado fica `não verificado`.
- Não contornar bloqueio de site nem formulário de acesso.
- Prazo: um dia útil, até o fim de `2026-11-28`.
- `hra-f/1.10-1`, EXP-0021 e EXP-0022 não são alterados.

## 6. Metodologia
Para cada fonte, preencher em `pesquisa/resultados/EXP-0023/fontes.md`, com URL comprobatória por campo:
1. Número de mulheres independentes (e de homens). Indicar se o sexo está nos metadados por caso.
2. Estruturas efetivamente segmentadas, com destaque para pelve, fêmur, tíbia, fíbula, patela, pé e músculos do membro inferior.
3. Disponibilidade de exames, máscaras volumétricas e malhas; forma de acesso (download direto, cadastro, formulário, contrato).
4. Resolução espacial (voxel/espessura de corte) e cobertura corporal (região do corpo incluída nos exames).
5. Presença de patologias, implantes ou alterações anatômicas relevantes.
6. Licença, separadamente para: pesquisa; transformação (obra derivada); redistribuição; uso comercial.
7. Uso possível como referência independente de validação (sim/não/parcial, com motivo).
8. Custo para um experimento regional: tamanho do download necessário, se dá para baixar só um subconjunto (só mulheres, só a região) e processamento estimado na CPU local.

Se houver arquivo de metadados pequeno (`≤ 50 MB`, por exemplo `meta.csv`), contar as mulheres a partir dele e registrar o hash SHA-256.

## 7. Critérios de sucesso (definidos antes da execução)
- **D1 — Completude:** os 8 campos de S1–S4 (S4a/S4b dentro de S4) preenchidos com URL comprobatória ou `não verificado`.
- **D2 — Suficiência de uma fonte como referência de validação regional.** Atende se cumprir **todos**:
  - (a) `≥ 10` mulheres distintas da VHF, com sexo por caso nos metadados;
  - (b) máscaras volumétricas ou malhas da região: para H23a, pelo menos ossos do quadril e fêmur; para H23b, pelo menos 5 músculos do membro inferior segmentados individualmente;
  - (c) resolução `≤ 1,5 mm` nas três direções, ou no plano com corte `≤ 2 mm`;
  - (d) licença que permita pesquisa e transformação sem contrato institucional (uso comercial é registrado, mas não exigido para validação);
  - (e) subconjunto para o piloto obtido com `≤ 40 GB` de download e processável na CPU local.

Leitura:
- **H23a sustentada:** pelo menos uma fonte atende D2 para ossos.
- **H23b sustentada:** pelo menos uma fonte atende D2 para músculos.
- Uma fonte que só falha em (e) fica como `viável com custo`, não como `suficiente`.

**Regra de decisão (pré-registrada):**
- H23a e/ou H23b sustentada → propor um novo experimento de piloto regional do membro inferior, com a fonte como conjunto de validação. A decisão de iniciar fica com o usuário.
- Nenhuma sustentada → congelar a linha do atlas feminino e encaminhar a solicitação institucional de dados (KISTI/CVH) à futura parceria universitária.

## 8. Resultados
Levantamento por Antigravity (S1, S3; `fontes_S1_S3.md`) e Codex (S2, S4; `fontes_S2_S4.md`) em 2026-11-27. A revisão (Claude Code) refez as consultas decisivas e acrescentou dados (seção 9). Nenhum volume de imagem, máscara ou malha foi baixado.

| Fonte | Mulheres | Estruturas relevantes | Resolução | Licença dos dados | Acesso / tamanho |
|---|---|---|---|---|---|
| **S1** TotalSegmentator V3 (Zenodo 22688904, v3.0.0, 2026-09-10) | 823 exames `f` (685 de adultas); 325 de adultas com pelve/membro inferior no tipo de estudo; 200 desses com corte nativo `≤ 2 mm`; 58 desses sem patologia | quadril E/D, sacro, fêmur E/D; glúteos máx./méd./mín. e iliopsoas (sem tíbia, fíbula, patela, pé, músculos da coxa e da perna) | reamostrado a `1,5 mm` isotrópico | CC BY 4.0 | aberto; zip único de 37,42 GB; partes isoladas podem ser lidas por HTTP Range |
| **S2** VSDFullBodyBoneReconstruction (Zenodo 8302449) | 10 F completas + 3 F com ressalvas (sexo por ID na Tabela 1 do artigo) | quadril, sacro, fêmur, patela, tíbia, fíbula, ossos do pé (PLY + labelmaps); sem músculos | não verificada | CTs de origem CC BY-NC-SA; modelos MAT CC BY-NC-SA 4.0; campo de licença dos ZIPs vazio | aberto; ~7,7 GB para as 10 F |
| **S3** SAROS (TCIA) | 438 pacientes (450 séries), sexo por caso | só classes agregadas `bones` e `muscle` | corte 5 mm, anotação em 1 de cada 5 fatias | máscaras CC BY 4.0; imagens mistas (parte NC e parte restrita) | máscaras 87 MB; imagens ~103 GB |
| **S4a** Digital Chinese (DataON 1473) | 46 adultos, 92 membros; composição por sexo não verificada | STL de fêmur, patela, tíbia e fíbula; CT DICOM do quadril ao pé (e RM de joelho e pé) | `≥ 512²`, corte `≤ 1 mm` | CC BY 4.0 (página do DataON) | público; tamanho não verificado |
| **S4b** AI-ready (DataON 1472) | 10 F e 10 M (agregado); sexo por ID de caso não publicado | 31 ossos e 13 músculos por membro (reto femoral, semimembranoso, semitendinoso, bíceps femoral longo/curto, vasto, gastrocnêmio, tibiais anterior/posterior, fibulares longo/curto/terceiro, sóleo); glúteos excluídos | plano 0,496 mm; axial com espaçamento original de 0,7 mm | CC BY 4.0 (artigo e página do DataON); o artigo em si é CC BY-NC-ND | público; `images.zip` + `labels.zip`; tamanho não verificado |

**D1 — completude:** atendido. Os 8 campos das cinco entradas estão preenchidos com URL ou `não verificado`.

**D2 — avaliação final (revisor):**

| Fonte | (a) ≥10 F com sexo por caso | (b) estruturas | (c) resolução | (d) licença | (e) custo | Veredito |
|---|---|---|---|---|---|---|
| S1 — ossos | atende (200 exames; ver limitação de paciente) | atende (quadril + fêmur) | atende | atende | atende | **suficiente** |
| S1 — músculos | atende | não atende (4 músculos do quadril) | atende | atende | atende | insuficiente |
| S2 — ossos | atende (10) | atende | não verificado | atende para pesquisa (NC-SA) | atende (~7,7 GB) | provável; (c) pendente |
| S3 | atende | não atende | não atende | parcial | atende | insuficiente |
| S4a — ossos | não verificado | não atende (sem osso do quadril) | atende | atende | não verificado | insuficiente para o critério; útil para fêmur e perna |
| S4b — músculos | não verificado (sem sexo por ID) | provável (13 músculos; volume reconstituível empilhando as fatias axiais, não demonstrado) | atende | atende | não verificado | **inconclusivo** |

- **H23a: sustentada** (S1; S2 provável como segunda fonte, de doadores post-mortem distintos).
- **H23b: não sustentada** pelo critério pré-registrado. A única candidata real (S4b) falha em (a) por falta de sexo por caso e depende de verificação do empilhamento.

## 9. Validação
Conferência da revisão (Claude Code), feita diretamente:
- **S1:** API do Zenodo confirma título, versão 3.0.0, data 2026-09-10, CC BY 4.0 e um único arquivo de 37.415.622.057 bytes. O `meta.csv` (163.753 bytes, SHA-256 `b9ca9a5ce9407f9caad1d039c7574cba154efe93f3a5802bc1aed2e05a732922`) foi lido de dentro do zip remoto por HTTP Range (`extrair_meta_s1.py`), transferindo 35,9 MB (diretório central + o arquivo), dentro do limite de 50 MB. As contagens de mulheres são do revisor (`contar_s1_totalseg.py`); o Antigravity as havia deixado `não verificado`.
- **S3:** `contar_s3_saros.py` reexecutado; mesmos números (438 F / 444 M; 900 séries).
- **S2:** o DOI `8302448` citado no artigo é o DOI-conceito e redireciona para `8302449`; não há divergência (correção ao relatório do Codex). O espelho da VSD (Zenodo `8270365`) declara CC BY-NC-SA para os CTs; o campo de licença da API está vazio nos dois registros.
- **S4:** o PDF do artigo (11 páginas) confirma: 10 F / 10 M; CC BY 4.0 para 1472 e 1473; acesso sem solicitação manual; axial mantém o espaçamento original de 0,7 mm, ~1.291 fatias axiais por membro, e só foram excluídas fatias "só de fundo". As páginas do DataON abriram para o revisor (o Codex as registrou como bloqueadas) e confirmam CC-BY-4.0, status público e, no 1473, STL de fêmur, patela, tíbia e fíbula de 46 adultos.

Não houve validação anatômica humana.

## 10. Limitações
- Exames clínicos têm patologia, postura em decúbito e campo de visão variável; a coorte não é "anatomia normal".
- O `meta.csv` do TotalSegmentator identifica exames, não pacientes; a mesma mulher pode ter mais de um exame. O tipo de estudo indica a região, mas não garante máscara completa do fêmur.
- As máscaras do TotalSegmentator foram produzidas com apoio de modelo e revisão humana; não são segmentação manual pura.
- S2 é post-mortem; S4 é de população chinesa e S1 majoritariamente suíça: variação populacional não controlada.
- Metadados de sexo são administrativos; não há dado de paridade, que influencia a pelve.
- Verificação feita por agentes de IA lendo páginas públicas, com conferência da revisão nos pontos decisivos.

## 11. Conclusão
- **Observado:** existe referência feminina independente e aberta para os **ossos** da pelve e do fêmur (TotalSegmentator V3, CC BY 4.0, centenas de exames de mulheres; VSD como segunda fonte). Para **músculos** do membro inferior, a única base encontrada com segmentação individual (KISTI AI-ready) tem só 10 mulheres, sem sexo por caso, em fatias 2D.
- **Interpretação:** a crítica ao EXP-0021 se confirma para ossos: não é preciso o Visible Korean para validar pelve e fêmur. Para músculos, a lacuna continua, mas ficou menor e mais concreta.
- **Veredito:** H23a sustentada; H23b não sustentada (inconclusiva para S4b).

## 12. Próximos passos
Pela regra pré-registrada (H23a sustentada), propor ao usuário um experimento de piloto regional:
- validar ossos do quadril e fêmures do `hra-f` (e, se houver adaptação, do BP3D adaptado) contra a variabilidade de mulheres do TotalSegmentator V3, extraindo só os casos selecionados por HTTP Range;
- antes de usar S4b para músculos: obter o sexo por caso (Tabela 2 do artigo, `class_info.csv` ou contato com os autores) e verificar, em um caso, que as fatias axiais empilham sem lacunas.

A decisão de iniciar o piloto é do usuário. `hra-f/1.10-1` segue intacto.

## 13. Rastreabilidade
- `pesquisa/resultados/EXP-0023/fontes_S1_S3.md`, `fontes_S2_S4.md`
- Scripts: `extrair_meta_s1.py`, `contar_s1_totalseg.py`, `contar_s3_saros.py`, `metadados/contar_sexo.py`
- Metadados: `metadados/S1_totalsegmentator/meta.csv`, `metadados/S3_saros/*`, transcrições em `metadados/S2/` e `metadados/S4/`
- Versões: Python 3.14.4; pypdf (leitura do PDF do artigo S4).

## 14. Revisão
- **Revisor:** Claude Code (refez as consultas decisivas, contou as mulheres do S1, abriu o DataON e corrigiu a divergência de DOI do S2)
- **Revisão humana:** pendente
- **Validação científica:** não se aplica (levantamento de fontes)
