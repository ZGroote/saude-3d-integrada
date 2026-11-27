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
- **Situação:** `planejado`

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
A preencher.

## 9. Validação
A preencher.

## 10. Limitações
- Exames clínicos têm patologia, postura em decúbito e campo de visão variável; a coorte não é "anatomia normal".
- Metadados de sexo podem estar ausentes ou ser autodeclarados.
- Verificação feita por agentes de IA lendo páginas públicas; erros de leitura são possíveis e a revisão confere por amostragem.

## 11. Conclusão
A preencher.

## 12. Próximos passos
A preencher.

## 13. Rastreabilidade
- `pesquisa/resultados/EXP-0023/fontes.md` (a criar).

## 14. Revisão
- **Revisor:** Claude Code
- **Revisão humana:** pendente
- **Validação científica:** não se aplica (levantamento de fontes)
