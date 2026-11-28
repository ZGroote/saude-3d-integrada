"""EXP-0024 round 2: offline only; uses published atlas node/world geometry."""
from pathlib import Path
import sys,site,json,csv,hashlib,importlib.util,struct,random,math,gc
sys.path.append(site.getusersitepackages())
import numpy as np, trimesh
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[4]
R1=ROOT/'pesquisa/resultados/EXP-0024'; OUT=R1/'rodada2'; DATA=ROOT/'hra/externo/totalseg_v3'
spec=importlib.util.spec_from_file_location('exp24_round1',R1/'analisar_local.py'); r1=importlib.util.module_from_spec(spec);spec.loader.exec_module(r1)
R0=np.array([[-1.,0,0],[0,0,1],[0,1,0]])
N=30000; COVER_N=300000; SEED=220024; Q4_PREFILTER=.05; Q4_LIMIT=1.0

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def load_published_meshes():
 meta=json.loads((OUT/'malhas_publicadas.json').read_text(encoding='utf-8'))
 raw=(OUT/'malhas_publicadas.bin').read_bytes(); meshes={}
 for x in meta['meshes']:
  v=np.frombuffer(raw,dtype='<f8',count=x['vertices']*3,offset=x['vertex_offset']).reshape(-1,3).copy()
  f=np.frombuffer(raw,dtype='<u4',count=x['triangles']*3,offset=x['index_offset']).reshape(-1,3).copy()
  # Match round-1 comparison frame conversion from published atlas axes to RAS millimetres.
  v=(v@R0.T)*1000.0
  meshes[(x['atlas'],x['name'])]=trimesh.Trimesh(vertices=v,faces=f,process=False)
 return meta,meshes

def join(parts):return trimesh.util.concatenate(parts)
def atlas_data(meshes,atlas):
 if atlas=='hra-f':
  names={'right':'VH_F_ilium_compact_bone_R','left':'VH_F_ilium_compact_bone_L'}
  sac='VH_F_sacrum'; fem={'right':'VH_F_femur_R','left':'VH_F_femur_L'}
  pelvis=join([meshes[(atlas,names['right'])],meshes[(atlas,names['left'])],meshes[(atlas,sac)]])
 else:
  names={'right':'FJ3152','left':'FJ3288'};sac='FJ3393';fem={'right':'FJ3365','left':'FJ3259'}
  pelvis=join([meshes[(atlas,names['right'])],meshes[(atlas,names['left'])],meshes[(atlas,sac)]])
 points=r1.points_sample(pelvis,N,SEED+(1 if atlas=='hra-f' else 2))
 fem_points={side:r1.points_sample(meshes[(atlas,n)],N,SEED+({'hra-f':{'right':4,'left':3},'bp3d-m':{'right':6,'left':5}}[atlas][side])) for side,n in fem.items()}
 return {'pelvis_mesh':pelvis,'pelvis':points,'femurs':fem_points,'femur_names':fem,'hip_names':names,'sacrum_name':sac}

def pelvic_qc(cid):
 reasons=[]
 for name in ('hip_left','hip_right','sacrum'):
  try: img=r1.load_img(cid,name); a=np.asanyarray(img.dataobj)>0
  except Exception as e:return False,[f'{name}: unavailable {type(e).__name__}']
  if not a.any():reasons.append(f'{name}: empty')
  elif np.any(a[:,:,0]) or np.any(a[:,:,-1]):reasons.append(f'{name}: touches first/last slice')
  del a,img;gc.collect()
 return not reasons,reasons

def surface(cid,names,seed):
 m=r1.mask_union_mesh(cid,names)
 if m is None:return None,None
 area=float(m.area);p=r1.points_sample(m,N,seed)
 return m,p,area

def closest_fraction(tree,points,threshold=5.0):
 d=tree.query(points,k=1,workers=1)[0]
 return float(np.mean(d<=threshold)),float(np.median(d)),float(np.percentile(d,95))

def sample_femur_head(points,side):return r1.proximal_head_center(points,side)

def main():
 base=json.loads((R1/'resultados.json').read_text(encoding='utf-8'))
 frozen=json.loads((R1/'parametros_congelados.json').read_text(encoding='utf-8'))
 oldqc=json.loads((R1/'qc.json').read_text(encoding='utf-8'))
 z=np.load(R1/'surface_samples.npz')
 dev=frozen['development_ids'];val=frozen['validation_ids'];women={c:z[f'p_{c}'] for c in val};template=z[f'p_{frozen["template_case_id"]}']
 mesh_meta,meshes=load_published_meshes();hra=atlas_data(meshes,'hra-f');bp=atlas_data(meshes,'bp3d-m')
 # Front-view proof: actual world-positioned published mesh parts, in atlas axes.
 fig,axs=plt.subplots(1,2,figsize=(12,8)); colors={'ilium_R':'#cf5961','ilium_L':'#e39a4c','sacrum':'#8b65a5','femur_R':'#4c78a8','femur_L':'#56a878'}
 specs={'hra-f':[('VH_F_ilium_compact_bone_R','ilium_R'),('VH_F_ilium_compact_bone_L','ilium_L'),('VH_F_sacrum','sacrum'),('VH_F_femur_R','femur_R'),('VH_F_femur_L','femur_L')],
        'bp3d-m':[('FJ3152','ilium_R'),('FJ3288','ilium_L'),('FJ3393','sacrum'),('FJ3365','femur_R'),('FJ3259','femur_L')]}
 for ax,atlas in zip(axs,('hra-f','bp3d-m')):
  for name,part in specs[atlas]:
   m=meshes[(atlas,name)];pts=r1.points_sample(m,min(6000,max(1000,len(m.faces))),SEED+int(hashlib.sha256(name.encode()).hexdigest()[:8],16))
   ax.scatter(pts[:,0],pts[:,2],s=1.0,alpha=.38,color=colors[part],label=part)
  ax.set_title(atlas+' — vista frontal (X–Z)');ax.set_xlabel('RAS X (mm)');ax.set_ylabel('RAS Z (mm)');ax.set_aspect('equal',adjustable='datalim');ax.grid(alpha=.2);ax.legend(markerscale=5)
 fig.suptitle('Atlas publicados montados em matrixWorld; malhas selecionadas pelo indice.json');fig.tight_layout();fig.savefig(OUT/'atlas_publicados_frontal.png',dpi=180);plt.close(fig)
 # Female femur mirror test. Report the canonical midline X=0 and the
 # centroid-derived sagittal plane, rather than declaring exact symmetry.
 fr=meshes[('hra-f','VH_F_femur_R')].vertices.copy();fl=meshes[('hra-f','VH_F_femur_L')].vertices.copy()
 # Transform back from RAS mm to published local coordinates in metres before testing the sagittal mirror.
 fr_local=(fr/1000.0)@R0;fl_local=(fl/1000.0)@R0
 reflected=fr_local.copy();reflected[:,0]*=-1
 mirror_d=cKDTree(fl_local).query(reflected,k=1,workers=1)[0]
 midplane_ras=float((fr[:,0].mean()+fl[:,0].mean())/2.0)
 reflected_best=fr.copy();reflected_best[:,0]=2*midplane_ras-reflected_best[:,0]
 mirror_best_d=cKDTree(fl).query(reflected_best,k=1,workers=1)[0]
 mirror={'same_vertex_count':len(fr_local)==len(fl_local),'right_vertices':len(fr_local),'left_vertices':len(fl_local),
         'reflect_plane_canonical':'published atlas x=0 (x is patient-left)',
         'mean_mm':float(mirror_d.mean()*1000),'p95_mm':float(np.percentile(mirror_d,95)*1000),'max_mm':float(mirror_d.max()*1000),
         'centroid_midplane_ras_x_mm':midplane_ras,
         'centroid_midplane_mean_mm':float(mirror_best_d.mean()),'centroid_midplane_p95_mm':float(np.percentile(mirror_best_d,95)),
         'centroid_midplane_max_mm':float(mirror_best_d.max()),
         'interpretation':'approximate mirror about the centroid-derived sagittal plane; not exact (nearest-vertex surface residuals reported, no protocol threshold specified)'}
 # Calculate reference female bands and M1 scores are immutable round-1 inputs.
 female_scores=base['female_scores']; bands=base['bands']; female_lim=bands['M1_mean_mm']['p97_5']
 # Surface coverage: women hip_left/right, against the aligned *published* HRA iliac/sacral triangles.
 cover_atlas=r1.points_sample(hra['pelvis_mesh'],COVER_N,SEED+901)
 coverage=[]; hip_cache={}; transforms={}
 for wi,cid in enumerate(val):
  st,_=r1.symmetric_after_similarity(hra['pelvis'],women[cid]);transforms[cid]=st
  R=np.asarray(st['rotation']);t=np.asarray(st['translation_mm']);ss=st['uniform_scale']
  ref=(cover_atlas*ss)@R.T+t; tree=cKDTree(ref)
  sides=[]
  for side in ('left','right'):
   nm='hip_'+side
   m,p,area=surface(cid,[nm],r1.id_seed(cid,700+(side=='right')))
   if m is None:raise RuntimeError(f'missing validation hip mask surface {cid}/{nm}')
   frac,med,p95=closest_fraction(tree,p)
   sides.append({'side':side,'surface_area_mm2':area,'sample_count':len(p),'fraction_within_5mm':frac,'distance_median_mm':med,'distance_p95_mm':p95})
   hip_cache[(cid,side)]={'mesh':m,'points':p,'area':area}
  total_area=sum(x['surface_area_mm2'] for x in sides)
  coverage.append({'case_id':cid,'fraction_within_5mm':sum(x['fraction_within_5mm']*x['surface_area_mm2'] for x in sides)/total_area,
                   'sides':sides,'alignment':{k:st[k] for k in ('uniform_scale','iterations','converged','last_delta')}})
 coverage_values=[x['fraction_within_5mm'] for x in coverage];coverage_median=float(np.median(coverage_values))
 # Ordered male replacement: retain original 12, then QC/Q4 candidates until 20.
 initial=list(oldqc['male_control_unique']);assert len(initial)==12
 orddata=json.loads((R1/'homens_r2_ordem.json').read_text(encoding='utf-8'));order=orddata['ordem']
 accepted=list(initial); men_pts={c:z[f'p_{c}'] for c in initial}; sizes={c:r1.centroid_size(men_pts[c]) for c in initial}
 male_qc=[];male_q4=[];used=[]
 for cid in order:
  if len(accepted)>=20:break
  used.append(cid);ok,reasons=pelvic_qc(cid)
  row={'id':cid,'q1_q2_pass':ok,'reasons':reasons,'decision':None}
  if not ok:row['decision']='excluded_qc';male_qc.append(row);continue
  try:
   mesh=r1.mask_union_mesh(cid,['hip_left','hip_right','sacrum'])
   if mesh is None:row['decision']='excluded_empty_union';male_qc.append(row);continue
   pts=r1.points_sample(mesh,N,r1.id_seed(cid,101));del mesh;gc.collect()
  except Exception as e:row['decision']='excluded_surface_error';row['reasons'].append(type(e).__name__);male_qc.append(row);continue
  size=r1.centroid_size(pts);dup=None;candidate_pairs=[]
  for prior in accepted:
   rel=abs(size-sizes[prior])/max(size,sizes[prior])
   if rel>=Q4_PREFILTER:
    candidate_pairs.append({'prior':prior,'relative_size_difference':rel,'icp_run':False,'reason':'size prefilter >=5%'});continue
   st,_=r1.symmetric_after_rigid(pts,men_pts[prior],5000,10000)
   pair={k:st[k] for k in ('mean_mm','p95_mm','iterations','converged')};pair.update({'prior':prior,'relative_size_difference':rel,'icp_run':True})
   candidate_pairs.append(pair)
   if st['mean_mm']<Q4_LIMIT:dup=prior;break
  male_q4.append({'candidate':cid,'pairs':candidate_pairs})
  if dup:
   row['decision']='excluded_q4_duplicate';row['duplicate_of']=dup
  else:
   accepted.append(cid);men_pts[cid]=pts;sizes[cid]=size;row['decision']='included';row['centroid_size_mm']=size
  male_qc.append(row)
 if len(accepted)!=20:print('WARNING: only',len(accepted),'males passed; exhausted',len(used),'extension candidates')
 # Fingerprint masks consulted in round 2. No files are downloaded here.
 mask_manifest={'source':'local masks supplied by user; this script is offline-only','case_ids':used,'mask_records':[]}
 for cid in used:
  for nm in r1.MASKS:
   p=DATA/cid/'segmentations'/f'{nm}.nii.gz'
   if p.exists():mask_manifest['mask_records'].append({'case_id':cid,'mask':nm,'bytes':p.stat().st_size,'sha256':sha(p)})
 mask_manifest['present_mask_count']=len(mask_manifest['mask_records']);mask_manifest['total_size_on_disk_bytes']=sum(x['bytes'] for x in mask_manifest['mask_records'])
 (OUT/'mascaras_homens_r2_manifest.json').write_text(json.dumps(mask_manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'homens_r2_qc_q4.json').write_text(json.dumps({'initial_retained':initial,'replacement_order_seed':orddata['seed'],'replacement_order':order,'candidates_evaluated':used,'final_accepted':accepted,'candidate_qc':male_qc,'q4':male_q4},ensure_ascii=False,indent=2),encoding='utf-8')
 # Fresh comparison cache isolated to round 2. Round-1 female LOO results stay unchanged;
 # old male comparison rows can be reused for the twelve retained controls.
 sig=hashlib.sha256(json.dumps({'samples':N,'max_iter':r1.MAX_ITER,'trim':r1.TRIM,'tol':r1.TOL,'method':'similarity'},sort_keys=True).encode()).hexdigest()
 priorcache={}
 for line in (R1/'m1_pairs.jsonl').read_text(encoding='utf-8').splitlines():
  try:
   x=json.loads(line)
   if x.get('signature')==sig:priorcache[x['key']]=x['stats']
  except Exception:pass
 m1cache={};male_scores={};male_p95={};male_details={}
 for man in accepted:
  vals=[];p95s=[];items=[]
  for woman in val:
   key=f'male::{man}::{woman}'
   st=priorcache.get(key) if man in initial else None
   if st is None:st,_=r1.symmetric_after_similarity(men_pts[man],women[woman])
   vals.append(st['mean_mm']);p95s.append(st['p95_mm']);items.append({'woman':woman,**st})
  male_scores[man]=float(np.mean(vals));male_p95[man]=float(np.mean(p95s));male_details[man]=items
  m1cache[man]={'mean_mm':male_scores[man],'p95_mean_mm':male_p95[man],'reused_round1_pairs':man in initial,'comparisons':len(items)}
 # Recompute M1 for both true published atlas comparators.
 comps={}
 for key,d in [('hra-f',hra),('bp3d-m',bp)]:
  vals=[];p95=[];stats=[]
  for woman in val:
   st,_=r1.symmetric_after_similarity(d['pelvis'],women[woman]);vals.append(st['mean_mm']);p95.append(st['p95_mm']);stats.append({'woman':woman,**st})
  score=float(np.mean(vals));score95=float(np.mean(p95))
  rigid,aligned=r1.symmetric_after_rigid(d['pelvis'],template)
  p=aligned;width=float(np.ptp(p[:,0]));depth=float(np.ptp(p[:,1]));height=float(np.ptp(p[:,2]))
  heads={}
  R=np.asarray(rigid['rotation']);t=np.asarray(rigid['translation_mm'])
  for side in ('left','right'):
   c,meta=sample_femur_head(d['femurs'][side],side);heads[side]={'center_mm':(c@R.T+t).tolist(),**meta}
  hd=float(np.linalg.norm(np.array(heads['left']['center_mm'])-np.array(heads['right']['center_mm'])))
  comps[key]={'M1_mean_mm':score,'M1_p95_mean_mm':score95,'M1_validation_comparisons':stats,
   'M2_centroid_size_mm':r1.centroid_size(d['pelvis']),'M3':{'width_height':width/height,'width_depth':width/depth,'femoral_head_distance_width':hd/width,'width_mm':width,'depth_mm':depth,'height_mm':height,'head_distance_mm':hd,'head_centers':heads},
   'rigid_alignment_to_development_template':{k:rigid[k] for k in ('iterations','converged','last_delta','rotation','translation_mm')}}
 # AUC, criteria and coverage gate from the frozen female distributions.
 auc=r1.auc_rank(list(male_scores.values()),list(female_scores.values()))
 n_female=int(base['criteria']['V0']['n_female'])
 v0=(n_female>=30 and len(val)>=20 and len(accepted)>=20)
 v1=auc>=.80
 coverage_ok=coverage_median>=.90
 if coverage_ok:
  h3=comps['hra-f']['M3'];v2=bool(comps['hra-f']['M1_mean_mm']<=female_lim and all(bands['M3'][k]['p2_5']<=h3[k]<=bands['M3'][k]['p97_5'] for k in h3))
  v2record={'status':'evaluated','pass':v2,'hra_f_M1_mean_mm':comps['hra-f']['M1_mean_mm'],'female_M1_p97_5_mm':female_lim,'hra_f_M3':h3}
 else:
  v2=False;v2record={'status':'not_evaluable_incomplete_pelvis','pass':None,'coverage_median':coverage_median,'coverage_threshold':.90,'detail':'median hip_left/right surface coverage by HRA within 5 mm is below 90%; per protocol, incomplete HRA pelvis'}
 v3=comps['bp3d-m']['M1_mean_mm']>female_lim
 verdict=('inconclusive' if not v0 or not v1 else
          ('inconclusive — V2 not evaluable because the published hra-f pelvis is incomplete' if not coverage_ok else
           ('H24 sustained' if v2 and v3 else ('H24 partial' if v2 else 'H24 rejected'))))
 # Produce real frontal comparison capture.
 # Save sample arrays separately from report to keep the report compact.
 np.savez_compressed(OUT/'atlas_surface_samples.npz',hra_pelvis=hra['pelvis'],bp3d_m_pelvis=bp['pelvis'],
   hra_femur_left=hra['femurs']['left'],hra_femur_right=hra['femurs']['right'],bp3d_m_femur_left=bp['femurs']['left'],bp3d_m_femur_right=bp['femurs']['right'])
 covsummary={'median':coverage_median,'p2_5':float(np.percentile(coverage_values,2.5)),'p97_5':float(np.percentile(coverage_values,97.5)),'n':len(coverage_values),'within_5mm':coverage}
 result={'round':2,'offline_only':True,'round1_female_metrics_reused':True,'frozen_female_parameters':frozen,
  'female_sample':{'n_after_qc_q4':n_female,'n_dev':len(dev),'n_val':len(val),'M1_mean_band_mm':bands['M1_mean_mm']},
  'male_replacement':{'n_initial_retained':len(initial),'n_added':len(accepted)-len(initial),'n_final':len(accepted),'accepted_ids':accepted,'evaluated_replacement_ids':used,'order_seed':orddata['seed'],'qc_q4_file':'homens_r2_qc_q4.json','m1':m1cache},
  'published_atlases':{k:{'version':'1.10-1' if k=='hra-f' else '4.0-1','unit':'m; converted to mm','parts':(hra if k=='hra-f' else bp)['hip_names']|{'sacrum':(hra if k=='hra-f' else bp)['sacrum_name'],'femurs':(hra if k=='hra-f' else bp)['femur_names']},'metrics':v} for k,v in comps.items()},
  'hra_f_hip_surface_coverage':covsummary,'hra_f_femur_mirror_check':mirror,
  'criteria':{'V0':{'pass':v0,'n_female':len(female_scores),'n_validation':len(val),'n_male':len(accepted)},'V1':{'pass':v1,'auc':auc,'minimum':.80},'V2':v2record,'V3':{'pass':v3,'bp3d_m_M1_mean_mm':comps['bp3d-m']['M1_mean_mm'],'female_M1_p97_5_mm':female_lim}},
  'hypothesis_verdict':verdict,'limitations':{'coverage_distance':'surface point samples (30,000 per side) against 300,000 sampled points on transformed HRA pelvis surface; KD-tree nearest-point estimate, workers=1','ICP_nonconvergence':'M1 convergence recorded per pair; same frozen 200-iteration limit as round 1'},
  'provenance':{'round1_results_sha256':sha(R1/'resultados.json'),'frozen_script_sha256':frozen['analysis_script_sha256'],'mesh_assembly_script_sha256':sha(OUT/'montar_atlas.mjs'),'analysis_script_sha256':sha(Path(__file__)),'published_mesh_manifest_sha256':sha(OUT/'malhas_publicadas.json'),'published_mesh_binary_sha256':sha(OUT/'malhas_publicadas.bin'),'female_parameters_unchanged':True}}
 (OUT/'cobertura_hra_f.csv').open('w',encoding='utf-8',newline='').write('case_id,fraction_within_5mm,area_mm2,side,fraction_side,distance_median_mm,distance_p95_mm\n'+'\n'.join(f"{c['case_id']},{c['fraction_within_5mm']:.9f},{s['surface_area_mm2']:.6f},{s['side']},{s['fraction_within_5mm']:.9f},{s['distance_median_mm']:.6f},{s['distance_p95_mm']:.6f}" for c in coverage for s in c['sides'])+'\n')
 (OUT/'resultados.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 # Store detailed comparison scores in a sibling artifact, not inline in summary JSON.
 (OUT/'comparacoes_m1.json').write_text(json.dumps({'atlas':{k:v['M1_validation_comparisons'] for k,v in comps.items()},'male':male_details},ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'coverage_median':coverage_median,'coverage_p2_5':covsummary['p2_5'],'accepted_males':accepted,'n_added':len(accepted)-len(initial),'criteria':result['criteria'],'verdict':verdict,'mirror':mirror},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
