# EXP-0022 — auditoria técnica do Female Atlas externo

Execução do protocolo pré-registrado em `pesquisa/experimentos/EXP-0022-auditoria-female-atlas.md`. Os critérios não foram alterados e as seções 8–11 do protocolo permanecem intactas. Nenhum script, pacote ou comando do clone externo foi executado.

## Identificação e inventário

- Repositório clonado em `hra/externo/female-atlas`; HEAD `b0a20fa3a009ca5f6bfa07b7479312e04c862af2` (10 commits no histórico clonado).
- Manifesto do pacote corresponde exatamente às declarações: **3.004 malhas**, **2.557 conceitos**, **16 sistemas** e 3.893.539 triângulos.
- Prefixos de origem: **2.163 `BP3D_`**, **552 `VH_F_`**, **282 `Allen_`** e **7 `Yao_`**. As transformações dos grupos são registradas por malha em `proveniencia.csv`.
- `atlas.json` do clone declara Female Atlas v2.0; sua versão corresponde a `build-perfect-female-atlas.mjs`.

## Proveniência e transformações observadas

Os scripts publicados indicam duas fontes e um construtor final. `convert-female.py` recebe o GLB united-female v1.5 do HRA em metros/Y-up e adiciona `+0,794760942 m` ao eixo Y; o construtor final exclui a pele HRA antiga e fragmentos do joelho/fêmur/tíbia e do reto femoral, reclassifica estruturas mamárias e preserva as demais peças HRA. Isso corresponde a 552 nós `VH_F_`, 282 `Allen_` e 7 `Yao_` no pacote.

`convert-anatomy.py` declara a conversão BodyParts3D de milímetros para metros: `(x,y,z) → (0,001x, 0,001z + 0,0781112, −0,001y − 0,1)`. `build-perfect-female-atlas.mjs` então aplica escala global `(0,95; 0,96335; 0,95)`, deslocamento `Z = −0,052 m` e deformações por altura/região: estreitamento de pescoço e ombros, redução do tórax, cintura em ampulheta, abertura dos quadris, ajuste da lordose/glúteos, aproximação dos braços e remodelação de mama/virilha na pele. O grupo tem 2.163 malhas `BP3D_`.

`optimize-anatomy.mjs` solda vértices coincidentes nas malhas HRA, calcula médias de normais, reduz cada estrutura com `MeshoptSimplifier.simplify` e compacta os vértices. O script define alvo aproximado de **22% dos triângulos de entrada por estrutura** (`indexCount * .22`) e erro `0.002`; a atribuição do README descreve isso como erro relativo de 0,2%. O clone não contém as pastas temporárias de entrada dos construtores. A associação de `Allen_` e `Yao_` ao GLB de entrada HRA é indicada pelo fluxo do conversor, mas a proveniência do fornecedor desses nós não está detalhada no texto de atribuição.

## Referencial e método geométrico

O HRA e o atlas BP3D usam eixos locais `x` para a esquerda, `y` para cima, `z` para a frente, em metros. No pacote BP3D decodificado, FJ3288 (left hip bone) está no lado `x` positivo e os landmarks batem com a lateralidade do catálogo. Para comparar à TC RAS, foi usado o mapa de eixos `(x_RAS, y_RAS, z_RAS) = (−x_local, z_local, y_local)`, seguido de ajuste rígido com escala uniforme e translação.

Caixas observadas **antes do alinhamento**: HRA `VH_F_sacrum` vai de `[-0,0718; 0,8386; −0,1825]` a `[0,0556; 0,9376; −0,0776] m`. No GLB BP3D, FJ3288 (left hip bone) ocupa `x=+0,0034…+0,1454 m`; FJ3152 (right hip bone) ocupa `x=−0,1442…−0,0021 m`; FJ3393 (sacrum) ocupa `x=−0,0589…+0,0588 m`, com o eixo vertical local em Y. Na TC RAS, os componentes principais do hip esquerdo e direito ocupam respectivamente `x=−141,8…+5,2` e `+8,2…+155,2 mm`; o sacro ocupa `x=−53,2…+65,2 mm`. O componente desconectado de 30 voxels do `hip_left` foi excluído somente desses limites principais, mas mantido nas medidas.

A máscara `hra/nlm/bruto/saida/segmentacao.nii.gz` tem shape `320×320×1156`, voxel `1,5 mm` e affine diagonal `+1,5 mm` conferido contra `hra/alinhar/transformacoes.json`. No RAS, `x` cresce à direita, `y` anterior e `z` superior; a translação negativa em Z não inverte o eixo. A máscara `hip_left` contém também um componente desconectado de 30 voxels em `z≈−1261 mm`; ele foi mantido nas medidas e fica fora do recorte visual.

As superfícies de máscaras foram trianguladas em coordenadas de voxel e transformadas pelo affine NIfTI. As distâncias usam amostragem uniforme por área de triângulo, seed `220022`, KD-tree e distâncias simétricas (as duas direções concatenadas): 30.000 pontos por direção para pelve e 15.000 para cada outra estrutura. O ICP usou rotação própria, escala uniforme, trim de 12% e no máximo 50 iterações. **Todos os ajustes atingiram o limite de 50 iterações sem convergir**; os números são resultados observados do ajuste final e podem ser mínimos locais/limites superiores. Nenhum critério foi flexibilizado por isso.

### C3 — pelve contra NLM

| Fonte | Malhas consideradas | Média simétrica | p95 | Escala uniforme |
|---|---:|---:|---:|---:|
| Female Atlas | 16 (ossos bilaterais do quadril, fragmentos HRA e os sacros HRA/BP3D) | **3,881 mm** | **16,058 mm** | 0,948 |
| `bp3d-m` | 3 (os dois ossos do quadril e sacro) | **5,251 mm** | **14,038 mm** | 1,061 |

Redução da média do Female Atlas contra `bp3d-m`: **26,09%**. A média absoluta e a redução cumprem os limites; o p95 de 16,058 mm excede 12 mm. **C3 não atendido.** A métrica do Female Atlas inclui tanto o sacro HRA quanto o sacro BodyParts3D presentes no manifesto, conforme os dados efetivamente publicados.

### C4 — fêmures e vértebras lombares contra NLM

| Estrutura | Malha avaliada | Média (mm) | p95 (mm) | Resultado individual |
|---|---|---:|---:|---|
| Fêmur esquerdo | Female Atlas | 3,54 | 8,47 | passa |
| Fêmur esquerdo | `bp3d-m` | 3,35 | 9,28 | passa |
| Fêmur direito | Female Atlas | 3,58 | 8,21 | passa |
| Fêmur direito | `bp3d-m` | 3,69 | 10,51 | passa |
| L1 | HRA no Female Atlas | 4,80 | 31,25 | falha |
| L1 | BodyParts3D no Female Atlas | 5,76 | 30,22 | falha |
| L1 | `bp3d-m` | 5,54 | 30,82 | falha |
| L2 | HRA no Female Atlas | 6,45 | 23,34 | falha |
| L2 | BodyParts3D no Female Atlas | 6,88 | 21,82 | falha |
| L2 | `bp3d-m` | 6,19 | 23,34 | falha |
| L3 | HRA no Female Atlas | 3,79 | 26,52 | falha |
| L3 | BodyParts3D no Female Atlas | 5,74 | 24,00 | falha |
| L3 | `bp3d-m` | 4,54 | 26,79 | falha |
| L4 | HRA no Female Atlas | 1,21 | 2,96 | passa |
| L4 | BodyParts3D no Female Atlas | 1,97 | 4,92 | passa |
| L4 | `bp3d-m` | 1,58 | 4,10 | passa |
| L5 | HRA no Female Atlas | 1,80 | 4,95 | passa |
| L5 | BodyParts3D no Female Atlas | 1,99 | 5,31 | passa |
| L5 | `bp3d-m` | 1,64 | 4,11 | passa |

No total, **10/19** comparações passam e **9/19** falham; L1–L3 são as falhas. **C4 não atendido.** Também foram medidas as 12 costelas de cada lado disponíveis na máscara: 48 comparações entre os dois atlas, com médias de 1,70–7,72 mm e p95 de 4,57–44,53 mm. Costelas são dado suplementar e não alteram o critério C4 pré-registrado.

## C5 — medidas funcionais internas

- **F1 — não verificado:** a pele `BP3D_FJ2810` não é watertight. Só 13 das 698 malhas importadas de ossos/músculos são watertight; contenção volumétrica na pele aberta não é definida.
- **F2 — parcial, não verificado como critério completo:** distância mínima amostrada do fêmur inteiro ao osso do quadril homolateral: 0,065 mm (esquerdo) e 0,117 mm (direito). As 24 costelas estão a 0,008–0,107 mm do corpo vertebral torácico de mesmo número. O grupo de 18 ossos cranianos está a 0,116 mm do C1 HRA. São proxies entre malhas completas; cabeça femoral, facetas acetabulares, côndilos occipitais e facetas do atlas não são estruturas nomeadas isoladamente no pacote.
- **F3 — não verificado:** a razão de volume de interseção requer volumes fechados; entre os 2.163 importados, 162 são watertight, e entre 841 nós HRA/Allen/Yao, 397. Não se infere porcentagem de sobreposição por proximidade de superfície.
- **F4 — passa no subconjunto lateralizado:** 1.705 malhas com lado no catálogo comparadas ao nome final; 0 divergências e 0 IDs sem linha no catálogo. As outras malhas não declaram lateralidade.

**C5 não atendido**, pois F1/F3 não são verificáveis e F2 não isola todos os marcos articulares exigidos; F4 passa.

## Critérios e veredito

| Critério | Resultado | Veredito |
|---|---|---|
| C1 — proveniência 100% | Transformações agrupadas para 3.004; 7 IDs `Yao_` sem fonte de fornecedor identificável no clone | **Não atendido** |
| C2 — licença CC BY 4.0 por fonte | HRA e BodyParts3D são declarados CC BY 4.0 no README/ATTRIBUTION; licença/proveniência própria dos nós `Yao_` não verificada | **Não atendido** |
| C3 — pelve feminina | 3,881 mm; p95 16,058 mm; redução média 26,09% contra BP3D | **Não atendido** (p95) |
| C4 — ossos grandes | 10/19 passam; L1–L3 falham | **Não atendido** |
| C5 — funcionais | F1/F3 não verificados, F2 parcial, F4 passa | **Não atendido** |

Pela regra pré-registrada, C3 reprovado sustenta H22: a pelve do Female Atlas teve média menor que `bp3d-m`, mas não alcançou o p95 exigido. Independentemente disso, C1/C2 não estão demonstrados para 100% das malhas; o atlas **não fica qualificado como base do V3** por esta auditoria. Trata-se de comparação geométrica com uma única doadora, sem validação anatômica clínica.

## Capturas

- [Pelve de frente — Female Atlas × bp3d-m × NLM](pelve_frente.png)
- [Pelve de cima — Female Atlas × bp3d-m × NLM](pelve_de_cima.png)

## Artefatos, reprodutibilidade e limitações

- Scripts próprios: `auditar.py`, `medir.py`, `funcionais.py`, `gerar_artifacts.py`, `consolidar.py`.
- Dados: `inventory.json`, `proveniencia.csv`, `referencial.json`, `metrics.json`, `functional.json`, `resultados.json`.
- Comparador decodificado pelo usuário: `bp3d-esqueletico.glb` (244 nós; SHA-256 registrado em `resultados.json`). O decoder usado está no repositório (`hra/alinhar/decoder_glb.mjs`); nenhuma leitura ou escrita foi feita dentro de `atlas/`.
- Versões registradas: Python 3.14.4, NumPy 2.4.6, trimesh 5.2.2, SciPy 1.18.1, nibabel 5.5.0. Execução somente CPU.
- Resultados medidos não são validação clínica. As distâncias são amostradas; o ICP não convergiu em 50 iterações; F1/F3 volumétricos e partes articulares isoladas ficaram não verificadas.

## Correção do revisor (Claude Code)

Esta correção complementa a avaliação original acima; **a tabela e o veredito originais permanecem preservados**. A conferência de `hra/catalogo_hra.csv` localiza os 7 nós `Yao_` como entradas do HRA: `sistema_hra=VH_F_lymphatic_system`, `orgao=Yao_lymph_node`. O catálogo também contém os 282 registros `Allen_`. O README/ATTRIBUTION do clone declara o HRA united-female v1.5 como CC BY 4.0.

Foi conferido `proveniencia.csv`: **3.004 linhas**, uma para cada malha do manifesto, e **0 linhas sem transformação atribuída**. As 2.163 partes BodyParts3D apontam para conversão de eixos/unidades, escala, deslocamento, deformação e simplificação descritos pelos scripts; as 841 partes restantes apontam para o grupo HRA e a transformação `+0,794760942 m` em Y do conversor. Com a evidência de catálogo para os nós Yao e as transformações rastreadas para todas as entradas, a revisão corrige os vereditos atuais para **C1 atendido e C2 atendido**. O campo de catálogo não existe para 10 IDs do grupo HRA, mas a fonte do grupo e a transformação permanecem identificadas pelo GLB de entrada e `convert-female.py`.

## Limitação adicional — dependência da mesma doadora

O HRA female e a TC NLM usada neste experimento derivam da mesma doadora Visible Human Female. Assim, a semelhança dos fragmentos `VH_F_` da pelve com a máscara NLM **não é evidência independente**: parte dela é esperada por construção. Isso limita a interpretação de C3 original, que combina fragmentos HRA e malhas BodyParts3D.

## Análise pós-hoc, não altera critérios nem veredito

Repeti o ICP de similaridade uniforme, com o mesmo mapa de eixos, trim de 12%, amostragem de superfície e critério de convergência; o limite subiu de 50 para **200 iterações**. Todas as quatro execuções suplementares convergiram. Em cada comparação, as duas fontes usaram os mesmos pontos-alvo da superfície NLM.

| Comparação suplementar | Female Atlas — BP3D deformado | `bp3d-m` | Redução da média Female Atlas vs. BP3D |
|---|---:|---:|---:|
| (a) Só os dois ossos do quadril; alvo NLM `hip_left + hip_right` | média **5,078 mm**, p95 **14,253 mm** (135 iterações) | média **4,204 mm**, p95 **9,986 mm** (87 iterações) | **−20,80%** |
| (b) Os dois quadris + sacro BP3D; alvo NLM `hip_left + hip_right + sacrum` | média **5,830 mm**, p95 **15,670 mm** (152 iterações) | média **5,284 mm**, p95 **14,383 mm** (91 iterações) | **−10,33%** |

O sinal negativo indica que a média do Female Atlas foi maior que a do comparador `bp3d-m` nessas seleções só de malhas BP3D. Isso é compatível com o viés circular acima: no C3 original, incluir fragmentos pélvicos HRA reduz a distância à própria doadora que originou a TC.

Foram identificados **70 grupos de duplicação exata** entre fontes (45 por `conceptId` FMA compartilhado e 25 correspondências axiais por nome/anatomia: sacro, C1–C7, L1–L5 e T1–T12), além de **2 sobreposições parciais pai/fragmento** (os dois ossos do quadril BP3D e fragmentos HRA de ílio/púbis/ísquio). A lista contém 72 linhas em [suplementar_duplicadas.csv](suplementar_duplicadas.csv); o sacro HRA + BP3D aparece como duplicação exata. As métricas e os estados de convergência estão em [suplementar.json](suplementar.json).
