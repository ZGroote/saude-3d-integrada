# EXP-0025 — Rodada 2

**Estado:** execução concluída. O protocolo e a rodada 1 permaneceram intactos; H25 na rodada 1 continua rejeitada no registro original. A decisão desta rodada segue a seção 8.2: somente M2b em R1, R2 e R3 decide H25.

## Métodos e integridade

- **B0:** reutilizadas as 11 malhas B0 da rodada 1 (bíceps longo/curto em arquivos distintos). SHA-256 conferido antes da cópia e igual ao manifesto de origem; nenhuma malha B0 foi recalculada.
- **M2a:** thin-plate spline da rodada 1, sem projeção nem relaxamento.
- **M2b:** TPS; inserções definidas por vértices a ≤3 mm de osso BP3D **e** nos 10% terminais de uma das extremidades do eixo principal calculado por PCA separadamente em cada componente; projeção desses vértices no osso Denver e relaxamento laplaciano da rodada 1 (12 iterações, fator 0,22).
- **Barreira:** o adaptador mantém a asserção `_Muscle_` anterior à abertura e permite Denver somente com `_Bone_`; leu 13 caminhos ósseos e nenhum muscular. M2a/M2b e seus hashes foram gravados antes da avaliação abrir qualquer músculo Denver. O avaliador conferiu os 33 hashes (11 B0 + 11 M2a + 11 M2b) antes dessa leitura.
- Seeds: adaptação 25021; avaliação 25022; 6.000 pontos por direção e mesma regra de seeds por grupo da rodada 1; voxelização 1 mm.

## Resultados R1–R4

| Critério | M2a (secundário) | M2b (primário) |
|---|---|---|
| R1 — redução ≥20% em pelo menos 8/10 | REPROVOU (0/10) | REPROVOU (0/10) |
| R2 — mediana das inserções ≤2 mm | PASSOU (0.945 mm; n=4640) | PASSOU (0.000 mm; n=4640) |
| R3 — colisão <2% em todos os grupos | REPROVOU (máx. 20.081%; <2% em 3/10) | REPROVOU (máx. 23.316%; <2% em 3/10) |
| R4 — Dice mediano ≥0,60, exploratório | 0.2820 | 0.2668 |

**Veredito da rodada 2:** H25 **REJEITADA**: M2b falhou R1 (0/10) e R3; R2 passou. R4 é exploratório e não decide. M2a também falhou R1 e R3; não decide H25.

As reduções R1 por grupo, distâncias médias simétricas e distância exploratória Denver→adaptado estão em `metricas_r2.csv`. A distância unidirecional é a média de 6.000 pontos Denver até uma nuvem de 6.000 pontos da malha adaptada (aproximação por amostragem de superfície).

| Grupo | Redução R1 M2a | Redução R1 M2b | Simétrica média B0 / M2a / M2b (mm) | Denver→adaptado B0 / M2a / M2b (mm) |
|---|---:|---:|---:|---:|
| rectus_femoris | -16.9% | -15.7% | 18.68 / 21.84 / 21.62 | 7.80 / 9.60 / 10.02 |
| vastus_lateralis | -8.9% | -5.2% | 10.24 / 11.15 / 10.77 | 10.03 / 9.48 / 9.78 |
| vastus_medialis | -12.0% | -13.9% | 8.76 / 9.81 / 9.97 | 8.46 / 8.51 / 8.82 |
| sartorius | +3.3% | +8.9% | 17.03 / 16.47 / 15.51 | 16.66 / 15.45 / 15.88 |
| gracilis | -6.6% | -13.1% | 28.45 / 30.33 / 32.17 | 24.15 / 28.59 / 29.68 |
| adductor_longus | -4.7% | -7.4% | 12.14 / 12.71 / 13.04 | 11.16 / 13.53 / 13.90 |
| biceps_femoris | -22.3% | -21.3% | 9.71 / 11.87 / 11.78 | 7.78 / 9.56 / 10.22 |
| gastrocnemius_medial | -71.3% | -55.0% | 7.17 / 12.27 / 11.11 | 4.87 / 8.35 / 9.09 |
| gluteus_medius | -16.5% | -19.0% | 10.14 / 11.81 / 12.06 | 13.98 / 17.45 / 18.16 |
| tibialis_anterior | +3.0% | +5.6% | 7.67 / 7.44 / 7.24 | 5.10 / 3.92 / 4.20 |

## Fração de vértices de inserção M2b

| Músculo/componente | Vértices de inserção / total | Fração |
|---|---:|---:|
| rectus_femoris (único) | 398 / 3326 | 11.97% |
| vastus_lateralis (único) | 325 / 3974 | 8.18% |
| vastus_medialis (único) | 390 / 2772 | 14.07% |
| sartorius (único) | 585 / 2633 | 22.22% |
| gracilis (único) | 689 / 2085 | 33.05% |
| adductor_longus (único) | 240 / 1536 | 15.62% |
| biceps_femoris (longa) | 332 / 2837 | 11.70% |
| biceps_femoris (curta) | 256 / 1215 | 21.07% |
| gastrocnemius_medial (único) | 175 / 2264 | 7.73% |
| gluteus_medius (único) | 615 / 2308 | 26.65% |
| tibialis_anterior (único) | 635 / 2206 | 28.79% |
| **Total (10 grupos; 11 componentes)** | **4640 / 27156** | **17.09%** |

## Desvios, limitações e auditoria

- Não houve alteração de critérios nem desvio das regras M2a/M2b. Nenhum componente ficou sem vértices M2b selecionados.
- R2 usa os vértices candidatos M2b para ambos M2a/M2b. M2b projeta esses pontos por construção; R2 não é validação independente. M2a não projeta, mas usa o mesmo subconjunto para comparação.
- R3/R4 repetem a aproximação da rodada 1: voxelização a 1 mm, fechamento temporário de bordas em memória e união das malhas ósseas mapeadas. Contato de fronteira pode contribuir em R3; PLY gravados não são alterados pelo fechamento.
- **Inconsistência de reprodução da rodada 1:** o CSV arquivado registra 20.2167 mm para B0 do reto femoral. Recarregando os mesmos PLY e Denver com seed 25022 e a função simétrica atual, obtivemos 18.6840 mm; o SHA do B0 coincide com o manifesto da rodada 1. A causa não foi determinada. Nesta rodada, M2a/M2b foram comparados com o B0 medido no mesmo lote usando as seeds documentadas. Isso limita a comparação entre CSVs de rodadas, sem alterar critérios.
- Conferência final de SHA-256: 33 malhas; divergências: nenhuma.

## Arquivos e reprodução

- `adaptar_r2.py` — copia/verifica B0, adapta M2a/M2b, registra inserções e congela hashes.
- `avaliar_r2.py` — verifica hashes antes de ler músculos Denver e calcula R1–R4 e Denver→adaptado.
- Saídas: `hashes_adaptadas_r2.json`, `insercoes_m2b.csv`, `insercoes_vertices_m2b.json`, `metricas_r2.csv`, `metricas_meta_r2.json`, `veredito_r2.txt` e malhas PLY.
- Reproduzir em sequência com `C:\Python314\python.exe pesquisa/resultados/EXP-0025/rodada2/adaptar_r2.py` e depois `C:\Python314\python.exe pesquisa/resultados/EXP-0025/rodada2/avaliar_r2.py`. Sem instalação de pacotes.

**Revisão humana:** pendente. **Validação científica/clínica:** não realizada.
