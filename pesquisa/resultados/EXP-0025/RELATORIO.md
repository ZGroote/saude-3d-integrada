# EXP-0025 — relatório da prova de conceito

**Estado:** execução concluída; H25 rejeitada pela regra de parada pré-registrada. Protocolo `pesquisa/experimentos/EXP-0025-musculos-por-restricoes.md` não foi alterado. Nenhum pacote foi instalado.

## Resultados por critério

| Critério | Resultado | Evidência numérica |
|---|---|---|
| R1 — M reduz a distância média em ≥20% em pelo menos 8/10 grupos | **REPROVOU (0/10)** | M piorou a média simétrica em 9 dos 10 grupos: reto femoral −16,4%; vasto lateral −11,6%; vasto medial −12,0%; sartório −5,7%; grácil −12,8%; adutor longo −12,8%; bíceps femoral −17,4%; gastrocnêmio medial −42,0%; glúteo médio −22,6%; tibial anterior +0,4%. Percentuais usam `(B0−M)/B0`; a avaliação final usa 6.000 amostras por direção. |
| R2 — mediana da distância das inserções M ao osso Denver ≤2 mm | **PASSOU** | 0,000 mm; 14.490 vértices de inserção. Esta medida é por construção: M projeta esses vértices nas superfícies-alvo e a avaliação usa a mesma projeção ponto-triângulo. Portanto, o resultado confirma a execução da restrição, mas não é validação independente do campo TPS. |
| R3 — penetração óssea <2% em todos os grupos | **REPROVOU** | Máximo 22,060% (tibial anterior); 3/10 grupos ficaram abaixo de 2%. Colisão calculada por interseção de voxels ocupados de músculo e união das 13 malhas ósseas Denver a 1 mm; contato de fronteira pode contar como voxel de colisão. |
| R4 — Dice mediano M ≥0,60 (exploratório) | **REPROVOU** | Mediana 0,2684. |

**Leitura pré-registrada:** H25 **REJEITADA**, pois R1 falhou. R2 ter passado não altera essa regra; R4 é apenas exploratório.

As distâncias médias simétricas completas, p95, Dice, razão volumétrica, inserções e colisões para B0/M estão em `metricas.csv` (20 linhas: 10 grupos × 2 métodos). A figura solicitada compara reto femoral e glúteo médio em `comparacao_B0_M_Denver.png`.

## Execução e integridade da separação

- `adaptar.py` gerou 22 arquivos PLY (10 grupos; bíceps femoral com cabeças longa e curta separadas; B0 e M), `insercoes.csv`, `insercoes_vertices.json` e `hashes_adaptadas.json`.
- O carregador de Denver da adaptação exige `_Bone_` e aborta se o caminho contém `_Muscle_`. Na execução foram lidos 13 STLs ósseos (os seis ossos nomeados no protocolo e sete contrapartes do pé disponíveis nas duas fontes); nenhum caminho continha `_Muscle_`.
- `hashes_adaptadas.json` foi escrito após exportar todas as malhas e antes de executar `avaliar.py`. O avaliador verificou os 22 SHA-256 antes de abrir qualquer STL muscular Denver; `metricas_meta.json` registra `all_adapted_hashes_verified_before_denver_muscles: true`.
- O alinhamento B0 usa somente pelve/osso do quadril, fêmur e tíbia, como no protocolo. ICP com similaridade testou 24 rotações próprias (sem reflexão), amostrou 850 pontos por osso BP3D e 1.700 por osso Denver, removeu os 12% maiores resíduos a cada atualização e executou até 45 iterações. Escala ajustada: **0,895340**; determinante da rotação: **1,000000**; erro médio de vizinho mais próximo nos três ossos-âncora: **5,123 mm**.
- Checagem de referencial: os centros pélvicos/tibiais confirmam Z superior em ambas as fontes. As coordenadas dos ossos esquerdos indicam eixos X/Y em orientação oposta entre BP3D e Denver; a rotação própria selecionada acomoda isso sem reflexão. Dimensões ósseas são compatíveis com milímetros, mas os arquivos consultados não declaram unidade: mm é inferido, não metadado explícito.
- Método M: RBF thin-plate spline (`smoothing=2`, `neighbors=48`) ajustada por amostras ósseas (420 por osso selecionado), projeção de inserções derivadas dos vértices BP3D a ≤3 mm e relaxamento laplaciano (12 iterações, fator 0,22). `insercoes.csv` tem 27 combinações músculo-osso com referência “Gray's Anatomy, 42ª ed., capítulo/página: a conferir”; a checagem anatômica da literatura continua pendente.

## Desvios e limitações

- **DESVIO de medição para R3/R4:** a primeira voxelização sem limite de subdivisões abortou por crescimento de memória em triângulos longos; não gerou métricas aproveitadas. A rodada final manteve pitch de 1 mm e usou `trimesh` subdivide com `max_iter=8`.
- **DESVIO de medição para R3/R4:** os PLY M apresentam ciclos de borda após a projeção das inserções. Para calcular volumes, o avaliador fecha ciclos temporariamente em memória com leques ao centróide e voxeliza a cópia; os PLY guardados não são modificados. O fechamento encontrou 138 ciclos no reto femoral M. Isso torna Dice, razão volumétrica e colisão aproximações dependentes do fechamento, não uma máscara volumétrica observada diretamente.
- **Correção de implementação da distância simétrica:** uma execução preliminar foi substituída porque amostrava 6.000 pontos numa direção e 12.000 na outra, ponderando a média de forma desigual. A execução final usa 6.000 amostras em cada direção e calcula a média aritmética das duas médias direcionais. Limiares e critérios não mudaram.
- A carga das STL Denver na avaliação funde vértices coincidentes de triângulos, necessário porque o formato STL armazena facetas sem conectividade explícita. A geometria não é deslocada por essa operação.
- Os critérios são avaliados com os dados de uma única doadora VHF; os músculos BP3D são masculinos. Diferença de volume muscular por sexo não é modelada. A análise não é validação clínica nem permite generalizar para outras doadoras.
- “10 músculos” no protocolo enumera as cabeças longa e curta do bíceps como um músculo; para preservar o denominador R1=10, mantive dois arquivos por cabeça e uni as cabeças nas métricas do grupo bíceps femoral.
- Para inserções e TPS, usei os seis ossos explicitamente citados mais sete ossos do pé com contraparte BP3D/Denver (calcâneo, cuboide, três cuneiformes, navicular e tálus), pois §5 inclui o pé e há músculos com inserções distais nessa região. A base ICP continua restrita aos três ossos especificados.

## Arquivos e reprodução

- `adaptar.py` — seleção pelo catálogo, checagem de coordenadas, ICP, inserções, TPS, projeção, relaxamento, exportação e hashes.
- `avaliar.py` — valida hashes primeiro; depois lê músculos Denver e calcula métricas, veredito e figura.
- `insercoes.csv`, `insercoes_vertices.json`, `hashes_adaptadas.json`, `metricas.csv`, `metricas_meta.json`, `veredito_R1_R4.txt`, `comparacao_B0_M_Denver.png`.
- Execução usada: `C:\Python314\python.exe pesquisa/resultados/EXP-0025/adaptar.py`; depois `C:\Python314\python.exe pesquisa/resultados/EXP-0025/avaliar.py`.
- Seeds: adaptação 25021; avaliação 25022. Versões registradas: Python 3.14.4; NumPy 2.4.6; SciPy 1.18.1; trimesh 5.2.2; scikit-image 0.26.0; Matplotlib 3.11.1.

**Revisão humana:** pendente. **Validação científica/clínica:** não realizada.
