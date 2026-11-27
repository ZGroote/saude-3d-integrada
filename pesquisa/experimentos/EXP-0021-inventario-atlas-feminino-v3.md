# EXP-0021 — Inventário comparativo bp3d-m × hra-f e levantamento de fontes para o Atlas Feminino V3

## 1. Identificação
- **ID:** `EXP-0021`
- **Título:** Inventário anatômico comparativo (lacunas femininas) e levantamento de fontes externas
- **Data:** `2026-11-27`
- **Responsável:** usuário (decisão de reabrir a linha), Claude Code (protocolo)
- **Agentes de IA:** Claude Code (protocolo e revisão), Codex (Frente A), Antigravity (Frente B); plano de origem redigido com apoio do ChatGPT
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** a preencher
- **Linha de pesquisa:** `LP01`
- **Situação:** `inconclusivo`

## 2. Problema
O atlas feminino do MVP (`hra-f/1.10-1`, 956 malhas) tem cobertura menor que o masculino (`bp3d-m/4.0-1`, 2.234 malhas). Os EXP-0014, 0015 e 0016 tentaram completar o corpo feminino com transformações globais/regionais e não foram aceitos. Antes de qualquer nova reconstrução, falta saber **exatamente quais estruturas faltam** no feminino e **quais fontes externas existem de fato**, com licença compatível.

## 3. Hipótese
H21: as lacunas do `hra-f` em relação ao `bp3d-m` (excluídas as estruturas exclusivamente masculinas) concentram-se em ossos e músculos do membro superior, vasos dos membros e nervos periféricos — como registrado de forma não quantitativa no estado do projeto em 2026-11-25.

## 4. Fundamentação teórica
O `bp3d-m` identifica malhas por FMA e o `hra-f` por UBERON. O UBERON publica referências cruzadas (`xref: FMA:…`) que permitem o cruzamento por ontologia; correspondência por nome e revisão manual cobrem o restante.

## 5. Materiais e ambiente
- **Datasets e versões:** `bodyparts3d/catalogo_bp3d.csv` (2.234 linhas, FMA), `hra/catalogo_hra.csv` (956 linhas, UBERON), `supabase/dados/bodysite_snomed.csv` (âncoras SNOMED→FMA/UBERON); UBERON `uberon-basic.obo` (versão e SHA-256 a registrar na execução).
- **Licenças:** BodyParts3D CC BY 4.0; HRA CC BY 4.0; UBERON CC BY 3.0.
- **Hardware / SO / bibliotecas:** a registrar na execução.

## 6. Metodologia

### Frente A — Inventário (Codex)
1. Para cada malha do `bp3d-m`, procurar a correspondente no `hra-f`, nesta ordem: (a) UBERON do HRA cujo `xref` aponta para o FMA da malha; (b) nome normalizado igual; (c) revisão manual. Registrar o método usado em cada linha.
2. Classificar cada malha do `bp3d-m` em exatamente uma categoria: `presente` (mesma estrutura e lado), `parcial` (estrutura pai/filha ou agrupamento diferente), `ausente`, `exclusivo_masculino`, `nao_mapeavel` (sem FMA ou sem correspondência decidível).
3. Classificar cada malha do `hra-f` como `presente_no_bp3d`, `exclusivo_feminino` ou `so_no_hra`.
4. Prioridade clínica: **P1** = estrutura referenciada em `bodysite_snomed.csv`; **P2** = demais ossos e órgãos; **P3** = o restante.
5. Matriz de cobertura por sistema × prioridade (contagens e porcentagens).

### Frente B — Fontes externas (Antigravity, só pesquisa)
Para cada fonte — Female Atlas (GitHub HiMahendraBeniwal/female-atlas), Visible Korean Female, Chinese Visible Human, HRA-VCCF, University of Denver (máscaras e exames), Visible Human Female da NLM (RM e criossecções) — registrar, **com URL da página que comprova cada item**: disponibilidade real para download, formato, quantidade de estruturas, origem dos dados, licença (uso, modificação, redistribuição, uso comercial), resolução, referencial e método de reconstrução. Item não comprovado = `não verificado`. Proibido contornar proteção contra robôs, preencher formulários de cadastro ou baixar conjuntos grandes.

## 7. Critérios de sucesso (definidos antes da execução)
- **A1:** 100% das 2.234 malhas do `bp3d-m` e das 956 do `hra-f` classificadas em exatamente uma categoria, com método registrado.
- **A2:** revisão por Claude Code de uma amostra aleatória de 50 classificações automáticas (seed registrada); concordância `≥ 90%`. Abaixo disso, o método de cruzamento é revisto e a falha é registrada.
- **A3:** H21 é considerada **sustentada** se as quatro categorias citadas (ossos do membro superior, músculos do membro superior, vasos dos membros, nervos periféricos) somarem `≥ 50%` das malhas `ausente` do `bp3d-m`; senão, **rejeitada**.
- **B1:** as 6 fontes têm todos os campos preenchidos com valor comprovado por URL ou `não verificado`.

Este experimento é descritivo: ele não aprova nem reprova nenhum atlas.

## 8. Resultados

### Rodada 1 (2026-11-27, Codex) — A2 reprovado
- UBERON `releases/2026-11-05`, SHA-256 `1F119822…1810A397` (`uberon_origem.txt`).
- **A1 atendido:** 2.234 malhas BP3D e 956 malhas HRA classificadas. BP3D: 250 `presente`, 13 `parcial`, 1.936 `ausente`, 18 `exclusivo_masculino` e 17 `nao_mapeavel`. HRA: 184 `presente_no_bp3d`, 58 `exclusivo_feminino` e 714 `so_no_hra`.
- **A2 reprovado: 43/50 = 86% (< 90%)** na revisão de Claude Code (`revisao_A2_rodada1.csv`). As 7 divergências têm três causas:
  - (a) os nomes dos nós do HRA (`VH_F_intervertebral_disk_of_third_lumbar_vertebra`, `Allen_fornix_L`) foram ignorados. Há 50 malhas com o rótulo genérico `skeletal system` e 210 sem rótulo;
  - (b) a relação parte/todo não foi usada (árvore brônquica segmentar × brônquio segmentar, giro do cíngulo × partes, ramo × veia porta);
  - (c) a lateralidade dos nós `Allen_*_L/_R` não foi lida.
- **A3 calculado, mas sem valor de conclusão:** 257/1.936 = 13,27%. Como o denominador vem de uma classificação reprovada em A2, H21 **não** é julgada nesta rodada.

### Rodada 2 — método revisto (registrado antes de executar)
Pela regra de A2, o cruzamento é refeito. Os critérios A1–A3 e B1 **não mudam**. Mudanças no método:
1. Usar também o nome do nó do HRA: sem o prefixo `VH_F_`/`Allen_`, com `_` trocado por espaço, e com `_L`/`_R` convertidos em lado.
2. A relação pai/filha (`part_of`/`is_a`) do UBERON e as xrefs FMA dos ancestrais definem a categoria `parcial`.
3. A revisão A2 usa uma nova amostra de 50 classificações automáticas (`random.seed(22)`).

### Rodada 2 (2026-11-27, Codex) — A2 reprovado
- BP3D: 288 `presente`, 277 `parcial`, 1.634 `ausente`, 18 `exclusivo_masculino` e 17 `nao_mapeavel` (arquivos `*_r2`).
- **A2 reprovado: 37/50 = 74%** (`revisao_A2_rodada2.csv`). As 13 divergências são quase todas relações parte/todo que o método não pegou:
  - tributária × veia hepática, parte do jejuno/íleo × jejuno/íleo, cúspides × valva pulmonar, núcleo × amígdala, giro orbital;
  - sinônimos (`supraparietal lobule` = lóbulo parietal superior);
  - grafia errada no HRA (`VH_F_jejenum`).
- A3 = 257/1.634 = 15,73%, sem valor de conclusão, pelo mesmo motivo da rodada 1.

### Rodada 3 — método revisto e regra de parada (registrados antes de executar)
1. Hierarquia parte/todo do lado BP3D pela própria ontologia FMA (`fma.owl`, OBO PURL; versão e SHA-256 a registrar). Os ancestrais `part_of`/`is_a` de cada FMA do BP3D, até 6 níveis, são comparados com os FMA do catálogo HRA e com as xrefs FMA dos UBERON do HRA. O mesmo vale na direção HRA→BP3D.
2. Sinônimos exatos e relacionados do UBERON e do FMA entram na comparação por nome.
3. Grafias erradas e casos que não se resolvem automaticamente entram em `decisoes_manuais.csv`, com justificativa.
4. Nova amostra A2 com `random.seed(23)`.
5. **Regra de parada:** se a rodada 3 também reprovar em A2, a Frente A é encerrada como `inconclusiva`. A matriz é então publicada só como estimativa, com a taxa de erro medida, e H21 não é julgada.

### Rodada 3 (2026-11-27, Codex) — A2 reprovado; regra de parada aplicada
- FMA `5.1.0`, SHA-256 `BEB3DC47…191194C3` (`fma_origem.txt`). Foram 20 decisões manuais (13 BP3D, 7 HRA), excluídas da amostra.
- BP3D: 243 `presente`, 998 `parcial`, 958 `ausente`, 18 `exclusivo_masculino` e 17 `nao_mapeavel`. HRA: 435 `presente_no_bp3d`, 54 `exclusivo_feminino` e 467 `so_no_hra`.
- **A2 reprovado: 43/50 = 86%** (`revisao_A2_rodada3.csv`). Os erros vão nas duas direções:
  - **excesso de correspondência:** a subida por `is_a`/`part_of` casa estruturas irmãs por um ancestral comum. Exemplos: costela × discos intervertebrais e esterno; disco de L1 × ossos do quadril. Isso explica os 950 casamentos hierárquicos, entre eles 104 artérias penduradas no tronco braquiocefálico;
  - **falta de correspondência** na direção HRA→BP3D: partes do hipocampo, do ventrículo lateral e da amígdala, e o quarto ventrículo, ficaram `so_no_hra`, embora o BP3D tenha o todo.
- **Frente A encerrada como `inconclusiva`.** H21 não é julgada. A3 estimado na rodada 3: 222/958 = 23,17%.

### Estimativa de lacunas (não é resultado aceito)
`pesquisa/resultados/EXP-0021/estimativa_lacunas.md` traz, por sistema, o intervalo de malhas ausentes entre a rodada 3 (que superestima correspondências) e a rodada 2 (que as subestima). Total: **958–1.634 de 2.199 malhas elegíveis (44–74%) sem equivalente no feminino**.
- Os intervalos estreitos, e portanto robustos, são:
  - muscular: 374–378 de 397 (94–95%);
  - esquelético: 158–210 de 244 (65–86%);
  - respiratório: 2–4 de 104;
  - endócrino: 8 de 11.
- Arterial (22–82%) e venoso (31–68%) seguem indeterminados.

### Frente B (Antigravity) — B1 atendido
`fontes.md` cobre as 6 fontes, com URL comprobatória em cada campo ou `não verificado`.
- **Utilizáveis sem permissão** (atribuição exigida):
  - Denver: CC BY 4.0, com máscaras originais de segmentação; só da pelve aos pés;
  - Visible Human Female da NLM: RM e criossecções sem licença desde 2019; sem segmentação;
  - HRA-VCCF: CC BY 4.0, só tabelas, sem malhas;
  - Female Atlas: auditado no EXP-0022, não serve de base.
- **Exigem acordo:**
  - Visible Korean: KISTI, relatório anual, contrato separado para uso comercial; 143 modelos 3D só da pelve;
  - Chinese Visible Human: contrato com a TMMU, termos não públicos.

## 9. Validação
Claude Code revisou 3 amostras aleatórias de 50 classificações (seeds 21, 22, 23), cada uma com justificativa por linha em `revisao_A2_rodada{1,2,3}.csv`. A revisão é de uma só pessoa (um agente de IA). Não houve revisão anatômica humana.

## 10. Limitações
- Correspondência por ontologia não garante equivalência geométrica (uma malha pode ser `presente` mas incompleta).
- A prioridade P1 reflete as âncoras já mapeadas, não uma priorização clínica validada.

- O cruzamento automático entre FMA e UBERON em nível de malha não chegou a 90% de concordância com nenhum dos três métodos. Subir pela hierarquia sem restringir o tipo de relação (só `part_of` direto, sem `is_a`) gera falsos positivos.
- A revisão A2 foi feita por um único revisor de IA.

## 11. Conclusão
- **Observado:**
  - Frente A inconclusiva: A2 reprovado com 86%, 74% e 86%.
  - Frente B concluída (B1).
  - Mesmo nas estimativas mais otimistas, o feminino não tem cerca de 95% dos músculos e 65–86% dos ossos do BP3D, e no total faltam entre 44% e 74% das malhas.
- **Interpretação:**
  - A paridade com o masculino exigiria principalmente musculatura (~375 malhas) e esqueleto (~160–210 malhas: mãos, pés, crânio).
  - Nenhuma fonte aberta encontrada tem essas estruturas femininas observadas. A única aberta com músculos femininos reais é a Denver, e só da pelve aos pés. A Visible Korean exige contrato e só tem a pelve em 3D.
- **Veredito da hipótese:** H21 `inconclusiva` (não julgada, pela regra de parada).

## 12. Próximos passos
- Se a linha continuar, um inventário aceitável precisa de outro método:
  - usar só `part_of` direto, nos dois sentidos;
  - revisar por sistema, começando pelo muscular e pelo esquelético, onde a lacuna é robusta;
  - ter revisão humana.
- A decisão de continuar o Atlas Feminino V3 é do usuário. Os insumos estão aqui e no EXP-0022.

## 13. Rastreabilidade
- **Scripts:** `pesquisa/resultados/EXP-0021/inventario.py`; as ontologias ficam em `hra/externo/uberon/` e `hra/externo/fma/` (fora do git, com SHA-256 registrado).
- **Resultados / artefatos:**
  - `inventario_bp3d*.csv`, `inventario_hra*.csv`, `matriz_cobertura*.md`;
  - `resultado_h21*.txt`, `amostra_revisao*.csv`, `revisao_A2_rodada{1,2,3}.csv`;
  - `decisoes_manuais*.csv`, `estimativa_lacunas.md`, `fontes.md`.

## 14. Revisão
- **Revisor:** Claude Code (amostra A2)
- **Revisão humana:** pendente
- **Validação científica:** não se aplica (inventário)
