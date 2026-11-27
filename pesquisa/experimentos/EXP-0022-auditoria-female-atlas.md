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
- **Situação:** `concluído — hipótese sustentada; não serve de base`

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
Execução por Codex 2 em 2026-11-27, somente na CPU. O relatório completo está em `pesquisa/resultados/EXP-0022/RELATORIO.md`. Clone externo: HEAD `b0a20fa3a009ca5f6bfa07b7479312e04c862af2`. Nenhum script do clone foi executado.

- **Inventário:** confere com o declarado (3.004 malhas, 2.557 conceitos, 16 sistemas, 3.893.539 triângulos). Origem das malhas: 2.163 `BP3D_`, 552 `VH_F_`, 282 `Allen_` e 7 `Yao_`.
- **Transformações** (`proveniencia.csv`, uma linha por malha):
  - HRA v1.5: só translação em Y.
  - BodyParts3D: conversão mm→m, escala global `(0,95; 0,963; 0,95)` e deformações por região: pescoço e ombros, tórax, "cintura ampulheta", quadris, lordose e glúteos, braços, mama e virilha.
  - Todas: simplificação de ~22% dos triângulos por estrutura (meshoptimizer).

| Critério | Resultado | Veredito |
|---|---|---|
| C1 — proveniência | 3.004/3.004 com transformação atribuída. A execução marcou os 7 nós `Yao_` como sem fonte; a revisão os achou no catálogo do HRA (linfonodo, `VH_F_lymphatic_system`) | **Atendido** (após correção do revisor; o veredito original está preservado no relatório) |
| C2 — licença | HRA e BodyParts3D, ambos CC BY 4.0 | **Atendido** (idem) |
| C3 — pelve vs. NLM | Female Atlas: média 3,881 mm, p95 16,058 mm. `bp3d-m`: 5,251 / 14,038. Redução de 26,09% | **Não atendido** (p95 > 12 mm) |
| C4 — fêmures e L1–L5 | 10/19 comparações passam. L1–L3 falham para **todas** as fontes, inclusive o HRA da mesma doadora | **Não atendido** |
| C5 — funcionais | F1/F3 não verificáveis (pele e 2.001/2.163 malhas BP3D abertas); F2 só por aproximações; F4 1.705/1.705 | **Não atendido** |

**Análise pós-hoc** (registrada como tal; não altera critérios nem veredito). O ICP usou até 200 iterações e todas as execuções convergiram. Foram comparadas só as malhas BP3D deformadas pelo autor com as originais do `bp3d-m`, contra a NLM:
- (a) Ossos do quadril: Female Atlas média 5,078 mm, p95 14,253 mm. `bp3d-m`: 4,204 / 9,986. **A pelve deformada ficou 20,8% pior que a masculina original.**
- (b) Quadris + sacro: 5,830 / 15,670 contra 5,284 / 14,383, ou seja, 10,3% pior.
- (c) **70 estruturas duplicadas** entre as fontes:
  - a coluna inteira C1–L5 e o sacro aparecem como HRA e também como BP3D;
  - há 45 estruturas com o mesmo FMA nas duas fontes (por exemplo, veia cava inferior e veias hepáticas);
  - há também 2 sobreposições pai/fragmento.

## 9. Validação
Revisão por Claude Code:
- **Yao:** a ausência de fonte foi conferida contra `hra/catalogo_hra.csv`; os 7 nós estão lá e o C1/C2 foi corrigido.
- **Viés circular:** os fragmentos `VH_F_` vêm da mesma doadora da TC de referência. Por isso a análise pós-hoc isolou as malhas BP3D.
- **ICP:** a falta de convergência em 50 iterações foi refeita com 200 iterações na análise pós-hoc.
- **L1–L3:** falham também para a malha HRA da mesma doadora. Isso sugere um problema na referência (máscara ou postura), não no atlas, e torna C4 pouco discriminativo para as lombares altas.

Não houve validação anatômica humana.

## 10. Limitações
- A NLM é uma única doadora; "mais próximo dela" não significa "anatomia feminina típica".
- A TC da NLM pode cortar parte dos membros superiores (EXP-0015).
- Distâncias geométricas não substituem avaliação anatômica humana.
- O HRA female deriva da mesma doadora da TC da NLM, então a NLM não é referência independente para as malhas `VH_F_`.
- F1 e F3 não puderam ser medidos, porque a maioria das malhas é aberta.

## 11. Conclusão
- **Observado:**
  - O Female Atlas não passa em C3, C4 e C5.
  - A deformação "feminina" que o autor aplicou ao BodyParts3D **afastou** a pelve de uma pelve feminina real, em vez de aproximá-la.
  - A melhora aparente em C3 vem de fragmentos HRA da mesma doadora da referência.
  - O pacote ainda duplica 70 estruturas.
- **Interpretação:** é uma adaptação visual, não anatômica. Ela não serve de base para o Atlas Feminino V3. Também mostra que deformar por silhueta (cintura, quadris) não reproduz a morfologia pélvica feminina.
- **Veredito da hipótese:** H22 **sustentada** (C3 reprovado, e a análise pós-hoc vai na mesma direção).

## 12. Próximos passos
- Não usar o Female Atlas como base nem como fonte de geometria.
- No máximo, servir de referência de interface (explosão e busca).
- Qualquer adaptação de estruturas do BodyParts3D (Método A do plano V3) precisa de referência feminina real por região (pelve, tórax) e de validação independente da doadora do HRA.

## 13. Rastreabilidade
- **Scripts:** `pesquisa/resultados/EXP-0022/` (`auditar.py`, `medir.py`, `funcionais.py`, `gerar_artifacts.py`, `consolidar.py`) e `hra/externo/female-atlas/` (clone, fora do git).
- **Resultados / artefatos:**
  - `RELATORIO.md`, `resultados.json`, `metrics.json`, `functional.json`, `proveniencia.csv`, `inventory.json`, `referencial.json`;
  - `suplementar.json` e `suplementar_duplicadas.csv`;
  - `pelve_frente.png` e `pelve_de_cima.png`.
- **Versões:** Python 3.14.4, NumPy 2.4.6, trimesh 5.2.2, SciPy 1.18.1, nibabel 5.5.0. Seed de amostragem `220022`.

## 14. Revisão
- **Revisor:** Claude Code (corrigiu C1/C2, identificou o viés circular e pediu a análise pós-hoc)
- **Revisão humana:** pendente
- **Validação científica:** não realizada
