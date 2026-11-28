# Alinhamento Denver → TC → HRA

Rodada EXP-0014 com a segmentação NLM em resolução normal. O EXP-0011 permanece REPROVADO pelo critério original do sacro de 3 mm; a aceitação desta rodada é avaliada pelos critérios por finalidade e pelas verificações funcionais abaixo.

## Etapa A — Denver STL → TC

Sinais vencedores: `[1, 1, 1]`; máscara sacrum contra união Denver Sacrum + Coccyx: média 3.785 mm, p95 9.602 mm.

| Estrutura | Média (mm) | P95 (mm) |
|---|---:|---:|
| Femur Left | 3.006 | 5.717 |
| Femur Right | 3.234 | 6.155 |
| Pelvis Left | 3.027 | 4.771 |
| Pelvis Right | 2.707 | 4.743 |
| Sacrum NLM vs Denver Sacrum + Coccyx (holdout) | 3.785 | 9.602 |

## Etapa B — TC → HRA **EXP-0011 REPROVADO no limite original do sacro de 3 mm; EXP-0014 avaliado independentemente.**

HRA convertido explicitamente de metros/eixos do app para RAS mm: `x_ras=-x_app*1000`, `y_ras=z_app*1000`, `z_ras=y_app*1000`. ICP sem busca de sinais/eixos, inicializado pela diferença de centroides das uniões pareadas; objetivo de distância média simétrica. Escala uniforme e por eixo limitadas a `[0.85, 1.15]`.

### Pareamento usado

| Máscara TotalSegmentator | Malha(s) HRA | Uso |
|---|---|---|
| vertebrae_L1 | VH_F_lumbar_vertebra_1 | ajuste |
| vertebrae_L2 | VH_F_lumbar_vertebra_2 | ajuste |
| vertebrae_L3 | VH_F_lumbar_vertebra_3 | ajuste |
| vertebrae_L4 | VH_F_lumbar_vertebra_4 | ajuste |
| vertebrae_L5 | VH_F_lumbar_vertebra_5 | ajuste |
| vertebrae_T10 | VH_F_thoracic_vertebra_10 | ajuste |
| vertebrae_T11 | VH_F_thoracic_vertebra_11 | ajuste |
| vertebrae_T12 | VH_F_thoracic_vertebra_12 | ajuste |
| sacrum | VH_F_sacrum | ajuste |
| femur_left | VH_F_femur_L | ajuste |
| femur_right | VH_F_femur_R | ajuste |
| hip_left | VH_F_ilium_compact_bone_L, VH_F_ilium_spongy_bone_L | ajuste |
| hip_right | VH_F_ilium_compact_bone_R, VH_F_ilium_spongy_bone_R | ajuste |
| kidney_left | VH_F_kidney_capsule_L, VH_F_outer_cortex_of_kidney_L, VH_F_hilum_of_kidney_L, VH_F_renal_pelvis_L | validação holdout (composite HRA, approximate) |
| kidney_right | VH_F_kidney_capsule_R, VH_F_outer_cortex_of_kidney_R, VH_F_hilum_of_kidney_R, VH_F_renal_pelvis_R | validação holdout (composite HRA, approximate) |
| superior_vena_cava | VH_F_superior_vena_cava | validação holdout (large-vessel holdout) |
| inferior_vena_cava | VH_F_inferior_vena_cava_a, VH_F_inferior_vena_cava_b | validação holdout (large-vessel composite holdout) |
| pulmonary_vein | VH_F_pulmonary_vein_L_sup, VH_F_pulmonary_vein_R_inf, VH_F_pulmonary_vein_R_sup, VH_F_pulmonary_vein_L_inf | validação holdout (large-vessel composite holdout) |
| liver | VH_F_bare_area_of_liver, VH_F_capsule_of_the_liver, VH_F_caudate_lobe, VH_F_colic_impression_of_liver, VH_F_coronary_ligament_of_liver, VH_F_diaphragmatic_surface_of_liver, VH_F_duodenal_impression_of_liver, VH_F_esophageal_impression_of_liver, VH_F_falciform_ligament, VH_F_gastric_impression_of_liver, VH_F_hepataduodenal_ligament, VH_F_left_anterolateral_segment, VH_F_left_inferomedial_segment, VH_F_left_superomedial_segment, VH_F_left_superomedial_segment1, VH_F_ligamentum_venosum, VH_F_porta_hepatis, VH_F_quadrate_lobe, VH_F_renal_impression_of_liver, VH_F_right_anteroinferior_segment, VH_F_right_anterosuperior_segment, VH_F_right_posteroinferior_segment, VH_F_right_posterosuperior_segment, VH_F_round_ligament_of_liver, VH_F_suprarenal_impression_of_liver, VH_F_triangular_ligament_of_liver | validação holdout (HRA catalog organ-group composite; diagnostic) |
| spleen | VH_F_colic_surface_of_spleen, VH_F_diaphragmatic_surface_of_spleen, VH_F_gastric_surface_of_spleen, VH_F_hilum_of_spleen, VH_F_renal_surface_of_spleen | validação holdout (HRA catalog organ-group composite; diagnostic) |
| heart | VH_F_aortic_valve, VH_F_interventricular_septum, VH_F_left_cardiac_atrium, VH_F_left_ventricle, VH_F_mitral_valve, VH_F_papillary_muscle_of_heart_ant, VH_F_papillary_muscle_of_heart_antlat, VH_F_papillary_muscle_of_heart_med, VH_F_papillary_muscle_of_heart_pos, VH_F_papillary_muscle_of_heart_posmed, VH_F_pulmonary_valve, VH_F_right_cardiac_atrium, VH_F_right_ventricle, VH_F_tricuspid_valve | validação holdout (HRA catalog organ-group composite; diagnostic) |

### Similaridade uniforme

| Estrutura | Média (mm) | P95 (mm) |
|---|---:|---:|
| vertebrae_L1 | 5.649 | 29.944 |
| vertebrae_L2 | 7.661 | 32.189 |
| vertebrae_L3 | 11.796 | 32.348 |
| vertebrae_L4 | 19.155 | 35.653 |
| vertebrae_L5 | 19.228 | 36.734 |
| vertebrae_T10 | 2.399 | 4.331 |
| vertebrae_T11 | 2.116 | 3.735 |
| vertebrae_T12 | 1.786 | 3.107 |
| sacrum | 3.704 | 10.386 |
| femur_left | 10.541 | 30.964 |
| femur_right | 19.747 | 49.640 |
| hip_left | 11.857 | 73.494 |
| hip_right | 11.777 | 71.875 |

### Escala por eixo

Escalas XYZ: `[1.0942753201022495, 1.0111053630757378, 0.9933437591081744]`; alteração da média de ajuste: 11.11%.

| Estrutura | Média (mm) | P95 (mm) |
|---|---:|---:|
| vertebrae_L1 | 5.637 | 30.251 |
| vertebrae_L2 | 7.674 | 31.620 |
| vertebrae_L3 | 11.547 | 31.135 |
| vertebrae_L4 | 17.862 | 33.396 |
| vertebrae_L5 | 17.188 | 33.229 |
| vertebrae_T10 | 1.822 | 3.443 |
| vertebrae_T11 | 1.700 | 3.246 |
| vertebrae_T12 | 1.659 | 3.102 |
| sacrum | 3.514 | 9.470 |
| femur_left | 9.459 | 29.828 |
| femur_right | 14.091 | 42.644 |
| hip_left | 11.546 | 66.765 |
| hip_right | 9.560 | 63.237 |

### Validação fora do ajuste

| Estrutura | Similaridade média/P95 (mm) | Escala XYZ média/P95 (mm) |
|---|---:|---:|
| kidney_left | 4.588/8.991 | 4.753/9.133 |
| kidney_right | 4.433/8.900 | 5.820/12.476 |
| superior_vena_cava | 5.678/11.186 | 6.338/11.829 |
| inferior_vena_cava | 4.800/15.107 | 4.962/13.687 |
| pulmonary_vein | 4.958/11.194 | 4.795/12.219 |
| liver | 5.108/10.379 | 6.177/13.456 |
| spleen | 3.791/8.065 | 4.954/9.645 |
| heart | 8.240/23.992 | 8.163/21.985 |

Matrizes 4×4, parâmetros e erros completos: `transformacoes.json`.

## EXP-0014 - critério de aceitação por finalidade

Os limites abaixo são propostas de engenharia para investigação e não foram validados clinicamente. O EXP-0011 permanece REPROVADO sob o critério original de 3 mm; o EXP-0014 registra uma mudança de critério sem alterar retroativamente aquele resultado.
Esta rodada usou a segmentação `normal` em `hra\nlm\bruto\saida\segmentacao.nii.gz`.

### Critérios geométricos

| Classe | Limite médio (mm) | Limite p95 (mm) | Similaridade | Escala XYZ |
|---|---:|---:|---|---|
| skin | 10.0 | N/A | N/A (0) | N/A (0) |
| large_bones | 5.0 | 12.0 | FAIL (78) | FAIL (78) |
| large_organs | 5.0 | 12.0 | FAIL (5) | FAIL (5) |
| large_muscles | 5.0 | 12.0 | N/A (72) | N/A (72) |
| vertebrae | 3.0 | N/A | FAIL (8) | FAIL (8) |
| large_vessels | 3.0 | N/A | FAIL (14) | FAIL (14) |
| individual_review | N/A | N/A | REVIEW (8) | REVIEW (8) |

| Estrutura | Classe | Média / p95 similaridade (mm) | Estado | Média / p95 escala XYZ (mm) | Estado |
|---|---|---:|---|---:|---|
| vertebrae_L1 | vertebrae | 5.649 / 29.944 | FAIL | 5.637 / 30.251 | FAIL |
| vertebrae_L2 | vertebrae | 7.661 / 32.189 | FAIL | 7.674 / 31.620 | FAIL |
| vertebrae_L3 | vertebrae | 11.796 / 32.348 | FAIL | 11.547 / 31.135 | FAIL |
| vertebrae_L4 | vertebrae | 19.155 / 35.653 | FAIL | 17.862 / 33.396 | FAIL |
| vertebrae_L5 | vertebrae | 19.228 / 36.734 | FAIL | 17.188 / 33.229 | FAIL |
| vertebrae_T10 | vertebrae | 2.399 / 4.331 | PASS | 1.822 / 3.443 | PASS |
| vertebrae_T11 | vertebrae | 2.116 / 3.735 | PASS | 1.700 / 3.246 | PASS |
| vertebrae_T12 | vertebrae | 1.786 / 3.107 | PASS | 1.659 / 3.102 | PASS |
| sacrum | large_bones | 3.704 / 10.386 | PASS | 3.514 / 9.470 | PASS |
| femur_left | large_bones | 10.541 / 30.964 | FAIL | 9.459 / 29.828 | FAIL |
| femur_right | large_bones | 19.747 / 49.640 | FAIL | 14.091 / 42.644 | FAIL |
| hip_left | large_bones | 11.857 / 73.494 | FAIL | 11.546 / 66.765 | FAIL |
| hip_right | large_bones | 11.777 / 71.875 | FAIL | 9.560 / 63.237 | FAIL |
| kidney_left | large_organs | 4.588 / 8.991 | PASS | 4.753 / 9.133 | PASS |
| kidney_right | large_organs | 4.433 / 8.900 | PASS | 5.820 / 12.476 | FAIL |
| superior_vena_cava | large_vessels | 5.678 / 11.186 | FAIL | 6.338 / 11.829 | FAIL |
| inferior_vena_cava | large_vessels | 4.800 / 15.107 | FAIL | 4.962 / 13.687 | FAIL |
| pulmonary_vein | large_vessels | 4.958 / 11.194 | FAIL | 4.795 / 12.219 | FAIL |
| liver | large_organs | 5.108 / 10.379 | FAIL | 6.177 / 13.456 | FAIL |
| spleen | large_organs | 3.791 / 8.065 | PASS | 4.954 / 9.645 | PASS |
| heart | large_organs | 8.240 / 23.992 | FAIL | 8.163 / 21.985 | FAIL |
| Bone Calcaneous Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Cuboid Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Femur Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Fibula Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone IntermediateCuneiform Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone LateralCuneiform Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone MedialCuneiform Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Navicular Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Patella Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Phalanges Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Talus Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Tibia Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Cartilage FemurDistal Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Cartilage FemurHead Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Cartilage Patella Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Cartilage Talus Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Cartilage TibiaDistal Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Cartilage TibiaLateral Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Cartilage TibiaMedial Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Ligament ACL Left | individual_review | N/A / N/A | REVIEW | N/A / N/A | REVIEW |
| Ligament LCL Left | individual_review | N/A / N/A | REVIEW | N/A / N/A | REVIEW |
| Ligament MCL Left | individual_review | N/A / N/A | REVIEW | N/A / N/A | REVIEW |
| Ligament PCL Left | individual_review | N/A / N/A | REVIEW | N/A / N/A | REVIEW |
| Muscle AdductorBrevis Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle AdductorLongus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle AdductorMagnus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle BicepsFemorisLong Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle BicepsFemorisShort Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle ExtensorDigitorumLongus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle ExtensorHallucisLongus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle FlexorDigitorumLongus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle FlexorHallucisLongus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle GastrocnemiusLateral Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle GastrocnemiusMedial Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle GluteusMaximus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle GluteusMedius Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle GluteusMinimus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Gracilis Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Illiacus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle InferiorGemellus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle ObturatorExternus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle ObturatorInternus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Pectineus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle PeroneusLongus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Piriformis Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Plantaris Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Popliteus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle PsoasMajor Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle QuadratusFemoris Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle RectusFemoris Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Sartorius Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Semimembranosus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Semitendinosus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Soleus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle SuperiorGemellus Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle TensorFasciaeLatae Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle TibialisAnterior Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle TibialisPosterior Left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle VastusIntermedius Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle VastusLateralis Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle VastusMedialis Left | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Calcaneous Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Cuboid Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Femur Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Fibula Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone IntermediateCuneiform Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone LateralCuneiform Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone MedialCuneiform Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Navicular Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Patella Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Phalanges Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Talus Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Bone Tibia Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Cartilage FemurDistal Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Cartilage FemurHead Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Cartilage Patella Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Cartilage Talus Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Cartilage TibiaDistal Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Cartilage TibiaLateral Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Cartilage TibiaMedial Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Ligament ACL Right | individual_review | N/A / N/A | REVIEW | N/A / N/A | REVIEW |
| Ligament LCL Right | individual_review | N/A / N/A | REVIEW | N/A / N/A | REVIEW |
| Ligament MCL Right | individual_review | N/A / N/A | REVIEW | N/A / N/A | REVIEW |
| Ligament PCL Right | individual_review | N/A / N/A | REVIEW | N/A / N/A | REVIEW |
| Muscle AdductorBrevis Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle AdductorLongus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle AdductorMagnus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle BicepsFemorisLongHead Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle BicepsFemorisShortHead Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle ExtensorDigitorumLongus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle ExtensorHallucisLongus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle FlexorDigitorumLongus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle FlexorHallucisLongus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle GastrocnemiusLateral Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle GastrocnemiusMedial Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle GluteusMaximus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle GluteusMedius Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle GluteusMinimus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Gracilis Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Illiacus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle InferiorGemellus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle ObturatorExternus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle ObturatorInternus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Pectineus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle PeroneusLongus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Piriformis Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Plantaris Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Popliteus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle PsoasMajor Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle QuadratisFemoris Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle RectusFemoris Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Sartorius Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Semimembranosus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Semitendonosus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle Soleus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle SuperiorGemellus Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle TensorFasciaeLatae Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle TibialisAnterior Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle TibialisPosterior Right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle VastusIntermedius Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle VastusLateralis Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| Muscle VastusMedialis Right | large_muscles | N/A / N/A | N/A | N/A / N/A | N/A |
| aorta | large_vessels | N/A / N/A | N/A | N/A / N/A | N/A |
| brachiocephalic_trunk | large_vessels | N/A / N/A | N/A | N/A / N/A | N/A |
| brachiocephalic_vein_left | large_vessels | N/A / N/A | N/A | N/A / N/A | N/A |
| brachiocephalic_vein_right | large_vessels | N/A / N/A | N/A | N/A / N/A | N/A |
| clavicula_left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| clavicula_right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| common_carotid_artery_left | large_vessels | N/A / N/A | N/A | N/A / N/A | N/A |
| common_carotid_artery_right | large_vessels | N/A / N/A | N/A | N/A / N/A | N/A |
| humerus_left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| humerus_right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| iliac_artery_left | large_vessels | N/A / N/A | N/A | N/A / N/A | N/A |
| iliac_artery_right | large_vessels | N/A / N/A | N/A | N/A / N/A | N/A |
| portal_vein_and_splenic_vein | large_vessels | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_left_1 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_left_10 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_left_11 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_left_12 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_left_2 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_left_3 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_left_4 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_left_5 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_left_6 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_left_7 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_left_8 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_left_9 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_right_1 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_right_10 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_right_11 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_right_12 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_right_2 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_right_3 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_right_4 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_right_5 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_right_6 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_right_7 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_right_8 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| rib_right_9 | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| scapula_left | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| scapula_right | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| skull | large_bones | N/A / N/A | N/A | N/A / N/A | N/A |
| subclavian_artery_left | large_vessels | N/A / N/A | N/A | N/A / N/A | N/A |
| subclavian_artery_right | large_vessels | N/A / N/A | N/A | N/A / N/A | N/A |

### F1 - contenção assinada na pele HRA

Estado geral: FAIL. Pele disponível: True; malha fechada: False; orientação: median_radial_normal_points_outward; escore radial mediano: 125.09167077737457; fração de faces radiais externas: 0.7905667876533581; verificação: global winding retained; positive median radial dot means majority orientation is outward; open concave regions can have locally negative radial dots. Each imported vertex is queried against the 4 nearest skin triangle centroids; closest points are computed exactly on those candidate triangles and signed offsets use the local skin normal. Open-surface orientation uses median radial face-normal direction from the mesh centroid.

| Estrutura importada | Fonte | Vértices | Fração fora | Distância máxima fora (mm) | Estado |
|---|---|---:|---:|---:|---|
| Bone Calcaneous Left | Denver | 52416 | 0.16142 (16.14%) | 7.423 | FAIL |
| Bone Cuboid Left | Denver | 14778 | 0.72405 (72.40%) | 24.084 | FAIL |
| Bone Femur Left | Denver | 275658 | 0.00000 (0.00%) | 0.000 | PASS |
| Bone Fibula Left | Denver | 56754 | 0.02284 (2.28%) | 2.848 | FAIL |
| Bone IntermediateCuneiform Left | Denver | 6984 | 0.68099 (68.10%) | 16.930 | FAIL |
| Bone LateralCuneiform Left | Denver | 8094 | 0.80702 (80.70%) | 20.850 | FAIL |
| Bone MedialCuneiform Left | Denver | 12270 | 0.98003 (98.00%) | 29.712 | FAIL |
| Bone Navicular Left | Denver | 13830 | 0.23160 (23.16%) | 7.748 | FAIL |
| Bone Patella Left | Denver | 19572 | 0.00000 (0.00%) | 0.000 | PASS |
| Bone Phalanges Left | Denver | 104820 | 1.00000 (100.00%) | 91.313 | FAIL |
| Bone Talus Left | Denver | 33222 | 0.00000 (0.00%) | 0.000 | PASS |
| Bone Tibia Left | Denver | 178368 | 0.00000 (0.00%) | 0.000 | PASS |
| Cartilage FemurDistal Left | Denver | 84432 | 0.00000 (0.00%) | 0.000 | PASS |
| Cartilage FemurHead Left | Denver | 49722 | 0.00000 (0.00%) | 0.000 | PASS |
| Cartilage Patella Left | Denver | 19722 | 0.00000 (0.00%) | 0.000 | PASS |
| Cartilage Talus Left | Denver | 119964 | 0.00000 (0.00%) | 0.000 | PASS |
| Cartilage TibiaDistal Left | Denver | 8124 | 0.00000 (0.00%) | 0.000 | PASS |
| Cartilage TibiaLateral Left | Denver | 11430 | 0.00000 (0.00%) | 0.000 | PASS |
| Cartilage TibiaMedial Left | Denver | 17316 | 0.00000 (0.00%) | 0.000 | PASS |
| Ligament ACL Left | Denver | 10818 | 0.00000 (0.00%) | 0.000 | PASS |
| Ligament LCL Left | Denver | 6150 | 0.05626 (5.63%) | 0.993 | FAIL |
| Ligament MCL Left | Denver | 12852 | 0.00000 (0.00%) | 0.000 | PASS |
| Ligament PCL Left | Denver | 11442 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle AdductorBrevis Left | Denver | 33360 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle AdductorLongus Left | Denver | 37320 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle AdductorMagnus Left | Denver | 94500 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle BicepsFemorisLong Left | Denver | 53358 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle BicepsFemorisShort Left | Denver | 36714 | 0.02217 (2.22%) | 2.433 | FAIL |
| Muscle ExtensorDigitorumLongus Left | Denver | 26556 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle ExtensorHallucisLongus Left | Denver | 12186 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle FlexorDigitorumLongus Left | Denver | 18792 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle FlexorHallucisLongus Left | Denver | 27648 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle GastrocnemiusLateral Left | Denver | 33942 | 0.19159 (19.16%) | 5.114 | FAIL |
| Muscle GastrocnemiusMedial Left | Denver | 59574 | 0.13315 (13.31%) | 6.348 | FAIL |
| Muscle GluteusMaximus Left | Denver | 137328 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle GluteusMedius Left | Denver | 90216 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle GluteusMinimus Left | Denver | 50982 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Gracilis Left | Denver | 40068 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Illiacus Left | Denver | 66990 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle InferiorGemellus Left | Denver | 3462 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle ObturatorExternus Left | Denver | 43674 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle ObturatorInternus Left | Denver | 54786 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Pectineus Left | Denver | 133368 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle PeroneusLongus Left | Denver | 48648 | 0.10399 (10.40%) | 3.105 | FAIL |
| Muscle Piriformis Left | Denver | 19458 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Plantaris Left | Denver | 5640 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Popliteus Left | Denver | 9168 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle PsoasMajor Left | Denver | 59076 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle QuadratusFemoris Left | Denver | 16176 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle RectusFemoris Left | Denver | 48846 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Sartorius Left | Denver | 56682 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Semimembranosus Left | Denver | 61830 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Semitendinosus Left | Denver | 40878 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Soleus Left | Denver | 85356 | 0.00258 (0.26%) | 0.794 | PASS |
| Muscle SuperiorGemellus Left | Denver | 2712 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle TensorFasciaeLatae Left | Denver | 27846 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle TibialisAnterior Left | Denver | 37260 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle TibialisPosterior Left | Denver | 31866 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle VastusIntermedius Left | Denver | 111852 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle VastusLateralis Left | Denver | 126450 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle VastusMedialis Left | Denver | 81900 | 0.00000 (0.00%) | 0.000 | PASS |
| Bone Calcaneous Right | Denver | 52722 | 0.34983 (34.98%) | 11.695 | FAIL |
| Bone Cuboid Right | Denver | 15126 | 0.84266 (84.27%) | 26.198 | FAIL |
| Bone Femur Right | Denver | 268398 | 0.00000 (0.00%) | 0.000 | PASS |
| Bone Fibula Right | Denver | 58440 | 0.00000 (0.00%) | 0.000 | PASS |
| Bone IntermediateCuneiform Right | Denver | 6942 | 0.99741 (99.74%) | 24.679 | FAIL |
| Bone LateralCuneiform Right | Denver | 8424 | 0.97448 (97.45%) | 27.236 | FAIL |
| Bone MedialCuneiform Right | Denver | 12648 | 1.00000 (100.00%) | 39.436 | FAIL |
| Bone Navicular Right | Denver | 13494 | 0.47666 (47.67%) | 12.641 | FAIL |
| Bone Patella Right | Denver | 19764 | 0.00000 (0.00%) | 0.000 | PASS |
| Bone Phalanges Right | Denver | 108606 | 1.00000 (100.00%) | 97.163 | FAIL |
| Bone Talus Right | Denver | 32028 | 0.00000 (0.00%) | 0.000 | PASS |
| Bone Tibia Right | Denver | 181086 | 0.00000 (0.00%) | 0.000 | PASS |
| Cartilage FemurDistal Right | Denver | 73884 | 0.00000 (0.00%) | 0.000 | PASS |
| Cartilage FemurHead Right | Denver | 68844 | 0.00000 (0.00%) | 0.000 | PASS |
| Cartilage Patella Right | Denver | 16998 | 0.00000 (0.00%) | 0.000 | PASS |
| Cartilage Talus Right | Denver | 13452 | 0.00000 (0.00%) | 0.000 | PASS |
| Cartilage TibiaDistal Right | Denver | 10572 | 0.00000 (0.00%) | 0.000 | PASS |
| Cartilage TibiaLateral Right | Denver | 15312 | 0.00000 (0.00%) | 0.000 | PASS |
| Cartilage TibiaMedial Right | Denver | 19482 | 0.00000 (0.00%) | 0.000 | PASS |
| Ligament ACL Right | Denver | 12888 | 0.00000 (0.00%) | 0.000 | PASS |
| Ligament LCL Right | Denver | 6066 | 0.00000 (0.00%) | 0.000 | PASS |
| Ligament MCL Right | Denver | 9330 | 0.00000 (0.00%) | 0.000 | PASS |
| Ligament PCL Right | Denver | 10836 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle AdductorBrevis Right | Denver | 32814 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle AdductorLongus Right | Denver | 38550 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle AdductorMagnus Right | Denver | 94890 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle BicepsFemorisLongHead Right | Denver | 52302 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle BicepsFemorisShortHead Right | Denver | 33294 | 0.01123 (1.12%) | 2.015 | FAIL |
| Muscle ExtensorDigitorumLongus Right | Denver | 29760 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle ExtensorHallucisLongus Right | Denver | 11022 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle FlexorDigitorumLongus Right | Denver | 18846 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle FlexorHallucisLongus Right | Denver | 27222 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle GastrocnemiusLateral Right | Denver | 36114 | 0.53771 (53.77%) | 13.803 | FAIL |
| Muscle GastrocnemiusMedial Right | Denver | 57240 | 0.18015 (18.02%) | 8.492 | FAIL |
| Muscle GluteusMaximus Right | Denver | 145308 | 0.00096 (0.10%) | 0.281 | PASS |
| Muscle GluteusMedius Right | Denver | 78474 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle GluteusMinimus Right | Denver | 47742 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Gracilis Right | Denver | 39036 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Illiacus Right | Denver | 61608 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle InferiorGemellus Right | Denver | 6234 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle ObturatorExternus Right | Denver | 46332 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle ObturatorInternus Right | Denver | 76500 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Pectineus Right | Denver | 19410 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle PeroneusLongus Right | Denver | 49518 | 0.33242 (33.24%) | 8.275 | FAIL |
| Muscle Piriformis Right | Denver | 18564 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Plantaris Right | Denver | 5016 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Popliteus Right | Denver | 9300 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle PsoasMajor Right | Denver | 53268 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle QuadratisFemoris Right | Denver | 207444 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle RectusFemoris Right | Denver | 45888 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Sartorius Right | Denver | 58572 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Semimembranosus Right | Denver | 59592 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Semitendonosus Right | Denver | 41148 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle Soleus Right | Denver | 85680 | 0.18955 (18.96%) | 10.865 | FAIL |
| Muscle SuperiorGemellus Right | Denver | 3180 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle TensorFasciaeLatae Right | Denver | 27984 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle TibialisAnterior Right | Denver | 35658 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle TibialisPosterior Right | Denver | 29862 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle VastusIntermedius Right | Denver | 107010 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle VastusLateralis Right | Denver | 122202 | 0.00000 (0.00%) | 0.000 | PASS |
| Muscle VastusMedialis Right | Denver | 73074 | 0.00000 (0.00%) | 0.000 | PASS |
| aorta | TotalSegmentator | 22732 | 0.00000 (0.00%) | 0.000 | PASS |
| brachiocephalic_trunk | TotalSegmentator | 744 | 0.00000 (0.00%) | 0.000 | PASS |
| brachiocephalic_vein_left | TotalSegmentator | 2132 | 0.00000 (0.00%) | 0.000 | PASS |
| brachiocephalic_vein_right | TotalSegmentator | 1294 | 0.00000 (0.00%) | 0.000 | PASS |
| clavicula_left | TotalSegmentator | 5292 | 0.30310 (30.31%) | 28.733 | FAIL |
| clavicula_right | TotalSegmentator | 5468 | 0.16295 (16.29%) | 16.930 | FAIL |
| common_carotid_artery_left | TotalSegmentator | 1570 | 0.00000 (0.00%) | 0.000 | PASS |
| common_carotid_artery_right | TotalSegmentator | 1046 | 0.00000 (0.00%) | 0.000 | PASS |
| humerus_left | TotalSegmentator | 17714 | 0.26324 (26.32%) | 40.606 | FAIL |
| humerus_right | TotalSegmentator | 16676 | 0.17138 (17.14%) | 24.190 | FAIL |
| iliac_artery_left | TotalSegmentator | 3362 | 0.00000 (0.00%) | 0.000 | PASS |
| iliac_artery_right | TotalSegmentator | 3542 | 0.00000 (0.00%) | 0.000 | PASS |
| portal_vein_and_splenic_vein | TotalSegmentator | 3923 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_left_1 | TotalSegmentator | 3337 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_left_10 | TotalSegmentator | 4302 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_left_11 | TotalSegmentator | 3608 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_left_12 | TotalSegmentator | 2095 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_left_2 | TotalSegmentator | 4185 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_left_3 | TotalSegmentator | 4694 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_left_4 | TotalSegmentator | 5092 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_left_5 | TotalSegmentator | 5710 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_left_6 | TotalSegmentator | 6397 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_left_7 | TotalSegmentator | 5539 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_left_8 | TotalSegmentator | 4935 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_left_9 | TotalSegmentator | 4380 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_right_1 | TotalSegmentator | 3584 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_right_10 | TotalSegmentator | 4297 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_right_11 | TotalSegmentator | 3668 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_right_12 | TotalSegmentator | 2146 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_right_2 | TotalSegmentator | 4020 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_right_3 | TotalSegmentator | 4501 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_right_4 | TotalSegmentator | 4996 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_right_5 | TotalSegmentator | 5927 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_right_6 | TotalSegmentator | 6534 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_right_7 | TotalSegmentator | 5644 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_right_8 | TotalSegmentator | 4696 | 0.00000 (0.00%) | 0.000 | PASS |
| rib_right_9 | TotalSegmentator | 4302 | 0.00000 (0.00%) | 0.000 | PASS |
| scapula_left | TotalSegmentator | 18603 | 0.17868 (17.87%) | 33.019 | FAIL |
| scapula_right | TotalSegmentator | 19306 | 0.10841 (10.84%) | 20.384 | FAIL |
| skull | TotalSegmentator | 117156 | 0.02977 (2.98%) | 6.462 | FAIL |
| subclavian_artery_left | TotalSegmentator | 2292 | 0.00000 (0.00%) | 0.000 | PASS |
| subclavian_artery_right | TotalSegmentator | 2088 | 0.00000 (0.00%) | 0.000 | PASS |

### F2 - articulações e emendas regionais

Estado geral: FAIL

| Articulação | Distância (mm) | Limite (mm) | Estado |
|---|---:|---:|---|
| Denver femoral head center to HRA acetabulum proxy left | 17.139 | 5.0 | FAIL |
| rib_left_1 to T1 | 1.599 | 5.0 | PASS |
| rib_left_2 to T2 | 1.589 | 5.0 | PASS |
| rib_left_3 to T3 | 4.532 | 5.0 | PASS |
| rib_left_4 to T4 | 7.033 | 5.0 | FAIL |
| rib_left_5 to T5 | 6.302 | 5.0 | FAIL |
| rib_left_6 to T6 | 6.954 | 5.0 | FAIL |
| rib_left_7 to T7 | 3.682 | 5.0 | PASS |
| rib_left_8 to T8 | 3.361 | 5.0 | PASS |
| rib_left_9 to T9 | 2.800 | 5.0 | PASS |
| rib_left_10 to T10 | 1.801 | 5.0 | PASS |
| rib_left_11 to T11 | 4.913 | 5.0 | PASS |
| rib_left_12 to T12 | 4.428 | 5.0 | PASS |
| Denver femoral head center to HRA acetabulum proxy right | 20.590 | 5.0 | FAIL |
| rib_right_1 to T1 | 0.348 | 5.0 | PASS |
| rib_right_2 to T2 | 0.291 | 5.0 | PASS |
| rib_right_3 to T3 | 1.455 | 5.0 | PASS |
| rib_right_4 to T4 | 2.790 | 5.0 | PASS |
| rib_right_5 to T5 | 3.271 | 5.0 | PASS |
| rib_right_6 to T6 | 3.048 | 5.0 | PASS |
| rib_right_7 to T7 | 2.473 | 5.0 | PASS |
| rib_right_8 to T8 | 2.537 | 5.0 | PASS |
| rib_right_9 to T9 | 2.863 | 5.0 | PASS |
| rib_right_10 to T10 | 1.779 | 5.0 | PASS |
| rib_right_11 to T11 | 5.324 | 5.0 | FAIL |
| rib_right_12 to T12 | 10.712 | 5.0 | FAIL |
| skull to C1 | 0.678 | 5.0 | PASS |
| Regional seam head_neck/thorax | 1.689 | 5.0 | PASS |
| Regional seam thorax/abdomen_pelvis | 1.810 | 5.0 | PASS |

### F3 - sobreposição de volume com órgãos/ossos HRA

Estado geral: FAIL. Amostragem: up to 5,000 interior voxel centers per source mesh at 5 mm pitch. Campo de obstáculos: malhas preenchidas voxelizadas a 5 mm em grade comum do mundo.

| Estrutura importada | Fonte | Amostras internas | Fração sobreposta | Estado |
|---|---|---:|---:|---|
| Bone Calcaneous Left | Denver | 1005 | 0.00000 (0.00%) | PASS |
| Bone Cuboid Left | Denver | 229 | 0.00000 (0.00%) | PASS |
| Bone Femur Left | Denver | 4508 | 0.00466 (0.47%) | PASS |
| Bone Fibula Left | Denver | 699 | 0.00000 (0.00%) | PASS |
| Bone IntermediateCuneiform Left | Denver | 91 | 0.00000 (0.00%) | PASS |
| Bone LateralCuneiform Left | Denver | 105 | 0.00000 (0.00%) | PASS |
| Bone MedialCuneiform Left | Denver | 180 | 0.00000 (0.00%) | PASS |
| Bone Navicular Left | Denver | 192 | 0.00000 (0.00%) | PASS |
| Bone Patella Left | Denver | 327 | 0.00000 (0.00%) | PASS |
| Bone Phalanges Left | Denver | 1435 | 0.00000 (0.00%) | PASS |
| Bone Talus Left | Denver | 591 | 0.00000 (0.00%) | PASS |
| Bone Tibia Left | Denver | 3558 | 0.00000 (0.00%) | PASS |
| Cartilage FemurDistal Left | Denver | 347 | 0.00000 (0.00%) | PASS |
| Cartilage FemurHead Left | Denver | 191 | 0.17801 (17.80%) | FAIL |
| Cartilage Patella Left | Denver | 110 | 0.00000 (0.00%) | PASS |
| Cartilage Talus Left | Denver | 5 | 0.00000 (0.00%) | PASS |
| Cartilage TibiaDistal Left | Denver | 36 | 0.00000 (0.00%) | PASS |
| Cartilage TibiaLateral Left | Denver | 54 | 0.00000 (0.00%) | PASS |
| Cartilage TibiaMedial Left | Denver | 91 | 0.00000 (0.00%) | PASS |
| Ligament ACL Left | Denver | 79 | 0.00000 (0.00%) | PASS |
| Ligament LCL Left | Denver | 48 | 0.00000 (0.00%) | PASS |
| Ligament MCL Left | Denver | 81 | 0.00000 (0.00%) | PASS |
| Ligament PCL Left | Denver | 83 | 0.00000 (0.00%) | PASS |
| Muscle AdductorBrevis Left | Denver | 843 | 0.00000 (0.00%) | PASS |
| Muscle AdductorLongus Left | Denver | 1039 | 0.00000 (0.00%) | PASS |
| Muscle AdductorMagnus Left | Denver | 3897 | 0.00000 (0.00%) | PASS |
| Muscle BicepsFemorisLong Left | Denver | 1854 | 0.00000 (0.00%) | PASS |
| Muscle BicepsFemorisShort Left | Denver | 850 | 0.00000 (0.00%) | PASS |
| Muscle ExtensorDigitorumLongus Left | Denver | 713 | 0.00000 (0.00%) | PASS |
| Muscle ExtensorHallucisLongus Left | Denver | 308 | 0.00000 (0.00%) | PASS |
| Muscle FlexorDigitorumLongus Left | Denver | 511 | 0.00000 (0.00%) | PASS |
| Muscle FlexorHallucisLongus Left | Denver | 919 | 0.00000 (0.00%) | PASS |
| Muscle GastrocnemiusLateral Left | Denver | 1257 | 0.00000 (0.00%) | PASS |
| Muscle GastrocnemiusMedial Left | Denver | 2708 | 0.00000 (0.00%) | PASS |
| Muscle GluteusMaximus Left | Denver | 5000 | 0.01740 (1.74%) | PASS |
| Muscle GluteusMedius Left | Denver | 3484 | 0.12256 (12.26%) | FAIL |
| Muscle GluteusMinimus Left | Denver | 1456 | 0.33379 (33.38%) | FAIL |
| Muscle Gracilis Left | Denver | 920 | 0.00000 (0.00%) | PASS |
| Muscle Illiacus Left | Denver | 1743 | 0.34596 (34.60%) | FAIL |
| Muscle InferiorGemellus Left | Denver | 71 | 0.00000 (0.00%) | PASS |
| Muscle ObturatorExternus Left | Denver | 554 | 0.00000 (0.00%) | PASS |
| Muscle ObturatorInternus Left | Denver | 598 | 0.02007 (2.01%) | FAIL |
| Muscle Pectineus Left | Denver | 612 | 0.00000 (0.00%) | PASS |
| Muscle PeroneusLongus Left | Denver | 1585 | 0.00000 (0.00%) | PASS |
| Muscle Piriformis Left | Denver | 541 | 0.01294 (1.29%) | PASS |
| Muscle Plantaris Left | Denver | 69 | 0.00000 (0.00%) | PASS |
| Muscle Popliteus Left | Denver | 254 | 0.00000 (0.00%) | PASS |
| Muscle PsoasMajor Left | Denver | 1826 | 0.30285 (30.28%) | FAIL |
| Muscle QuadratusFemoris Left | Denver | 445 | 0.00000 (0.00%) | PASS |
| Muscle RectusFemoris Left | Denver | 1470 | 0.00000 (0.00%) | PASS |
| Muscle Sartorius Left | Denver | 1336 | 0.00749 (0.75%) | PASS |
| Muscle Semimembranosus Left | Denver | 2185 | 0.00000 (0.00%) | PASS |
| Muscle Semitendinosus Left | Denver | 1141 | 0.00000 (0.00%) | PASS |
| Muscle Soleus Left | Denver | 4130 | 0.00000 (0.00%) | PASS |
| Muscle SuperiorGemellus Left | Denver | 57 | 0.00000 (0.00%) | PASS |
| Muscle TensorFasciaeLatae Left | Denver | 725 | 0.00138 (0.14%) | PASS |
| Muscle TibialisAnterior Left | Denver | 1302 | 0.00000 (0.00%) | PASS |
| Muscle TibialisPosterior Left | Denver | 1030 | 0.00000 (0.00%) | PASS |
| Muscle VastusIntermedius Left | Denver | 3136 | 0.00000 (0.00%) | PASS |
| Muscle VastusLateralis Left | Denver | 4032 | 0.00000 (0.00%) | PASS |
| Muscle VastusMedialis Left | Denver | 2711 | 0.00000 (0.00%) | PASS |
| Bone Calcaneous Right | Denver | 1039 | 0.00000 (0.00%) | PASS |
| Bone Cuboid Right | Denver | 231 | 0.00000 (0.00%) | PASS |
| Bone Femur Right | Denver | 4377 | 0.00091 (0.09%) | PASS |
| Bone Fibula Right | Denver | 771 | 0.00000 (0.00%) | PASS |
| Bone IntermediateCuneiform Right | Denver | 96 | 0.00000 (0.00%) | PASS |
| Bone LateralCuneiform Right | Denver | 118 | 0.00000 (0.00%) | PASS |
| Bone MedialCuneiform Right | Denver | 189 | 0.00000 (0.00%) | PASS |
| Bone Navicular Right | Denver | 198 | 0.00000 (0.00%) | PASS |
| Bone Patella Right | Denver | 323 | 0.00000 (0.00%) | PASS |
| Bone Phalanges Right | Denver | 1464 | 0.00000 (0.00%) | PASS |
| Bone Talus Right | Denver | 555 | 0.00000 (0.00%) | PASS |
| Bone Tibia Right | Denver | 3592 | 0.00000 (0.00%) | PASS |
| Cartilage FemurDistal Right | Denver | 323 | 0.00000 (0.00%) | PASS |
| Cartilage FemurHead Right | Denver | 273 | 0.07326 (7.33%) | FAIL |
| Cartilage Patella Right | Denver | 90 | 0.00000 (0.00%) | PASS |
| Cartilage Talus Right | Denver | 69 | 0.00000 (0.00%) | PASS |
| Cartilage TibiaDistal Right | Denver | 57 | 0.00000 (0.00%) | PASS |
| Cartilage TibiaLateral Right | Denver | 97 | 0.00000 (0.00%) | PASS |
| Cartilage TibiaMedial Right | Denver | 119 | 0.00000 (0.00%) | PASS |
| Ligament ACL Right | Denver | 89 | 0.00000 (0.00%) | PASS |
| Ligament LCL Right | Denver | 43 | 0.00000 (0.00%) | PASS |
| Ligament MCL Right | Denver | 62 | 0.00000 (0.00%) | PASS |
| Ligament PCL Right | Denver | 75 | 0.00000 (0.00%) | PASS |
| Muscle AdductorBrevis Right | Denver | 949 | 0.00000 (0.00%) | PASS |
| Muscle AdductorLongus Right | Denver | 1076 | 0.00000 (0.00%) | PASS |
| Muscle AdductorMagnus Right | Denver | 3952 | 0.00000 (0.00%) | PASS |
| Muscle BicepsFemorisLongHead Right | Denver | 1809 | 0.00000 (0.00%) | PASS |
| Muscle BicepsFemorisShortHead Right | Denver | 818 | 0.00000 (0.00%) | PASS |
| Muscle ExtensorDigitorumLongus Right | Denver | 792 | 0.00000 (0.00%) | PASS |
| Muscle ExtensorHallucisLongus Right | Denver | 308 | 0.00000 (0.00%) | PASS |
| Muscle FlexorDigitorumLongus Right | Denver | 502 | 0.00000 (0.00%) | PASS |
| Muscle FlexorHallucisLongus Right | Denver | 900 | 0.00000 (0.00%) | PASS |
| Muscle GastrocnemiusLateral Right | Denver | 1327 | 0.00000 (0.00%) | PASS |
| Muscle GastrocnemiusMedial Right | Denver | 2461 | 0.00000 (0.00%) | PASS |
| Muscle GluteusMaximus Right | Denver | 5000 | 0.00320 (0.32%) | PASS |
| Muscle GluteusMedius Right | Denver | 2999 | 0.07436 (7.44%) | FAIL |
| Muscle GluteusMinimus Right | Denver | 1433 | 0.25471 (25.47%) | FAIL |
| Muscle Gracilis Right | Denver | 926 | 0.00000 (0.00%) | PASS |
| Muscle Illiacus Right | Denver | 1631 | 0.32679 (32.68%) | FAIL |
| Muscle InferiorGemellus Right | Denver | 60 | 0.00000 (0.00%) | PASS |
| Muscle ObturatorExternus Right | Denver | 613 | 0.00000 (0.00%) | PASS |
| Muscle ObturatorInternus Right | Denver | 643 | 0.06998 (7.00%) | FAIL |
| Muscle Pectineus Right | Denver | 516 | 0.00000 (0.00%) | PASS |
| Muscle PeroneusLongus Right | Denver | 1631 | 0.00000 (0.00%) | PASS |
| Muscle Piriformis Right | Denver | 531 | 0.01507 (1.51%) | PASS |
| Muscle Plantaris Right | Denver | 132 | 0.00000 (0.00%) | PASS |
| Muscle Popliteus Right | Denver | 271 | 0.00000 (0.00%) | PASS |
| Muscle PsoasMajor Right | Denver | 1729 | 0.14633 (14.63%) | FAIL |
| Muscle QuadratisFemoris Right | Denver | 425 | 0.00000 (0.00%) | PASS |
| Muscle RectusFemoris Right | Denver | 1389 | 0.00000 (0.00%) | PASS |
| Muscle Sartorius Right | Denver | 1374 | 0.00000 (0.00%) | PASS |
| Muscle Semimembranosus Right | Denver | 2125 | 0.00000 (0.00%) | PASS |
| Muscle Semitendonosus Right | Denver | 1139 | 0.00000 (0.00%) | PASS |
| Muscle Soleus Right | Denver | 4083 | 0.00000 (0.00%) | PASS |
| Muscle SuperiorGemellus Right | Denver | 69 | 0.00000 (0.00%) | PASS |
| Muscle TensorFasciaeLatae Right | Denver | 792 | 0.00126 (0.13%) | PASS |
| Muscle TibialisAnterior Right | Denver | 1257 | 0.00000 (0.00%) | PASS |
| Muscle TibialisPosterior Right | Denver | 1022 | 0.00000 (0.00%) | PASS |
| Muscle VastusIntermedius Right | Denver | 3050 | 0.00000 (0.00%) | PASS |
| Muscle VastusLateralis Right | Denver | 3998 | 0.00000 (0.00%) | PASS |
| Muscle VastusMedialis Right | Denver | 2531 | 0.00000 (0.00%) | PASS |
| aorta | TotalSegmentator | 2509 | 0.07533 (7.53%) | FAIL |
| brachiocephalic_trunk | TotalSegmentator | 65 | 0.00000 (0.00%) | PASS |
| brachiocephalic_vein_left | TotalSegmentator | 192 | 0.00000 (0.00%) | PASS |
| brachiocephalic_vein_right | TotalSegmentator | 115 | 0.00000 (0.00%) | PASS |
| clavicula_left | TotalSegmentator | 499 | 0.00000 (0.00%) | PASS |
| clavicula_right | TotalSegmentator | 522 | 0.00000 (0.00%) | PASS |
| common_carotid_artery_left | TotalSegmentator | 135 | 0.00000 (0.00%) | PASS |
| common_carotid_artery_right | TotalSegmentator | 90 | 0.01111 (1.11%) | PASS |
| humerus_left | TotalSegmentator | 2165 | 0.00000 (0.00%) | PASS |
| humerus_right | TotalSegmentator | 2059 | 0.00000 (0.00%) | PASS |
| iliac_artery_left | TotalSegmentator | 269 | 0.02602 (2.60%) | FAIL |
| iliac_artery_right | TotalSegmentator | 282 | 0.00000 (0.00%) | PASS |
| portal_vein_and_splenic_vein | TotalSegmentator | 333 | 0.16817 (16.82%) | FAIL |
| rib_left_1 | TotalSegmentator | 247 | 0.01215 (1.21%) | PASS |
| rib_left_10 | TotalSegmentator | 348 | 0.33621 (33.62%) | FAIL |
| rib_left_11 | TotalSegmentator | 280 | 0.34286 (34.29%) | FAIL |
| rib_left_12 | TotalSegmentator | 163 | 0.16564 (16.56%) | FAIL |
| rib_left_2 | TotalSegmentator | 328 | 0.01524 (1.52%) | PASS |
| rib_left_3 | TotalSegmentator | 360 | 0.00000 (0.00%) | PASS |
| rib_left_4 | TotalSegmentator | 397 | 0.00000 (0.00%) | PASS |
| rib_left_5 | TotalSegmentator | 435 | 0.00000 (0.00%) | PASS |
| rib_left_6 | TotalSegmentator | 507 | 0.00000 (0.00%) | PASS |
| rib_left_7 | TotalSegmentator | 444 | 0.00000 (0.00%) | PASS |
| rib_left_8 | TotalSegmentator | 404 | 0.00000 (0.00%) | PASS |
| rib_left_9 | TotalSegmentator | 344 | 0.00581 (0.58%) | PASS |
| rib_right_1 | TotalSegmentator | 252 | 0.04762 (4.76%) | FAIL |
| rib_right_10 | TotalSegmentator | 325 | 0.18154 (18.15%) | FAIL |
| rib_right_11 | TotalSegmentator | 284 | 0.19718 (19.72%) | FAIL |
| rib_right_12 | TotalSegmentator | 162 | 0.05556 (5.56%) | FAIL |
| rib_right_2 | TotalSegmentator | 308 | 0.02597 (2.60%) | FAIL |
| rib_right_3 | TotalSegmentator | 357 | 0.01401 (1.40%) | PASS |
| rib_right_4 | TotalSegmentator | 399 | 0.00752 (0.75%) | PASS |
| rib_right_5 | TotalSegmentator | 485 | 0.02680 (2.68%) | FAIL |
| rib_right_6 | TotalSegmentator | 531 | 0.04520 (4.52%) | FAIL |
| rib_right_7 | TotalSegmentator | 469 | 0.03198 (3.20%) | FAIL |
| rib_right_8 | TotalSegmentator | 382 | 0.05236 (5.24%) | FAIL |
| rib_right_9 | TotalSegmentator | 342 | 0.11404 (11.40%) | FAIL |
| scapula_left | TotalSegmentator | 1532 | 0.00000 (0.00%) | PASS |
| scapula_right | TotalSegmentator | 1587 | 0.00000 (0.00%) | PASS |
| skull | TotalSegmentator | 5000 | 0.00800 (0.80%) | PASS |
| subclavian_artery_left | TotalSegmentator | 219 | 0.00000 (0.00%) | PASS |
| subclavian_artery_right | TotalSegmentator | 183 | 0.00000 (0.00%) | PASS |

### F4 - lateralidade

Estado geral: PASS; regra: left RAS x < 0; right RAS x > 0.

| Estrutura | Fonte | X RAS médio (mm) | Sinal esperado | Estado |
|---|---|---:|---|---|
| Bone Calcaneous Left | Denver | -135.74 | negative | PASS |
| Bone Cuboid Left | Denver | -153.94 | negative | PASS |
| Bone Femur Left | Denver | -126.34 | negative | PASS |
| Bone Fibula Left | Denver | -158.70 | negative | PASS |
| Bone IntermediateCuneiform Left | Denver | -141.77 | negative | PASS |
| Bone LateralCuneiform Left | Denver | -151.13 | negative | PASS |
| Bone MedialCuneiform Left | Denver | -127.38 | negative | PASS |
| Bone Navicular Left | Denver | -133.69 | negative | PASS |
| Bone Patella Left | Denver | -132.36 | negative | PASS |
| Bone Phalanges Left | Denver | -146.83 | negative | PASS |
| Bone Talus Left | Denver | -137.31 | negative | PASS |
| Bone Tibia Left | Denver | -134.22 | negative | PASS |
| Cartilage FemurDistal Left | Denver | -120.35 | negative | PASS |
| Cartilage FemurHead Left | Denver | -93.99 | negative | PASS |
| Cartilage Patella Left | Denver | -131.26 | negative | PASS |
| Cartilage Talus Left | Denver | -150.58 | negative | PASS |
| Cartilage TibiaDistal Left | Denver | -139.02 | negative | PASS |
| Cartilage TibiaLateral Left | Denver | -143.02 | negative | PASS |
| Cartilage TibiaMedial Left | Denver | -103.69 | negative | PASS |
| Ligament ACL Left | Denver | -126.00 | negative | PASS |
| Ligament LCL Left | Denver | -167.41 | negative | PASS |
| Ligament MCL Left | Denver | -85.55 | negative | PASS |
| Ligament PCL Left | Denver | -115.21 | negative | PASS |
| Muscle AdductorBrevis Left | Denver | -87.40 | negative | PASS |
| Muscle AdductorLongus Left | Denver | -82.25 | negative | PASS |
| Muscle AdductorMagnus Left | Denver | -94.68 | negative | PASS |
| Muscle BicepsFemorisLong Left | Denver | -128.18 | negative | PASS |
| Muscle BicepsFemorisShort Left | Denver | -139.38 | negative | PASS |
| Muscle ExtensorDigitorumLongus Left | Denver | -164.65 | negative | PASS |
| Muscle ExtensorHallucisLongus Left | Denver | -157.64 | negative | PASS |
| Muscle FlexorDigitorumLongus Left | Denver | -126.34 | negative | PASS |
| Muscle FlexorHallucisLongus Left | Denver | -142.64 | negative | PASS |
| Muscle GastrocnemiusLateral Left | Denver | -135.98 | negative | PASS |
| Muscle GastrocnemiusMedial Left | Denver | -103.70 | negative | PASS |
| Muscle GluteusMaximus Left | Denver | -103.02 | negative | PASS |
| Muscle GluteusMedius Left | Denver | -126.95 | negative | PASS |
| Muscle GluteusMinimus Left | Denver | -119.35 | negative | PASS |
| Muscle Gracilis Left | Denver | -62.11 | negative | PASS |
| Muscle Illiacus Left | Denver | -95.43 | negative | PASS |
| Muscle InferiorGemellus Left | Denver | -110.58 | negative | PASS |
| Muscle ObturatorExternus Left | Denver | -72.91 | negative | PASS |
| Muscle ObturatorInternus Left | Denver | -64.45 | negative | PASS |
| Muscle Pectineus Left | Denver | -85.05 | negative | PASS |
| Muscle PeroneusLongus Left | Denver | -165.31 | negative | PASS |
| Muscle Piriformis Left | Denver | -58.08 | negative | PASS |
| Muscle Plantaris Left | Denver | -141.25 | negative | PASS |
| Muscle Popliteus Left | Denver | -123.80 | negative | PASS |
| Muscle PsoasMajor Left | Denver | -42.79 | negative | PASS |
| Muscle QuadratusFemoris Left | Denver | -114.44 | negative | PASS |
| Muscle RectusFemoris Left | Denver | -123.02 | negative | PASS |
| Muscle Sartorius Left | Denver | -89.64 | negative | PASS |
| Muscle Semimembranosus Left | Denver | -93.15 | negative | PASS |
| Muscle Semitendinosus Left | Denver | -104.87 | negative | PASS |
| Muscle Soleus Left | Denver | -130.66 | negative | PASS |
| Muscle SuperiorGemellus Left | Denver | -112.82 | negative | PASS |
| Muscle TensorFasciaeLatae Left | Denver | -153.59 | negative | PASS |
| Muscle TibialisAnterior Left | Denver | -157.15 | negative | PASS |
| Muscle TibialisPosterior Left | Denver | -143.22 | negative | PASS |
| Muscle VastusIntermedius Left | Denver | -138.42 | negative | PASS |
| Muscle VastusLateralis Left | Denver | -155.25 | negative | PASS |
| Muscle VastusMedialis Left | Denver | -104.83 | negative | PASS |
| Bone Calcaneous Right | Denver | 141.88 | positive | PASS |
| Bone Cuboid Right | Denver | 161.98 | positive | PASS |
| Bone Femur Right | Denver | 135.44 | positive | PASS |
| Bone Fibula Right | Denver | 166.82 | positive | PASS |
| Bone IntermediateCuneiform Right | Denver | 151.28 | positive | PASS |
| Bone LateralCuneiform Right | Denver | 160.28 | positive | PASS |
| Bone MedialCuneiform Right | Denver | 136.86 | positive | PASS |
| Bone Navicular Right | Denver | 143.25 | positive | PASS |
| Bone Patella Right | Denver | 141.09 | positive | PASS |
| Bone Phalanges Right | Denver | 154.52 | positive | PASS |
| Bone Talus Right | Denver | 145.63 | positive | PASS |
| Bone Tibia Right | Denver | 142.93 | positive | PASS |
| Cartilage FemurDistal Right | Denver | 127.98 | positive | PASS |
| Cartilage FemurHead Right | Denver | 107.51 | positive | PASS |
| Cartilage Patella Right | Denver | 138.73 | positive | PASS |
| Cartilage Talus Right | Denver | 144.14 | positive | PASS |
| Cartilage TibiaDistal Right | Denver | 143.95 | positive | PASS |
| Cartilage TibiaLateral Right | Denver | 153.75 | positive | PASS |
| Cartilage TibiaMedial Right | Denver | 110.71 | positive | PASS |
| Ligament ACL Right | Denver | 136.78 | positive | PASS |
| Ligament LCL Right | Denver | 171.27 | positive | PASS |
| Ligament MCL Right | Denver | 95.28 | positive | PASS |
| Ligament PCL Right | Denver | 125.07 | positive | PASS |
| Muscle AdductorBrevis Right | Denver | 93.35 | positive | PASS |
| Muscle AdductorLongus Right | Denver | 86.50 | positive | PASS |
| Muscle AdductorMagnus Right | Denver | 102.64 | positive | PASS |
| Muscle BicepsFemorisLongHead Right | Denver | 135.52 | positive | PASS |
| Muscle BicepsFemorisShortHead Right | Denver | 148.09 | positive | PASS |
| Muscle ExtensorDigitorumLongus Right | Denver | 174.39 | positive | PASS |
| Muscle ExtensorHallucisLongus Right | Denver | 167.03 | positive | PASS |
| Muscle FlexorDigitorumLongus Right | Denver | 135.59 | positive | PASS |
| Muscle FlexorHallucisLongus Right | Denver | 150.40 | positive | PASS |
| Muscle GastrocnemiusLateral Right | Denver | 146.60 | positive | PASS |
| Muscle GastrocnemiusMedial Right | Denver | 114.78 | positive | PASS |
| Muscle GluteusMaximus Right | Denver | 118.43 | positive | PASS |
| Muscle GluteusMedius Right | Denver | 139.35 | positive | PASS |
| Muscle GluteusMinimus Right | Denver | 130.42 | positive | PASS |
| Muscle Gracilis Right | Denver | 67.56 | positive | PASS |
| Muscle Illiacus Right | Denver | 108.14 | positive | PASS |
| Muscle InferiorGemellus Right | Denver | 118.21 | positive | PASS |
| Muscle ObturatorExternus Right | Denver | 80.81 | positive | PASS |
| Muscle ObturatorInternus Right | Denver | 75.25 | positive | PASS |
| Muscle Pectineus Right | Denver | 91.63 | positive | PASS |
| Muscle PeroneusLongus Right | Denver | 174.90 | positive | PASS |
| Muscle Piriformis Right | Denver | 69.87 | positive | PASS |
| Muscle Plantaris Right | Denver | 149.35 | positive | PASS |
| Muscle Popliteus Right | Denver | 135.12 | positive | PASS |
| Muscle PsoasMajor Right | Denver | 53.80 | positive | PASS |
| Muscle QuadratisFemoris Right | Denver | 123.35 | positive | PASS |
| Muscle RectusFemoris Right | Denver | 132.02 | positive | PASS |
| Muscle Sartorius Right | Denver | 97.92 | positive | PASS |
| Muscle Semimembranosus Right | Denver | 100.51 | positive | PASS |
| Muscle Semitendonosus Right | Denver | 112.45 | positive | PASS |
| Muscle Soleus Right | Denver | 142.63 | positive | PASS |
| Muscle SuperiorGemellus Right | Denver | 122.03 | positive | PASS |
| Muscle TensorFasciaeLatae Right | Denver | 162.03 | positive | PASS |
| Muscle TibialisAnterior Right | Denver | 166.83 | positive | PASS |
| Muscle TibialisPosterior Right | Denver | 154.50 | positive | PASS |
| Muscle VastusIntermedius Right | Denver | 146.74 | positive | PASS |
| Muscle VastusLateralis Right | Denver | 163.88 | positive | PASS |
| Muscle VastusMedialis Right | Denver | 112.40 | positive | PASS |
| brachiocephalic_vein_left | TotalSegmentator | -8.50 | negative | PASS |
| brachiocephalic_vein_right | TotalSegmentator | 29.27 | positive | PASS |
| clavicula_left | TotalSegmentator | -72.23 | negative | PASS |
| clavicula_right | TotalSegmentator | 72.42 | positive | PASS |
| common_carotid_artery_left | TotalSegmentator | -16.78 | negative | PASS |
| common_carotid_artery_right | TotalSegmentator | 22.82 | positive | PASS |
| humerus_left | TotalSegmentator | -191.35 | negative | PASS |
| humerus_right | TotalSegmentator | 190.76 | positive | PASS |
| iliac_artery_left | TotalSegmentator | -46.49 | negative | PASS |
| iliac_artery_right | TotalSegmentator | 46.27 | positive | PASS |
| rib_left_1 | TotalSegmentator | -53.73 | negative | PASS |
| rib_left_10 | TotalSegmentator | -100.99 | negative | PASS |
| rib_left_11 | TotalSegmentator | -93.46 | negative | PASS |
| rib_left_12 | TotalSegmentator | -70.19 | negative | PASS |
| rib_left_2 | TotalSegmentator | -75.37 | negative | PASS |
| rib_left_3 | TotalSegmentator | -88.26 | negative | PASS |
| rib_left_4 | TotalSegmentator | -95.52 | negative | PASS |
| rib_left_5 | TotalSegmentator | -99.17 | negative | PASS |
| rib_left_6 | TotalSegmentator | -105.28 | negative | PASS |
| rib_left_7 | TotalSegmentator | -105.71 | negative | PASS |
| rib_left_8 | TotalSegmentator | -104.40 | negative | PASS |
| rib_left_9 | TotalSegmentator | -102.07 | negative | PASS |
| rib_right_1 | TotalSegmentator | 57.68 | positive | PASS |
| rib_right_10 | TotalSegmentator | 102.93 | positive | PASS |
| rib_right_11 | TotalSegmentator | 94.51 | positive | PASS |
| rib_right_12 | TotalSegmentator | 71.12 | positive | PASS |
| rib_right_2 | TotalSegmentator | 77.30 | positive | PASS |
| rib_right_3 | TotalSegmentator | 87.58 | positive | PASS |
| rib_right_4 | TotalSegmentator | 94.52 | positive | PASS |
| rib_right_5 | TotalSegmentator | 96.02 | positive | PASS |
| rib_right_6 | TotalSegmentator | 101.63 | positive | PASS |
| rib_right_7 | TotalSegmentator | 104.43 | positive | PASS |
| rib_right_8 | TotalSegmentator | 103.35 | positive | PASS |
| rib_right_9 | TotalSegmentator | 102.01 | positive | PASS |
| scapula_left | TotalSegmentator | -107.26 | negative | PASS |
| scapula_right | TotalSegmentator | 112.04 | positive | PASS |
| subclavian_artery_left | TotalSegmentator | -42.71 | negative | PASS |
| subclavian_artery_right | TotalSegmentator | 52.64 | positive | PASS |

### F5 - revisão humana

Estado: PENDING. Vistas necessárias: {}. O script não presume aprovação humana.

### Registro de fonte única

| Estrutura | Fonte selecionada |
|---|---|
| Bone Calcaneous Left | Denver |
| Bone Cuboid Left | Denver |
| Bone Femur Left | Denver |
| Bone Fibula Left | Denver |
| Bone IntermediateCuneiform Left | Denver |
| Bone LateralCuneiform Left | Denver |
| Bone MedialCuneiform Left | Denver |
| Bone Navicular Left | Denver |
| Bone Patella Left | Denver |
| Bone Phalanges Left | Denver |
| Bone Talus Left | Denver |
| Bone Tibia Left | Denver |
| Cartilage FemurDistal Left | Denver |
| Cartilage FemurHead Left | Denver |
| Cartilage Patella Left | Denver |
| Cartilage Talus Left | Denver |
| Cartilage TibiaDistal Left | Denver |
| Cartilage TibiaLateral Left | Denver |
| Cartilage TibiaMedial Left | Denver |
| Ligament ACL Left | Denver |
| Ligament LCL Left | Denver |
| Ligament MCL Left | Denver |
| Ligament PCL Left | Denver |
| Muscle AdductorBrevis Left | Denver |
| Muscle AdductorLongus Left | Denver |
| Muscle AdductorMagnus Left | Denver |
| Muscle BicepsFemorisLong Left | Denver |
| Muscle BicepsFemorisShort Left | Denver |
| Muscle ExtensorDigitorumLongus Left | Denver |
| Muscle ExtensorHallucisLongus Left | Denver |
| Muscle FlexorDigitorumLongus Left | Denver |
| Muscle FlexorHallucisLongus Left | Denver |
| Muscle GastrocnemiusLateral Left | Denver |
| Muscle GastrocnemiusMedial Left | Denver |
| Muscle GluteusMaximus Left | Denver |
| Muscle GluteusMedius Left | Denver |
| Muscle GluteusMinimus Left | Denver |
| Muscle Gracilis Left | Denver |
| Muscle Illiacus Left | Denver |
| Muscle InferiorGemellus Left | Denver |
| Muscle ObturatorExternus Left | Denver |
| Muscle ObturatorInternus Left | Denver |
| Muscle Pectineus Left | Denver |
| Muscle PeroneusLongus Left | Denver |
| Muscle Piriformis Left | Denver |
| Muscle Plantaris Left | Denver |
| Muscle Popliteus Left | Denver |
| Muscle PsoasMajor Left | Denver |
| Muscle QuadratusFemoris Left | Denver |
| Muscle RectusFemoris Left | Denver |
| Muscle Sartorius Left | Denver |
| Muscle Semimembranosus Left | Denver |
| Muscle Semitendinosus Left | Denver |
| Muscle Soleus Left | Denver |
| Muscle SuperiorGemellus Left | Denver |
| Muscle TensorFasciaeLatae Left | Denver |
| Muscle TibialisAnterior Left | Denver |
| Muscle TibialisPosterior Left | Denver |
| Muscle VastusIntermedius Left | Denver |
| Muscle VastusLateralis Left | Denver |
| Muscle VastusMedialis Left | Denver |
| Bone Calcaneous Right | Denver |
| Bone Cuboid Right | Denver |
| Bone Femur Right | Denver |
| Bone Fibula Right | Denver |
| Bone IntermediateCuneiform Right | Denver |
| Bone LateralCuneiform Right | Denver |
| Bone MedialCuneiform Right | Denver |
| Bone Navicular Right | Denver |
| Bone Patella Right | Denver |
| Bone Phalanges Right | Denver |
| Bone Talus Right | Denver |
| Bone Tibia Right | Denver |
| Cartilage FemurDistal Right | Denver |
| Cartilage FemurHead Right | Denver |
| Cartilage Patella Right | Denver |
| Cartilage Talus Right | Denver |
| Cartilage TibiaDistal Right | Denver |
| Cartilage TibiaLateral Right | Denver |
| Cartilage TibiaMedial Right | Denver |
| Ligament ACL Right | Denver |
| Ligament LCL Right | Denver |
| Ligament MCL Right | Denver |
| Ligament PCL Right | Denver |
| Muscle AdductorBrevis Right | Denver |
| Muscle AdductorLongus Right | Denver |
| Muscle AdductorMagnus Right | Denver |
| Muscle BicepsFemorisLongHead Right | Denver |
| Muscle BicepsFemorisShortHead Right | Denver |
| Muscle ExtensorDigitorumLongus Right | Denver |
| Muscle ExtensorHallucisLongus Right | Denver |
| Muscle FlexorDigitorumLongus Right | Denver |
| Muscle FlexorHallucisLongus Right | Denver |
| Muscle GastrocnemiusLateral Right | Denver |
| Muscle GastrocnemiusMedial Right | Denver |
| Muscle GluteusMaximus Right | Denver |
| Muscle GluteusMedius Right | Denver |
| Muscle GluteusMinimus Right | Denver |
| Muscle Gracilis Right | Denver |
| Muscle Illiacus Right | Denver |
| Muscle InferiorGemellus Right | Denver |
| Muscle ObturatorExternus Right | Denver |
| Muscle ObturatorInternus Right | Denver |
| Muscle Pectineus Right | Denver |
| Muscle PeroneusLongus Right | Denver |
| Muscle Piriformis Right | Denver |
| Muscle Plantaris Right | Denver |
| Muscle Popliteus Right | Denver |
| Muscle PsoasMajor Right | Denver |
| Muscle QuadratisFemoris Right | Denver |
| Muscle RectusFemoris Right | Denver |
| Muscle Sartorius Right | Denver |
| Muscle Semimembranosus Right | Denver |
| Muscle Semitendonosus Right | Denver |
| Muscle Soleus Right | Denver |
| Muscle SuperiorGemellus Right | Denver |
| Muscle TensorFasciaeLatae Right | Denver |
| Muscle TibialisAnterior Right | Denver |
| Muscle TibialisPosterior Right | Denver |
| Muscle VastusIntermedius Right | Denver |
| Muscle VastusLateralis Right | Denver |
| Muscle VastusMedialis Right | Denver |
| aorta | TotalSegmentator |
| brachiocephalic_trunk | TotalSegmentator |
| brachiocephalic_vein_left | TotalSegmentator |
| brachiocephalic_vein_right | TotalSegmentator |
| clavicula_left | TotalSegmentator |
| clavicula_right | TotalSegmentator |
| common_carotid_artery_left | TotalSegmentator |
| common_carotid_artery_right | TotalSegmentator |
| humerus_left | TotalSegmentator |
| humerus_right | TotalSegmentator |
| iliac_artery_left | TotalSegmentator |
| iliac_artery_right | TotalSegmentator |
| portal_vein_and_splenic_vein | TotalSegmentator |
| rib_left_1 | TotalSegmentator |
| rib_left_10 | TotalSegmentator |
| rib_left_11 | TotalSegmentator |
| rib_left_12 | TotalSegmentator |
| rib_left_2 | TotalSegmentator |
| rib_left_3 | TotalSegmentator |
| rib_left_4 | TotalSegmentator |
| rib_left_5 | TotalSegmentator |
| rib_left_6 | TotalSegmentator |
| rib_left_7 | TotalSegmentator |
| rib_left_8 | TotalSegmentator |
| rib_left_9 | TotalSegmentator |
| rib_right_1 | TotalSegmentator |
| rib_right_10 | TotalSegmentator |
| rib_right_11 | TotalSegmentator |
| rib_right_12 | TotalSegmentator |
| rib_right_2 | TotalSegmentator |
| rib_right_3 | TotalSegmentator |
| rib_right_4 | TotalSegmentator |
| rib_right_5 | TotalSegmentator |
| rib_right_6 | TotalSegmentator |
| rib_right_7 | TotalSegmentator |
| rib_right_8 | TotalSegmentator |
| rib_right_9 | TotalSegmentator |
| scapula_left | TotalSegmentator |
| scapula_right | TotalSegmentator |
| skull | TotalSegmentator |
| subclavian_artery_left | TotalSegmentator |
| subclavian_artery_right | TotalSegmentator |

### EXP-0014 - resultado por região

| Região | Geometria | F1 contenção | F2 articulações | F3 sobreposição | F4 lateralidade | F5 revisão | Fonte única |
|---|---|---|---|---|---|---|---|
| head_neck | N/A: incomplete | FAIL | PASS | PASS | N/A | PENDING | PASS |
| thorax | N/A: incomplete | FAIL | FAIL | FAIL | PASS | PENDING | PASS |
| abdomen_pelvis | FAIL | N/A | N/A | N/A | N/A | PENDING | PASS |
| lower_limbs | N/A: incomplete | FAIL | FAIL | FAIL | PASS | PENDING | PASS |

### Impedimentos para montar o atlas

- head_neck: geometry = N/A: incomplete
- head_neck: F1_containment = FAIL
- head_neck: F5_human_review = PENDING
- thorax: geometry = N/A: incomplete
- thorax: F1_containment = FAIL
- thorax: F3_overlap = FAIL
- thorax: F2_articulations = FAIL
- thorax: F5_human_review = PENDING
- abdomen_pelvis: geometry = FAIL
- abdomen_pelvis: F5_human_review = PENDING
- lower_limbs: geometry = N/A: incomplete
- lower_limbs: F1_containment = FAIL
- lower_limbs: F3_overlap = FAIL
- lower_limbs: F2_articulations = FAIL
- lower_limbs: F5_human_review = PENDING

### Ajustes diretos Denver → HRA das pernas

| Lado | Região | Escala |
|---|---|---:|
| Left | thigh | 0.93989 |
| Left | lower_leg | 1.04669 |
| Right | thigh | 0.94858 |
| Right | lower_leg | 1.05601 |

| Joelho | Distância mínima fêmur–tíbia (mm) | Estado |
|---|---:|---|
| Left | 24.960 | FAIL |
| Right | 23.159 | FAIL |

### Ajuste por região (--por-regiao)

| Região | Estado | Escala uniforme | Âncoras |
|---|---|---:|---:|
| head_neck | completed | 1.0185 | 7 |
| thorax | completed | 0.9980 | 12 |
| abdomen_pelvis | completed | 0.9903 | 8 |

| Emenda | Descontinuidade (mm) | Estado |
|---|---:|---|
| head_neck/thorax | 1.689 | PASS |
| thorax/abdomen_pelvis | 1.810 | PASS |

#### Erros das âncoras por região

| Região | Estrutura | Média (mm) | p95 (mm) | Estado |
|---|---|---:|---:|---|
| head_neck | vertebrae_C1 | 1.396 | 2.472 | PASS |
| head_neck | vertebrae_C2 | 1.135 | 2.052 | PASS |
| head_neck | vertebrae_C3 | 1.068 | 2.039 | PASS |
| head_neck | vertebrae_C4 | 0.983 | 1.817 | PASS |
| head_neck | vertebrae_C5 | 1.032 | 1.842 | PASS |
| head_neck | vertebrae_C6 | 1.006 | 1.803 | PASS |
| head_neck | vertebrae_C7 | 1.089 | 1.929 | PASS |
| thorax | vertebrae_T1 | 1.138 | 2.034 | PASS |
| thorax | vertebrae_T2 | 1.167 | 2.096 | PASS |
| thorax | vertebrae_T3 | 1.214 | 2.273 | PASS |
| thorax | vertebrae_T4 | 1.233 | 2.350 | PASS |
| thorax | vertebrae_T5 | 1.218 | 2.186 | PASS |
| thorax | vertebrae_T6 | 1.228 | 2.255 | PASS |
| thorax | vertebrae_T7 | 1.224 | 2.239 | PASS |
| thorax | vertebrae_T8 | 1.296 | 2.372 | PASS |
| thorax | vertebrae_T9 | 1.244 | 2.276 | PASS |
| thorax | vertebrae_T10 | 1.278 | 2.263 | PASS |
| thorax | vertebrae_T11 | 1.280 | 2.286 | PASS |
| thorax | vertebrae_T12 | 1.440 | 2.604 | PASS |
| abdomen_pelvis | vertebrae_L1 | 5.698 | 29.525 | FAIL |
| abdomen_pelvis | vertebrae_L2 | 7.293 | 29.431 | FAIL |
| abdomen_pelvis | vertebrae_L3 | 11.160 | 30.292 | FAIL |
| abdomen_pelvis | vertebrae_L4 | 16.276 | 32.215 | FAIL |
| abdomen_pelvis | vertebrae_L5 | 15.685 | 32.102 | FAIL |
| abdomen_pelvis | sacrum | 4.026 | 8.955 | PASS |
| abdomen_pelvis | kidney_left | 5.063 | 10.630 | FAIL |
| abdomen_pelvis | kidney_right | 3.365 | 7.744 | PASS |
| thorax | aorta | N/A | N/A | N/A |
| thorax | brachiocephalic_trunk | N/A | N/A | N/A |
| thorax | brachiocephalic_vein_left | N/A | N/A | N/A |
| thorax | brachiocephalic_vein_right | N/A | N/A | N/A |
| thorax | clavicula_left | N/A | N/A | N/A |
| thorax | clavicula_right | N/A | N/A | N/A |
| thorax | common_carotid_artery_left | N/A | N/A | N/A |
| thorax | common_carotid_artery_right | N/A | N/A | N/A |
| thorax | humerus_left | N/A | N/A | N/A |
| thorax | humerus_right | N/A | N/A | N/A |
| thorax | iliac_artery_left | N/A | N/A | N/A |
| thorax | iliac_artery_right | N/A | N/A | N/A |
| thorax | portal_vein_and_splenic_vein | N/A | N/A | N/A |
| thorax | rib_left_1 | N/A | N/A | N/A |
| thorax | rib_left_10 | N/A | N/A | N/A |
| thorax | rib_left_11 | N/A | N/A | N/A |
| thorax | rib_left_12 | N/A | N/A | N/A |
| thorax | rib_left_2 | N/A | N/A | N/A |
| thorax | rib_left_3 | N/A | N/A | N/A |
| thorax | rib_left_4 | N/A | N/A | N/A |
| thorax | rib_left_5 | N/A | N/A | N/A |
| thorax | rib_left_6 | N/A | N/A | N/A |
| thorax | rib_left_7 | N/A | N/A | N/A |
| thorax | rib_left_8 | N/A | N/A | N/A |
| thorax | rib_left_9 | N/A | N/A | N/A |
| thorax | rib_right_1 | N/A | N/A | N/A |
| thorax | rib_right_10 | N/A | N/A | N/A |
| thorax | rib_right_11 | N/A | N/A | N/A |
| thorax | rib_right_12 | N/A | N/A | N/A |
| thorax | rib_right_2 | N/A | N/A | N/A |
| thorax | rib_right_3 | N/A | N/A | N/A |
| thorax | rib_right_4 | N/A | N/A | N/A |
| thorax | rib_right_5 | N/A | N/A | N/A |
| thorax | rib_right_6 | N/A | N/A | N/A |
| thorax | rib_right_7 | N/A | N/A | N/A |
| thorax | rib_right_8 | N/A | N/A | N/A |
| thorax | rib_right_9 | N/A | N/A | N/A |
| thorax | scapula_left | N/A | N/A | N/A |
| thorax | scapula_right | N/A | N/A | N/A |
| head_neck | skull | N/A | N/A | N/A |
| thorax | subclavian_artery_left | N/A | N/A | N/A |
| thorax | subclavian_artery_right | N/A | N/A | N/A |
| lower_limbs | thigh Left | 3.914 | 10.426 | PASS |
| lower_limbs | lower_leg Left | 3.008 | 6.462 | PASS |
| lower_limbs | thigh Right | 4.100 | 11.203 | PASS |
| lower_limbs | lower_leg Right | 3.349 | 8.256 | PASS |
| lower_limbs | Bone Calcaneous Left | N/A | N/A | N/A |
| lower_limbs | Bone Cuboid Left | N/A | N/A | N/A |
| lower_limbs | Bone Femur Left | N/A | N/A | N/A |
| lower_limbs | Bone Fibula Left | N/A | N/A | N/A |
| lower_limbs | Bone IntermediateCuneiform Left | N/A | N/A | N/A |
| lower_limbs | Bone LateralCuneiform Left | N/A | N/A | N/A |
| lower_limbs | Bone MedialCuneiform Left | N/A | N/A | N/A |
| lower_limbs | Bone Navicular Left | N/A | N/A | N/A |
| lower_limbs | Bone Patella Left | N/A | N/A | N/A |
| lower_limbs | Bone Phalanges Left | N/A | N/A | N/A |
| lower_limbs | Bone Talus Left | N/A | N/A | N/A |
| lower_limbs | Bone Tibia Left | N/A | N/A | N/A |
| lower_limbs | Cartilage FemurDistal Left | N/A | N/A | N/A |
| lower_limbs | Cartilage FemurHead Left | N/A | N/A | N/A |
| lower_limbs | Cartilage Patella Left | N/A | N/A | N/A |
| lower_limbs | Cartilage Talus Left | N/A | N/A | N/A |
| lower_limbs | Cartilage TibiaDistal Left | N/A | N/A | N/A |
| lower_limbs | Cartilage TibiaLateral Left | N/A | N/A | N/A |
| lower_limbs | Cartilage TibiaMedial Left | N/A | N/A | N/A |
| lower_limbs | Ligament ACL Left | N/A | N/A | REVIEW |
| lower_limbs | Ligament LCL Left | N/A | N/A | REVIEW |
| lower_limbs | Ligament MCL Left | N/A | N/A | REVIEW |
| lower_limbs | Ligament PCL Left | N/A | N/A | REVIEW |
| lower_limbs | Muscle AdductorBrevis Left | N/A | N/A | N/A |
| lower_limbs | Muscle AdductorLongus Left | N/A | N/A | N/A |
| lower_limbs | Muscle AdductorMagnus Left | N/A | N/A | N/A |
| lower_limbs | Muscle BicepsFemorisLong Left | N/A | N/A | N/A |
| lower_limbs | Muscle BicepsFemorisShort Left | N/A | N/A | N/A |
| lower_limbs | Muscle ExtensorDigitorumLongus Left | N/A | N/A | N/A |
| lower_limbs | Muscle ExtensorHallucisLongus Left | N/A | N/A | N/A |
| lower_limbs | Muscle FlexorDigitorumLongus Left | N/A | N/A | N/A |
| lower_limbs | Muscle FlexorHallucisLongus Left | N/A | N/A | N/A |
| lower_limbs | Muscle GastrocnemiusLateral Left | N/A | N/A | N/A |
| lower_limbs | Muscle GastrocnemiusMedial Left | N/A | N/A | N/A |
| lower_limbs | Muscle GluteusMaximus Left | N/A | N/A | N/A |
| lower_limbs | Muscle GluteusMedius Left | N/A | N/A | N/A |
| lower_limbs | Muscle GluteusMinimus Left | N/A | N/A | N/A |
| lower_limbs | Muscle Gracilis Left | N/A | N/A | N/A |
| lower_limbs | Muscle Illiacus Left | N/A | N/A | N/A |
| lower_limbs | Muscle InferiorGemellus Left | N/A | N/A | N/A |
| lower_limbs | Muscle ObturatorExternus Left | N/A | N/A | N/A |
| lower_limbs | Muscle ObturatorInternus Left | N/A | N/A | N/A |
| lower_limbs | Muscle Pectineus Left | N/A | N/A | N/A |
| lower_limbs | Muscle PeroneusLongus Left | N/A | N/A | N/A |
| lower_limbs | Muscle Piriformis Left | N/A | N/A | N/A |
| lower_limbs | Muscle Plantaris Left | N/A | N/A | N/A |
| lower_limbs | Muscle Popliteus Left | N/A | N/A | N/A |
| lower_limbs | Muscle PsoasMajor Left | N/A | N/A | N/A |
| lower_limbs | Muscle QuadratusFemoris Left | N/A | N/A | N/A |
| lower_limbs | Muscle RectusFemoris Left | N/A | N/A | N/A |
| lower_limbs | Muscle Sartorius Left | N/A | N/A | N/A |
| lower_limbs | Muscle Semimembranosus Left | N/A | N/A | N/A |
| lower_limbs | Muscle Semitendinosus Left | N/A | N/A | N/A |
| lower_limbs | Muscle Soleus Left | N/A | N/A | N/A |
| lower_limbs | Muscle SuperiorGemellus Left | N/A | N/A | N/A |
| lower_limbs | Muscle TensorFasciaeLatae Left | N/A | N/A | N/A |
| lower_limbs | Muscle TibialisAnterior Left | N/A | N/A | N/A |
| lower_limbs | Muscle TibialisPosterior Left | N/A | N/A | N/A |
| lower_limbs | Muscle VastusIntermedius Left | N/A | N/A | N/A |
| lower_limbs | Muscle VastusLateralis Left | N/A | N/A | N/A |
| lower_limbs | Muscle VastusMedialis Left | N/A | N/A | N/A |
| lower_limbs | Bone Calcaneous Right | N/A | N/A | N/A |
| lower_limbs | Bone Cuboid Right | N/A | N/A | N/A |
| lower_limbs | Bone Femur Right | N/A | N/A | N/A |
| lower_limbs | Bone Fibula Right | N/A | N/A | N/A |
| lower_limbs | Bone IntermediateCuneiform Right | N/A | N/A | N/A |
| lower_limbs | Bone LateralCuneiform Right | N/A | N/A | N/A |
| lower_limbs | Bone MedialCuneiform Right | N/A | N/A | N/A |
| lower_limbs | Bone Navicular Right | N/A | N/A | N/A |
| lower_limbs | Bone Patella Right | N/A | N/A | N/A |
| lower_limbs | Bone Phalanges Right | N/A | N/A | N/A |
| lower_limbs | Bone Talus Right | N/A | N/A | N/A |
| lower_limbs | Bone Tibia Right | N/A | N/A | N/A |
| lower_limbs | Cartilage FemurDistal Right | N/A | N/A | N/A |
| lower_limbs | Cartilage FemurHead Right | N/A | N/A | N/A |
| lower_limbs | Cartilage Patella Right | N/A | N/A | N/A |
| lower_limbs | Cartilage Talus Right | N/A | N/A | N/A |
| lower_limbs | Cartilage TibiaDistal Right | N/A | N/A | N/A |
| lower_limbs | Cartilage TibiaLateral Right | N/A | N/A | N/A |
| lower_limbs | Cartilage TibiaMedial Right | N/A | N/A | N/A |
| lower_limbs | Ligament ACL Right | N/A | N/A | REVIEW |
| lower_limbs | Ligament LCL Right | N/A | N/A | REVIEW |
| lower_limbs | Ligament MCL Right | N/A | N/A | REVIEW |
| lower_limbs | Ligament PCL Right | N/A | N/A | REVIEW |
| lower_limbs | Muscle AdductorBrevis Right | N/A | N/A | N/A |
| lower_limbs | Muscle AdductorLongus Right | N/A | N/A | N/A |
| lower_limbs | Muscle AdductorMagnus Right | N/A | N/A | N/A |
| lower_limbs | Muscle BicepsFemorisLongHead Right | N/A | N/A | N/A |
| lower_limbs | Muscle BicepsFemorisShortHead Right | N/A | N/A | N/A |
| lower_limbs | Muscle ExtensorDigitorumLongus Right | N/A | N/A | N/A |
| lower_limbs | Muscle ExtensorHallucisLongus Right | N/A | N/A | N/A |
| lower_limbs | Muscle FlexorDigitorumLongus Right | N/A | N/A | N/A |
| lower_limbs | Muscle FlexorHallucisLongus Right | N/A | N/A | N/A |
| lower_limbs | Muscle GastrocnemiusLateral Right | N/A | N/A | N/A |
| lower_limbs | Muscle GastrocnemiusMedial Right | N/A | N/A | N/A |
| lower_limbs | Muscle GluteusMaximus Right | N/A | N/A | N/A |
| lower_limbs | Muscle GluteusMedius Right | N/A | N/A | N/A |
| lower_limbs | Muscle GluteusMinimus Right | N/A | N/A | N/A |
| lower_limbs | Muscle Gracilis Right | N/A | N/A | N/A |
| lower_limbs | Muscle Illiacus Right | N/A | N/A | N/A |
| lower_limbs | Muscle InferiorGemellus Right | N/A | N/A | N/A |
| lower_limbs | Muscle ObturatorExternus Right | N/A | N/A | N/A |
| lower_limbs | Muscle ObturatorInternus Right | N/A | N/A | N/A |
| lower_limbs | Muscle Pectineus Right | N/A | N/A | N/A |
| lower_limbs | Muscle PeroneusLongus Right | N/A | N/A | N/A |
| lower_limbs | Muscle Piriformis Right | N/A | N/A | N/A |
| lower_limbs | Muscle Plantaris Right | N/A | N/A | N/A |
| lower_limbs | Muscle Popliteus Right | N/A | N/A | N/A |
| lower_limbs | Muscle PsoasMajor Right | N/A | N/A | N/A |
| lower_limbs | Muscle QuadratisFemoris Right | N/A | N/A | N/A |
| lower_limbs | Muscle RectusFemoris Right | N/A | N/A | N/A |
| lower_limbs | Muscle Sartorius Right | N/A | N/A | N/A |
| lower_limbs | Muscle Semimembranosus Right | N/A | N/A | N/A |
| lower_limbs | Muscle Semitendonosus Right | N/A | N/A | N/A |
| lower_limbs | Muscle Soleus Right | N/A | N/A | N/A |
| lower_limbs | Muscle SuperiorGemellus Right | N/A | N/A | N/A |
| lower_limbs | Muscle TensorFasciaeLatae Right | N/A | N/A | N/A |
| lower_limbs | Muscle TibialisAnterior Right | N/A | N/A | N/A |
| lower_limbs | Muscle TibialisPosterior Right | N/A | N/A | N/A |
| lower_limbs | Muscle VastusIntermedius Right | N/A | N/A | N/A |
| lower_limbs | Muscle VastusLateralis Right | N/A | N/A | N/A |
| lower_limbs | Muscle VastusMedialis Right | N/A | N/A | N/A |

Fonte única por anatomia: PASS; duplicatas detectadas: 0.

Dados detalhados de vértices, volumes amostrados, transformações e erros estão em `transformacoes.json`.
