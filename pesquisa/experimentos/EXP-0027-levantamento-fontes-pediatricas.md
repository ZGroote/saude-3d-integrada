# EXP-0027 — Levantamento de fontes anatômicas pediátricas

## 1. Identificação
- **ID:** `EXP-0027`
- **Título:** Fontes abertas para atlas e referência anatômica pediátrica, por faixa etária e sexo
- **Data:** `2026-11-27`
- **Responsável:** usuário (decisão de abrir em paralelo), Claude Code (protocolo e revisão)
- **Agentes de IA:** Claude Code (protocolo e revisão), Antigravity (levantamento)
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** a preencher
- **Linha de pesquisa:** `LP01`
- **Situação:** `planejado`

## 2. Problema
O MVP não tem atlas pediátrico: o prontuário infantil é estruturado, sem corpo 3D, e nunca usa um corpo adulto no lugar (`SPEC-MVP.md`). Reduzir um atlas adulto não reproduz a anatomia infantil (proporções, placas de crescimento, ossos não fundidos, órgãos em proporção diferente). Antes de qualquer reconstrução, é preciso saber que fontes pediátricas existem, para que faixas etárias, e com que licença.

## 3. Hipótese
- **H27a:** existe pelo menos uma fonte aberta (sem contrato institucional) que serve como **referência de validação** para pelo menos duas das faixas 0–1, 2–5, 6–11 e 12–17 anos.
- **H27b:** existe pelo menos um conjunto de **malhas pediátricas por idade** cuja licença permite transformação e uso comercial, servindo como base de geometria do produto.

Expectativa registrada: H27a provável (o TotalSegmentator V3 tem 286 exames de menores de 18 anos); H27b improvável (modelos pediátricos de referência costumam ter acesso por pedido ou restrição de uso).

## 4. Fundamentação teórica
O mesmo raciocínio do EXP-0023: uma fonte pode servir só para validação (exige licença de pesquisa) ou como base do produto (exige transformação e uso comercial). Para crianças, a cobertura precisa ser avaliada por faixa etária, porque a anatomia muda com a idade.

## 5. Materiais e ambiente
Fontes candidatas (existência, conteúdo e licença a confirmar; outras encontradas no caminho podem ser registradas à parte):

| # | Fonte |
|---|---|
| P1 | TotalSegmentator V3, subconjunto pediátrico (Zenodo `22688904`; metadados já em `pesquisa/resultados/EXP-0023/metadados/S1_totalsegmentator/meta.csv`) |
| P2 | Modelos computacionais pediátricos de referência da ICRP (Publicação 143 e versões em malha, se existirem) |
| P3 | Série de modelos pediátricos híbridos da University of Florida / National Cancer Institute (UF/NCI) |
| P4 | XCAT pediátrico (Duke University) |
| P5 | Coleções pediátricas segmentadas do TCIA (por exemplo, "Pediatric-CT-SEG", se existir) |

**Restrições (pré-registradas):**
- Só páginas, documentação e metadados `≤ 50 MB` por arquivo. Nenhum volume de imagem ou malha.
- Não contornar login, formulário ou bloqueio; acesso por pedido é registrado como tal.
- Nenhum campo sem URL comprobatória; o resto fica `não verificado`.
- Prazo: um dia útil, até o fim de `2026-11-30`.

## 6. Metodologia
Para cada fonte, em `pesquisa/resultados/EXP-0027/fontes.md`, com URL por campo:
1. Indivíduos por faixa etária (0–1, 2–5, 6–11, 12–17) e sexo; se é um modelo de referência (um por idade) ou uma coorte.
2. Estruturas disponíveis (ossos, órgãos, músculos) e se há placas de crescimento/centros de ossificação.
3. Formato: malha, voxel ou máscara; resolução.
4. Forma de acesso (download direto, cadastro, pedido, contrato).
5. Licença separada: pesquisa; transformação; redistribuição; uso comercial.
6. Uso possível: base do produto, referência de validação, ou nenhum.
7. Para P1: cobertura corporal dos exames pediátricos (campo `study_type` está vazio em 277 de 286; verificar se o diretório do zip indica quais máscaras estão preenchidas, sem baixar volumes).

## 7. Critérios de sucesso (definidos antes da execução)
- **P-D1 — Completude:** os 6 primeiros campos de P1–P5 preenchidos com URL ou `não verificado`.
- **P-D2 — Referência de validação (H27a):** fonte com `≥ 10` indivíduos por faixa e sexo em pelo menos duas faixas, máscaras volumétricas ou malhas de ossos ou órgãos, e licença de pesquisa sem contrato.
- **P-D3 — Base do produto (H27b):** malhas por idade (pelo menos 3 faixas), cobrindo esqueleto e órgãos principais, com licença que permite transformação e uso comercial.

**Regra de decisão (pré-registrada):** a linha pediátrica só abre experimento de reconstrução depois que o método muscular/ósseo do atlas feminino (EXP-0024 e EXP-0025) tiver resultado positivo. Este levantamento apenas registra o que existe.

## 8. Resultados
A preencher.

## 9. Validação
A preencher.

## 10. Limitações
- Levantamento por agente de IA em páginas públicas, com conferência por amostragem.
- Exames pediátricos clínicos têm patologia e protocolos de baixa dose; ver resolução por caso.

## 11. Conclusão
A preencher.

## 12. Próximos passos
A preencher.

## 13. Rastreabilidade
- `pesquisa/resultados/EXP-0027/fontes.md` (a criar).

## 14. Revisão
- **Revisor:** Claude Code
- **Revisão humana:** pendente
- **Validação científica:** não se aplica (levantamento de fontes)
