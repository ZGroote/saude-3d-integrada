# Inventário Denver — Visible Human Female

Dados: University of Denver, Visible Human Female; licença CC BY 4.0.
STLs em `bruto/Final 3D STL Models-stl/`; dimensões exportadas em mm conforme unidade do STL.

- Arquivos: **128**
- Triângulos: **2.335.390**

## Contagem por tipo

| Tipo | Arquivos |
|---|---:|
| cartilagem | 16 |
| gordura | 0 |
| ligamento | 8 |
| musculo | 76 |
| osso | 28 |

## Contagem por lado

| Lado | Arquivos |
|---|---:|
| Left | 65 |
| Right | 63 |

## TC alinhada

- Cortes: **1.727**
- Matriz NIfTI (coluna, linha, corte): **(673, 670, 1727)**
- Pixel spacing DICOM [linha, coluna]: **[0.722656, 0.722656] mm**; espaçamento entre cortes: **1 mm**
- ImageOrientationPatient: **[1.0, 0.0, 0.0, 0.0, 1.0, 0.0]**
- ImagePositionPatient disponível: **False**; SliceLocation inicial/final: **0.000000 / 1726.000000**
- Extensão RAS (mm): **X -485.625..0.000; Y -483.457..0.000; Z 0.000..1726.000**
- Intensidades convertidas para HU por `pixel * RescaleSlope + RescaleIntercept`; geometria NIfTI em mm, DICOM LPS convertido para RAS.
- RescaleType no DICOM: **US**; valores foram calculados com slope/intercept. O tag não declara literalmente HU, então a interpretação como HU é assumida para a prova.
- IOP ausente: True; orientação axial convencional assumida. Origem XY ausente e assumida como (0,0) mm.
- NIfTI gerado: `bruto/tc_alinhada.nii.gz`

## Prova de referencial: fêmures versus TC

Amostragem determinística de 2.000 vértices por STL; todos os pontos amostrados entram no denominador e pontos fora do volume contam como HU não maior que 200.

| Transformação aplicada aos vértices STL | Left HU > 200 | Right HU > 200 |
|---|---:|---:|
| direto (STL em RAS) | 0.0% | 0.0% |
| espelho Z (origem preservada) | 0.0% | 0.0% |
| LPS para RAS | 0.9% | 0.0% |
| espelho Z + LPS para RAS | 0.0% | 0.0% |

Melhor resultado entre as conversões sem origem extra: **LPS para RAS**. Todos os vértices amostrados entram no denominador; pontos fora contam como negativos.


Busca diagnóstica de origem XY: melhor sinal XYZ=(-1,1,1), deslocamento STL=(300,-700,0) mm; frações Left/Right=100.000%/100.000%.
Transformação operacional dos vértices STL para as coordenadas RAS do NIfTI: x'=-1·x+300 mm; y'=1·y-700 mm; z'=1·z mm.
A origem estimada não recupera o posicionamento DICOM ausente; a TC NIfTI mantém a origem XY convencional (0,0).

## Validação independente da transformação STL→TC

Transformação testada sem reajuste por estrutura: `x' = −x + 300`, `y' = y − 700`, `z' = z` mm. Todos os vértices de cada STL são usados; pontos fora da TC contam como falhas.

**Interpretação das unidades:** os DICOMs têm `Modality=OT`, `RescaleType=US`, `PixelRepresentation=0`, slope 1 e intercept 0. Os valores reescalados não incluem HU negativos e o padrão não declara HU. Portanto, as frações abaixo são numericamente calculadas nos valores reescalados, mas não podem ser validadas como frações HU; os intervalos clínicos pedidos são apenas comparadores numéricos aqui.

### Os 28 STLs ósseos (valor reescalado > 200)

| Estrutura | Vértices | Dentro da TC | Fração > 200 |
|---|---:|---:|---:|
| Left_Bone_Calcaneous | 52416 | 52416/52416 | 95.05% |
| Left_Bone_Coccyx | 7026 | 7026/7026 | 65.64% |
| Left_Bone_Cuboid | 14778 | 14778/14778 | 100.00% |
| Left_Bone_Femur | 275658 | 275658/275658 | 100.00% |
| Left_Bone_Fibula | 56754 | 56754/56754 | 100.00% |
| Left_Bone_IntermediateCuneiform | 6984 | 6984/6984 | 97.45% |
| Left_Bone_LateralCuneiform | 8094 | 8094/8094 | 100.00% |
| Left_Bone_MedialCuneiform | 12270 | 12270/12270 | 55.77% |
| Left_Bone_Navicular | 13830 | 13830/13830 | 67.66% |
| Left_Bone_Patella | 19572 | 19572/19572 | 99.00% |
| Left_Bone_Pelvis | 297924 | 297924/297924 | 99.99% |
| Left_Bone_Phalanges | 104820 | 104820/104820 | 91.43% |
| Left_Bone_Sacrum | 153222 | 153222/153222 | 91.70% |
| Left_Bone_Talus | 33222 | 33222/33222 | 86.84% |
| Left_Bone_Tibia | 178368 | 178368/178368 | 96.40% |
| Right_Bone_Calcaneous | 52722 | 52722/52722 | 50.00% |
| Right_Bone_Cuboid | 15126 | 15126/15126 | 37.58% |
| Right_Bone_Femur | 268398 | 268398/268398 | 100.00% |
| Right_Bone_Fibula | 58440 | 58440/58440 | 47.00% |
| Right_Bone_IntermediateCuneiform | 6942 | 6942/6942 | 92.97% |
| Right_Bone_LateralCuneiform | 8424 | 8424/8424 | 55.94% |
| Right_Bone_MedialCuneiform | 12648 | 12648/12648 | 100.00% |
| Right_Bone_Navicular | 13494 | 13494/13494 | 89.22% |
| Right_Bone_Patella | 19764 | 19764/19764 | 100.00% |
| Right_Bone_Pelvis | 295266 | 295266/295266 | 99.90% |
| Right_Bone_Phalanges | 108606 | 108606/108606 | 48.56% |
| Right_Bone_Talus | 32028 | 32028/32028 | 82.45% |
| Right_Bone_Tibia | 181086 | 181086/181086 | 95.81% |

### Três músculos grandes (valor reescalado entre −50 e 150)

| Estrutura | Vértices | Dentro da TC | Fração no intervalo |
|---|---:|---:|---:|
| Left_Muscle_GluteusMaximus | 137328 | 137328/137328 | 5.11% |
| Left_Muscle_Soleus | 85356 | 85356/85356 | 0.00% |
| Left_Muscle_VastusLateralis | 126450 | 126450/126450 | 0.00% |
| Right_Muscle_GluteusMaximus | 145308 | 145308/145308 | 8.94% |
| Right_Muscle_Soleus | 85680 | 85680/85680 | 40.00% |
| Right_Muscle_VastusLateralis | 122202 | 122202/122202 | 0.70% |

### Sensibilidade do fêmur a deslocamentos

Fração de 2.000 vértices por lado em voxels com valor reescalado > 200 após variar uma coordenada do deslocamento; os outros dois eixos permanecem fixos.

| Eixo | Perturbação (mm) | Left | Right |
|---|---:|---:|---:|
| X | -10 | 100.00% | 98.60% |
| X | -5 | 100.00% | 99.85% |
| X | -2 | 100.00% | 100.00% |
| X | +2 | 100.00% | 100.00% |
| X | +5 | 100.00% | 100.00% |
| X | +10 | 100.00% | 100.00% |
| Y | -10 | 100.00% | 99.05% |
| Y | -5 | 100.00% | 99.85% |
| Y | -2 | 100.00% | 100.00% |
| Y | +2 | 100.00% | 100.00% |
| Y | +5 | 100.00% | 100.00% |
| Y | +10 | 100.00% | 100.00% |
| Z | -10 | 100.00% | 100.00% |
| Z | -5 | 100.00% | 100.00% |
| Z | -2 | 100.00% | 100.00% |
| Z | +2 | 100.00% | 100.00% |
| Z | +5 | 100.00% | 100.00% |
| Z | +10 | 100.00% | 100.00% |

### Origem do deslocamento nos metadados

| Corte DICOM | ImagePositionPatient | ImageOrientationPatient | SliceLocation | Modality / RescaleType |
|---|---|---|---:|---|
| VHF_FullBody_CT0000.dcm | ausente | ausente | 0.000000 | OT / US |
| VHF_FullBody_CT1726.dcm | ausente | ausente | 1726.000000 | OT / US |

Amostra de valores reescalados por corte (mínimo, p50, p90, máximo):

| Corte | Mínimo | p50 | p90 | Máximo |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 72 | 1164 |
| 400 | 0 | 0 | 466 | 2726 |
| 800 | 0 | 58 | 988 | 2530 |
| 1200 | 0 | 77 | 1063 | 2609 |
| 1726 | 0 | 0 | 65 | 1607 |

Auditoria das planilhas em `bruto/MetaData`: os cabeçalhos das planilhas listam geometria/volume e maximum overclosure (mm), sem origem, posição, matriz de transformação ou coordenadas. `ImagePositionPatient` e `ImageOrientationPatient` estão ausentes nos dois DICOMs extremos. Portanto, os metadados disponíveis não explicam os 300/−700 mm.

A resposta ao deslocamento permanece em um platô: ±10 mm mantém o fêmur em 98,60–100% acima do limiar numérico. Isso **não demonstra um ótimo estreito**. Somado às frações mistas dos ossos e baixas nos músculos e à unidade não-HU, a transformação não está validada para uso anatômico/clínico; fica registrada como hipótese empírica provisória. O NIfTI continua com origem XY convencional por ausência de IPP/IOP.

JSON da transformação e auditoria detalhada: `transformacao_stl_para_tc.json`.

## Busca e validação por borda (Otsu multinível)

Amostra uniforme de **1,500,000 voxels** (seed 20261125); Otsu de 3 classes deu limiares **228.889** (ar/fundo→tecido mole) e **726.434** (tecido mole→osso). Os valores são intensidades reescaladas; DICOM não declara HU.

| Classe Otsu | Fração da amostra | Mediana | P10–P90 |
|---|---:|---:|---:|
| ar/fundo (inclui exterior) | 75.47% | 0.00 | 0.00–73.00 |
| tecido mole | 4.83% | 427.00 | 274.00–596.00 |
| osso | 19.71% | 994.00 | 898.00–1106.00 |

Pico dominante por classe Otsu (contagens suavizadas): ar/fundo≈0.5; tecido mole≈435.1; osso≈916.0. Pico amostral em 0: 624,057 voxels.
Picos locais proeminentes: 19.0, 54.1, 46.7, 65.2, 77.2, 916.0, 906.8, 927.1.
A máscara óssea é `valor > 726.434`. Borda = máscara XOR erosão binária 3×3×3; métrica = fração dos vértices cujo voxel arredondado está na borda dilatada por uma vizinhança 3×3×3 (até 1 voxel, 26-conectividade). Pontos fora do volume contam como falha.

### Busca conjunta em fêmures e pelve

Busca coarse nos quatro STLs (Left/Right femur e pelvis), peso igual por estrutura, 500 vértices aleatórios determinísticos por estrutura, seguida de refinamento em torno do melhor coarse. Varredura coarse: X −1200…800, Y −1200…0 e Z −400…1200 em 40 mm; ambos sinais de X foram testados. Os dois refinamentos foram comparados usando todos os vértices.

| Sinal X | Offset coarse (mm) | Macro coarse | Offset refinado (mm) | Macro refinado (amostra) | Macro refinado (todos vértices) |
|---:|---|---:|---|---:|---:|
| -1 | (280, -680, 440) | 18.700% | (290, -690, 430) | 20.800% | 19.888% |
| +1 | (-800, -680, 440) | 18.500% | (-790, -680, 445) | 21.000% | 18.234% |

Vencedor escolhido pelo macro score de todos os vértices:

| Estrutura | Fração na casca de borda |
|---|---:|
| Femur Left | 12.186% |
| Pelvis Left | 28.466% |
| Femur Right | 6.847% |
| Pelvis Right | 32.053% |
| Macro (peso igual) | 19.888% |

Transformação candidata atualizada: `x' = -1·x+290`, `y' = y-690`, `z' = z+430` mm.

### Curva ao variar um eixo por vez

Frações de todos os vértices de cada estrutura no shell da borda; eixos não listados ficam no offset vencedor.

| Estrutura | Base | Eixo | −20 | −10 | −5 | −2 | +2 | +5 | +10 | +20 |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Femur Left | 12.186% | X | 16.056% | 13.726% | 12.705% | 12.275% | 12.065% | 11.844% | 10.870% | 8.776% |
| Femur Left | 12.186% | Y | 10.556% | 11.527% | 12.463% | 12.168% | 12.261% | 12.143% | 12.028% | 11.555% |
| Femur Left | 12.186% | Z | 8.402% | 10.443% | 11.119% | 11.803% | 12.248% | 12.015% | 12.198% | 12.152% |
| Pelvis Left | 28.466% | X | 26.965% | 27.992% | 28.516% | 28.723% | 28.471% | 28.640% | 28.226% | 24.621% |
| Pelvis Left | 28.466% | Y | 28.744% | 27.864% | 27.411% | 28.215% | 28.793% | 29.243% | 28.745% | 26.898% |
| Pelvis Left | 28.466% | Z | 29.582% | 29.947% | 28.937% | 28.808% | 28.144% | 28.151% | 27.572% | 25.937% |
| Femur Right | 6.847% | X | 6.929% | 6.389% | 6.921% | 6.947% | 6.683% | 6.508% | 6.457% | 7.273% |
| Femur Right | 6.847% | Y | 6.236% | 6.298% | 6.770% | 6.923% | 6.799% | 6.424% | 6.853% | 6.190% |
| Femur Right | 6.847% | Z | 4.665% | 5.560% | 6.025% | 6.503% | 7.152% | 7.647% | 8.804% | 9.495% |
| Pelvis Right | 32.053% | X | 19.445% | 25.620% | 28.975% | 31.182% | 32.575% | 32.763% | 33.258% | 32.595% |
| Pelvis Right | 32.053% | Y | 28.236% | 31.222% | 31.278% | 32.079% | 32.049% | 31.369% | 30.621% | 29.334% |
| Pelvis Right | 32.053% | Z | 30.360% | 31.891% | 31.745% | 32.048% | 32.022% | 31.663% | 31.475% | 31.052% |

### Validação final de todos os 28 ossos

| STL | Fração de vértices a até 1 voxel da borda | Dentro do volume |
|---|---:|---:|
| Left_Bone_Calcaneous | 7.133% | 52416/52416 |
| Left_Bone_Coccyx | 10.376% | 7026/7026 |
| Left_Bone_Cuboid | 0.000% | 14778/14778 |
| Left_Bone_Femur | 12.186% | 275658/275658 |
| Left_Bone_Fibula | 0.000% | 56754/56754 |
| Left_Bone_IntermediateCuneiform | 22.308% | 6984/6984 |
| Left_Bone_LateralCuneiform | 4.077% | 8094/8094 |
| Left_Bone_MedialCuneiform | 14.319% | 12270/12270 |
| Left_Bone_Navicular | 13.507% | 13830/13830 |
| Left_Bone_Patella | 14.485% | 19572/19572 |
| Left_Bone_Pelvis | 28.466% | 297924/297924 |
| Left_Bone_Phalanges | 2.374% | 104820/104820 |
| Left_Bone_Sacrum | 12.101% | 153222/153222 |
| Left_Bone_Talus | 13.319% | 33222/33222 |
| Left_Bone_Tibia | 2.837% | 178368/178368 |
| Right_Bone_Calcaneous | 3.627% | 52722/52722 |
| Right_Bone_Cuboid | 0.000% | 15126/15126 |
| Right_Bone_Femur | 6.847% | 268398/268398 |
| Right_Bone_Fibula | 0.726% | 58440/58440 |
| Right_Bone_IntermediateCuneiform | 0.000% | 6942/6942 |
| Right_Bone_LateralCuneiform | 0.000% | 8424/8424 |
| Right_Bone_MedialCuneiform | 0.000% | 12648/12648 |
| Right_Bone_Navicular | 0.000% | 13494/13494 |
| Right_Bone_Patella | 0.000% | 19764/19764 |
| Right_Bone_Pelvis | 32.053% | 295266/295266 |
| Right_Bone_Phalanges | 3.469% | 108606/108606 |
| Right_Bone_Talus | 0.000% | 32028/32028 |
| Right_Bone_Tibia | 0.000% | 181086/181086 |

A transformação anterior `(-1, 1, 1), (300, -700, 0)` teve macro score por borda de 0.264% (todos os vértices), contra 19.888% para o novo candidato.

**Conclusão: não há pico estreito nem registro robusto.** A melhor fração é baixa e a curva é irregular; deslocamentos vizinhos por vezes pontuam mais que o centro. O sinal/offset fica registrado como melhor candidato desta métrica, mas está marcado no JSON como não validado e não deve ser usado como transformação anatômica aceita. Recomendação: plano B por ICP com o TotalSegmentator.
Limiar, amostragem, busca e resultados completos estão em `transformacao_stl_para_tc.json`.
