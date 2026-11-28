# EXP-0025 — Rodada 3 (final)

**Estado:** execução concluída. Protocolo não alterado; rodadas 1 e 2 preservadas. A pré-condição Q-osso foi avaliada antes de qualquer músculo Denver. Como passou, M3 foi gerada e avaliada.

## Implementação CPD e integridade

- Coherent Point Drift não rígido, fonte móvel = 1.500 amostras de cada osso BP3D transformadas pelo B0; alvo fixo = 1.500 amostras Denver. Seed 25031; `w=0,1`, `beta=2,0`, `lambda=3,0`, até 150 iterações; norma comum por par (centro médio dos centroides e raio RMS combinado). Beta opera no referencial normalizado.
- Self-check obrigatório (esfera sintética → elipsoide com eixo 20% esticado): redução da distância média = 99.999880%; assert ≥80% passou.
- **DESVIO de implementação para viabilidade computacional:** a solução densa de CPD 1.500×1.500 por iteração foi interrompida antes de produzir métricas. Foi substituída por aproximação Nyström de posto 128 do kernel gaussiano, mantendo a E-step CPD, os hiperparâmetros, as amostras e o teto de iterações. A aproximação está registrada no manifesto; Q-osso mede sua qualidade fora da amostra. Não houve mudança de critério.
- B0: 11 PLY da rodada 1 copiados e hashes conferidos. Após Q-osso passar, foram gravadas 11 malhas M3; os 22 hashes (B0 + M3) foram conferidos antes de abrir músculos Denver. A adaptação não leu arquivos `_Muscle_`; só leu os 13 STL `_Bone_`.

## Q-osso (500 pontos holdout independentes por osso)

| Osso | B0, distância média (mm) | CPD, distância média (mm) | ≤2 mm | menor que B0 | Iterações |
|---|---:|---:|---|---|---:|
| pelvis | 4.404 | 1.432 | sim | sim | 150 |
| sacrum | 18.756 | 1.949 | sim | sim | 150 |
| femur | 4.567 | 0.964 | sim | sim | 90 |
| patella | 17.835 | 0.331 | sim | sim | 150 |
| tibia | 2.876 | 0.689 | sim | sim | 150 |
| fibula | 6.948 | 0.721 | sim | sim | 150 |
| calcaneus | 5.110 | 0.674 | sim | sim | 98 |
| cuboid | 18.486 | 0.433 | sim | sim | 150 |
| intermediate_cuneiform | 28.805 | 0.321 | sim | sim | 150 |
| lateral_cuneiform | 26.591 | 0.397 | sim | sim | 150 |
| medial_cuneiform | 27.649 | 0.384 | sim | sim | 150 |
| navicular | 14.931 | 0.399 | sim | sim | 132 |
| talus | 4.487 | 0.626 | sim | sim | 150 |

**Q-osso: PASSOU** (13/13 ossos). Foram medidos pontos BP3D fora da amostra CPD; a distância foi medida ponto-superfície no mesh Denver.

## Avaliação R1–R4 e medida exploratória

| Critério | Resultado |
|---|---|
| R1 — redução ≥20% em ≥8/10 | **1/10**; REPROVOU |
| R2 — mediana das inserções ≤2 mm | **0.000 mm** (n=4640); PASSOU |
| R3 — colisão <2% em todos | máximo **8.956%**; REPROVOU |
| R4 — Dice mediano ≥0,60 (exploratório) | **0.3623**; REPROVOU |

**Veredito:** H25 **REJEITADA**. R1 falhou; a regra de parada pré-registrada encerra EXP-0025 como rejeitado. Não há rodada 4.

| Grupo | Redução R1 M3 | Média simétrica B0 / M3 (mm) | Denver→adaptado B0 / M3 (mm) | Colisão M3 (%) | Dice M3 |
|---|---:|---:|---:|---:|---:|
| rectus_femoris | -44.7% | 18.68 / 27.04 | 7.80 / 9.35 | 2.385 | 0.1961 |
| vastus_lateralis | +3.1% | 10.24 / 9.93 | 10.03 / 9.73 | 2.103 | 0.4392 |
| vastus_medialis | -63.9% | 8.76 / 14.35 | 8.46 / 11.17 | 6.450 | 0.3025 |
| sartorius | -32.0% | 17.03 / 22.48 | 16.66 / 22.28 | 1.780 | 0.0676 |
| gracilis | -16.1% | 28.45 / 33.02 | 24.15 / 28.77 | 2.146 | 0.0019 |
| adductor_longus | -14.0% | 12.14 / 13.85 | 11.16 / 12.78 | 3.650 | 0.0579 |
| biceps_femoris | +7.4% | 9.71 / 8.99 | 7.78 / 7.41 | 1.532 | 0.4796 |
| gastrocnemius_medial | -39.0% | 7.17 / 9.96 | 4.87 / 8.60 | 1.203 | 0.4220 |
| gluteus_medius | +23.3% | 10.14 / 7.77 | 13.98 / 10.68 | 4.375 | 0.6663 |
| tibialis_anterior | +10.4% | 7.67 / 6.87 | 5.10 / 2.32 | 8.956 | 0.7677 |

A distância Denver→adaptado é exploratória, média de 6.000 pontos da superfície Denver às 6.000 amostras da superfície adaptada. As métricas completas, p95, volumes e contagens estão em `metricas_r3.csv`. R3/R4 usam voxelização de 1 mm e fechamento temporário em memória, como na rodada 1.

## Inserções M2b e limitações

- Inserções M3: vértices do BP3D a ≤3 mm de osso e nos 10% terminais de cada extremidade ao longo do eixo principal PCA; projeção e relaxamento laplaciano (12 iterações, fator 0,22). Frações por músculo/osso em `insercoes_m3.csv` e índices em `insercoes_vertices_m3.json`.
- R2 é em parte por construção porque os pontos de inserção são projetados no osso Denver. R3 é uma aproximação por voxels; contato de fronteira pode contribuir.
- B0 é idêntico aos arquivos arquivados. A rodada 2 registrou discrepância não resolvida: CSV rodada 1 tem 20,2167 mm para B0 do reto femoral, enquanto reamostragem registrada com seed 25022 deu 18,6840 mm. Nesta rodada, R1 compara M3 e B0 no mesmo lote/seed; isso limita comparação direta dos valores R1 entre rodadas.
- Um único indivíduo Denver e molde BP3D masculino; sem validação clínica ou generalização para outras mulheres.

Conferência final dos hashes: 22 malhas; divergências: nenhuma.

## Arquivos e reprodução

- `adaptar_r3.py`: self-check, CPD, Q-osso, parada condicional, M3 e hashes.
- `avaliar_r3.py`: verifica hashes e Q-osso antes de ler músculos Denver; calcula R1–R4 e Denver→adaptado.
- `qosso.csv`, `hashes_adaptadas_r3.json`, `insercoes_m3.csv`, `insercoes_vertices_m3.json`, `metricas_r3.csv`, `metricas_meta_r3.json`, `veredito_r3.txt` e malhas PLY.
- Reproduzir, nesta ordem: `C:\Python314\python.exe pesquisa/resultados/EXP-0025/rodada3/adaptar_r3.py`; se Q-osso passar, `C:\Python314\python.exe pesquisa/resultados/EXP-0025/rodada3/avaliar_r3.py`.

**Revisão humana:** pendente. **Validação científica/clínica:** não realizada.
