"""Fast deterministic post-processing of round-2 sample/verdict fields."""
from pathlib import Path
import json,hashlib
import sys,site
sys.path.append(site.getusersitepackages())
import numpy as np
from scipy.spatial import cKDTree
HERE=Path(__file__).resolve().parent;R1=HERE.parent;OUT=HERE
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=json.loads((OUT/'resultados.json').read_text(encoding='utf-8'))
 base=json.loads((R1/'resultados.json').read_text(encoding='utf-8'))
 meta=json.loads((OUT/'malhas_publicadas.json').read_text(encoding='utf-8'));raw=(OUT/'malhas_publicadas.bin').read_bytes()
 parts={}
 for x in meta['meshes']:
  if x['name'] in ('VH_F_femur_R','VH_F_femur_L'):
   a=np.frombuffer(raw,dtype='<f8',count=x['vertices']*3,offset=x['vertex_offset']).reshape(-1,3).copy()
   R0=np.array([[-1.,0,0],[0,0,1],[0,1,0]])
   parts[x['name']]=(a@R0.T)*1000
 right,left=parts['VH_F_femur_R'],parts['VH_F_femur_L']
 plane=float((right[:,0].mean()+left[:,0].mean())/2)
 def mirror_stats(x):
  q=x.copy();q[:,0]=2*plane-q[:,0];d=cKDTree(left).query(q,k=1,workers=1)[0]
  return {'mean_mm':float(d.mean()),'p95_mm':float(np.percentile(d,95)),'max_mm':float(d.max())}
 q=right.copy();q[:,0]*=-1;d0=cKDTree(left).query(q,k=1,workers=1)[0]
 r['hra_f_femur_mirror_check']={'same_vertex_count':len(right)==len(left),'right_vertices':len(right),'left_vertices':len(left),
  'reflect_plane_canonical':'published atlas x=0 (x is patient-left)',
  'canonical_plane_nearest_vertex_residual':{'mean_mm':float(d0.mean()),'p95_mm':float(np.percentile(d0,95)),'max_mm':float(d0.max())},
  'centroid_midplane_ras_x_mm':plane,'centroid_midplane_nearest_vertex_residual':mirror_stats(right),
  'interpretation':'approximate mirror about the centroid-derived sagittal plane; not exact (nearest-vertex residuals reported; protocol defines no mirror threshold)'}
 v0n=int(base['criteria']['V0']['n_female']);nval=int(base['criteria']['V0']['n_validation']);nmen=int(r['male_replacement']['n_final'])
 v0=bool(v0n>=30 and nval>=20 and nmen>=20)
 r['female_sample']={'n_after_qc_q4':v0n,'n_dev':int(base['criteria']['V0']['n_female']-nval),'n_val':nval,'M1_mean_band_mm':base['bands']['M1_mean_mm']}
 r['criteria']['V0']={'pass':v0,'n_female':v0n,'n_validation':nval,'n_male':nmen}
 v1=bool(r['criteria']['V1']['pass']);cov=float(r['hra_f_hip_surface_coverage']['median'])
 if not v0 or not v1:verdict='inconclusive'
 elif cov<.90:verdict='inconclusive — V2 not evaluable because the published hra-f pelvis is incomplete'
 elif r['criteria']['V2']['pass'] and r['criteria']['V3']['pass']:verdict='H24 sustained'
 elif r['criteria']['V2']['pass']:verdict='H24 partial'
 else:verdict='H24 rejected'
 r['hypothesis_verdict']=verdict
 r['provenance']['analysis_script_sha256']=sha(OUT/'analisar_rodada2.py')
 r['provenance']['finalizer_sha256']=sha(Path(__file__))
 artifact_names=['analisar_rodada2.py','montar_atlas.mjs','finalizar_resultados.py','gerar_relatorio.py','gerar_figuras.py',
  'malhas_publicadas.json','malhas_publicadas.bin','atlas_publicados_frontal.png','distribuicao_m1.png','pelve_tipica.png',
  'atlas_surface_samples.npz','mascaras_homens_r2_manifest.json','homens_r2_qc_q4.json','cobertura_hra_f.csv','comparacoes_m1.json','RELATORIO.md']
 r['artifact_sha256']={name:sha(OUT/name) for name in artifact_names if (OUT/name).exists()}
 p=OUT/'resultados.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'V0':r['criteria']['V0'],'V1':r['criteria']['V1'],'V2':r['criteria']['V2'],'V3':r['criteria']['V3'],'verdict':verdict,'coverage_median':cov,'mirror':r['hra_f_femur_mirror_check']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
