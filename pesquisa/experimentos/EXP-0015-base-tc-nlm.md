# EXP-0015 — Atlas feminino com base na TC da NLM (inversão de base)

> **PROTOCOLO PRÉ-REGISTRADO:** Registrado **ANTES** da execução (`2026-11-26 ~01:50`, registro em `2026-11-26T01:45:53-03:00`).

## 1. Identificação
- **ID:** `EXP-0015`
- **Título:** Atlas feminino com base na TC da NLM (inversão de base)
- **Data e hora de registro:** `2026-11-26T01:45:53-03:00` (previsto `2026-11-26 ~01:50`)
- **Responsável:** Coordenador do projeto
- **Agentes de IA:** Antigravity (documentação); consultoria externa (ChatGPT)
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** não aplicável (pré-execução)
- **Linha de pesquisa:** `LP01`
- **Situação:** `executado parcialmente; nao aceito nesta rodada`

## 2. Problema
No `EXP-0014` (rodada real, commit `5ec1c34`), a tentativa de usar o HRA como corpo base foi **NÃO ACEITA**: o HRA remodelado por ilustradores diverge na pelve, pernas e coluna lombar (joelho `23–25 mm`, cabeça do fêmur à pelve HRA `17–21 mm`, `32/164` fora da pele HRA aberta, `28/164` sobreposições), enquanto **Denver ↔ TC NLM** (mesma doadora e mesmo exame) encaixa em `~3–4 mm`. A consultoria externa (ChatGPT) aprovou a inversão de base, vetou deformação não rígida global e sugeriu um teto de **5 dias úteis**.

## 3. Hipótese
Usando a **TC da NLM como corpo base** (`TotalSegmentator 'total' + 'body'`) com as **pernas da Denver** e **somente os complementos do HRA por ajuste local**, o atlas feminino passa no protocolo do `EXP-0014` sem afrouxar critérios.

## 4. Fundamentação teórica
Registro intramodal/cadavérico de mesma doadora (Denver STLs ↔ TC NLM) como estrutura anatômica primária, complementado por ajuste regional local (similaridade local e, apenas se falhar, deformação não rígida estritamente local e preservadora de volume) para estruturas não segmentadas na TC.

## 5. Materiais e ambiente (previstos)
- **Datasets e versões:**
  - TC original da NLM (`hra/nlm/bruto/tc_nlm_1p5.nii.gz`) segmentada com `TotalSegmentator 'total'` (`hra/nlm/bruto/saida/`) e `'body'`.
  - Modelos STL da University of Denver (`CC BY 4.0`, membros inferiores).
  - Complementos selecionados do HRA `v1.10` (`atlas/hra-f/1.10-1/`).
- **Licenças:** Denver `CC BY 4.0`; TotalSegmentator `'total'` sob `Apache-2.0`; **licença da task `'body'` do TotalSegmentator a confirmar no README oficial antes de usar — se não for aberta, PARAR e reportar**; Termos NLM (crédito NLM).
- **Hashes:** SHA-256 dos insumos, scripts, manifesto, avaliação e todos os STL registrados em `atlas/hra-f/2.0-1/proveniencia_sha256.json`.
- **Hardware:** não documentado.
- **Sistema operacional:** Windows.
- **Bibliotecas e versões:** `TotalSegmentator 2.18.0`, Python (`numpy`, `trimesh`, `nibabel`, `scikit-image`).
- **Seed:** a definir na execução.

## 6. Metodologia
### Fontes por estrutura (regra de fonte única)
- **Pele / superfície:** `TotalSegmentator` task `'body'` (com verificação prévia obrigatória de licença aberta no README oficial).
- **Esqueleto, órgãos, grandes vasos:** `TotalSegmentator 'total'` em resolução normal (`hra/nlm/bruto/saida/`).
- **Membros inferiores (ossos, músculos, cartilagens, ligamentos):** University of Denver, usando a transformação da Etapa A (`Denver → TC NLM`).
- **Somente do HRA:** útero, ovários, tubas, mama (glândula, lóbulos, ductos) e cérebro detalhado (Allen) — por **ajuste LOCAL por região**:
  - **Pelve:** âncoras em quadris, sacro e bexiga.
  - **Tórax:** âncoras em esterno, costelas e pulmões.
  - **Crânio:** âncoras em crânio/cérebro do TotalSegmentator.
  - Deformação não rígida **apenas local e preservadora de volume**, somente se a similaridade local falhar (deformação não rígida global vetada).
- **Placenta / âmnio / cordão:** camada gestacional separada (não entra no corpo base).

### Governança e prazo
- **Teto de esforço:** **5 dias úteis**. Se não passar até lá: congelar o que passou, marcar o restante como lacuna e voltar ao MVP clínico.
- **Saída prevista:** `atlas/hra-f/2.0-1` (nome do atlas a decidir: como o corpo deixa de ser HRA, propor **`vhf-f`**).
- **Comandos para reproduzir:** a definir na execução.

## 7. Critérios de sucesso (os MESMOS do EXP-0014, sem alteração + checagem pélvica)
- **Critérios geométricos (distância de superfície simétrica):**
  - Pele / superfície: média `≤ 10 mm`
  - Ossos grandes (fêmur, pelve, sacro+cóccix), órgãos grandes, músculos grandes: média `≤ 5 mm` e `p95 ≤ 12 mm`
  - Vértebras e grandes vasos: média `≤ 3 mm`
  - Pequenos vasos e nervos: avaliação individual
- **Critérios funcionais:**
  - **F1 — Contenção:** `≥ 99%` dos vértices dentro da pele `'body'` (agora malha fechada).
  - **F2 — Articulações:** quadril pela cabeça do fêmur Denver ao acetábulo do quadril do TotalSegmentator `≤ 5 mm`; joelho `≤ 5 mm`; costelas–vértebras `≤ 5 mm`; crânio–`C1` `≤ 5 mm`.
  - **F3 — Sobreposição:** `< 2%` do volume próprio invadindo órgãos/ossos.
  - **F4 — Lateralidade:** correta (`esquerda`/`direita`) em todas as estruturas.
  - **F5 — Revisão humana:** capturas em 4 vistas aprovadas por uma pessoa.
- **Critério adicional específico para complementos pélvicos do HRA:**
  - Útero e ovários dentro da cavidade pélvica (**F1** em relação à pele e **F3** em relação aos ossos e à bexiga).

## 8. Resultados (execução em 2026-11-26)
- Conferência da licença: README oficial lista `body` sob “Openly available for any usage (Apache-2.0 license)”; trecho e URL registrados em `hra/vhf/LEIAME.md`.
- Implementados `hra/vhf/montar_base.py` e `hra/vhf/avaliar_base.py`; dependências sem instalação: execução com `C:\Python314\python.exe` (os pacotes geométricos não estão no venv `C:\Users\respawn\venvs\totalseg\Scripts\python.exe`).
- Geração final corrigida: 229 malhas no manifesto, em RAS mm, incluindo 122 Denver; sem decimação. 227/229 malhas são watertight (as exceções são esôfago e lobo superior esquerdo); a pele `body` é watertight. Deriva volumétrica máxima após correção uniforme: `2,46e-15` (erro numérico).
- **F1:** `2.396.767 / 2.451.108` vértices dentro da pele (`97,78%`; **FAIL** frente a `≥99%`). 196/228 estruturas individualmente atingem 99%; o critério global falha, com concentração dos escapes nas malhas Denver distais e em alguns músculos/cartilagens, além de úmeros TotalSegmentator. Avaliação por classificação em grade sólida de 3 mm.
- **F2 quadril:** cabeça femoral Denver ao vértice mais próximo da malha `hip` TotalSegmentator: esquerda `19,418 mm`, direita `17,911 mm` (**FAIL** como proxy; acetábulo não vem segmentado separadamente). Centro da cabeça aproximado pelo centroide da cartilagem femoral.
- **F2 joelho:** separação mínima fêmur–tíbia: esquerda `5,693 mm` (**FAIL**), direita `4,948 mm` (**PASS**); aproximação por distância entre vértices amostrados, não centro articular.
- **F2 costelas–vértebras:** `1/24` pares ≤5 mm; faixa observada `3,821–46,612 mm` (**FAIL**). Distâncias são estimativas superfície-vértices amostradas; a correspondência nível a nível requer revisão.
- **F2 crânio–C1:** `3,350 mm` (**PASS**, distância mínima amostrada).
- **F3:** não avaliado. A tentativa all-pairs de sobreposição volumétrica excedeu os recursos locais; nenhum resultado foi inferido.
- **F4:** `178/178` estruturas laterais concordam com o sinal de X em RAS (**PASS**); estruturas medianas excluídas.
- **F5:** pendente; nenhuma revisão humana/captura em 4 vistas.
- **Ambiente de montagem/avaliação:** Python 3.14.4; numpy 2.4.6; nibabel 5.5.0; trimesh 5.2.2; scikit-image 0.26.0; scipy 1.18.1. Sem instalação de pacotes; execução no Python local com dependências geométricas disponíveis.

- **Hashes SHA-256:** entradas (`total`, `body`, transformação Etapa A), manifesto e avaliação registrados em `atlas/hra-f/2.0-1/proveniencia_sha256.json`.

### 8.2 Diagn?stico de FOV, F1, F3 e costovertebral (2026-11-26)
Diagn?stico sem altera??o das malhas ou crit?rios; dados detalhados em `atlas/hra-f/2.0-1/diagnostico_EXP-0015.json`, script `hra/vhf/diagnosticar_base.py`.

#### Observa??es ? FOV e F1
Volume de 320?320?1156 voxels isotr?picos de 1,5 mm; limites RAS aproximados X/Y ?240 mm e Z ?1771,75 a ?37,75 mm. A m?scara `body` toca **1.607 voxels de superf?cie na face Z superior (cabe?a)** e **175 na face X positiva (bra?o esquerdo do paciente em RAS)**; nas outras quatro faces s?o zero. ?rea regional coincidente com a borda estimada em: cabe?a **2,68%**, bra?o esquerdo **0,197%**, bra?o direito/m?os/p?s **0%**. Estimativa usa ?rea da face por voxel (2,25 mm?) e ?rea regional da pele por amostragem uniforme. O p? fica a aproximadamente 2 mm do limite inferior, mas a m?scara n?o toca essa face. Regi?es s?o bins aproximados em coordenadas RAS, n?o labels anat?micos dedicados.

Os escapes dos h?meros localizam-se nos bra?os, sem coincidirem em geral com a borda: lookup no voxel `body` original encontrou 1.032 v?rtices externos no ?mero esquerdo (0 a ?3 mm do FOV) e 1.683 no direito (28 a ?3 mm). Nos p?s: falanges Denver E 9.544 externos (1.247 a ?3 mm da borda), D 14.151 (8.770 pr?ximos); extensor longo do h?lux E 2.033/59 e D 1.839/110. Nenhum v?rtice externo foi localizado na cabe?a ou m?os. O lookup regional usa o voxel `body` original e ? diagn?stico espacial; n?o substitui o F1 oficial, que classifica na pele fechada preenchida em grade de 3 mm, e por isso os contadores diferem.

#### Interpreta??o ? FOV e F1
O contato exato indica prov?vel corte da pele na cabe?a e bra?o esquerdo, fechados no STL por tampas artificiais. N?o h? evid?ncia de m?os cortadas. O p? n?o toca a borda, mas a proximidade inferior pode contribuir para os escapes distais. A maioria dos escapes dos ?meros n?o est? junto ao FOV; o corte n?o explica todos os escapes dos bra?os.

#### Observa??es ? F3
Dos **289 pares** com sobreposi??o amostrada ?2% em ao menos uma dire??o, volume foi estimado pela m?dia direcional (fra??o amostrada ? volume fechado), com at? 2.000 centros internos por estrutura e grade de 2 mm. Profundidade usa transformada Euclidiana de dist?ncia da grade alvo: **0 pares ?1,5 mm**, **24 entre 1,5?3 mm**, **265 >3 mm**. A grade quantiza a estimativa em 2 mm; n?o ? dist?ncia cont?nua entre tri?ngulos.

Top 20 por volume m?dio estimado (cm?):
| Estrutura A | Estrutura B | cm? | Maior fra??o | Profundidade |
|---|---|---:|---:|---|
| `total__iliopsoas_left` | `denver__muscle_psoasmajor__left` | 121.00 | 73.7% | penetration_gt_3mm |
| `total__brain` | `total__skull` | 111.63 | 13.8% | penetration_gt_3mm |
| `total__iliopsoas_right` | `denver__muscle_psoasmajor__right` | 111.49 | 73.8% | penetration_gt_3mm |
| `total__iliopsoas_left` | `denver__muscle_illiacus__left` | 101.50 | 68.8% | penetration_gt_3mm |
| `total__iliopsoas_right` | `denver__muscle_illiacus__right` | 78.36 | 59.7% | penetration_gt_3mm |
| `total__hip_right` | `denver__muscle_illiacus__right` | 42.13 | 33.2% | penetration_gt_3mm |
| `total__hip_left` | `denver__muscle_illiacus__left` | 40.78 | 28.7% | penetration_gt_3mm |
| `denver__muscle_vastusintermedius__right` | `denver__muscle_vastuslateralis__right` | 37.50 | 12.8% | penetration_gt_3mm |
| `denver__muscle_vastusintermedius__left` | `denver__muscle_vastuslateralis__left` | 32.49 | 11.8% | penetration_gt_3mm |
| `denver__muscle_gastrocnemiuslateral__left` | `denver__muscle_soleus__left` | 23.81 | 25.2% | penetration_gt_3mm |
| `denver__bone_femur__left` | `denver__muscle_vastusintermedius__left` | 23.53 | 7.1% | penetration_gt_3mm |
| `denver__muscle_gastrocnemiuslateral__right` | `denver__muscle_soleus__right` | 21.71 | 25.3% | penetration_gt_3mm |
| `total__liver` | `total__stomach` | 21.56 | 2.2% | intermediate_1_5_to_3mm |
| `total__hip_left` | `total__iliopsoas_left` | 17.89 | 7.8% | penetration_gt_3mm |
| `denver__muscle_sartorius__left` | `denver__muscle_vastusmedialis__left` | 17.74 | 17.2% | penetration_gt_3mm |
| `denver__muscle_sartorius__right` | `denver__muscle_vastusmedialis__right` | 16.64 | 15.3% | penetration_gt_3mm |
| `total__hip_right` | `total__iliopsoas_right` | 16.08 | 7.7% | penetration_gt_3mm |
| `denver__bone_femur__left` | `denver__muscle_vastusmedialis__left` | 16.05 | 5.5% | penetration_gt_3mm |
| `denver__bone_femur__right` | `denver__muscle_vastusintermedius__right` | 15.52 | 6.2% | penetration_gt_3mm |
| `total__hip_left` | `denver__muscle_obturatorinternus__left` | 15.41 | 32.9% | penetration_gt_3mm |

Top 20 por maior percentual direcional:
| Estrutura A | Estrutura B | Maior fra??o | cm? estimados | Profundidade |
|---|---|---:|---:|---|
| `denver__bone_tibia__left` | `denver__ligament_acl__left` | 100.0% | 2.99 | penetration_gt_3mm |
| `denver__bone_tibia__right` | `denver__ligament_acl__right` | 100.0% | 3.74 | penetration_gt_3mm |
| `total__lung_upper_lobe_right` | `total__rib_right_1` | 88.2% | 11.86 | penetration_gt_3mm |
| `denver__bone_intermediatecuneiform__right` | `denver__bone_phalanges__right` | 81.8% | 3.33 | penetration_gt_3mm |
| `total__lung_upper_lobe_right` | `total__rib_right_2` | 79.0% | 12.06 | penetration_gt_3mm |
| `denver__cartilage_talus__left` | `denver__muscle_flexordigitorumlongus__left` | 76.0% | 0.03 | penetration_gt_3mm |
| `total__iliopsoas_right` | `denver__muscle_psoasmajor__right` | 73.8% | 111.49 | penetration_gt_3mm |
| `total__iliopsoas_left` | `denver__muscle_psoasmajor__left` | 73.7% | 121.00 | penetration_gt_3mm |
| `total__aorta` | `total__brachiocephalic_trunk` | 69.9% | 1.66 | penetration_gt_3mm |
| `total__iliopsoas_left` | `denver__muscle_illiacus__left` | 68.8% | 101.50 | penetration_gt_3mm |
| `denver__bone_tibia__right` | `denver__cartilage_tibiamedial__right` | 67.2% | 2.73 | penetration_gt_3mm |
| `denver__bone_tibia__left` | `denver__ligament_pcl__left` | 64.7% | 2.48 | penetration_gt_3mm |
| `denver__bone_femur__left` | `denver__cartilage_femurhead__left` | 62.5% | 4.33 | penetration_gt_3mm |
| `denver__bone_tibia__right` | `denver__ligament_pcl__right` | 61.3% | 1.56 | penetration_gt_3mm |
| `total__iliopsoas_right` | `denver__muscle_illiacus__right` | 59.7% | 78.36 | penetration_gt_3mm |
| `denver__bone_femur__right` | `denver__cartilage_femurhead__right` | 59.0% | 7.38 | penetration_gt_3mm |
| `denver__bone_femur__left` | `denver__cartilage_pelvisacetabulum__left` | 57.8% | 1.17 | penetration_gt_3mm |
| `denver__bone_lateralcuneiform__left` | `denver__bone_phalanges__left` | 56.9% | 2.64 | penetration_gt_3mm |
| `denver__bone_fibula__left` | `denver__muscle_plantaris__left` | 56.8% | 1.15 | penetration_gt_3mm |
| `denver__bone_tibia__left` | `denver__muscle_flexordigitorumlongus__left` | 55.4% | 14.94 | penetration_gt_3mm |

#### Interpreta??o ? F3
A lista mistura colis?es prov?veis e interfaces esperadas (cartilagem/osso, ligamentos e m?sculos). Os pares >3 mm s?o prioridades de inspe??o; volumes e profundidades s?o estimativas amostradas. O crit?rio F3 n?o foi alterado.

#### Observa??es ? costelas e v?rtebras
Os labels TotalSegmentator s?o `rib_left/right_1?12` e `vertebrae_T1?T12`; n?o h? sublabels para cabe?a/colo costal, corpo, faceta ou processo transverso. A dist?ncia costela?T(i) e costela?proxy lateral do processo transverso (quartil lateral da superf?cie vertebral em |RAS-X|) praticamente coincidem. T1: E/D 7,4/3,8 mm. T2?T9: padr?o bilateral **8,6?14,5 mm**. T10: 17,2/22,9 mm; T11: 21,2/28,2 mm; T12: 28,9/46,6 mm (E/D). Para T2?T9 h? centenas a milhares de pontos costais a ?20 mm, mas quase nenhum a ?10 mm. Dados por n?vel, pontos RAS e pares T(i?1)/T(i) est?o no JSON.

#### Interpreta??o ? costelas e v?rtebras
O afastamento de ~10?14 mm ? sistem?tico bilateralmente entre m?scaras TotalSegmentator extra?das da mesma TC; a transforma??o Denver?TC n?o participa, favorecendo limita??o ou separa??o dos r?tulos da segmenta??o em vez de erro de transforma??o. Sem sublabels, n?o se prova que cabe?a/colo foi omitida; as malhas atuais n?o representam contato no complexo costovertebral.

## 9. Validação
Parcial e **não aceita** pelos critérios funcionais: F1 falha; F2 quadril proxy e joelho esquerdo falham; costelas–vértebras falham; F3 não avaliado; F5 pendente. Joelho direito, crânio–C1 e F4 passaram nas métricas exploratórias. Nenhum resultado é validação clínica.

## 10. Limitações
Dependência de confirmação prévia da licença aberta da task `'body'`, da qualidade do fechamento da malha de pele gerada e do prazo máximo de 5 dias úteis.

## 11. Conclusão
- **Observado:** licença `Apache-2.0` da task `body` confirmada; corpo-base foi exportado com fonte única, incluindo sacro/S1 TotalSegmentator e membros inferiores Denver.
- **Interpretação:** os resultados atuais não sustentam aceitação; F1 abaixo do limite e falhas em articulações/alinhamento costovertebral. O protocolo e limites não foram afrouxados.
- **Veredito da hipótese:** `não aceita nesta rodada; F3/F5 e quadril seguem lacunas`

## 12. Próximos passos
1. Investigar F1 e as separações funcionais que falharam sem deformação global.
2. Executar F3 com avaliação de sobreposição volumétrica por pares anatomicamente relevantes; resolver disponibilidade do acetábulo para o F2.
3. Obter revisão humana F5 em quatro vistas.

## 13. Rastreabilidade
- **Commits:** não aplicável (pré-execução)
- **Scripts:** `hra/vhf/segmentar_body.py`, `hra/vhf/montar_base.py`, `hra/vhf/avaliar_base.py`; matriz etapa A: `hra/alinhar/transformacoes.json`
- **Logs:** não aplicável
- **Resultados / artefatos:** `pesquisa/experimentos/EXP-0015-base-tc-nlm.md`

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** pendente
- **Validação científica:** pendente
- **Validação clínica:** pendente
