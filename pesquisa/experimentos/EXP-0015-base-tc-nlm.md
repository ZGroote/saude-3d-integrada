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

## 7.1 Pre-registro da Rodada 3 - definicao F3 v2 (2026-11-26, antes de recalcular)

Regra 15: mudanca explicita de definicao. F3 v1 e os numeros anteriores ficam preservados nas secoes historicas e no JSON de diagnostico, sem recalculo retroativo. F3 v2 avalia apenas pares sem relacao anatomica conhecida, conforme lista exata e versionada em hra/vhf/avaliar_base.py. Nos pares restantes, invasao exige fracao amostrada >=2% em ao menos uma direcao e profundidade estimada >3 mm. Os limites do EXP-0014 nao mudam.

Exclusoes F3 v2 a implementar por pares exatos:
- Parte-de: apendice atrial esquerdo/coracao; pares entre lobos do mesmo pulmao.
- Insercoes e superficies articulares: ligamentos ACL/PCL/MCL/LCL com ossos de insercao; cartilagens Denver com ossos de suporte; meniscos com tibia/femur se houver labels.
- Ramificacoes vasculares: aorta com troncos, carotidas, subclavias e iliacas; tronco braquiocefalico com carotida/subclavia direita; veia cava com tributarias; sistema porta com esplenica. Aplicar apenas a labels separados existentes.
- Cavidade craniana: cerebro/cranio.

Fonte unica: Denver fornece membros inferiores e cintura pelvica que constem no catalogo, incluindo pelve, sacro e coccix; fornece tambem gluteos e musculos pelvicos. TotalSegmentator fornece o restante e a pele body. A lista efetivamente removida sera registrada nos resultados. Sem complementos HRA, sem mudar limites e sem commit.

## 7.2 Plano registrado antes da analise e do pacote F5 (2026-11-26)

Sem mudanca de criterios: separar invasoes F3 v2 existentes em `mesma_fonte` (Denver-Denver e TotalSegmentator-TotalSegmentator) e `entre_fontes` (TotalSegmentator-Denver). Reportar todos os pares entre fontes que satisfazem a regra de invasao ja registrada, com volume e profundidade; nao criar novo criterio.

Gerar pacote local de revisao humana em `atlas/vhf-f/0.1-0`, sem publicacao: status explicito `rascunho, nao publicado, nao aceito`. Seguir SPEC-MVP.md secao 5.3; um GLB por cada um dos 16 sistemas de `bp3d-m`; coordenadas do app em metros: `x=-x_RAS`, `y=z_RAS`, `z=y_RAS` (mm para m); indice com campos `malha`, `estrutura:null`, `nome_en`, `nome_pt:null`, `sistema`, `lateralidade`, `glb`, `triangulos`, `fonte`. GLBs completos usam meshopt sem simplificacao. Pele recebe `glb_leve` simplificado por decimacao quadratica trimesh, alvo aproximado 40.000 triangulos. Incluir SHA-256 dos arquivos no manifesto. Mapeamentos de sistema e rotulos ficam rastreados no gerador. Reportar contagem de entradas e MB por sistema. Sem commit e sem instalar pacotes.

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

### 8.2 Diagnostico inicial de FOV, F1, F3 e costovertebral (Rodada 2)
Esta subseccao preserva os resultados da Rodada 2; nao deve ser substituida pelos valores da Rodada 3.

- F1 inicial: 2.426.192/2.480.533 vertices dentro (97,8093%). A mascara body tocava 1.607 voxels no limite superior da cabeca e 175 voxels na face RAS X positiva, no braco direito; estimativa regional 2,68% e 0,197%. As outras quatro faces sem contato. A localizacao dos vertices fora e aproximada; detalhes completos estao no diagnostico_EXP-0015.json da Rodada 2.
- F3 v1 Rodada 2: 2.137 candidatos por caixas; 74 pares com malha aberta excluidos; 541 com sobreposicao; 289 pares >=2%. Profundidade estimada em grade 2 mm: 0 <=1,5 mm, 24 entre 1,5-3 mm e 265 >3 mm. Esses numeros sao preservados; a Rodada 3 tem novo manifesto source-unique e seus proprios resultados na secao 8.3.
- F2 quadril na Rodada 2: folga superficial Denver femoral/cartilagem acetabular 0,019/0,025 mm; para superficie TotalSegmentator hip 0,038/0,097 mm. F2 joelho anterior: E 5,693 mm, D 4,948 mm. Cr?nio-C1 anterior: 3,350 mm.
- Costelas-T2 a T9 apresentavam gaps bilaterais em torno de 8,6-14,5 mm; o diagnostico identificou ausencia de sublabels para cabeca/colo costal e processo transverso e registrou limitacao provavel da segmentacao TotalSegmentator, nao da transformacao Denver.
- Interpretacao FOV/F1: contato na cabeca e braco direito e escapes nas malhas Denver distais; contacto do limite inferior com a mascara nao foi observado, embora os pes estejam proximos. F4 da Rodada 2 era 156/156 antes da correcao da classificacao dos ossos medianos.

## 8.3 Rodada 3 - resultados (2026-11-26)
Executada apos o pre-registro da secao 7.1, sem mudar limites do EXP-0014. Dados completos em atlas/hra-f/2.0-1/avaliacao_F1-F4.json e diagnostico_EXP-0015.json.

### Fonte unica
Manifesto: 229 malhas, 128 Denver, RAS mm. Denver acrescentou Bone Pelvis E/D, Bone Sacrum e Bone Coccyx. Excluidos da base 12 labels TotalSegmentator: hip E/D, iliopsoas E/D, sacrum, vertebrae_S1 e gluteus maximus/medius/minimus E/D. Os seis labels gluteais ja eram filtrados e nao tinham STL no manifesto anterior; seis STL antigos (hip E/D, iliopsoas E/D, sacrum, vertebrae_s1) foram removidos no rebuild. Denver fornece gluteos, iliacus, psoas major e estruturas inferiores selecionadas. Sacrum e Coccyx constam como Left no catalogo, mas sao medianos e ficam fora do denominador F4.

### F1 - contencao e localizacao
REPROVOU: 2.383.329/2.437.670 vertices dentro (97,7708%, limite >=99%). Pele body fechada. Distancia maxima ate o vertice de pele mais proximo para vertices classificados fora na grade solida de 3 mm. Regiao e bin RAS aproximado; borda indica vertices externos a <=3 mm do limite pelo lookup no voxel body original.

| Estrutura com escape | Fracao fora | Maximo fora (mm) | Regiao | Escape perto da borda |
|---|---:|---:|---|---|
| denver__ligament_lcl__left | 100.00% | 67.96 | foot/distal leg | no (0 <=3 mm) |
| denver__muscle_extensorhallucislongus__left | 100.00% | 52.33 | foot/distal leg | yes (59) |
| denver__muscle_extensorhallucislongus__right | 100.00% | 50.42 | foot/distal leg | yes (110) |
| denver__bone_phalanges__right | 74.03% | 36.79 | foot/distal leg | yes (8770) |
| denver__cartilage_tibiadistal__left | 100.00% | 34.76 | foot/distal leg | no (0 <=3 mm) |
| denver__muscle_plantaris__right | 69.21% | 28.81 | foot/distal leg | no (0 <=3 mm) |
| denver__bone_phalanges__left | 49.00% | 26.80 | foot/distal leg | yes (1247) |
| denver__muscle_flexordigitorumlongus__right | 6.94% | 25.56 | foot/distal leg | no (0 <=3 mm) |
| denver__muscle_extensordigitorumlongus__left | 77.82% | 24.71 | foot/distal leg | no (0 <=3 mm) |
| denver__bone_fibula__left | 43.39% | 19.70 | foot/distal leg | no (0 <=3 mm) |
| denver__ligament_lcl__right | 100.00% | 18.25 | other | no (0 <=3 mm) |
| denver__muscle_flexordigitorumlongus__left | 5.62% | 17.58 | foot/distal leg | no (0 <=3 mm) |
| denver__muscle_peroneuslongus__left | 42.22% | 15.68 | foot/distal leg | no (0 <=3 mm) |
| denver__ligament_mcl__right | 100.00% | 15.65 | foot/distal leg | no (0 <=3 mm) |
| denver__cartilage_tibiadistal__right | 61.56% | 11.00 | foot/distal leg | no (0 <=3 mm) |
| denver__cartilage_patella__right | 43.00% | 10.56 | patella/knee | no (0 <=3 mm) |
| denver__bone_cuboid__left | 29.29% | 9.98 | foot/distal leg | no (0 <=3 mm) |
| denver__muscle_extensordigitorumlongus__right | 35.61% | 9.41 | foot/distal leg | no (0 <=3 mm) |
| denver__bone_lateralcuneiform__left | 28.50% | 7.32 | foot/distal leg | no (0 <=3 mm) |
| denver__bone_medialcuneiform__right | 23.13% | 7.09 | foot/distal leg | no (0 <=3 mm) |
| denver__bone_intermediatecuneiform__right | 14.75% | 6.16 | foot/distal leg | no (0 <=3 mm) |
| denver__bone_calcaneous__left | 10.75% | 5.80 | foot/distal leg | no (0 <=3 mm) |
| denver__bone_lateralcuneiform__right | 9.10% | 5.21 | foot/distal leg | no (0 <=3 mm) |
| denver__cartilage_patella__left | 11.04% | 4.89 | patella/knee | no (0 <=3 mm) |
| denver__bone_fibula__right | 3.57% | 4.78 | foot/distal leg | no (0 <=3 mm) |
| denver__muscle_peroneuslongus__right | 7.14% | 4.62 | foot/distal leg | no (0 <=3 mm) |
| total__humerus_right | 7.42% | 4.57 | arm | yes (28) |
| denver__bone_cuboid__right | 5.19% | 4.46 | foot/distal leg | no (0 <=3 mm) |
| denver__bone_patella__right | 14.17% | 4.21 | patella/knee | no (0 <=3 mm) |
| total__humerus_left | 3.86% | 4.02 | arm | no (0 <=3 mm) |
| denver__bone_patella__left | 14.19% | 3.99 | patella/knee | no (0 <=3 mm) |
| denver__muscle_flexorhallucislongus__left | 3.93% | 3.37 | foot/distal leg | no (0 <=3 mm) |
| denver__cartilage_femurdistal__right | 0.51% | 3.06 | other | no (0 <=3 mm) |
| denver__bone_intermediatecuneiform__left | 0.94% | 2.47 | foot/distal leg | no (0 <=3 mm) |
| denver__muscle_tibialisanterior__right | 0.94% | 2.27 | other | no (0 <=3 mm) |
| denver__bone_navicular__right | 0.80% | 2.12 | foot/distal leg | no (0 <=3 mm) |
| denver__bone_tibia__right | 0.18% | 2.04 | foot/distal leg | no (0 <=3 mm) |
| denver__bone_talus__left | 0.29% | 1.74 | foot/distal leg | no (0 <=3 mm) |
| denver__bone_calcaneous__right | 0.30% | 1.64 | foot/distal leg | no (0 <=3 mm) |
| denver__bone_tibia__left | 0.02% | 0.90 | foot/distal leg | no (0 <=3 mm) |

A mascara body toca a borda superior na cabeca (2,68% da superficie regional estimada) e a face RAS X positiva no braco direito (0,197%). Nao toca nas faces das maos nem dos pes. Em RAS, X positivo corresponde ao lado direito. Escapes Denver distais ficam nos pes; falanges e extensor do halux tem parte dos vertices a <=3 mm do limite inferior. Humeros escapam nos bracos, mas quase todos longe da borda (28 vertices externos do humero direito e zero do esquerdo a <=3 mm). O lookup regional nao substitui a contagem F1 oficial.

### F3 v1 e F3 v2
F3 v1 - REPROVOU: 2.016 pares de caixas intersectantes (inclui abertos), 74 pares abertos sem volume avaliavel, 516 com alguma sobreposicao e 279 com fracao >=2%. O v1 anterior (289 pares >=2%) permanece preservado; a diferenca decorre do manifesto source-unique desta rodada.

F3 v2 - REPROVOU: lista EXP-0015-F3-v2.0 em hra/vhf/avaliar_base.py; 31 relacoes pre-listadas apareceram entre os candidatos e foram excluidas. Restaram 1.985 caixas elegiveis, incluindo 73 pares abertos; 492 pares com alguma sobreposicao, 256 com fracao >=2%. Profundidade pela distancia Euclidiana em grade de 2 mm: 19 pares <=3 mm e 237 invasoes >3 mm. Volume medio e media direcional (fracao amostrada x volume fechado); ate 2.000 pontos internos por estrutura. Estimativas de grade/amostragem.

Top 20 por volume medio estimado (cm3):
| Estrutura A | Estrutura B | cm3 | Maior fracao | Profundidade (mm) |
|---|---|---:|---:|---:|
| denver__bone_pelvis__left | denver__muscle_illiacus__left | 42.29 | 29.8% | 7 |
| denver__bone_pelvis__right | denver__muscle_illiacus__right | 39.83 | 29.6% | 9 |
| denver__muscle_vastusintermedius__right | denver__muscle_vastuslateralis__right | 37.14 | 13.8% | 6 |
| denver__muscle_vastusintermedius__left | denver__muscle_vastuslateralis__left | 33.08 | 11.2% | 4 |
| total__liver | total__stomach | 23.71 | 2.4% | 3 |
| denver__bone_femur__left | denver__muscle_vastusintermedius__left | 22.41 | 7.0% | 4 |
| denver__muscle_gastrocnemiuslateral__right | denver__muscle_soleus__right | 21.37 | 23.8% | 9 |
| denver__muscle_gastrocnemiuslateral__left | denver__muscle_soleus__left | 20.96 | 22.7% | 9 |
| denver__muscle_sartorius__right | denver__muscle_vastusmedialis__right | 17.91 | 17.3% | 11 |
| denver__muscle_sartorius__left | denver__muscle_vastusmedialis__left | 17.78 | 17.5% | 11 |
| denver__bone_femur__left | denver__muscle_vastusmedialis__left | 17.48 | 6.6% | 4 |
| denver__bone_femur__right | denver__muscle_vastusintermedius__right | 15.32 | 5.0% | 4 |
| denver__bone_tibia__left | denver__muscle_flexordigitorumlongus__left | 14.58 | 55.1% | 16 |
| total__costal_cartilages | total__liver | 13.61 | 7.9% | 9 |
| denver__bone_femur__right | denver__muscle_vastusmedialis__right | 13.36 | 5.1% | 4 |
| denver__muscle_gluteusmedius__left | denver__muscle_gluteusminimus__left | 12.65 | 9.8% | 4 |
| denver__bone_fibula__left | denver__muscle_peroneuslongus__left | 12.33 | 34.8% | 10 |
| total__lung_upper_lobe_right | total__rib_right_1 | 12.01 | 88.4% | 16 |
| denver__bone_tibia__right | denver__muscle_flexordigitorumlongus__right | 11.65 | 45.1% | 14 |
| denver__muscle_bicepsfemorislong__left | denver__muscle_semitendinosus__left | 11.11 | 10.8% | 6 |

Top 20 por maior percentual direcional:
| Estrutura A | Estrutura B | Maior fracao | cm3 | Profundidade (mm) |
|---|---|---:|---:|---:|
| total__lung_upper_lobe_right | total__rib_right_1 | 88.4% | 12.01 | 16 |
| denver__bone_intermediatecuneiform__right | denver__bone_phalanges__right | 81.8% | 3.17 | 11 |
| total__lung_upper_lobe_right | total__rib_right_2 | 79.2% | 10.53 | 13 |
| denver__cartilage_talus__left | denver__muscle_flexordigitorumlongus__left | 76.0% | 0.06 | 4 |
| denver__bone_femur__left | denver__cartilage_pelvisacetabulum__left | 57.8% | 1.86 | 13 |
| denver__bone_lateralcuneiform__left | denver__bone_phalanges__left | 56.9% | 2.80 | 10 |
| denver__bone_fibula__left | denver__muscle_plantaris__left | 56.8% | 1.16 | 10 |
| total__lung_upper_lobe_right | total__subclavian_artery_right | 55.2% | 6.12 | 12 |
| denver__bone_tibia__left | denver__muscle_flexordigitorumlongus__left | 55.1% | 14.58 | 16 |
| denver__bone_tibia__right | denver__cartilage_femurdistal__right | 54.4% | 5.72 | 21 |
| denver__bone_lateralcuneiform__right | denver__bone_phalanges__right | 53.0% | 2.89 | 11 |
| denver__bone_tibia__left | denver__cartilage_femurdistal__left | 52.3% | 7.98 | 20 |
| total__lung_lower_lobe_right | total__pulmonary_vein | 46.6% | 8.68 | 16 |
| denver__bone_tibia__right | denver__muscle_flexordigitorumlongus__right | 45.1% | 11.65 | 14 |
| total__autochthon_left | total__rib_left_12 | 44.8% | 2.74 | 13 |
| total__iliac_artery_right | total__small_bowel | 40.9% | 6.17 | 14 |
| total__iliac_vena_right | total__small_bowel | 37.9% | 10.12 | 12 |
| total__autochthon_right | total__rib_right_12 | 37.8% | 3.14 | 16 |
| denver__bone_femur__right | denver__cartilage_pelvisacetabulum__right | 37.6% | 1.38 | 15 |
| denver__muscle_adductormagnus__right | denver__muscle_superiorgemellus__right | 36.2% | 1.90 | 12 |

### F2, F4, F5 e criterios geometricos
F2 - REPROVOU no conjunto. Quadril Denver cartilagem femoral para cartilagem acetabular: E 0,014 mm, D 0,037 mm (PASSOU, <=5 mm); osso femoral para cartilagem acetabular 0,088/0,079 mm. Joelho, medida anterior preservada: E 5,693 mm (REPROVOU), D 4,948 mm (PASSOU). Costelas-vertebras: 1/46 pares <=5 mm (REPROVOU); folga sistematica bilateral T2-T9 ~8,6-14,5 mm tambem para o proxy lateral do processo transverso; T10 E/D 17,2/22,9 mm, T11 21,2/28,2 mm, T12 28,9/46,6 mm. Limitacao da segmentacao TotalSegmentator: ambas as mascaras sao da mesma TC, sem transformacao Denver nessa medida; nao ha sublabels para cabeca/colo costal ou processo transverso. Cranio-C1 3,350 mm (PASSOU, medida anterior preservada).

F4 - PASSOU: 154/154 estruturas laterais corretas em RAS; sacro/coccix medianos excluidos apesar do sufixo Left. F5 - PENDENTE: sem revisao humana/capturas em quatro vistas.

Criterios geometricos do EXP-0014 (pele media <=10 mm; ossos grandes/orgaos/musculos grandes media <=5 mm e P95 <=12 mm; vertebras/grandes vasos media <=3 mm; vasos pequenos/nervos avaliacao individual): NAO AVALIADOS nesta rodada; nao foi feita comparacao simetrica por classe contra referencia. Complementos uterinos/ovarianos HRA nao incluidos nesta rodada.

Quadro funcional: F1 REPROVOU; F2 REPROVOU (quadril PASSOU, joelho E e costovertebral REPROVARAM; joelho D e cranio-C1 PASSARAM); F3 v1 REPROVOU; F3 v2 REPROVOU; F4 PASSOU; F5 PENDENTE. Sem validacao clinica.

## 8.4 Estratificacao das invasoes F3 v2 - analise, sem novo criterio (2026-11-26)

Aplicada a particao por campo fonte do manifesto somente aos 237 pares que ja satisfazem a regra F3 v2 (sobreposicao >=2% e profundidade >3 mm). Resultado: 133 pares Denver-Denver, 90 pares TotalSegmentator-TotalSegmentator e **14 pares entre fontes**. Os dois grupos de mesma fonte medem consistencia dentro da origem; nao medem a integracao entre fontes. A lista entre fontes mede a interface TotalSegmentator-Denver. Volumes sao a media das estimativas direcionais por amostragem, em cm3; profundidade e estimativa na grade 2 mm.

| Estrutura TotalSegmentator | Estrutura Denver | Volume medio estimado (cm3) | Maior fracao direcional | Profundidade (mm) |
|---|---|---:|---:|---:|
| total__spinal_cord | denver__bone_sacrum__left | 8.371 | 8.00% | 14.1 |
| total__vertebrae_l5 | denver__bone_sacrum__left | 4.492 | 6.25% | 10.0 |
| total__iliac_vena_left | denver__muscle_pectineus__left | 2.541 | 10.65% | 8.2 |
| total__iliac_vena_left | denver__bone_pelvis__left | 2.401 | 12.15% | 11.7 |
| total__iliac_vena_right | denver__bone_pelvis__right | 2.280 | 12.80% | 11.5 |
| total__urinary_bladder | denver__bone_pelvis__right | 1.997 | 5.45% | 6.0 |
| total__urinary_bladder | denver__bone_pelvis__left | 1.754 | 4.75% | 7.2 |
| total__iliac_artery_right | denver__bone_pelvis__right | 0.940 | 9.70% | 11.5 |
| total__iliac_artery_left | denver__muscle_pectineus__left | 0.854 | 8.25% | 10.0 |
| total__iliac_artery_left | denver__muscle_sartorius__left | 0.806 | 7.10% | 6.3 |
| total__small_bowel | denver__cartilage_pelvisacetabulum__left | 0.589 | 5.09% | 8.0 |
| total__iliac_artery_left | denver__bone_pelvis__left | 0.496 | 4.90% | 6.6 |
| total__iliac_artery_right | denver__muscle_sartorius__right | 0.396 | 3.45% | 4.5 |
| total__stomach | denver__cartilage_pelvisacetabulum__left | 0.036 | 4.26% | 26.4 |

Esta estratificacao e descritiva: nao muda o universo, o limite de 2%, a regra de profundidade >3 mm ou a avaliacao PASS/REPROVOU. Dados completos em `diagnostico_EXP-0015.json`, campo `f3_depth_and_rankings.source_stratification`.

## 8.5 Analise por fonte e pacote F5 provis?rio (2026-11-26)

### Estratos F3 v2
Sem novo criterio, as 237 invasoes ja contabilizadas em F3 v2 se dividem em **133 Denver-Denver**, **90 TotalSegmentator-TotalSegmentator** e **14 entre fontes**. Os dois primeiros estratos medem consistencia interna da fonte; apenas o terceiro mede diretamente a integracao. Todos os 14 pares entre fontes, com volume medio estimado e profundidade, estao registrados na secao 8.4 e em `diagnostico_EXP-0015.json`; a estratificacao nao altera nenhum status anterior.

### Pacote de revisao
Gerado em `atlas/vhf-f/0.1-0`, com **rascunho, nao publicado, nao aceito** no manifesto. Tem 229 entradas: 101 TotalSegmentator (inclui pele) e 128 Denver. Foram produzidos todos os 16 sistemas do `bp3d-m`; fascia, gestacional e sensorial estao como GLBs vazios porque esta base nao tem entradas para eles. GLBs completos sem simplificacao, meshopt preservou nome dos nos e triangulos. Pele completa: 2.076.986 triangulos; `tegumentar_leve.glb`: 40.000 triangulos por simplificacao quadratica trimesh. Referencial app em metros, `x=-x_RAS`, `y=z_RAS`, `z=y_RAS`. `indice.json`: 229 itens com `estrutura` e `nome_pt` null e `fonte` preenchida em cada item. Hashes SHA-256 dos 18 arquivos de pacote no manifesto; hashes dos 229 STLs de origem tambem registrados.

| Sistema / GLB | Estruturas | Triangulos | Tamanho |
|---|---:|---:|---:|
| arterial | 8 | 74708 | 1.015 MB |
| articular | 25 | 334918 | 5.193 MB |
| cardiaco | 2 | 70834 | 1.037 MB |
| digestorio | 8 | 644284 | 8.747 MB |
| endocrino | 3 | 9728 | 0.160 MB |
| esqueletico | 84 | 1698598 | 25.955 MB |
| fascia | 0 | 0 | 0.000 MB |
| gestacional | 0 | 0 | 0.000 MB |
| linfatico | 1 | 29186 | 0.429 MB |
| muscular | 78 | 1474934 | 23.445 MB |
| nervoso | 2 | 121332 | 1.663 MB |
| respiratorio | 6 | 284004 | 4.085 MB |
| sensorial | 0 | 0 | 0.000 MB |
| tegumentar | 1 | 2076986 | 22.941 MB |
| urogenital | 3 | 67644 | 1.009 MB |
| venoso | 8 | 65628 | 0.954 MB |
| tegumentar_leve (LOD) | 1 | 40000 | 0.376 MB |

Soma dos GLBs (incluindo LOD): **97,010 MB**; pacote ainda nao foi publicado nem aceito. O manifesto e indice foram verificados quanto a campos, nomes, contagens e hashes. O pacote foi produzido para revisao humana F5; nao constitui validacao clinica.

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

## Decisão de encerramento (2026-11-26)
Decisão do usuário após a revisão F5 e o resultado do `EXP-0016`: **manter o `hra-f/1.10-1` como atlas feminino do MVP e congelar a linha de pesquisa do corpo feminino**, dentro do teto de 5 dias úteis. Os pacotes `atlas/vhf-f/0.1-0` e `atlas/hib-f/0.1-0` ficam como rascunhos locais, não publicados e não aceitos (o `copiar-atlas` ignora rascunhos). As lacunas conhecidas do HRA (esqueleto remodelado, `EXP-0014`) continuam registradas. Sem validação clínica.
