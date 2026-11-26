# EXP-0016 — Atlas feminino híbrido: pele e órgãos do HRA + esqueleto TC NLM/Denver

> **PROTOCOLO PRÉ-REGISTRADO:** registrado **antes** da execução (2026-11-26). Escolha do usuário na revisão F5 do `EXP-0015`: opção "híbrido".

## 1. Identificação
- **ID:** `EXP-0016`
- **Título:** Atlas feminino híbrido (pele/órgãos HRA + esqueleto `vhf-f`)
- **Responsável:** Coordenador do projeto (decisão do usuário; protocolo pelo Claude coordenador)
- **Agentes de IA:** Claude (protocolo), Codex (execução)
- **Branch:** `etapa-1-fundacao`
- **Linha de pesquisa:** `LP01`
- **Situação:** `planejado`

## 2. Problema
Na comparação F5 (`web/testes/capturas/f5/comparacao.html`), o corpo `vhf-f` (`EXP-0015`) tem esqueleto completo da doadora, mas pele com rosto real, braços cortados pelo campo da TC e degraus. O `hra-f` tem pele idealizada e completa e órgãos ricos (956 malhas), mas esqueleto remodelado que falhou no `EXP-0014`. A proposta é juntar a pele e os órgãos do HRA ao esqueleto da TC/Denver.

## 3. Hipótese
O esqueleto `vhf-f` (ossos e articular, TotalSegmentator + Denver), levado ao referencial do HRA pela similaridade global já calculada (Etapa B do `EXP-0014`), fica contido na pele do HRA e não invade os órgãos do HRA, nos limites do `EXP-0014`.

**Risco conhecido antes de rodar:** o `EXP-0014` mediu a mesma interface (TC/Denver → HRA) e reprovou (F1 `32/164`, F3 `28/164`, fêmur `10–20 mm`, `L1–L5` `5,6–19,2 mm`). O que muda aqui é a regra de fonte: o esqueleto inteiro passa a vir de uma única doadora/exame, então as articulações internas não dependem do HRA.

## 4. Materiais
- `atlas/hra-f/1.10-1/` (HRA v1.10, CC BY 4.0): **pele** (sistema tegumentar, inclusive mama) e **todos os sistemas não esqueléticos**.
- `atlas/vhf-f/0.1-0/` (rascunho `EXP-0015`): somente sistemas **esqueletico** e **articular**.
- Transformação: `hra/alinhar/transformacoes.json`, `stage_b.similarity` (TC RAS mm → HRA RAS mm), e `stage_b.regional_registration` para a variante B.
- Conversão app ↔ RAS: `x_RAS = -x·1000`, `y_RAS = z·1000`, `z_RAS = y·1000`.

## 5. Metodologia
### Regra de fonte única
- Esquelético e articular: só `vhf-f`. Os 117 + 16 itens esquelético/articular do HRA saem.
- Todo o resto (pele, órgãos, vasos, nervos, músculos, gestacional, sensorial): só HRA, sem mudança.

### Variantes (só estas duas, nesta ordem)
- **A — global:** uma similaridade (`stage_b.similarity`) para todo o esqueleto.
- **B — regional:** só se A reprovar em F1 ou F3. As três matrizes de `stage_b.regional_registration.matrices_4x4` (`head_neck`, `thorax`, `abdomen_pelvis`), aplicadas por osso conforme a região. Os membros superiores seguem o tórax e os inferiores seguem abdome/pelve, porque não há matriz própria para eles; nenhuma matriz nova é ajustada. Continuidade nas emendas medida por F2.

Nenhuma deformação não rígida.

### Medidas
- **F1 — contenção:** % de vértices do esqueleto importado dentro da pele HRA. A pele HRA é aberta (`EXP-0014`), então é fechada por voxelização em grade de 3 mm + preenchimento de buracos (`scipy.ndimage.binary_fill_holes`) por fatia axial. Reportar o volume preenchido como checagem de sanidade.
- **F2 — articulações:** quadril, joelhos, costelas–vértebras e crânio–C1 herdados do `EXP-0015` na variante A (a similaridade global não muda distâncias relativas além da escala, que será reportada). Na variante B, medir de novo as emendas entre regiões.
- **F3 — sobreposição entre fontes:** pares osso `vhf-f` × órgão/estrutura HRA; invasão = fração ≥ 2% do volume próprio e profundidade > 3 mm (regra F3 v2, mesmas exclusões anatômicas do `EXP-0015`). Os pares de mesma fonte já reprovados no `EXP-0015` (133 Denver–Denver, 90 TotalSegmentator–TotalSegmentator) são herdados e não medidos de novo.
- **F4 — lateralidade:** como no `EXP-0015`.
- **F5 — revisão humana:** capturas nas 4 vistas × 3 modos, ao lado do `hra-f` atual, no formato de `web/testes/capturas/f5/`.

## 6. Critérios de sucesso (os do `EXP-0014`, sem alteração)
- F1 `≥ 99%`; F2 cada articulação `≤ 5 mm`; F3 `< 2%` (regra acima); F4 todas corretas; F5 aprovação humana.
- **Herança conhecida:** F2 costelas–vértebras e o F3 de mesma fonte já reprovaram no `EXP-0015`. Logo, **a aceitação formal completa é improvável antes da execução**. O que este experimento decide é se a interface nova (esqueleto × pele/órgãos HRA) passa. O registro do resultado deve separar "interface nova" de "herdado".

## 7. Governança
- Dentro do teto de 5 dias úteis aberto pelo `EXP-0015` (2026-11-26 a 2026-12-02).
- Parada: se A e B reprovarem F1 ou F3 de interface, o híbrido é **não aceito**; preserva-se o registro e o usuário escolhe entre o corpo novo (`vhf-f` com rosto suavizado) ou manter o HRA.
- Saída: pacote `atlas/hib-f/0.1-0`, status `rascunho, nao publicado, nao aceito` até F5, no mesmo formato do `vhf-f/0.1-0` (SPEC §5.3, um GLB por sistema, `glb_leve` da pele reaproveitado do HRA). Sem publicação, sem uso em produção.
- Sem validação clínica em nenhum caso.

## 8. Resultados
_A preencher após a execução._

## 9. Rastreabilidade
- Protocolo: este arquivo (commit de registro).
- Scripts: `hra/hibrido/` (a criar).
