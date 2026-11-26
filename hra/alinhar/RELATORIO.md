# Alignment diagnostic: Denver STL - NLM CT - HRA

Input: hra/nlm/bruto/fast/segmentacao.nii.gz. This is diagnostic only; the normal-resolution NLM segmentation is pending.

## Stage A - Denver STL to NLM CT

Rigid fit: bilateral femurs and hips. Winning axis signs: [1, 1, 1]. The independent holdout compares the NLM sacrum label against the union of Denver Bone Sacrum and Bone Coccyx.

| Structure | Mean (mm) | P95 (mm) |
|---|---:|---:|
| Femur Left | 3.344 | 6.167 |
| Femur Right | 3.243 | 5.675 |
| Pelvis Left | 2.816 | 4.926 |
| Pelvis Right | 2.718 | 4.848 |
| NLM sacrum vs Denver sacrum+coccyx (holdout) | 3.817 | 10.113 |

The holdout mean remains above the 3 mm gate. Stage A and B therefore remain diagnostic; no transform is approved for atlas use.

## Stage B - NLM CT to HRA (diagnostic)

HRA conversion to RAS mm: x_ras=-x_app*1000, y_ras=z_app*1000, z_ras=y_app*1000. No axis-sign search is used. ICP starts from the centroid difference of the paired-structure unions and minimizes symmetric mean surface distance. Uniform and axis scales are bounded to [0.85, 1.15].

Uniform scale: 1.017535. Axis scales XYZ: [1.100973, 1.028789, 0.998435]. Axis scaling improves aggregate fit mean by 12.69%.

Fit pairs: vertebrae L1-L5 and T10-T12, sacrum, bilateral femurs, and bilateral hips. Kidney left/right are held out.

### Uniform similarity

| Structure | Mean (mm) | P95 (mm) |
|---|---:|---:|
| vertebrae_L1 | 1.694 | 3.188 |
| vertebrae_L2 | 2.333 | 3.570 |
| vertebrae_L3 | 6.215 | 28.950 |
| vertebrae_L4 | 10.627 | 30.568 |
| vertebrae_L5 | 15.472 | 34.258 |
| vertebrae_T10 | 2.343 | 4.550 |
| vertebrae_T11 | 2.028 | 3.814 |
| vertebrae_T12 | 1.800 | 3.354 |
| sacrum | 3.625 | 10.047 |
| femur_left | 11.068 | 32.811 |
| femur_right | 20.253 | 49.800 |
| hip_left | 11.552 | 72.594 |
| hip_right | 11.860 | 70.090 |

### Axis scale

| Structure | Mean (mm) | P95 (mm) |
|---|---:|---:|
| vertebrae_L1 | 1.520 | 2.736 |
| vertebrae_L2 | 2.465 | 3.896 |
| vertebrae_L3 | 6.358 | 28.593 |
| vertebrae_L4 | 10.585 | 30.419 |
| vertebrae_L5 | 14.862 | 32.827 |
| vertebrae_T10 | 1.619 | 3.111 |
| vertebrae_T11 | 1.471 | 2.792 |
| vertebrae_T12 | 1.446 | 2.712 |
| sacrum | 3.590 | 9.755 |
| femur_left | 9.954 | 32.507 |
| femur_right | 13.077 | 40.402 |
| hip_left | 11.315 | 68.471 |
| hip_right | 9.808 | 63.252 |

### Holdout validation

| Structure | Similarity mean / P95 (mm) | Axis scale mean / P95 (mm) |
|---|---:|---:|
| kidney_left | 4.250 / 8.631 | 4.342 / 8.406 |
| kidney_right | 3.899 / 8.434 | 5.322 / 12.604 |

Full matrices, per-direction errors, and ICP settings are in transformacoes.json.
