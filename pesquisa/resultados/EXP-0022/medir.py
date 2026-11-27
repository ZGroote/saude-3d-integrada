"""Reproducible CPU geometry measurements for EXP-0022 (own code; python -I)."""
from __future__ import annotations
import sys,site,json,csv,re,hashlib
from pathlib import Path
from collections import defaultdict
from functools import lru_cache
sys.path.append(site.getusersitepackages())
import numpy as np
import nibabel as nib
import trimesh
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
EXT=ROOT/'hra/externo/female-atlas'; PACK=OUT/'bp3d-esqueletico.glb'
AT=json.loads((EXT/'public/models/atlas.json').read_text(encoding='utf8'))
T=json.loads((ROOT/'hra/alinhar/transformacoes.json').read_text(encoding='utf8'))
LABELS={int(k):v for k,v in T['source_multilabel']['nonempty_label_ids'].items()}
IMG=nib.load(str(ROOT/'hra/nlm/bruto/saida/segmentacao.nii.gz'))
VOL=np.asanyarray(IMG.dataobj); AFF=IMG.affine
RNG=np.random.default_rng(220022)

@lru_cache(maxsize=22)
def chunk_external(n):return (EXT/'public/models'/f'female-{n}.bin').read_bytes()

def mesh_external(p):
    raw=chunk_external(p['chunk'])
    v=np.frombuffer(raw,dtype='<f4',count=p['vertexCount']*3,offset=p['positions']).reshape(-1,3).copy()
    f=np.frombuffer(raw,dtype='<u4',count=p['indexCount'],offset=p['indices']).reshape(-1,3).copy()
    return trimesh.Trimesh(vertices=v,faces=f,process=False)

def external_all():
    return {p['id']:(p,mesh_external(p)) for p in AT['parts']}

def bp3d_all():
    scene=trimesh.load(str(PACK),force='scene',process=False)
    cat={r['arquivo']:r for r in csv.DictReader((ROOT/'bodyparts3d/catalogo_bp3d.csv').open(encoding='utf-8-sig'))}
    out={}
    for node in scene.graph.nodes_geometry:
        mat,gid=scene.graph.get(node); raw=scene.geometry[gid]
        # KHR_mesh_quantization encodes local positions as signed int16; scale the
        # quantized coordinates to [-1,1], then apply the GLTF node transform.
        verts=raw.vertices.astype(np.float64)/32767.0
        verts=trimesh.transform_points(verts,mat)
        m=trimesh.Trimesh(vertices=verts,faces=raw.faces.copy(),process=False)
        out[node]=(cat.get(node,{}),m)
    return out

def sample_surface(mesh,n,rng=RNG):
    if not len(mesh.faces): return np.empty((0,3))
    area=np.asarray(mesh.area_faces,dtype=float); total=area.sum()
    if total<=0:return np.empty((0,3))
    idx=rng.choice(len(area),size=n,p=area/total)
    tri=np.asarray(mesh.triangles[idx]); uv=rng.random((n,2)); su=np.sqrt(uv[:,0])
    return (1-su)[:,None]*tri[:,0]+(su*(1-uv[:,1]))[:,None]*tri[:,1]+(su*uv[:,1])[:,None]*tri[:,2]

def merged(meshes):
    return trimesh.util.concatenate(meshes)

def target_mesh(names):
    ids=[k for k,v in LABELS.items() if v in names]
    mask=np.isin(VOL,ids); coords=np.argwhere(mask)
    if not len(coords): raise ValueError(f'no NLM voxels for {names}')
    lo=coords.min(0); hi=coords.max(0)+1
    local=mask[tuple(slice(int(a),int(b)) for a,b in zip(lo,hi))]
    # Native trimesh voxel marching cubes: local voxel coordinates are transformed
    # through the recorded NIfTI affine to world RAS millimetres.
    m=trimesh.voxel.ops.matrix_to_marching_cubes(local,pitch=1.0)
    ijk=m.vertices+lo
    m.vertices=trimesh.transform_points(ijk,AFF)
    return m,{'labels':names,'ids':ids,'voxel_count':int(mask.sum()),'surface_faces':len(m.faces),'bbox_world_mm':m.bounds.tolist()}

def sample_count(mesh,n=25000):return sample_surface(mesh,n)

def fit_similarity_icp(src_local,target_points,max_iter=50,trim=.88):
    # Anatomical coordinates are x-left, y-up, z-front in metres. TC uses RAS mm.
    R0=np.array([[-1.,0,0],[0,0,1],[0,1,0]])
    src=np.asarray(src_local,dtype=float)
    dst=np.asarray(target_points,dtype=float)
    tree=cKDTree(dst)
    # Initialize orientation from documented frames; only translation is estimated.
    Q=src@(R0*1000).T
    trans=dst.mean(0)-Q.mean(0); scale=1.0; R=R0.copy()
    keep=max(3,int(len(src)*trim))
    for iteration in range(max_iter):
        moved=(src*(scale*1000))@R.T+trans
        d,ix=tree.query(moved,k=1,workers=-1)
        chosen=np.argpartition(d,keep-1)[:keep]
        X=src[chosen]; Y=dst[ix[chosen]]
        xm=X.mean(0);ym=Y.mean(0);X0=X-xm;Y0=Y-ym
        u,singular,vt=np.linalg.svd(X0.T@Y0);rr=vt.T@u.T
        if np.linalg.det(rr)<0:vt[-1]*=-1;rr=vt.T@u.T
        s_mm=float(np.sum((X0@rr.T)*Y0)/max(np.sum(X0*X0),1e-12))
        if s_mm<=0: raise ValueError('non-positive similarity scale')
        s=s_mm/1000.0
        tt=ym-(xm*s_mm)@rr.T
        change=np.linalg.norm(rr-R)+abs(s-scale)+np.linalg.norm(tt-trans)/1000
        R,scale,trans=rr,s,tt
        if change<1e-7:break
    return R,scale,trans,iteration+1

def symmetric_stats(srcmesh,targetmesh,n=25000):
    sp=sample_count(srcmesh,n);tp=sample_count(targetmesh,n)
    if not len(sp) or not len(tp): raise ValueError(f'empty surface samples: source={len(sp)} target={len(tp)}')
    ds=cKDTree(tp).query(sp,k=1,workers=-1)[0]
    dt=cKDTree(sp).query(tp,k=1,workers=-1)[0]
    both=np.r_[ds,dt]
    return {'mean_mm':float(both.mean()),'p95_mm':float(np.percentile(both,95)),
            'source_to_target_mean_mm':float(ds.mean()),'target_to_source_mean_mm':float(dt.mean()),'samples_each_direction':n}

def pelvis_sources(ext,bp):
    # Atlas pelvis = bilateral hip bones, all separately published HRA pelvic bone
    # fragments, and sacrum (coccyx excluded because the NLM segmentation has no coccyx label).
    em=[]; kept=[]
    for id,(p,m) in ext.items():
        text=(p['id']+' '+p['name']).lower()
        if p['system']=='skeletal' and (('hip bone' in text) or any(x in text for x in ('ilium','pubis','ischium')) or 'sacrum' in text):
            em.append(m);kept.append(p['id'])
    bm=[];bk=[]
    for id,(r,m) in bp.items():
        nm=r.get('nome_en','').lower()
        if ('hip bone' in nm) or nm=='sacrum':bm.append(m);bk.append(id)
    return merged(em),kept,merged(bm),bk

def category_metrics():
    ext=external_all();bp=bp3d_all()
    results={'metadata':{'python':'3.14.4','numpy':np.__version__,'trimesh':trimesh.__version__,'scipy':__import__('scipy').__version__,'nibabel':nib.__version__,
                         'nlm_path':'hra/nlm/bruto/saida/segmentacao.nii.gz','affine_ijk_to_world_RAS_mm':AFF.tolist(),
                         'bp3d_decoded_glb_nodes':244,
                         'sampling':'area-uniform triangle sampling; fixed seed 220022; pelvis 30,000 points/direction; femur/vertebra/rib 15,000 points/direction; exact cKDTree nearest distances; symmetric stats over concatenated directed distances',
                         'registration':'proper-rotation uniform similarity ICP; initial axis map local (x-left,y-up,z-front) to RAS (x-right,y-anterior,z-superior); trim 12%; 30,000 pelvis or 15,000 other source points; maximum 50 iterations; no reflection'},
              'masks':{},'comparisons':{}}
    pm,pi,bpm,bpi=pelvis_sources(ext,bp)
    pelvis_target,pd=target_mesh(['hip_left','hip_right','sacrum']);tp=sample_count(pelvis_target,30000)
    results['masks']['pelvis']=pd
    for label,mesh,parts in [('female_atlas',pm,pi),('bp3d_m',bpm,bpi)]:
        src=sample_count(mesh,30000);R,s,t,it=fit_similarity_icp(src,tp)
        transformed=mesh.copy();transformed.vertices=(transformed.vertices*(s*1000))@R.T+t
        print('pelvis fit',label,'scale',s,'iters',it,'parts',len(parts),flush=True)
        results['comparisons'][f'pelvis_{label}']={**symmetric_stats(transformed,pelvis_target,30000),'parts':parts,'uniform_scale':s,'iterations':it,
            'aligned_bounds_mm':transformed.bounds.tolist(),'rotation':R.tolist(),'translation_mm':t.tolist()}
        # Save fitted meshes for projections and reproducibility.
        transformed.export(OUT/f'{label}_pelvis_aligned.ply')
    # Femora, lumbar vertebrae and NLM-present ribs; each atlas mesh fitted independently.
    groups=[]
    for side in ('left','right'):
        groups.append((f'femur_{side}',[f'femur_{side}'],lambda p,s=side: p['system']=='skeletal' and (('femur' in p['name'].lower()) and (s in p['name'].lower() or ('left' if s=='left' else 'right') in p['name'].lower()))))
    # Match full names directly in both catalogs, preserving duplicate HRA/BP3D vertebrae.
    for i in range(1,6):groups.append((f'vertebrae_L{i}',[f'vertebrae_L{i}'],None))
    for side in ('left','right'):
        for i in range(1,13):groups.append((f'rib_{side}_{i}',[f'rib_{side}_{i}'],None))
    for key,names,_ in groups:
        try: tm,md=target_mesh(names)
        except ValueError:continue
        results['masks'][key]=md;targetpts=sample_count(tm,15000)
        candidate=[]
        if key.startswith('femur_'):
            side=key.split('_')[1]
            # For the HRA composite, choose the single explicitly sided femur; BP3D source uses the same part id.
            candidate=[(f'female_atlas:{p["id"]}',m) for p,m in ext.values() if p['system']=='skeletal' and 'femur' in p['name'].lower() and side in p['name'].lower()]
            namesbp=[(f'bp3d_m:{id}',m) for id,(r,m) in bp.items() if (side=='left' and 'left femur'==r.get('nome_en','').lower()) or (side=='right' and 'right femur'==r.get('nome_en','').lower())]
            candidate += namesbp
        elif key.startswith('vertebrae_'):
            i=int(key[-1]);candidate=[(f'female_atlas:{p["id"]}',m) for p,m in ext.values() if p['system']=='skeletal' and re.search(fr'lumbar vertebra {i}(?:$|\\b)',p['name'].lower())]
            ordinal=["first","second","third","fourth","fifth"][i-1]
            candbp=[(f'female_atlas:{p["id"]}',m) for p,m in ext.values() if p['system']=='skeletal' and p['id'].startswith('BP3D_') and p['name'].lower()==f'{ordinal} lumbar vertebra']
            candbp += [(f'bp3d_m:{id}',m) for id,(r,m) in bp.items() if r.get('nome_en','').lower()==f'{["first","second","third","fourth","fifth"][i-1]} lumbar vertebra']
            candidate += candbp
        else:
            side=key.split('_')[1];num=int(key.rsplit('_',1)[1]);word={1:'first',2:'second',3:'third',4:'fourth',5:'fifth',6:'sixth',7:'seventh',8:'eighth',9:'ninth',10:'tenth',11:'eleventh',12:'twelfth'}[num]
            sideword='left' if side=='left' else 'right'
            candidate=[(f'female_atlas:{p["id"]}',m) for p,m in ext.values() if p['system']=='skeletal' and 'rib' in p['name'].lower() and sideword in p['name'].lower() and word in p['name'].lower()]
            candidate += [(f'bp3d_m:{id}',m) for id,(r,m) in bp.items() if r.get('nome_en','').lower()==f'{sideword} {word} rib']
        for cname,sm in candidate:
            print('fit',key,cname,flush=True)
            sp=sample_count(sm,15000);R,s,t,it=fit_similarity_icp(sp,targetpts)
            aligned=sm.copy();aligned.vertices=(aligned.vertices*(s*1000))@R.T+t
            results['comparisons'][f'{key}|{cname}']={**symmetric_stats(aligned,tm,15000),'uniform_scale':s,'iterations':it,'parts':[cname],
                  'aligned_bounds_mm':aligned.bounds.tolist()}
    return results,ext,bp

if __name__=='__main__':
    r,ext,bp=category_metrics();(OUT/'metrics.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'comparison_count':len(r['comparisons']),'keys':list(r['comparisons'])[:15]},ensure_ascii=False))
