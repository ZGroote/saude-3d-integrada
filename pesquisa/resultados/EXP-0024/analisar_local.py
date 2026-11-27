"""EXP-0024 local-only QC and analysis. Never opens network connections; python -I."""
from pathlib import Path
import sys,site,csv,json,hashlib,random,math,platform,struct,zlib,gc
sys.path.append(site.getusersitepackages())
import numpy as np, nibabel as nib, trimesh, scipy
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
from nibabel.processing import resample_from_to
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
DATA=ROOT/'hra/externo/totalseg_v3'; OUT22=ROOT/'pesquisa/resultados/EXP-0022'
MASKS=('hip_left','hip_right','sacrum','femur_left','femur_right')
SEED=240024; N_SURFACE=30000; N_Q4_FIT=5000; N_Q4_DIST=10000
TRIM=.88; TOL=1e-7; MAX_ITER=200; Q4_THRESHOLD_MM=1.0; Q4_SIZE_PREFILTER=0.05
R0=np.array([[-1.,0,0],[0,0,1],[0,1,0]]) # atlas local x-left,y-up,z-front -> RAS x-right,y-anterior,z-superior
SAMPLE_SEED=220024

def sha_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def id_seed(case,offset=0):return (SEED+int(hashlib.sha256(case.encode()).hexdigest()[:8],16)+offset)%(2**32)
def points_sample(mesh,n,seed):
    pts,_=trimesh.sample.sample_surface(mesh,n,seed=int(seed));return np.asarray(pts,dtype=np.float64)
def load_img(case,name):return nib.load(str(DATA/case/'segmentations'/f'{name}.nii.gz'))
def same_grid(a,b):return a.shape==b.shape and np.allclose(a.affine,b.affine,atol=1e-5)

def mask_union_mesh(case,names):
    ref=load_img(case,names[0]);parts=[];overall_lo=np.array(ref.shape);overall_hi=np.zeros(3,dtype=int)
    for name in names:
        img=ref if name==names[0] else load_img(case,name)
        if not same_grid(ref,img):img=resample_from_to(img,(ref.shape,ref.affine),order=0)
        a=np.asanyarray(img.dataobj)>0
        if not a.any():del a,img;continue
        bounds=[]
        for axis in range(3):
            other=tuple(i for i in range(3) if i!=axis)
            nz=np.flatnonzero(np.any(a,axis=other));bounds.append((int(nz[0]),int(nz[-1])+1))
        lo=np.array([x[0] for x in bounds]);hi=np.array([x[1] for x in bounds])
        cropped=a[tuple(slice(int(x),int(y)) for x,y in zip(lo,hi))].copy();parts.append((lo,hi,cropped))
        overall_lo=np.minimum(overall_lo,lo);overall_hi=np.maximum(overall_hi,hi)
        del a,img,cropped;gc.collect()
    if not parts:return None
    union=np.zeros(tuple(overall_hi-overall_lo),dtype=np.uint8)
    for lo,hi,cropped in parts:
        sl=tuple(slice(int(x-overall_lo[i]),int(y-overall_lo[i])) for i,(x,y) in enumerate(zip(lo,hi)))
        union[sl]|=cropped
    mesh=trimesh.voxel.ops.matrix_to_marching_cubes(union,pitch=1.0)
    mesh.vertices=trimesh.transform_points(mesh.vertices+overall_lo,ref.affine)
    del union,parts;gc.collect()
    return mesh

def femur_qc(case,name):
    img=load_img(case,name);a=np.asanyarray(img.dataobj)>0
    if not a.any():return {'pass':False,'reason':'empty mask','principal_extent_mm':None,'touches_superior_volume_edge':None}
    # Exact principal-axis moments, accumulated by slice to avoid a full-volume
    # coordinate array. The NIfTI affine maps voxel indices to millimetres.
    count=0;sum_p=np.zeros(3,dtype=np.float64);sum_pp=np.zeros((3,3),dtype=np.float64)
    for z in range(a.shape[2]):
        xy=np.argwhere(a[:,:,z])
        if not len(xy):continue
        ijk=np.column_stack((xy,np.full(len(xy),z)))
        world=ijk@img.affine[:3,:3].T+img.affine[:3,3]
        count+=len(world);sum_p+=world.sum(0);sum_pp+=world.T@world
    center=sum_p/count
    cov=sum_pp/count-np.outer(center,center)
    vals,vecs=np.linalg.eigh(cov);axis=vecs[:,int(np.argmax(vals))]
    lo=float('inf');hi=float('-inf')
    for z in range(a.shape[2]):
        xy=np.argwhere(a[:,:,z])
        if not len(xy):continue
        ijk=np.column_stack((xy,np.full(len(xy),z)))
        world=ijk@img.affine[:3,:3].T+img.affine[:3,3]
        proj=(world-center)@axis
        lo=min(lo,float(proj.min()));hi=max(hi,float(proj.max()))
    extent=hi-lo
    slice_axis=int(np.argmax(np.abs(img.affine[2,:3])));superior_high=img.affine[2,slice_axis]>0
    edge_idx=a.shape[slice_axis]-1 if superior_high else 0
    edge=bool(np.any(np.take(a,edge_idx,axis=slice_axis)))
    ok=extent>=100 and not edge
    del a;gc.collect()
    return {'pass':ok,'principal_extent_mm':extent,'touches_superior_volume_edge':edge,
            'reason':None if ok else ('extent below 100 mm' if extent<100 else 'touches superior volume edge')}

def basic_qc(case):
    reasons=[];q1=True;q2=True
    for name in ('hip_left','hip_right','sacrum'):
        try:img=load_img(case,name);a=np.asanyarray(img.dataobj)>0
        except Exception as e:q1=False;reasons.append(f'Q1 unavailable {name}: {type(e).__name__}');continue
        if not a.any():q1=False;reasons.append(f'Q1 empty {name}')
        elif np.any(a[:,:,0]) or np.any(a[:,:,-1]):q2=False;reasons.append(f'Q2 {name} touches first/last slice')
        del a,img;gc.collect()
    q3={name:femur_qc(case,name) for name in ('femur_left','femur_right')}
    return {'Q1':q1,'Q2':q2,'Q3':q3,'pelvis_pass':q1 and q2,'reasons':reasons}

def centroid_size(points):
    c=points.mean(0);return float(np.sqrt(np.sum(np.sum((points-c)**2,axis=1))))

def rigid_fit(src,dst,max_iter=MAX_ITER,trim=TRIM,tol=TOL):
    src=np.asarray(src,dtype=np.float64);dst=np.asarray(dst,dtype=np.float64)
    tree=cKDTree(dst);R=np.eye(3);t=dst.mean(0)-src.mean(0);keep=max(3,int(len(src)*trim));converged=False;delta=None
    for it in range(max_iter):
        moved=src@R.T+t;d,ix=tree.query(moved,k=1,workers=1);sel=np.argpartition(d,keep-1)[:keep]
        X=src[sel];Y=dst[ix[sel]];xm=X.mean(0);ym=Y.mean(0)
        u,_,vt=np.linalg.svd((X-xm).T@(Y-ym));rr=vt.T@u.T
        if np.linalg.det(rr)<0:vt[-1]*=-1;rr=vt.T@u.T
        tt=ym-xm@rr.T
        delta=float(np.linalg.norm(rr-R)+np.linalg.norm(tt-t)/1000)
        R,t=rr,tt
        if delta<tol:converged=True;break
    return R,t,it+1,converged,delta

def similarity_fit(src,dst,max_iter=MAX_ITER,trim=TRIM,tol=TOL):
    src=np.asarray(src,dtype=np.float64);dst=np.asarray(dst,dtype=np.float64)
    tree=cKDTree(dst);R=np.eye(3);scale=1.0;t=dst.mean(0)-src.mean(0);keep=max(3,int(len(src)*trim));converged=False;delta=None
    for it in range(max_iter):
        moved=(src*scale)@R.T+t;d,ix=tree.query(moved,k=1,workers=1);sel=np.argpartition(d,keep-1)[:keep]
        X=src[sel];Y=dst[ix[sel]];xm=X.mean(0);ym=Y.mean(0);X0=X-xm;Y0=Y-ym
        u,_,vt=np.linalg.svd(X0.T@Y0);rr=vt.T@u.T
        if np.linalg.det(rr)<0:vt[-1]*=-1;rr=vt.T@u.T
        ss=float(np.sum((X0@rr.T)*Y0)/max(np.sum(X0*X0),1e-12))
        if ss<=0:raise ValueError('non-positive similarity scale')
        tt=ym-(xm*ss)@rr.T
        delta=float(np.linalg.norm(rr-R)+abs(ss-scale)+np.linalg.norm(tt-t)/1000)
        R,scale,t=rr,ss,tt
        if delta<tol:converged=True;break
    return R,scale,t,it+1,converged,delta

def symmetric_after_similarity(src,dst):
    R,s,t,it,conv,delta=similarity_fit(src,dst)
    aligned=(src*s)@R.T+t
    ds=cKDTree(dst).query(aligned,k=1,workers=1)[0]
    dt=cKDTree(aligned).query(dst,k=1,workers=1)[0]
    both=np.r_[ds,dt]
    return {'mean_mm':float(both.mean()),'p95_mm':float(np.percentile(both,95)),
            'source_to_target_mean_mm':float(ds.mean()),'target_to_source_mean_mm':float(dt.mean()),
            'uniform_scale':s,'iterations':it,'converged':conv,'last_delta':delta,
            'rotation':R.tolist(),'translation_mm':t.tolist()},aligned

def symmetric_after_rigid(src,dst,nfit=None,ndist=None):
    if nfit and len(src)>nfit:srcfit=src[np.linspace(0,len(src)-1,nfit,dtype=int)]
    else:srcfit=src
    R,t,it,conv,delta=rigid_fit(srcfit,dst)
    aligned=src@R.T+t
    if ndist and len(aligned)>ndist:
        ai=aligned[np.linspace(0,len(aligned)-1,ndist,dtype=int)];di=dst[np.linspace(0,len(dst)-1,ndist,dtype=int)]
    else:ai=aligned;di=dst
    ds=cKDTree(di).query(ai,k=1,workers=1)[0]
    dt=cKDTree(ai).query(di,k=1,workers=1)[0]
    both=np.r_[ds,dt]
    return {'mean_mm':float(both.mean()),'p95_mm':float(np.percentile(both,95)),
            'source_to_target_mean_mm':float(ds.mean()),'target_to_source_mean_mm':float(dt.mean()),
            'iterations':it,'converged':conv,'last_delta':delta,'rotation':R.tolist(),'translation_mm':t.tolist()},aligned

def q4_filter(ids,case_points,qc):
    accepted=[];decisions={};pairs=[];sizes={c:centroid_size(case_points[c]) for c in ids}
    for cid in sorted(ids):
        if not qc[cid]['pelvis_pass']:
            decisions[cid]=('excluded','; '.join(qc[cid]['reasons']) or 'Q1/Q2 failed');continue
        dup=None
        for prior in accepted:
            a=sizes[cid];b=sizes[prior];rel=abs(a-b)/max(a,b)
            if rel>=Q4_SIZE_PREFILTER:
                pairs.append({'case_a':prior,'case_b':cid,'centroid_size_a':b,'centroid_size_b':a,'relative_difference':rel,'icp_run':False,'reason':'Q4 size prefilter >=5%'})
                continue
            stats,_=symmetric_after_rigid(case_points[cid],case_points[prior],N_Q4_FIT,N_Q4_DIST)
            pair={'case_a':prior,'case_b':cid,'centroid_size_a':b,'centroid_size_b':a,'relative_difference':rel,'icp_run':True,**stats}
            pairs.append(pair)
            if stats['mean_mm']<Q4_THRESHOLD_MM:dup=prior;break
        if dup:
            decisions[cid]=('excluded',f'Q4 duplicate of {dup}; rigid symmetric mean {pair["mean_mm"]:.6f} mm < 1.0 mm')
        else:
            accepted.append(cid);decisions[cid]=('included','Q1/Q2 passed; no Q4 duplicate below 1.0 mm among size-prefilter candidate pairs')
    return accepted,decisions,pairs,sizes

def load_patient_data(cases,cached_qc=None,mask_signature=None):
    qc={};pelvis={};femurs={};m2={}
    cache_path=HERE/'surface_samples.npz';cache_meta=HERE/'surface_samples.json'
    if mask_signature and cache_path.exists() and cache_meta.exists():
        meta=json.loads(cache_meta.read_text(encoding='utf-8'))
        if meta.get('mask_set_sha256')==mask_signature and cached_qc:
            z=np.load(cache_path);pelvis={c:z[f'p_{c}'] for c in cases if f'p_{c}' in z.files};femurs={(c,s):z[f'f_{c}_{s}'] for c in cases for s in ('left','right') if f'f_{c}_{s}' in z.files}
            qc={c:cached_qc[c] for c in cases};m2={c:centroid_size(pelvis[c]) for c in pelvis}
            print('Reusing saved surface samples; mask hashes match.',flush=True)
            return qc,pelvis,femurs,m2
    for cid in cases:
        print('QC and surfaces',cid,flush=True)
        qc[cid]=cached_qc[cid] if cached_qc and cid in cached_qc else basic_qc(cid)
        try:
            mesh=mask_union_mesh(cid,['hip_left','hip_right','sacrum'])
            if mesh is None:qc[cid]['Q1']=qc[cid]['Q2']=qc[cid]['pelvis_pass']=False;qc[cid]['reasons'].append('empty pelvis union');continue
            pts=points_sample(mesh,N_SURFACE,id_seed(cid,101));pelvis[cid]=pts;m2[cid]=centroid_size(pts)
            del mesh;gc.collect()
            for side in ('left','right'):
                fm=mask_union_mesh(cid,[f'femur_{side}'])
                if fm is None:femurs[(cid,side)]=np.empty((0,3));continue
                femurs[(cid,side)]=points_sample(fm,N_SURFACE,id_seed(cid,200+(side=='right')));del fm;gc.collect()
        except Exception as e:
            qc[cid]['Q1']=qc[cid]['Q2']=qc[cid]['pelvis_pass']=False;qc[cid]['reasons'].append(f'surface extraction failed: {type(e).__name__}: {e}')
    arr={}
    for cid in pelvis:arr['p_'+cid]=pelvis[cid]
    for (cid,side),p in femurs.items():arr[f'f_{cid}_{side}']=p
    np.savez_compressed(cache_path,**arr)
    cache_meta.write_text(json.dumps({'mask_set_sha256':mask_signature,'case_ids':cases,'samples_each_surface':N_SURFACE},indent=2),encoding='utf-8')
    return qc,pelvis,femurs,m2

def proximal_head_center(points,side):
    if len(points)<100:raise ValueError(f'insufficient femur points: {len(points)}')
    c=points.mean(0);_,_,vt=np.linalg.svd(points-c,full_matrices=False);axis=vt[0]
    if axis[2]<0:axis=-axis
    q=(points-c)@axis;top=q.max();prox=points[q>=top-100.0];qprox=q[q>=top-100.0]
    if len(prox)<100:raise ValueError('proximal 100mm region has too few sampled points')
    # Head cap: proximal 35mm, then medial quarter (RAS: left head points toward -X; right toward +X).
    cap=prox[qprox>=top-35.0];medial_x=np.percentile(cap[:,0],25 if side=='left' else 75)
    head=cap[cap[:,0]<=medial_x] if side=='left' else cap[cap[:,0]>=medial_x]
    if len(head)<30:head=cap
    A=np.column_stack((2*head,np.ones(len(head))));b=np.sum(head*head,axis=1)
    sol=np.linalg.lstsq(A,b,rcond=None)[0];center=sol[:3];radius=np.sqrt(max(0.,sol[3]+center@center))
    return center,{'sphere_radius_mm':float(radius),'head_sample_count':int(len(head)),'proximal_region_mm':100,'head_cap_mm':35,'method':'algebraic sphere fit to proximal 35mm, medial 25% of sampled cap'}

def atlas_sources():
    sys.path.insert(0,str(OUT22));import medir as g
    ext_parts=[p for p in g.AT['parts'] if p['system']=='skeletal' and (('hip bone' in p['name'].lower()) or any(x in p['name'].lower() for x in ('ilium','pubis','ischium')) or 'sacrum' in p['name'].lower() or 'femur' in p['name'].lower())]
    ext={p['id']:(p,g.mesh_external(p)) for p in ext_parts}
    bp=g.bp3d_all()
    em,enames,bm,bnames=g.pelvis_sources(ext,bp)
    # Atlas meshes share the published local frame (metres; x-left,y-up,z-front).
    def to_ras(mesh):
        m=mesh.copy();m.vertices=(m.vertices@R0.T)*1000
        return m
    ep=points_sample(to_ras(em),N_SURFACE,SAMPLE_SEED+1)
    bppt=points_sample(to_ras(bm),N_SURFACE,SAMPLE_SEED+2)
    out={'hra':{'pelvis':ep,'pelvis_parts':enames},'bp3d_m':{'pelvis':bppt,'pelvis_parts':bnames}}
    for key,mid in [('left','BP3D_FJ3259'),('right','BP3D_FJ3365')]:
        p,m=next(((p,m) for p,m in ext.values() if p['id']==mid), (None,None))
        if m is None:raise ValueError(f'HRA femur {mid} not found')
        out['hra'][f'femur_{key}']=points_sample(to_ras(m),N_SURFACE,SAMPLE_SEED+(3 if key=='left' else 4))
        # Names in the BP3D GLB use the same source IDs.
        bmesh=bp['FJ3259' if key=='left' else 'FJ3365'][1]
        out['bp3d_m'][f'femur_{key}']=points_sample(to_ras(bmesh),N_SURFACE,SAMPLE_SEED+(5 if key=='left' else 6))
    return out

def auc_rank(pos,neg):
    if not pos or not neg:return None
    wins=sum(1.0 if a>b else .5 if a==b else 0.0 for a in pos for b in neg)
    return wins/(len(pos)*len(neg))

def metric_row(rows,group,case,metric,value,unit,status='measured',detail=''):
    rows.append({'group':group,'id':case,'metric':metric,'value':value,'unit':unit,'status':status,'detail':detail})

def make_figures(female_scores,male_scores,band,typical,aligned_clouds):
    fig,ax=plt.subplots(figsize=(10,6));bins=12
    ax.hist(female_scores,bins=bins,alpha=.65,label='Mulheres (val; M1 LOO)',color='#bb6688')
    ax.hist(male_scores,bins=bins,alpha=.60,label='Homens (controle; M1)',color='#5577aa')
    ax.axvline(band['p97_5'],color='black',linestyle='--',label='p97,5 feminino')
    ax.set(xlabel='M1 médio — distância simétrica (mm)',ylabel='Casos',title='EXP-0024 — M1 feminina e controle masculino')
    for key,name,color in [('hra','hra-f','#df852d'),('bp3d_m','bp3d-m','#278c68')]:
        if key in aligned_clouds:
            val=aligned_clouds[key]['m1_mean_mm'];ax.axvline(val,color=color,linewidth=2,label=f'{name}: {val:.2f} mm')
    ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(HERE/'distribuicao_m1.png',dpi=160);plt.close(fig)
    fig=plt.figure(figsize=(10,8));ax=fig.add_subplot(111,projection='3d')
    for key,color,label in [('typical','#aa4466',f'Feminina típica {typical}'),('hra','#e38730','hra-f'),('bp3d_m','#278866','bp3d-m')]:
        p=aligned_clouds[key]['aligned_points'];step=max(1,len(p)//5000);p=p[::step]
        ax.scatter(p[:,0],p[:,1],p[:,2],s=1,alpha=.25,c=color,label=label)
    ax.set_xlabel('RAS X (mm)');ax.set_ylabel('RAS Y (mm)');ax.set_zlabel('RAS Z (mm)');ax.set_title(f'Pelve típica da validação — {typical}');ax.legend();fig.tight_layout();fig.savefig(HERE/'pelve_tipica.png',dpi=160);plt.close(fig)

def write_manifest(cases):
    masks=[];case_summary={};total=0
    for cid in cases:
        rows=[];case_total=0
        for name in MASKS:
            p=DATA/cid/'segmentations'/f'{name}.nii.gz'
            if not p.exists():continue
            size=p.stat().st_size;case_total+=size;total+=size
            rows.append({'mask':name,'size_on_disk_bytes':size,'sha256':sha_file(p),'path':str(p.relative_to(ROOT))})
        case_summary[cid]={'mask_count':len(rows),'size_on_disk_bytes':case_total,'masks':rows}
    canonical='\n'.join(f"{cid}/{name}/{item['sha256']}" for cid,v in sorted(case_summary.items()) for name,item in sorted((x['mask'],x) for x in v['masks']))
    mask_set_sha256=hashlib.sha256(canonical.encode()).hexdigest()
    data={'status':'locally_present','downloaded_by':'reviewer Claude Code','download_date':'2026-11-27','download_source':'TotalSegmentator V3 Zenodo 22688904, masks only; no CT downloaded',
          'case_count':len(case_summary),'mask_count':sum(v['mask_count'] for v in case_summary.values()),
          'size_on_disk_total_bytes':total,'range_transfer_bytes':'not recorded by downloader; do not equate with disk size',
          'mask_set_sha256':mask_set_sha256,'cases':case_summary}
    (HERE/'download_manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return data

def main():
    rows=list(csv.DictReader((HERE/'casos.csv').open(encoding='utf-8-sig',newline='')))
    prim=[r['id'] for r in rows if r['pool']=='female_primary']
    males=[r['id'] for r in rows if r['pool']=='male_control' and r['selection']=='selected']
    ids=sorted(set(prim+males))
    previous_manifest=json.loads((HERE/'download_manifest.json').read_text(encoding='utf-8')) if (HERE/'download_manifest.json').exists() else {}
    old_qc=json.loads((HERE/'qc.json').read_text(encoding='utf-8')) if (HERE/'qc.json').exists() else {}
    old_q4=json.loads((HERE/'q4.json').read_text(encoding='utf-8')) if (HERE/'q4.json').exists() else {}
    manifest=write_manifest(ids)
    same_masks=(previous_manifest.get('mask_set_sha256')==manifest['mask_set_sha256'] or
        (previous_manifest.get('case_count')==manifest['case_count'] and all(
          previous_manifest.get('cases',{}).get(c,{}).get('masks')==manifest['cases'].get(c,{}).get('masks') for c in ids)))
    if manifest['mask_count']!=len(ids)*5:print('WARN: expected masks mismatch',manifest['mask_count'],len(ids)*5,flush=True)
    cached_qc=old_qc.get('qc') if same_masks and old_qc.get('protocol_Q0_masks')==manifest['mask_count'] else None
    qc,pelvis,femurs,_=load_patient_data(ids,cached_qc,manifest['mask_set_sha256'])
    # Recompute exact Q3 even when the pelvis surface/Q1-Q2 cache is reusable.
    for cid in ids:
        if cid in qc:
            qc[cid]['Q3']={name:femur_qc(cid,name) for name in ('femur_left','femur_right')}
    females=[x for x in prim if x in pelvis];men=[x for x in males if x in pelvis]
    if same_masks and old_qc and old_q4:
        accepted_f=old_qc['female_primary_unique'];fdec=old_qc['female_decisions'];fpairs=old_q4['female_pairs'];fsizes={}
        accepted_m=old_qc['male_control_unique'];mdec=old_qc['male_decisions'];mpairs=old_q4['male_pairs'];msizes={}
        print('Reusing QC/Q4 cache; mask hashes match.',flush=True)
    else:
        accepted_f,fdec,fpairs,fsizes=q4_filter(females,pelvis,qc)
        accepted_m,mdec,mpairs,msizes=q4_filter(men,pelvis,qc)
    ext=[r['id'] for r in rows if r['pool']=='female_extension' and r['selection']=='reserve_random_order']
    missing=max(0,30-len(accepted_f));next_ext=ext[:missing]
    (HERE/'extension_needed.json').write_text(json.dumps({'female_unique_after_primary_qc_q4':len(accepted_f),'protocol_minimum':30,'additional_cases_needed':missing,'extension_masks_not_downloaded':True,'next_extension_ids_in_seed_order':next_ext,'q4_prefilter':f'run ICP only when centroid size relative difference < {Q4_SIZE_PREFILTER:.0%}; unchanged Q4 cutoff < {Q4_THRESHOLD_MM} mm'},ensure_ascii=False,indent=2),encoding='utf-8')
    # Update the case ledger, preserving seed-selected controls and explicit non-assessment for extension.
    for r in rows:
        cid=r['id']
        if r['pool']=='female_primary':
            if cid not in qc:r['included']='not_assessed';r['reason']='pelvic mask extraction unavailable';r['split']='not_assigned';continue
            r['included']=fdec.get(cid,('excluded','not retained'))[0];r['reason']=fdec.get(cid,('excluded','not retained'))[1]
            r['q1']=qc[cid]['Q1'];r['q2']=qc[cid]['Q2'];r['q3']=json.dumps(qc[cid]['Q3'],ensure_ascii=False,separators=(',',':'))
        elif r['pool']=='male_control' and r['selection']=='selected':
            r['included']=mdec.get(cid,('excluded','QC unavailable'))[0];r['reason']=mdec.get(cid,('excluded','QC unavailable'))[1]
            r['q1']=qc[cid]['Q1'];r['q2']=qc[cid]['Q2'];r['q3']=json.dumps(qc[cid]['Q3'],ensure_ascii=False,separators=(',',':'))
    # Freeze a deterministic 10-case development split before any validation metric is calculated.
    split_rng=random.Random(SEED)
    if len(accepted_f)>=10:
        dev=sorted(split_rng.sample(accepted_f,10));val=sorted(x for x in accepted_f if x not in set(dev))
    else:dev=[];val=[]
    template_id=dev[0] if dev else None
    frozen={'seed':SEED,'rng':'random.Random','development_ids':dev,'validation_ids':val,'template_case_id':template_id,
      'parameters':{'surface_samples':N_SURFACE,'Q4_fit_samples':N_Q4_FIT,'Q4_distance_samples':N_Q4_DIST,'Q4_size_prefilter_relative':Q4_SIZE_PREFILTER,'Q4_mean_distance_mm':Q4_THRESHOLD_MM,'trim':TRIM,'icp_max_iterations':MAX_ITER,'convergence_delta':TOL,'workers':1,'Q4_rigid_only':True,'M1_uniform_similarity':True,'M3_template_rigid':True},
      'analysis_script_sha256':sha_file(Path(__file__)),'frozen_before_validation_metrics':True,
      'template_rule':'first ID-sorted development case; validation metrics use this fixed target'}
    (HERE/'parametros_congelados.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2),encoding='utf-8')
    for r in rows:
        if r['id'] in dev:r['split']='dev'
        elif r['id'] in val:r['split']='val'
        elif r['pool']=='female_primary':r['split']='not_applicable'
        elif r['pool']=='female_extension' and r['selection']=='reserve_random_order':r['included']='not_downloaded';r['reason']='Only needed if fewer than 30 unique QC-passing primary women';r['split']='not_assigned'
    fields=list(dict.fromkeys([k for r in rows for k in r.keys()]))
    with (HERE/'casos.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    q4={'female_pairs':fpairs,'male_pairs':mpairs,'prefilter_relative_size':Q4_SIZE_PREFILTER,'criterion_distance_mm':Q4_THRESHOLD_MM,
        'female_pair_count':len(fpairs),'female_icp_runs':sum(p['icp_run'] for p in fpairs),'male_pair_count':len(mpairs),'male_icp_runs':sum(p['icp_run'] for p in mpairs)}
    (HERE/'q4.json').write_text(json.dumps(q4,ensure_ascii=False,indent=2),encoding='utf-8')
    qc_out={'qc':qc,'female_primary_unique':accepted_f,'male_control_unique':accepted_m,'female_decisions':fdec,'male_decisions':mdec,
            'counts':{'female_primary':len(prim),'female_QC_Q1Q2':sum(qc[x]['pelvis_pass'] for x in prim),'female_unique_after_Q4':len(accepted_f),'male_selected':len(males),'male_QC_Q1Q2':sum(qc[x]['pelvis_pass'] for x in males),'female_extension_needed':missing},
            'protocol_Q0_masks':manifest['mask_count'],'size_on_disk_bytes':manifest['size_on_disk_total_bytes']}
    (HERE/'qc.json').write_text(json.dumps(qc_out,ensure_ascii=False,indent=2),encoding='utf-8')
    if len(accepted_f)<30 or len(val)<20 or len(accepted_m)<20:
        print(json.dumps({'qc_counts':qc_out['counts'],'extension_needed':next_ext,'status':'sample threshold not met; measurements continue where possible'},ensure_ascii=False),flush=True)
    # Once the 10-case dev split and template rule are frozen, perform full metrics only when a valid split exists.
    if not dev or not val:
        write_blocked_metrics(qc_out,frozen,q4,manifest);return
    do_full_metrics(rows,accepted_f,accepted_m,dev,val,pelvis,femurs,frozen,qc_out,q4,manifest)

def write_blocked_metrics(qc,frozen,q4,manifest):
    (HERE/'metricas.csv').write_text('group,id,metric,value,unit,status,detail\n',encoding='utf-8-sig')
    result={'status':'insufficient_female_validation_sample','qc':qc['counts'],'development':frozen,'q4':q4,
            'criteria':{'V0':'fail' if qc['counts']['female_unique_after_Q4']<30 or qc['counts']['male_QC_Q1Q2']<20 else 'pass','V1':'not_measured','V2':'not_evaluable','V3':'not_evaluable'},
            'extension_needed':json.loads((HERE/'extension_needed.json').read_text(encoding='utf-8')),
            'download':{'size_on_disk_bytes':manifest['size_on_disk_total_bytes'],'range_transfer_bytes':'not recorded'}}
    (HERE/'resultados.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

def do_full_metrics(rows,accepted_f,accepted_m,dev,val,pelvis,femurs,frozen,qc_out,q4,manifest):
    atlas=atlas_sources()
    template=pelvis[frozen['template_case_id']]
    metrics=[];pair={};female_scores={x:[] for x in val};female_p95={x:[] for x in val}
    cache_path=HERE/'m1_pairs.jsonl'
    signature=hashlib.sha256(json.dumps({'samples':N_SURFACE,'max_iter':MAX_ITER,'trim':TRIM,'tol':TOL,'method':'similarity'},sort_keys=True).encode()).hexdigest()
    cache={}
    if cache_path.exists():
        for line in cache_path.read_text(encoding='utf-8').splitlines():
            try:
                item=json.loads(line)
                if item.get('signature')==signature:cache[item['key']]=item['stats']
            except Exception:pass
    def cached_m1(key,fn):
        if key in cache:return cache[key]
        stats,_=fn();cache[key]=stats
        with cache_path.open('a',encoding='utf-8') as f:f.write(json.dumps({'signature':signature,'key':key,'stats':stats},separators=(',',':'))+'\n')
        return stats
    # Female validation leave-one-out pairwise symmetric ICP.
    done=0
    for i,a in enumerate(val):
        for b in val[i+1:]:
            key=f'female::{a}::{b}';st=cached_m1(key,lambda a=a,b=b:symmetric_after_similarity(pelvis[a],pelvis[b]))
            pair[(a,b)]=st;pair[(b,a)]=st;done+=1
            if done%10==0:print(f'M1 pairs cached/computed: {done}',flush=True)
            metric_row(metrics,'female_pair',f'{a}|{b}','M1_symmetric_mean',st['mean_mm'],'mm',detail=f'p95={st["p95_mm"]}; convergence={st["converged"]}; iterations={st["iterations"]}')
            metric_row(metrics,'female_pair',f'{a}|{b}','M1_symmetric_p95',st['p95_mm'],'mm')
    for a in val:
        female_scores[a]=float(np.mean([pair[(a,b)]['mean_mm'] for b in val if b!=a]))
        female_p95[a]=float(np.mean([pair[(a,b)]['p95_mm'] for b in val if b!=a]))
    for a,v in female_scores.items():
        metric_row(metrics,'female_val',a,'M1_LOO_mean',v,'mm')
        metric_row(metrics,'female_val',a,'M1_LOO_p95',female_p95[a],'mm')
    # Frozen template registration; M2 and M3 are measured in the fixed dev frame.
    frame={}
    for cid in sorted(set(val+dev+accepted_m)):
        st,aligned=symmetric_after_rigid(pelvis[cid],template)
        frame[cid]={'transform':st,'pelvis_points':aligned}
    def m3(case,sidepoints,transform,include_head=True):
        p=frame[case]['pelvis_points'];width=float(np.ptp(p[:,0]));depth=float(np.ptp(p[:,1]));height=float(np.ptp(p[:,2]))
        result={'width_height':width/height,'width_depth':width/depth,'width_mm':width,'height_mm':height,'depth_mm':depth}
        if include_head:
            centers=[];sphere={};R=np.array(transform['rotation']);t=np.array(transform['translation_mm'])
            for side in ('left','right'):
                c,meta=proximal_head_center(sidepoints[(case,side)],side);centers.append(c@R.T+t);sphere[side]=meta
            head=float(np.linalg.norm(centers[0]-centers[1]));result.update({'femoral_head_distance_width':head/width,'head_centers_distance_mm':head,'sphere_fits':sphere})
        return result
    m3_case={}
    q3_valid=[]
    for cid in val:
        pelvis_only=not all(qc_out['qc'][cid]['Q3'][f'femur_{s}']['pass'] for s in ('left','right'))
        m3_case[cid]=m3(cid,femurs,frame[cid]['transform'],include_head=not pelvis_only)
        if not pelvis_only:q3_valid.append(cid)
        metric_row(metrics,'female_val',cid,'M2_centroid_size',centroid_size(pelvis[cid]),'mm')
        for k,v in m3_case[cid].items():
            if k in ('width_height','width_depth','femoral_head_distance_width'):metric_row(metrics,'female_val',cid,'M3_'+k,v,'ratio')
    def compare_atlas(key):
        atlas_points=atlas[key]['pelvis'];vals=[];p95s=[]
        for cid in val:
            st=cached_m1(f'atlas::{key}::{cid}',lambda cid=cid:symmetric_after_similarity(atlas_points,pelvis[cid]));vals.append(st['mean_mm']);p95s.append(st['p95_mm'])
            metric_row(metrics,key,cid,'M1_to_validation_case_mean',st['mean_mm'],'mm',detail=f'converged={st["converged"]};iterations={st["iterations"]};scale={st["uniform_scale"]}')
            metric_row(metrics,key,cid,'M1_to_validation_case_p95',st['p95_mm'],'mm')
            if len(vals)%5==0:print(f'M1 {key} atlas comparisons: {len(vals)}/{len(val)}',flush=True)
        score=float(np.mean(vals));score95=float(np.mean(p95s));st,ap=symmetric_after_rigid(atlas_points,template)
        # Atlas femur center fits are generated in the same RAS frame and aligned by pelvis fit.
        af={}
        for side in ('left','right'):
            af[side]=atlas[key][f'femur_{side}']
        # Fit atlas pelvis to dev template, then transform each sampled femur using same rigid transform.
        transformed={}
        # Put points under an artificial id expected by m3 helper.
        pseudo='__'+key
        frame[pseudo]={'pelvis_points':ap,'transform':st}
        for side in ('left','right'):transformed[(pseudo,side)]=af[side]
        a3=m3(pseudo,transformed,st)
        metric_row(metrics,key,key,'M2_centroid_size',centroid_size(atlas_points),'mm')
        return {'M1_mean_mm':score,'M1_p95_mean_mm':score95,'M1_pairwise_to_validation_mm':vals,'M1_pairwise_p95_mm':p95s,'M3':{k:v for k,v in a3.items() if k in ('width_height','width_depth','femoral_head_distance_width')},'M2_centroid_size_mm':centroid_size(atlas_points),'aligned_points':ap,'converged':st['converged'],'iterations':st['iterations']}
    comp={k:compare_atlas(k) for k in ('hra','bp3d_m')}
    # Controls: one score per QC-passing male, averaged over all female validation targets.
    male_scores={}
    male_p95={}
    for man in accepted_m:
        vals=[];p95s=[]
        for woman in val:
            st=cached_m1(f'male::{man}::{woman}',lambda man=man,woman=woman:symmetric_after_similarity(pelvis[man],pelvis[woman]));vals.append(st['mean_mm']);p95s.append(st['p95_mm'])
            metric_row(metrics,'male_control',man,'M1_to_validation_case_mean',st['mean_mm'],'mm',detail=f'target={woman}; converged={st["converged"]};scale={st["uniform_scale"]}')
            metric_row(metrics,'male_control',man,'M1_to_validation_case_p95',st['p95_mm'],'mm')
            if len(vals)%10==0:print(f'M1 male comparisons: {man}, {len(vals)}/{len(val)}',flush=True)
        male_scores[man]=float(np.mean(vals));male_p95[man]=float(np.mean(p95s))
        metric_row(metrics,'male_control',man,'M2_centroid_size',centroid_size(pelvis[man]),'mm')
        if all(qc_out['qc'][man]['Q3'][f'femur_{s}']['pass'] for s in ('left','right')):
            male_m3=m3(man,femurs,frame[man]['transform'])
            for k in ('width_height','width_depth','femoral_head_distance_width'):metric_row(metrics,'male_control',man,'M3_'+k,male_m3[k],'ratio')
    for man,v in male_scores.items():
        metric_row(metrics,'male_control',man,'M1_mean',v,'mm');metric_row(metrics,'male_control',man,'M1_p95_mean',male_p95[man],'mm')
    bands={'M1_mean_mm':{'p2_5':float(np.percentile(list(female_scores.values()),2.5)),'p97_5':float(np.percentile(list(female_scores.values()),97.5))},
           'M1_p95_mm':{'p2_5':float(np.percentile(list(female_p95.values()),2.5)),'p97_5':float(np.percentile(list(female_p95.values()),97.5))},
           'M2_centroid_size_mm':{'p2_5':float(np.percentile([centroid_size(pelvis[x]) for x in val],2.5)),'p97_5':float(np.percentile([centroid_size(pelvis[x]) for x in val],97.5))},'M3':{}}
    for k in ('width_height','width_depth'):
        vs=[m3_case[x][k] for x in val];bands['M3'][k]={'p2_5':float(np.percentile(vs,2.5)),'p97_5':float(np.percentile(vs,97.5)),'n':len(vs)}
    vs=[m3_case[x]['femoral_head_distance_width'] for x in q3_valid]
    bands['M3']['femoral_head_distance_width']={'p2_5':float(np.percentile(vs,2.5)),'p97_5':float(np.percentile(vs,97.5)),'n':len(vs)}
    auc=auc_rank(list(male_scores.values()),list(female_scores.values()))
    hra_m1=comp['hra']['M1_mean_mm'];bp_m1=comp['bp3d_m']['M1_mean_mm'];lim=bands['M1_mean_mm']['p97_5']
    v0=len(accepted_f)>=30 and len(val)>=20 and len(accepted_m)>=20
    v1=auc is not None and auc>=.80
    hra3=comp['hra']['M3'];v2=hra_m1<=lim and all(bands['M3'][k]['p2_5']<=hra3[k]<=bands['M3'][k]['p97_5'] for k in hra3)
    v3=bp_m1>lim
    if not v0 or not v1:verdict='inconclusive'
    elif v2 and v3:verdict='H24 sustained'
    elif v2 and not v3:verdict='H24 partial'
    else:verdict='H24 rejected'
    # The typical female validation pelvis is the medoid by M1 score.
    typical=min(val,key=lambda x:female_scores[x]);aligned_clouds={'typical':{'aligned_points':frame[typical]['pelvis_points']}}
    for k in ('hra','bp3d_m'):aligned_clouds[k]={'aligned_points':comp[k]['aligned_points'],'m1_mean_mm':comp[k]['M1_mean_mm']}
    female_vals=[female_scores[x] for x in val];male_vals=list(male_scores.values())
    make_figures(female_vals,male_vals,bands['M1_mean_mm'],typical,aligned_clouds)
    with (HERE/'metricas.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['group','id','metric','value','unit','status','detail']);w.writeheader();w.writerows(metrics)
    (HERE/'faixas_femininas.json').write_text(json.dumps({'n_female_validation':len(val),'n_female_validation_both_femurs_Q3_pass':len(q3_valid),'M1_LOO_mean':bands['M1_mean_mm'],'M1_LOO_p95':bands['M1_p95_mm'],'M2':bands['M2_centroid_size_mm'],'M3':bands['M3'],'seed':SEED},ensure_ascii=False,indent=2),encoding='utf-8')
    (HERE/'auc.json').write_text(json.dumps({'value':auc,'positive_class':'male','score':'M1 mean distance to women validation','female_scores':female_scores,'male_scores':male_scores,'criterion_minimum':.80,'n_female_validation':len(val),'n_male_QC':len(accepted_m)},ensure_ascii=False,indent=2),encoding='utf-8')
    result={'hypothesis_verdict':verdict,'criteria':{'V0':{'pass':v0,'n_female':len(accepted_f),'n_validation':len(val),'n_male':len(accepted_m)},'V1':{'pass':v1,'auc':auc,'minimum':.80},
        'V2':{'pass':v2,'hra_f_M1_mean_mm':hra_m1,'female_M1_p97_5_mm':lim,'hra_f_M3':hra3},'V3':{'pass':v3,'bp3d_m_M1_mean_mm':bp_m1,'female_M1_p97_5_mm':lim}},
      'qc_counts':qc_out['counts'],'development':frozen,'q4':q4,'bands':bands,'comparators':{k:{kk:vv for kk,vv in v.items() if kk not in ('aligned_points',)} for k,v in comp.items()},
      'female_scores':female_scores,'female_p95_scores':female_p95,'male_scores':male_scores,'male_p95_scores':male_p95,'n_female_M3_head_valid':len(q3_valid),'typical_validation_case':typical,'download':{'size_on_disk_bytes':manifest['size_on_disk_total_bytes'],'range_transfer_bytes':'not recorded'},
      'method':{'surface_samples':N_SURFACE,'M1_ICP':'uniform-scale similarity ICP, 12% trimmed correspondences, <=200 iterations, delta 1e-7; workers=1','M3_ICP':'rigid Kabsch ICP, 12% trimmed correspondences, <=200 iterations, delta 1e-7; workers=1','Q4_size_prefilter':Q4_SIZE_PREFILTER,'femur_head_fit':'algebraic sphere fit on sampled proximal cap; details in each M3 row'}}
    (HERE/'resultados.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    for r in rows:
        if r['id'] in dev:r['split']='dev'
        elif r['id'] in val:r['split']='val'
    fields=list(dict.fromkeys(k for r in rows for k in r.keys()))
    with (HERE/'casos.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

if __name__=='__main__':main()
