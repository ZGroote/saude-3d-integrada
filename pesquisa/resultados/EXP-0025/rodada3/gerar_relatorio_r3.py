"""Gera o relatório final da rodada 3 a partir dos artefatos medidos."""
import csv
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
R1=OUT.parent
manifest=json.loads((OUT/'hashes_adaptadas_r3.json').read_text(encoding='utf-8'))
qosso=list(csv.DictReader((OUT/'qosso.csv').open(encoding='utf-8-sig',newline='')))
qpass=manifest.get('qosso_pass') is True
lines=[
 '# EXP-0025 — Rodada 3 (final)','',
 '**Estado:** execução concluída. Protocolo não alterado; rodadas 1 e 2 preservadas. A pré-condição Q-osso foi avaliada antes de qualquer músculo Denver. Como passou, M3 foi gerada e avaliada.','',
 '## Implementação CPD e integridade','',
 '- Coherent Point Drift não rígido, fonte móvel = 1.500 amostras de cada osso BP3D transformadas pelo B0; alvo fixo = 1.500 amostras Denver. Seed 25031; `w=0,1`, `beta=2,0`, `lambda=3,0`, até 150 iterações; norma comum por par (centro médio dos centroides e raio RMS combinado). Beta opera no referencial normalizado.',
 f"- Self-check obrigatório (esfera sintética → elipsoide com eixo 20% esticado): redução da distância média = {100*manifest['cpd']['self_check_sphere_to_20pct_ellipsoid_mean_distance_reduction']:.6f}%; assert ≥80% passou.",
 '- **DESVIO de implementação para viabilidade computacional:** a solução densa de CPD 1.500×1.500 por iteração foi interrompida antes de produzir métricas. Foi substituída por aproximação Nyström de posto 128 do kernel gaussiano, mantendo a E-step CPD, os hiperparâmetros, as amostras e o teto de iterações. A aproximação está registrada no manifesto; Q-osso mede sua qualidade fora da amostra. Não houve mudança de critério.',
 '- B0: 11 PLY da rodada 1 copiados e hashes conferidos. Após Q-osso passar, foram gravadas 11 malhas M3; os 22 hashes (B0 + M3) foram conferidos antes de abrir músculos Denver. A adaptação não leu arquivos `_Muscle_`; só leu os 13 STL `_Bone_`.','',
 '## Q-osso (500 pontos holdout independentes por osso)','',
 '| Osso | B0, distância média (mm) | CPD, distância média (mm) | ≤2 mm | menor que B0 | Iterações |','|---|---:|---:|---|---|---:|'
]
for q in qosso:
 lines.append(f"| {q['osso']} | {float(q['distancia_media_b0_mm']):.3f} | {float(q['distancia_media_cpd_mm']):.3f} | {'sim' if q['qosso_le_2mm']=='True' else 'não'} | {'sim' if q['qosso_menor_que_b0']=='True' else 'não'} | {q['iteracoes_cpd']} |")
lines += ['',f"**Q-osso: {'PASSOU' if qpass else 'FALHOU'}** ({sum(r['qosso_le_2mm']=='True' and r['qosso_menor_que_b0']=='True' for r in qosso)}/{len(qosso)} ossos). Foram medidos pontos BP3D fora da amostra CPD; a distância foi medida ponto-superfície no mesh Denver.",'']

eval_path=OUT/'metricas_r3.csv'
if not eval_path.exists():
 lines += ['## Avaliação muscular','', '**Não medida:** Q-osso falhou; parada inconclusiva conforme protocolo. Nenhum músculo Denver foi avaliado.','']
else:
 rows=list(csv.DictReader(eval_path.open(encoding='utf-8-sig',newline='')))
 meta=json.loads((OUT/'metricas_meta_r3.json').read_text(encoding='utf-8'))
 lines += ['## Avaliação R1–R4 e medida exploratória','',
  '| Critério | Resultado |', '|---|---|',
  f"| R1 — redução ≥20% em ≥8/10 | **{meta['r1_count']}/10**; {'PASSOU' if meta['r1_count']>=8 else 'REPROVOU'} |",
  f"| R2 — mediana das inserções ≤2 mm | **{meta['r2_insertion_median_mm']:.3f} mm** (n={meta['r2_insertion_vertex_count']}); {'PASSOU' if meta['r2_insertion_median_mm']<=2 else 'REPROVOU'} |",
  f"| R3 — colisão <2% em todos | máximo **{meta['r3_max_collision_percent']:.3f}%**; {'PASSOU' if meta['r3_max_collision_percent']<2 else 'REPROVOU'} |",
  f"| R4 — Dice mediano ≥0,60 (exploratório) | **{meta['r4_dice_median']:.4f}**; {'PASSOU' if meta['r4_dice_median']>=.60 else 'REPROVOU'} |", '',
  f"**Veredito:** H25 **{meta['verdict']}**. R1 falhou; a regra de parada pré-registrada encerra EXP-0025 como rejeitado. Não há rodada 4.",'',
  '| Grupo | Redução R1 M3 | Média simétrica B0 / M3 (mm) | Denver→adaptado B0 / M3 (mm) | Colisão M3 (%) | Dice M3 |','|---|---:|---:|---:|---:|---:|']
 by={(r['grupo_muscular'],r['metodo']):r for r in rows}
 for group in dict.fromkeys(r['grupo_muscular'] for r in rows):
  b,m=by[group,'B0'],by[group,'M3']; red=meta['r1_reductions'][group]*100
  lines.append(f"| {group} | {red:+.1f}% | {float(b['dist_superficie_simetrica_media_mm']):.2f} / {float(m['dist_superficie_simetrica_media_mm']):.2f} | {float(b['dist_unidirecional_denver_para_adaptado_media_mm']):.2f} / {float(m['dist_unidirecional_denver_para_adaptado_media_mm']):.2f} | {float(m['penetracao_ossea_pct_voxel_1mm']):.3f} | {float(m['dice_voxel_1mm']):.4f} |")
 lines += ['', 'A distância Denver→adaptado é exploratória, média de 6.000 pontos da superfície Denver às 6.000 amostras da superfície adaptada. As métricas completas, p95, volumes e contagens estão em `metricas_r3.csv`. R3/R4 usam voxelização de 1 mm e fechamento temporário em memória, como na rodada 1.','']
lines += ['## Inserções M2b e limitações','',
 '- Inserções M3: vértices do BP3D a ≤3 mm de osso e nos 10% terminais de cada extremidade ao longo do eixo principal PCA; projeção e relaxamento laplaciano (12 iterações, fator 0,22). Frações por músculo/osso em `insercoes_m3.csv` e índices em `insercoes_vertices_m3.json`.',
 '- R2 é em parte por construção porque os pontos de inserção são projetados no osso Denver. R3 é uma aproximação por voxels; contato de fronteira pode contribuir.',
 '- B0 é idêntico aos arquivos arquivados. A rodada 2 registrou discrepância não resolvida: CSV rodada 1 tem 20,2167 mm para B0 do reto femoral, enquanto reamostragem registrada com seed 25022 deu 18,6840 mm. Nesta rodada, R1 compara M3 e B0 no mesmo lote/seed; isso limita comparação direta dos valores R1 entre rodadas.',
 '- Um único indivíduo Denver e molde BP3D masculino; sem validação clínica ou generalização para outras mulheres.','',
 '## Arquivos e reprodução','',
 '- `adaptar_r3.py`: self-check, CPD, Q-osso, parada condicional, M3 e hashes.',
 '- `avaliar_r3.py`: verifica hashes e Q-osso antes de ler músculos Denver; calcula R1–R4 e Denver→adaptado.',
 '- `qosso.csv`, `hashes_adaptadas_r3.json`, `insercoes_m3.csv`, `insercoes_vertices_m3.json`, `metricas_r3.csv`, `metricas_meta_r3.json`, `veredito_r3.txt` e malhas PLY.',
 '- Reproduzir, nesta ordem: `C:\\Python314\\python.exe pesquisa/resultados/EXP-0025/rodada3/adaptar_r3.py`; se Q-osso passar, `C:\\Python314\\python.exe pesquisa/resultados/EXP-0025/rodada3/avaliar_r3.py`.',
 '', '**Revisão humana:** pendente. **Validação científica/clínica:** não realizada.','']
bad=[r['arquivo'] for r in manifest.get('adapted_meshes',[]) if hashlib.sha256((OUT/r['arquivo']).read_bytes()).hexdigest()!=r['sha256']]
lines.insert(lines.index('## Arquivos e reprodução'),f"Conferência final dos hashes: {len(manifest.get('adapted_meshes',[]))} malhas; divergências: {', '.join(bad) if bad else 'nenhuma'}.\n")
(OUT/'RELATORIO.md').write_text('\n'.join(lines),encoding='utf-8')
print('RELATORIO.md gerado; Q-osso',qpass,'; hashes divergentes',len(bad))
