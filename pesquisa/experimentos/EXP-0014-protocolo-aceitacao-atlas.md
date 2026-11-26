# EXP-0014 — Protocolo de aceitação por finalidade para integração do atlas feminino (`hra-f`)

> **PROTOCOLO PRÉ-REGISTRADO:** Este protocolo foi definido **ANTES** da rodada com a segmentação em resolução normal (que ainda não rodou), em `2026-11-25T23:47:11-03:00`. Conforme a Regra 15 de `CLAUDE.md`/`AGENTS.md`, a mudança de critério é registrada explicitamente e o **`EXP-0011` permanece REPROVADO** no critério de `< 3 mm` que ele definiu.

## 1. Identificação
- **ID:** `EXP-0014`
- **Título:** Protocolo de aceitação por finalidade para integração do atlas feminino (`hra-f`)
- **Data e hora de registro:** `2026-11-25T23:47:11-03:00`
- **Responsável:** Coordenador do projeto (sugestão do usuário e consultoria)
- **Agentes de IA:** Antigravity (registro documental)
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** não aplicável (pré-execução)
- **Linha de pesquisa:** `LP01`
- **Situação:** `planejado`

## 2. Problema
No `EXP-0011` (segmentação `--fast`), o critério rígido único `< 3 mm` no sacro (*holdout*) reprovou a Etapa A (`3,990 mm`), bloqueando a Etapa B. Entretanto, um critério único indiferenciado não reflete a finalidade clínica/informacional de um atlas anatômico de referência nem distingue estruturas grandes, vértebras/grandes vasos e integridade funcional (contenção na pele, articulações e ausência de sobreposição).

## 3. Hipótese
A integração de fontes (`HRA` + `Denver` + `TotalSegmentator` em resolução normal) sob um protocolo estratificado por finalidade (critérios geométricos por classe anatômica e critérios funcionais F1–F5, com Plano B regional pré-registrado e regra de fonte única) produz um atlas feminino coerente e apto para localização clínica de referência.

## 4. Fundamentação teórica
Avaliação multi-critério de registro anatômico combinando distância simétrica de superfície (média e P95 por classe estrutural), métricas topológicas de contenção/interpenetração (F1–F3), consistência de lateralidade (F4) e inspeção visual em quatro vistas (F5).

## 5. Materiais e ambiente (previstos)
- **Datasets e versões:** `atlas/hra-f/1.10-1/`, modelos STL da University of Denver (`CC BY 4.0`, membros inferiores), e segmentação do `TotalSegmentator` (`total`, `Apache-2.0`) em resolução normal sobre a TC original da NLM (`hra/nlm/bruto/tc_nlm_1p5.nii.gz`).
- **Licenças:** `CC BY 4.0` (HRA / Denver), `Apache-2.0` (TotalSegmentator `total`), Termos NLM (crédito NLM).
- **Hashes:** a registrar após geração da segmentação em resolução normal.
- **Hardware:** `não documentado` (execução futura em CPU 64 GB RAM ou GPU em nuvem conforme `EXP-0013`).
- **Sistema operacional:** Windows / ambiente de execução da rodada.
- **Bibliotecas e versões:** Python (`numpy`, `trimesh`, `nibabel`, `scikit-image`).
- **Seed:** a registrar no script da rodada.

## 6. Metodologia
### Contexto da decisão
O `hra-f` é um atlas de **REFERÊNCIA** para localizar informação clínica, não um modelo individual para cirurgia (`4 mm` equivalem a `~0,24%` da altura corporal). A precisão exigida deve depender da finalidade. Os valores abaixo são **sugestões de engenharia PARA INVESTIGAÇÃO**, não tolerâncias clinicamente validadas — permanecem sujeitos à discussão com professores de medicina.

### Regra de fonte única
Cada estrutura do atlas final vem de **UMA** fonte (sem duplicar):
- **HRA:** pele, órgãos, coluna e o que já tiver.
- **Denver:** ossos, músculos, cartilagens e ligamentos dos membros inferiores (substituindo os equivalentes do HRA).
- **TotalSegmentator:** crânio, costelas, esterno, úmero, escápula, clavícula e grandes vasos que o HRA não tem.

### Plano B pré-registrado
Se o ajuste global (similaridade) falhar em alguma região, usar **ajuste por região** — **cabeça/pescoço**, **tórax**, **abdome/pelve**, **membros inferiores** — cada uma com sua similaridade ajustada nas âncoras da própria região, e verificar continuidade nas emendas (**F2**) e contenção (**F1**).

- **Comandos para reproduzir:** a definir quando a segmentação em resolução normal for concluída.

## 7. Critérios de sucesso (definidos ANTES da execução em resolução normal)

### Critérios geométricos (distância de superfície simétrica, após a transformação final)
- **Pele / superfície:** média `≤ 10 mm`
- **Ossos grandes (fêmur, pelve, sacro+cóccix), órgãos grandes, músculos grandes:** média `≤ 5 mm` e `p95 ≤ 12 mm`
- **Vértebras e grandes vasos:** média `≤ 3 mm`
- **Pequenos vasos e nervos:** avaliação individual

### Critérios funcionais (os mais importantes para o atlas)
- **F1 — Contenção:** `≥ 99%` dos vértices de ossos e músculos importados dentro da pele do HRA.
- **F2 — Articulações:** cabeça do fêmur a `≤ 5 mm` do acetábulo; costelas a `≤ 5 mm` das vértebras torácicas correspondentes; crânio a `≤ 5 mm` de `C1`.
- **F3 — Sobreposição:** estruturas importadas invadem órgãos/ossos do HRA em `< 2%` do próprio volume.
- **F4 — Lateralidade:** lateralidade correta (`esquerda`/`direita`) em todas as estruturas importadas.
- **F5 — Revisão humana:** capturas em 4 vistas (frente, costas, lados) aprovadas por uma pessoa.

## 8. Resultados
Planejado — a segmentação em resolução normal ainda não rodou.

## 9. Validação
Planejado — não executado.

## 10. Limitações
Os limiares geométricos e funcionais são critérios de engenharia para investigação e **não constituem tolerâncias clinicamente validadas** até avaliação por professores de medicina / especialistas.

## 11. Conclusão
- **Observado:** protocolo formalmente pré-registrado antes da execução em resolução normal; `EXP-0011` permanece **REPROVADO** no critério de `< 3 mm`.
- **Interpretação:** a estratificação por finalidade e os critérios F1–F5 permitem avaliar adequação de uso como atlas de referência sem mascarar o resultado prévio do `EXP-0011`.
- **Veredito da hipótese:** `em aberto`

## 12. Próximos passos
Executar a segmentação do `TotalSegmentator` em resolução normal (`1,5 mm`), aplicar o protocolo `EXP-0014` (e Plano B regional, se necessário) e discutir os limiares com professores de medicina.

## 13. Rastreabilidade
- **Commits:** não aplicável (pré-execução)
- **Scripts:** não aplicável
- **Logs:** não aplicável
- **Resultados / artefatos:** `pesquisa/experimentos/EXP-0014-protocolo-aceitacao-atlas.md`

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** pendente
- **Validação científica:** pendente
- **Validação clínica:** pendente (a discutir com professores de medicina)
