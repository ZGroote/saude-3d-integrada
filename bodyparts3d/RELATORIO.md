# BodyParts3D — inventário e teste de encaixe

Fonte: BodyParts3D release 4.0 (2013), árvore is_a (contém todas as do part_of), malhas com 99% de redução. 
Licença atual no site: CC BY 4.0 (página atualizada em 27/02/2025). O cabeçalho dos OBJ ainda diz CC BY-SA 2.1 JP (texto antigo).
Atribuição exigida: "BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International".

- **2234 malhas** (cada uma é uma estrutura folha com ID FMA)
- **1659 conceitos FMA distintos**, 3432 conceitos nomeados contando agrupamentos
- **6,681,030 triângulos** no total (média 2,990 por estrutura)
- Altura do corpo: 1730 mm · unidades em mm · Z para cima

## Por sistema

| Sistema | Estruturas | Triângulos |
|---|---:|---:|
| arterial | 633 | 975,238 |
| muscular | 410 | 2,362,772 |
| venoso | 385 | 942,206 |
| esqueletico | 244 | 605,596 |
| nervoso | 141 | 499,150 |
| digestorio | 137 | 334,532 |
| respiratorio | 104 | 78,740 |
| articular | 69 | 144,790 |
| sensorial | 45 | 316,334 |
| cardiaco | 28 | 108,206 |
| urogenital | 18 | 17,128 |
| endocrino | 11 | 25,896 |
| fascia | 4 | 36,852 |
| tegumentar | 4 | 232,260 |
| linfatico | 1 | 1,330 |

Classificação automática (árvore FMA + palavras-chave). Ver `catalogo_bp3d.csv`; os casos ambíguos foram revisados em `revisao_outros.csv`.

## Lacunas conhecidas do BodyParts3D

- Carótida: falta o trecho entre a carótida comum (termina a ~1373 mm) e a interna (começa a ~1434 mm), incluindo a bifurcação; não há carótida externa.
- Um único corpo masculino adulto (2013). Sem anatomia feminina. Nomes em português (`nomes_pt.csv`) ainda sem revisão médica.

## Encaixe com o caso s1371 (TotalSegmentator)

Ajuste de similaridade (escala + rotação + translação) sobre os centros de 28 estruturas comuns.

- Escala BP3D→s1371: **0.950**
- Erro médio após o ajuste: **36.5 mm** (máximo 86.2 mm)
- Rotação encontrada (deveria ser quase identidade ou só troca de eixos):
```
[[ 1.   -0.08 -0.02]
 [ 0.02  0.09  1.  ]
 [-0.08 -0.99  0.09]]
```

| s1371 | BP3D | erro (mm) | tamanho s1371 (mm) | tamanho BP3D×escala (mm) |
|---|---|---:|---|---|
| lung_upper_lobe_right | upper lobe of right lung | 86 | [139, 152, 195] | [99, 104, 317] |
| sacrum | sacrum | 55 | [103, 119, 320] | [84, 112, 137] |
| trachea | trachea | 55 | [78, 96, 110] | [25, 31, 105] |
| spleen | spleen | 54 | [72, 84, 109] | [55, 67, 90] |
| hip_left | left hip bone | 50 | [141, 161, 227] | [131, 135, 196] |
| gallbladder | gallbladder | 50 | [21, 35, 47] | [35, 38, 46] |
| lung_upper_lobe_left | upper lobe of left lung | 48 | [153, 169, 217] | [89, 145, 176] |
| liver | liver | 45 | [170, 222, 236] | [147, 151, 199] |
| vertebrae_T12 | twelfth thoracic vertebra | 44 | [55, 74, 90] | [41, 49, 75] |
| kidney_right | right kidney | 42 | [69, 85, 144] | [45, 54, 99] |
| kidney_left | left kidney | 42 | [70, 76, 152] | [39, 55, 101] |
| vertebrae_L1 | first lumbar vertebra | 42 | [78, 99, 103] | [54, 67, 76] |
| hip_right | right hip bone | 38 | [153, 160, 274] | [131, 135, 195] |
| lung_lower_lobe_right | lower lobe of right lung | 37 | [159, 162, 206] | [74, 102, 151] |
| pancreas | pancreas | 34 | [78, 123, 142] | [49, 70, 123] |
| urinary_bladder | urinary bladder | 31 | [87, 88, 137] | [38, 63, 68] |
| clavicula_left | left clavicle | 30 | [65, 67, 81] | [44, 88, 129] |
| vertebrae_T6 | sixth thoracic vertebra | 28 | [73, 91, 98] | [57, 61, 68] |
| lung_lower_lobe_left | lower lobe of left lung | 27 | [146, 150, 178] | [85, 116, 162] |
| esophagus | esophagus | 27 | [46, 69, 209] | [31, 55, 261] |
| vertebrae_L3 | third lumbar vertebra | 26 | [92, 107, 112] | [40, 75, 82] |
| sternum | sternum | 25 | [57, 76, 170] | [52, 79, 153] |
| heart | heart | 25 | [143, 145, 169] | [99, 101, 110] |
| clavicula_right | right clavicle | 25 | [63, 80, 83] | [44, 88, 129] |
| stomach | stomach | 19 | [106, 140, 161] | [107, 111, 128] |
| scapula_right | right scapula | 14 | [99, 105, 157] | [103, 104, 158] |
| scapula_left | left scapula | 13 | [92, 109, 157] | [102, 104, 158] |
| vertebrae_L5 | fifth lumbar vertebra | 10 | [87, 96, 97] | [48, 77, 96] |
