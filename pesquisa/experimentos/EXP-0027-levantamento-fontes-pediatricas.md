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
- **Situação:** `concluído — H27a sustentada (validação); H27b não sustentada (base do produto)`

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
Levantamento por Antigravity em 2026-11-27 (`pesquisa/resultados/EXP-0027/fontes.md`, `contar_p1_pediatrico.py`, `contar_p5_pediatrico.py`).

| Fonte | 0–1 (F/M) | 2–5 (F/M) | 6–11 (F/M) | 12–17 (F/M) | Formato | Licença | Uso |
|---|---|---|---|---|---|---|---|
| **P1** TotalSegmentator V3 | 12/9 | 46/54 | 70/74 | 10/11 | máscaras NIfTI, 117 estruturas | CC BY 4.0 | validação (3 faixas) |
| **P5** Pediatric-CT-SEG (TCIA) | 16/16 | 70/73 | 54/51 | 39/40 | TC + contornos RTSTRUCT de órgãos | CC BY 4.0 | validação (4 faixas) |
| **P2** ICRP 143/156 | 1 modelo por idade e sexo (RN, 1, 5, 10, 15 anos) | | | | voxel e malha | copyright ICRP; transformação, redistribuição e uso comercial só com permissão escrita | nenhum sem permissão |
| **P3** UF/NCI | 10 de referência + 362 por porte | | | | híbrido | acordo de transferência; comercial exige licença do NCI | pesquisa não comercial sob acordo |
| **P4** XCAT pediátrico | 10 de referência | | | | — | contrato com a Duke | nenhum sem contrato |

Fora do escopo do veredito: Stanford Pediatric Whole-Body CT (358 TCs, 0–16 anos, 117 estruturas), acesso por termo de uso não comercial; não verificado pelo revisor.

- **P-D1:** atendido.
- **H27a: sustentada.** P1 e P5 têm `≥ 10` crianças por sexo em pelo menos duas faixas, com segmentação volumétrica e CC BY 4.0.
- **H27b: não sustentada.** Os modelos pediátricos por idade (ICRP, UF/NCI, XCAT) existem, mas nenhum permite transformação e uso comercial sem permissão ou contrato.

## 9. Validação
Conferência do revisor (Claude Code):
- P1: `contar_p1_pediatrico.py` reexecutado; mesmos números. A cobertura corporal dos exames pediátricos (277 de 286 sem `study_type`) continua pendente.
- P5: página do TCIA confirma 359 sujeitos, 359 estudos, CC BY 4.0, acesso público, 65,69 GB; `contar_p5_pediatrico.py` reexecutado (179 F / 180 M). A lista de estruturas (incluindo ossos e cabeça femoral) não foi conferida pelo revisor.
- P2–P4: licenças conferidas só pelo relatório do agente.

## 10. Limitações
- Levantamento por agente de IA em páginas públicas, com conferência por amostragem.
- Exames pediátricos clínicos têm patologia e protocolos de baixa dose; P1 tem corte mediano de 2,5 mm.
- P5 cobre tórax, abdome e pelve, não o corpo inteiro.

## 11. Conclusão
- **Observado:** há referência aberta e comercialmente utilizável para **validar** anatomia infantil em todas as faixas (TotalSegmentator V3 e Pediatric-CT-SEG). Não há **geometria pediátrica pronta** com licença para o produto.
- **Interpretação:** um atlas pediátrico teria de ser construído (por exemplo, pelo método em teste no EXP-0025) ou licenciado (ICRP, NCI, Duke).
- **Veredito:** H27a sustentada; H27b não sustentada.

## 12. Próximos passos
- Pela regra pré-registrada, nenhuma reconstrução pediátrica antes de resultado positivo no método feminino (EXP-0024/EXP-0025).
- Opção comercial a decidir pelo usuário no futuro: pedir permissão à ICRP para os modelos em malha da Publicação 156.

## 13. Rastreabilidade
- `pesquisa/resultados/EXP-0027/fontes.md`, `contar_p1_pediatrico.py`, `contar_p5_pediatrico.py`, `metadados/`.

## 14. Revisão
- **Revisor:** Claude Code (reexecutou as contagens e conferiu P5 na página do TCIA)
- **Revisão humana:** pendente
- **Validação científica:** não se aplica (levantamento de fontes)
