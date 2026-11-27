# EXP-0022 — Auditoria técnica do Female Atlas externo (HiMahendraBeniwal/female-atlas)

## 1. Identificação
- **ID:** `EXP-0022`
- **Título:** Auditoria técnica do Female Atlas externo como candidato a base do Atlas Feminino V3
- **Data:** `2026-11-27`
- **Responsável:** usuário (decisão), Claude Code (protocolo)
- **Agentes de IA:** Claude Code (protocolo e revisão), Codex 2 (execução)
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** a preencher
- **Linha de pesquisa:** `LP01`
- **Situação:** `planejado`

## 2. Problema
O repositório declara 3.004 malhas e 2.557 conceitos em 16 sistemas, combinando HRA *female* v1.5 e BodyParts3D com "proporções morfológicas femininas" aplicadas pelo autor. É preciso saber se essa geometria serve como base anatômica ou se é apenas uma adaptação visual.

## 3. Hipótese
H22: o Female Atlas **não** traz anatomia feminina observada além da que já temos. Seu esqueleto e sua musculatura são o BodyParts3D (doador masculino) deformado por proporções estéticas, de modo que a pelve não fica mais próxima de uma pelve feminina real do que a pelve do BodyParts3D original.

Observações que motivam a hipótese, feitas antes da execução em `README.md` e `public/ATTRIBUTION.md` (commit remoto lido via API do GitHub em 2026-11-27):
- as fontes declaradas são as mesmas que já usamos;
- a adaptação é descrita em termos estéticos ("hourglass waist", "flared pelvic hips");
- houve simplificação com perda (meshoptimizer, 0,2% de erro relativo);
- o repositório tem 10 commits, todos de 2026-09-07.

## 4. Fundamentação teórica
A pelve feminina difere da masculina em forma (abertura superior, ângulo subpúbico, asas ilíacas), não só em escala. Uma deformação que imita a silhueta externa não reproduz essas diferenças.

## 5. Materiais e ambiente
- **Dados:** clone de `https://github.com/HiMahendraBeniwal/female-atlas` (hash do commit a registrar). Licença declarada: código MIT; dados CC BY 4.0. A referência feminina independente é a segmentação TotalSegmentator da TC original da Visible Human Female da NLM (`hra/nlm/bruto/saida/`, EXP-0010), que não foi usada pelo autor.
- **Comparador masculino:** `bp3d-m/4.0-1`.
- **Segurança:** o repositório é tratado como **dado não confiável**. Não se executa `npm ci`/`npm install` nem nenhum script dele; as malhas são lidas por scripts nossos (Python/trimesh e `hra/alinhar/decoder_glb.mjs` para meshopt).

## 6. Metodologia
1. **Proveniência:** ler `scripts/*.mjs|py` e documentar exatamente qual transformação foi aplicada a cada grupo (global, por eixo, por região, deformação livre) e de qual fonte vem cada malha.
2. **Inventário:** contar malhas e conceitos reais e comparar com os números declarados; cruzar com a matriz do EXP-0021 (se pronta), apontando o que ele tem e o `hra-f` não tem.
3. **Pelve (teste central):** alinhar por similaridade (escala uniforme) os ossos do quadril e o sacro de (a) Female Atlas e (b) `bp3d-m` à segmentação da NLM; distância de superfície simétrica (média e p95).
4. **Critérios do EXP-0014 no próprio Female Atlas:** F1 (contenção na pele dele), F3 (sobreposição entre estruturas), F4 (lateralidade); F2 (articulações quadril, costelas–vértebras, crânio–C1) medido nele.
5. **Ossos grandes vs. NLM:** fêmures, vértebras L1–L5 e costelas presentes na TC; média e p95 após similaridade.

## 7. Critérios de sucesso (definidos antes da execução)
O Female Atlas só é **candidato a base do V3** se cumprir **todos** os itens abaixo:
- **C1 — Proveniência:** a fonte e a transformação de 100% das malhas são reconstituíveis a partir dos scripts publicados.
- **C2 — Licença:** cada malha tem uma fonte CC BY 4.0 identificável. A atribuição pode ser reproduzida.
- **C3 — Pelve feminina:** a média de distância da pelve do Female Atlas à NLM é **menor** que a da pelve do `bp3d-m`, com redução `≥ 20%`, e a média absoluta é `≤ 5 mm`, com `p95 ≤ 12 mm` (critério de osso grande do EXP-0014).
- **C4 — Ossos grandes:** fêmures e vértebras com média `≤ 5 mm` e `p95 ≤ 12 mm` em relação à NLM.
- **C5 — Funcionais:** F1 `≥ 99%`, F2 `≤ 5 mm`, F3 `< 2%`, F4 100%, todos medidos no próprio Female Atlas.

Leitura do resultado:
- **H22 sustentada:** C3 falha.
- **H22 rejeitada:** C3 passa.
- Independentemente de C3, a falha de C1 ou C2 descarta o uso como base. Nesse caso o atlas ainda pode servir de referência de método.

## 8. Resultados
_A preencher._

## 9. Validação
_A preencher._

## 10. Limitações
- A NLM é uma única doadora; "mais próximo dela" não significa "anatomia feminina típica".
- A TC da NLM pode cortar parte dos membros superiores (EXP-0015).
- Distâncias geométricas não substituem avaliação anatômica humana.

## 11. Conclusão
_A preencher._

## 12. Próximos passos
_A preencher._

## 13. Rastreabilidade
- **Scripts:** `pesquisa/resultados/EXP-0022/` e `hra/externo/female-atlas/` (clone, fora do git)
- **Resultados / artefatos:** a preencher

## 14. Revisão
- **Revisor:** Claude Code
- **Revisão humana:** pendente
- **Validação científica:** pendente
