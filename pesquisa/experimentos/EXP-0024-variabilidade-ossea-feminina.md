# EXP-0024 — Caracterização da variabilidade óssea feminina (pelve e fêmur proximal) no TotalSegmentator V3

## 1. Identificação
- **ID:** `EXP-0024`
- **Título:** Faixas de variação feminina da pelve e do fêmur proximal e plausibilidade dos atlas atuais
- **Data:** `2026-11-27`
- **Responsável:** usuário (autorização do piloto), Claude Code (protocolo e revisão)
- **Agentes de IA:** Claude Code (protocolo e revisão), Codex 2 (execução); proposta de piloto discutida com o ChatGPT
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** a preencher
- **Linha de pesquisa:** `LP01`
- **Situação:** `planejado`

## 2. Problema
Até o EXP-0022, as geometrias femininas só eram comparadas com uma mulher (a doadora da Visible Human Female). O EXP-0023 mostrou que o TotalSegmentator V3 (CC BY 4.0) tem centenas de exames de mulheres com quadril, sacro e fêmur segmentados. Falta transformar isso em **faixas de variação** contra as quais qualquer pelve feminina do atlas (atual ou adaptada) possa ser julgada.

## 3. Hipótese
H24: com uma métrica que separa pelves masculinas de femininas, a pelve do `hra-f` (VHF) fica **dentro** da faixa feminina, e a pelve do `bp3d-m` fica **fora** dela.

## 4. Fundamentação teórica
A pelve é o osso com maior dimorfismo sexual (largura relativa, abertura superior, ângulo subpúbico). Uma referência populacional só serve para julgar plausibilidade se a própria métrica for capaz de separar homens de mulheres; por isso há um controle masculino. O alvo é um corpo feminino genérico plausível, não uma mulher específica.

## 5. Materiais e ambiente
- **Fonte:** TotalSegmentator V3, Zenodo `22688904`, `Totalsegmentator_dataset_v300.zip` (37.415.622.057 bytes), lido por HTTP Range com a mesma técnica de `pesquisa/resultados/EXP-0023/extrair_meta_s1.py`. Baixar **só** as máscaras `hip_left`, `hip_right`, `sacrum`, `femur_left`, `femur_right` de cada caso escolhido. Não baixar `ct.nii.gz`.
- **Metadados:** `pesquisa/resultados/EXP-0023/metadados/S1_totalsegmentator/meta.csv` (SHA-256 `b9ca9a5c…a732922`).
- **Armazenamento:** máscaras em `hra/externo/totalseg_v3/` (fora do git). No git, só IDs de caso, métricas e figuras.
- **Comparadores:** pelve e fêmures do `hra-f/1.10-1` e do `bp3d-m/4.0-1` (leitura apenas).
- **Ambiente:** CPU local; Python 3.14, trimesh 5.2.2, SciPy 1.18.1, nibabel 5.5.0, scikit-image 0.26.0.

## 6. Metodologia
**Seleção (determinística):**
1. Pool feminino: `gender == f`, idade `≥ 18`, `study_type` contendo `pelvis`, `lower limb`, `leg` ou `polytrauma`, `slice_thickness ≤ 2` (200 exames).
2. Pool primário: os 58 com `pathology == no_pathology`. Pool de extensão: os demais 142, excluindo `pathology` vazia ou `unclear` e `pathology_location` contendo `pelvis`, `bones` ou `extremity`.
3. Controle masculino: mesmos filtros com `gender == m` e `no_pathology` (77); sortear 20 com seed `240024`.
4. Baixar as máscaras do pool primário inteiro. Se, após o controle de qualidade, restarem menos de 30, completar com o pool de extensão em ordem sorteada (seed `240024`) até 30.

**Controle de qualidade (automático, antes de qualquer métrica):**
- Q1: quadril E, quadril D e sacro presentes e não vazios.
- Q2: nenhuma das três estruturas pélvicas toca a primeira ou a última fatia do volume (pelve truncada).
- Q3: cada fêmur com pelo menos 100 mm de extensão a partir do topo da cabeça, sem tocar a borda superior do volume; casos que falharem em Q3 entram na pelve, mas não no fêmur.
- Q4 (repetição de paciente): pares com distância média `< 1,0 mm` após alinhamento rígido da pelve são tratados como a mesma pessoa; fica só o primeiro em ordem de ID.
- Excluídos registrados com o motivo.

**Divisão:** sorteio (seed `240024`) de 10 casos femininos para **desenvolvimento** e o restante (`≥ 20`) para **validação**. Parâmetros de alinhamento e de extração de medidas são ajustados só no desenvolvimento e congelados (hash do script registrado) antes de tocar a validação.

**Superfícies:** marching cubes nas máscaras (espaçamento do NIfTI), pelve = união de quadril E + quadril D + sacro; fêmur proximal = 100 mm a partir do topo da cabeça ao longo do eixo principal do fêmur.

**Métricas:**
- **M1 — forma:** alinhamento por similaridade (rotação, translação, escala uniforme; ICP até 200 iterações, como no EXP-0022) e distância de superfície simétrica média e p95, em mm, no referencial do alvo.
- **M2 — tamanho:** tamanho de centróide (raiz da soma dos quadrados das distâncias dos vértices amostrados ao centróide) em mm, só para descrição (atlas e exames têm estaturas diferentes).
- **M3 — proporções (sem escala):** após alinhamento rígido a um gabarito do conjunto de desenvolvimento: largura da pelve / altura, largura / profundidade, e distância entre centros das cabeças femorais (ajuste de esfera na região da cabeça) / largura da pelve.

**Faixas:** para cada mulher da validação, M1 médio contra as demais mulheres da validação (leave-one-out). Faixa feminina = percentis 2,5–97,5 de cada métrica. Salvar em `faixas_femininas.json`.

**Comparadores:** `hra-f`, `bp3d-m` e cada homem do controle medidos contra todas as mulheres da validação (M1 médio) e por M3.

## 7. Critérios de sucesso (definidos antes da execução)
- **V0 — Amostra:** `≥ 30` mulheres após controle de qualidade (`≥ 20` na validação) e 20 homens.
- **V1 — Discriminação:** a métrica M1 separa homens de mulheres: AUC `≥ 0,80` usando o M1 médio contra as mulheres da validação como escore. Se V1 falhar, o experimento é inconclusivo para os comparadores (a faixa não discrimina sexo).
- **V2 — `hra-f`:** M1 médio dentro do p97,5 feminino, e cada proporção de M3 dentro de [p2,5; p97,5].
- **V3 — `bp3d-m`:** M1 médio acima do p97,5 feminino (controle positivo; esperado, não exigido).

Leitura: **H24 sustentada** se V0, V1, V2 e V3; **parcial** se V0, V1 e V2 sem V3; **rejeitada** se V1 vale e V2 falha; **inconclusiva** se V0 ou V1 falham.

## 8. Resultados
A preencher.

## 9. Validação
A preencher.

## 10. Limitações
- Exames clínicos em decúbito; "sem patologia" é o rótulo do dataset, não um laudo de normalidade.
- Máscaras do TotalSegmentator são geradas com apoio de modelo e revisão humana.
- Sem identificador de paciente; Q4 é uma aproximação.
- População majoritariamente de um centro suíço; sem dado de paridade.
- O fêmur de exames de pelve costuma estar truncado; só o fêmur proximal é avaliado.

## 11. Conclusão
A preencher.

## 12. Próximos passos
A preencher.

## 13. Rastreabilidade
- `pesquisa/resultados/EXP-0024/` (scripts, `casos.csv`, `faixas_femininas.json`, métricas, figuras).

## 14. Revisão
- **Revisor:** Claude Code
- **Revisão humana:** pendente
- **Validação científica:** não realizada
