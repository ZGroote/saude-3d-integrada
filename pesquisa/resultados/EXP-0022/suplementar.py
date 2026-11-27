"""Post-hoc pelvic comparisons and duplicate-source inventory; python -I."""
from pathlib import Path
import sys,site,json,csv,re
from collections import defaultdict
sys.path.append(site.getusersitepackages())
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import numpy as np
import trimesh
from scipy.spatial import cKDTree
import medir as g

SEED=220022;SAMPLES=30000;MAX_ITER=200;TRIM=.88;TOL=1e-7

def sample(mesh,n,rng):return g.sample_surface(mesh,n,rng)

def icp(src_local,target_points):
    """Same transform, trim, and convergence delta as medir.py; cap raised to 200."""
    R0=np.array([[-1.,0,0],[0,0,1],[0,1,0]])
    src=np.asarray(src_local,dtype=float);dst=np.asarray(target_points,dtype=float);tree=cKDTree(dst)
    q=src@(R0*1000).T;trans=dst.mean(0)-q.mean(0);scale=1.0;R=R0.copy()
    keep=max(3,int(len(src)*TRIM));last_delta=None;converged=False
    for iteration in range(MAX_ITER):
        moved=(src*(scale*1000))@R.T+trans
        d,ix=tree.query(moved,k=1,workers=-1);chosen=np.argpartition(d,keep-1)[:keep]
        X=src[chosen];Y=dst[ix[chosen]];xm=X.mean(0);ym=Y.mean(0);X0=X-xm;Y0=Y-ym
        u,_,vt=np.linalg.svd(X0.T@Y0);rr=vt.T@u.T
        if np.linalg.det(rr)<0:vt[-1]*=-1;rr=vt.T@u.T
        scale_mm=float(np.sum((X0@rr.T)*Y0)/max(np.sum(X0*X0),1e-12))
        if scale_mm<=0:raise ValueError('non-positive similarity scale')
        new_scale=scale_mm/1000;new_t=ym-(xm*scale_mm)@rr.T
        last_delta=float(np.linalg.norm(rr-R)+abs(new_scale-scale)+np.linalg.norm(new_t-trans)/1000)
        R,scale,trans=rr,new_scale,new_t
        if last_delta<TOL:converged=True;break
    return R,scale,trans,iteration+1,converged,last_delta

def metric(source,target,rng,target_fit,target_dist):
    # Both sources share identical target point samples for paired comparison.
    fit_src=sample(source,SAMPLES,rng)
    R,s,t,it,conv,delta=icp(fit_src,target_fit)
    aligned=source.copy();aligned.vertices=(aligned.vertices*(s*1000))@R.T+t
    # Symmetric sampled surface distances, same definition and count as baseline pelvis.
    ps=sample(aligned,SAMPLES,rng);pt=target_dist
    ds=cKDTree(pt).query(ps,k=1,workers=-1)[0];dt=cKDTree(ps).query(pt,k=1,workers=-1)[0]
    both=np.r_[ds,dt]
    return {'mean_mm':float(both.mean()),'p95_mm':float(np.percentile(both,95)),
            'source_to_target_mean_mm':float(ds.mean()),'target_to_source_mean_mm':float(dt.mean()),
            'uniform_scale':float(s),'iterations':it,'converged':conv,'last_delta':delta,
            'samples_each_direction':SAMPLES,'rotation':R.tolist(),'translation_mm':t.tolist(),
            'aligned_bounds_mm':aligned.bounds.tolist()}

def write_duplicates():
    parts=g.AT['parts'];hra=[p for p in parts if not p['id'].startswith('BP3D_')];bp=[p for p in parts if p['id'].startswith('BP3D_')]
    groups=[]
    # Exact shared FMA ontology IDs are the most conservative cross-source matches.
    hidx=defaultdict(list);bidx=defaultdict(list)
    for p in hra:
        cid=p.get('conceptId','').replace(':','')
        if cid.startswith('FMA'):hidx[cid].append(p)
    for p in bp:
        cid=p.get('conceptId','').replace(':','')
        if cid.startswith('FMA'):bidx[cid].append(p)
    for cid in sorted(hidx.keys()&bidx.keys()):
        hs=hidx[cid];bs=bidx[cid]
        groups.append({'match_basis':'shared FMA conceptId','structure_id':cid,'structure_label':hs[0]['name'],
                       'hra_mesh_ids':';'.join(p['id'] for p in hs),'hra_mesh_names':';'.join(p['name'] for p in hs),
                       'bp3d_mesh_ids':';'.join(p['id'] for p in bs),'bp3d_mesh_names':';'.join(p['name'] for p in bs),
                       'overlap_class':'same ontology structure'})
    signatures={(tuple(sorted(x['hra_mesh_ids'].split(';'))),tuple(sorted(x['bp3d_mesh_ids'].split(';')))) for x in groups}
    # Exact normalized English names add source pairs where the atlas did not
    # carry the same FMA concept identifier in both source records.
    hnames=defaultdict(list);bnames=defaultdict(list)
    for p in hra:hnames[p['name'].strip().lower()].append(p)
    for p in bp:bnames[p['name'].strip().lower()].append(p)
    name_groups=0
    for name in sorted(hnames.keys()&bnames.keys()):
        hs=hnames[name];bs=bnames[name];sig=(tuple(sorted(p['id'] for p in hs)),tuple(sorted(p['id'] for p in bs)))
        if sig in signatures:continue
        groups.append({'match_basis':'exact normalized mesh name','structure_id':'name:'+name,'structure_label':hs[0]['name'],
                       'hra_mesh_ids':';'.join(p['id'] for p in hs),'hra_mesh_names':';'.join(p['name'] for p in hs),
                       'bp3d_mesh_ids':';'.join(p['id'] for p in bs),'bp3d_mesh_names':';'.join(p['name'] for p in bs),
                       'overlap_class':'same normalized name; structure match inferred from labels'})
        signatures.add(sig);name_groups+=1
    # HRA has UBERON IDs for the vertebral column; match the named anatomy directly
    # to the BP3D FMA names and IDs. This includes sacrum and C1-C7/L1-L5/T1-T12.
    ords=['first','second','third','fourth','fifth','sixth','seventh','eighth','ninth','tenth','eleventh','twelfth']
    hbyid={p['id']:p for p in hra};bname=defaultdict(list)
    for p in bp:bname[p['name'].lower()].append(p)
    axial=[]
    axial.append(('VH_F_sacrum','sacrum','Sacrum'))
    for n in range(1,6):axial.append((f'VH_F_lumbar_vertebra_{n}',f'lumbar vertebra {n}',f'{ords[n-1]} lumbar vertebra'))
    for n in range(1,13):axial.append((f'VH_F_thoracic_vertebra_{n}',f'thoracic vertebra {n}',f'{ords[n-1]} thoracic vertebra'))
    for n in range(1,8):
        bname_text='Atlas' if n==1 else 'Axis' if n==2 else f'{ords[n-1]} cervical vertebra'
        axial.append((f'VH_F_cervical_vertebra_{n}',f'cervical vertebra {n}',bname_text))
    axial_groups=0
    for hid,label,bn in axial:
        h=hbyid.get(hid);bs=bname.get(bn.lower(),[])
        sig=((h['id'],),tuple(sorted(p['id'] for p in bs))) if h and bs else None
        if h and bs and sig not in signatures:
            groups.append({'match_basis':'canonical axial bone name / source catalog name','structure_id':label,'structure_label':label,
                           'hra_mesh_ids':h['id'],'hra_mesh_names':h['name'],'bp3d_mesh_ids':';'.join(p['id'] for p in bs),
                           'bp3d_mesh_names':';'.join(p['name'] for p in bs),'overlap_class':'same anatomical structure'})
            signatures.add(sig);axial_groups+=1
    exact_count=len(groups)
    # Parent/fragment overlap: the full BP3D hip bone overlaps HRA pubis/ilium/ischium parts;
    # these are reported separately as non-identical levels of anatomical granularity.
    for side,letter,bpid in [('left','L','BP3D_FJ3288'),('right','R','BP3D_FJ3152')]:
        hs=[p for p in hra if p['id'].startswith(('VH_F_pubis_','VH_F_ilium_','VH_F_ischium_')) and p['id'].endswith('_'+letter)]
        b=next((p for p in bp if p['id']==bpid),None)
        if hs and b:groups.append({'match_basis':'parent structure overlaps named HRA fragments','structure_id':f'hip_bone_{side}','structure_label':f'{side} hip bone / pubis+ilium+ischium',
                                   'hra_mesh_ids':';'.join(p['id'] for p in hs),'hra_mesh_names':';'.join(p['name'] for p in hs),
                                   'bp3d_mesh_ids':b['id'],'bp3d_mesh_names':b['name'],'overlap_class':'partial parent/fragment overlap; not counted as exact duplicate'})
    fields=['match_basis','structure_id','structure_label','hra_mesh_ids','hra_mesh_names','bp3d_mesh_ids','bp3d_mesh_names','overlap_class']
    with (HERE/'suplementar_duplicadas.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(groups)
    return {'exact_duplicate_structure_groups':exact_count,'partial_parent_fragment_overlap_groups':len(groups)-exact_count,
            'total_reported_groups':len(groups),'csv':'suplementar_duplicadas.csv',
            'exact_groups_by_basis':{'shared_FMA_concept':len(hidx.keys()&bidx.keys()),'exact_normalized_name':name_groups,'axial_name_mapping':axial_groups}}

def main():
    ext=g.external_all();bp=g.bp3d_all()
    hips_f=trimesh.util.concatenate([ext['BP3D_FJ3152'][1],ext['BP3D_FJ3288'][1]])
    hips_b=trimesh.util.concatenate([bp['FJ3152'][1],bp['FJ3288'][1]])
    pelvis_f=trimesh.util.concatenate([hips_f,ext['BP3D_FJ3393'][1]])
    pelvis_b=trimesh.util.concatenate([hips_b,bp['FJ3393'][1]])
    out={}
    for name,src_names,source in [('a_hips_only',['hip_left','hip_right'],{'female_atlas':['BP3D_FJ3152','BP3D_FJ3288'],'bp3d_m':['FJ3152','FJ3288']}),
                                  ('b_hips_plus_bp3d_sacrum',['hip_left','hip_right','sacrum'],{'female_atlas':['BP3D_FJ3152','BP3D_FJ3288','BP3D_FJ3393'],'bp3d_m':['FJ3152','FJ3288','FJ3393']})]:
        target,mask_info=g.target_mesh(src_names)
        target_fit=sample(target,SAMPLES,np.random.default_rng(SEED+1))
        target_dist=sample(target,SAMPLES,np.random.default_rng(SEED+2))
        fa=hips_f if name.startswith('a_') else pelvis_f;bm=hips_b if name.startswith('a_') else pelvis_b
        ma=metric(fa,target,np.random.default_rng(SEED+3),target_fit,target_dist)
        mb=metric(bm,target,np.random.default_rng(SEED+4),target_fit,target_dist)
        red=(1-ma['mean_mm']/mb['mean_mm'])*100
        p95red=(1-ma['p95_mm']/mb['p95_mm'])*100
        out[name]={'target_labels':mask_info,'sources':source,'female_atlas':ma,'bp3d_m':mb,'mean_reduction_percent':float(red),'p95_reduction_percent':float(p95red),
                   'interpretation':'post-hoc only; does not change preregistered criteria or verdict'}
    out['c_duplicates']=write_duplicates()
    out['method']={'analysis':'post-hoc, not part of fixed success criteria','seed':SEED,'surface_samples_each_direction':SAMPLES,
                   'sampling':'same area-uniform triangle sampling, cKDTree, concatenated bidirectional surface distances as baseline pelvis analysis',
                   'ICP':'same initial local-to-RAS axis map, proper rotation, uniform scale, translation, trim=0.12, delta tolerance=1e-7; max iterations raised from 50 to 200; convergence reported explicitly',
                   'python':'3.14.4','numpy':np.__version__,'trimesh':trimesh.__version__,'scipy':__import__('scipy').__version__}
    (HERE/'suplementar.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'a':{'female':(out['a_hips_only']['female_atlas']['mean_mm'],out['a_hips_only']['female_atlas']['p95_mm']),'bp3d':(out['a_hips_only']['bp3d_m']['mean_mm'],out['a_hips_only']['bp3d_m']['p95_mm']),'mean_reduction':out['a_hips_only']['mean_reduction_percent'],'p95_reduction':out['a_hips_only']['p95_reduction_percent'],'converged':[out['a_hips_only']['female_atlas']['converged'],out['a_hips_only']['bp3d_m']['converged']]},
                      'b':{'female':(out['b_hips_plus_bp3d_sacrum']['female_atlas']['mean_mm'],out['b_hips_plus_bp3d_sacrum']['female_atlas']['p95_mm']),'bp3d':(out['b_hips_plus_bp3d_sacrum']['bp3d_m']['mean_mm'],out['b_hips_plus_bp3d_sacrum']['bp3d_m']['p95_mm']),'mean_reduction':out['b_hips_plus_bp3d_sacrum']['mean_reduction_percent'],'p95_reduction':out['b_hips_plus_bp3d_sacrum']['p95_reduction_percent'],'converged':[out['b_hips_plus_bp3d_sacrum']['female_atlas']['converged'],out['b_hips_plus_bp3d_sacrum']['bp3d_m']['converged']]},'c':out['c_duplicates']}))

if __name__=='__main__':main()
