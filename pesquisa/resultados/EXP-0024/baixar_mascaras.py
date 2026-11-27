"""Fetch only protocol masks through ZIP HTTP Range; one remote ZIP handle/process."""
from pathlib import Path
import csv, io, json, sys, urllib.request, zipfile, hashlib
import site
sys.path.append(site.getusersitepackages())
import numpy as np
import nibabel as nib
import trimesh
from scipy.spatial import cKDTree

ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
EXT=ROOT/'hra/externo/totalseg_v3'
URL='https://zenodo.org/api/records/22688904/files/Totalsegmentator_dataset_v300.zip/content'
MASKS=('hip_left','hip_right','sacrum','femur_left','femur_right')
SEED=240024; MAX_ITER=200; DUP_THRESH_MM=1.0

class RemoteFile(io.RawIOBase):
    def __init__(self,url):
        self.url=url;self.pos=0;self.baixado=0;self.limit=2**63-1
        req=urllib.request.Request(url,method='HEAD')
        with urllib.request.urlopen(req,timeout=60) as r:self.size=int(r.headers['Content-Length'])
    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.pos
    def seek(self,off,whence=0):
        self.pos={0:off,1:self.pos+off,2:self.size+off}[whence];return self.pos
    def readinto(self,b):
        n=min(len(b),self.size-self.pos)
        if n<=0:return 0
        if self.baixado+n>self.limit:raise RuntimeError(f'Range transfer cap reached ({self.limit} bytes)')
        req=urllib.request.Request(self.url,headers={'Range':f'bytes={self.pos}-{self.pos+n-1}'})
        with urllib.request.urlopen(req,timeout=180) as r:
            if r.status!=206:raise RuntimeError(f'Zenodo did not honor HTTP Range (HTTP {r.status})')
            data=r.read()
        if len(data)!=n:raise RuntimeError(f'short Range response: expected {n}, got {len(data)}')
        b[:n]=data;self.pos+=n;self.baixado+=n;return n

def save_member(z,info,cid,name):
    out=EXT/cid/'segmentations'/f'{name}.nii.gz';out.parent.mkdir(parents=True,exist_ok=True)
    data=z.read(info);out.write_bytes(data)
    return {'id':cid,'mask':name,'archive_path':info.filename,'compressed_bytes':info.compress_size,
            'extracted_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'path':str(out.relative_to(ROOT))}

def readmask(cid,name):
    p=EXT/cid/'segmentations'/f'{name}.nii.gz'
    img=nib.load(str(p));a=np.asanyarray(img.dataobj)>0
    return img,a

def mask_surface(cid,names):
    meshes=[]
    for name in names:
        img,a=readmask(cid,name)
        if not a.any():continue
        lo=np.argwhere(a).min(0);hi=np.argwhere(a).max(0)+1
        crop=a[tuple(slice(int(x),int(y)) for x,y in zip(lo,hi))]
        m=trimesh.voxel.ops.matrix_to_marching_cubes(crop,pitch=1.0)
        m.vertices=trimesh.transform_points(m.vertices+lo,img.affine)
        meshes.append(m)
    if not meshes:return None
    return trimesh.util.concatenate(meshes)

def basic_qc(cid):
    out={'Q1':True,'Q2':True,'Q3':{},'reason':[]}
    imgs={};arrays={}
    for name in ('hip_left','hip_right','sacrum'):
        img,a=readmask(cid,name);imgs[name]=img;arrays[name]=a
        if not a.any():out['Q1']=False;out['reason'].append(f'Q1 empty/missing {name}')
        elif np.any(a[:,:,0]) or np.any(a[:,:,-1]):out['Q2']=False;out['reason'].append(f'Q2 pelvic mask {name} touches first/last volume slice')
    if not out['Q1'] or not out['Q2']:return out
    for name in ('femur_left','femur_right'):
        img,a=readmask(cid,name)
        if not a.any():out['Q3'][name]={'pass':False,'reason':'empty/missing'};continue
        idx=np.argwhere(a);world=trimesh.transform_points(idx,img.affine)
        centered=world-world.mean(0);_,_,vt=np.linalg.svd(centered,full_matrices=False)
        axis=vt[0];proj=centered@axis;length=float(proj.max()-proj.min())
        zaxis=int(np.argmax(np.abs(img.affine[2,:3])));superior_at_high=img.affine[2,zaxis]>0
        upper_touch=bool(np.any(idx[:,zaxis]==(a.shape[zaxis]-1 if superior_at_high else 0)))
        passed=length>=100 and not upper_touch
        out['Q3'][name]={'pass':passed,'principal_extent_mm':length,'touches_superior_volume_edge':upper_touch,
                         'reason':None if passed else ('extent below 100 mm' if length<100 else 'touches superior volume edge')}
    return out

def sample(m,n,rng):return trimesh.sample.sample_surface(m,n,seed=int(rng.integers(0,2**31-1)))[0]

def rigid_mean_distance(a,b):
    rng=np.random.default_rng(SEED)
    ap=sample(a,5000,rng);bp=sample(b,5000,rng);tree=cKDTree(bp);R=np.eye(3);t=bp.mean(0)-ap.mean(0)
    for _ in range(MAX_ITER):
        moved=ap@R.T+t;d,ix=tree.query(moved,k=1,workers=1)
        # Rigid Kabsch fit, no scale; same fixed 12% trim used by atlas ICP.
        keep=max(3,int(len(ap)*.88));sel=np.argpartition(d,keep-1)[:keep];X=ap[sel];Y=bp[ix[sel]]
        xm=X.mean(0);ym=Y.mean(0);u,_,vt=np.linalg.svd((X-xm).T@(Y-ym));rr=vt.T@u.T
        if np.linalg.det(rr)<0:vt[-1]*=-1;rr=vt.T@u.T
        tt=ym-xm@rr.T;delta=np.linalg.norm(rr-R)+np.linalg.norm(tt-t)/1000;R,t=rr,tt
        if delta<1e-7:break
    aa=a.copy();aa.vertices=aa.vertices@R.T+t
    x=sample(aa,10000,rng);y=sample(b,10000,rng)
    return float((cKDTree(y).query(x,workers=1)[0].mean()+cKDTree(x).query(y,workers=1)[0].mean())/2)

def main():
    rows=list(csv.DictReader((HERE/'casos.csv').open(encoding='utf-8-sig',newline='')))
    primary=[r['id'] for r in rows if r['pool']=='female_primary']
    ext_order=[r['id'] for r in rows if r['pool']=='female_extension' and r['selection']=='reserve_random_order']
    males=[r['id'] for r in rows if r['pool']=='male_control' and r['selection']=='selected']
    initial=sorted(set(primary+males));all_candidate=sorted(set(initial+ext_order))
    try:
        rf=RemoteFile(URL);z=zipfile.ZipFile(io.BufferedReader(rf,buffer_size=1<<16))
    except Exception as exc:
        blocked={'status':'blocked_before_transfer','zip_url':URL,'range_bytes_transferred':0,'extracted_total_bytes':0,
                 'reason':f'{type(exc).__name__}: external connection could not be established; no Range bytes transferred',
                 'exception':str(exc),'selected_primary_female':len(primary),'selected_male':len(males),
                 'extension_masks_requested':0,'workaround':'none available locally; no mask archive or CT was present'}
        (HERE/'download_manifest.json').write_text(json.dumps(blocked,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(blocked,ensure_ascii=False));return
    byname={i.filename:i for i in z.infolist()}
    def members(cid):
        pre=f'Totalsegmentator_dataset_v300/{cid}/segmentations/'
        return {n:byname.get(pre+n+'.nii.gz') for n in MASKS}
    # Budget is computed from selected mask members only, plus bounded Range/header overread.
    infos=[]
    for cid in all_candidate:
        for n,info in members(cid).items():
            if info is not None:infos.append(info)
    rf.limit=rf.baixado+sum(i.compress_size for i in infos)+len(infos)*(1<<16)+16*(1<<20)
    manifest=[];downloaded=set();qc={}
    def fetch(cid):
        if cid in downloaded:return
        missing=[]
        for n,info in members(cid).items():
            if info is None:missing.append(n)
            else:manifest.append(save_member(z,info,cid,n))
        downloaded.add(cid);qc[cid]=basic_qc(cid)
        if missing:qc[cid]['reason'].append('archive missing: '+','.join(missing))
    for cid in initial:fetch(cid)
    # Apply Q1/Q2 and deduplicate pelvises in ID order; fetch randomized extension only until 30 unique pass.
    def unique_females(ids):
        accepted=[];decisions={};meshes=[]
        for cid in sorted(ids):
            q=qc[cid]
            if not q['Q1'] or not q['Q2']:
                decisions[cid]=('excluded','; '.join(q['reason']));continue
            mesh=mask_surface(cid,['hip_left','hip_right','sacrum'])
            duplicate_of=None
            for prev,pm in zip(accepted,meshes):
                d=rigid_mean_distance(mesh,pm)
                if d<DUP_THRESH_MM:duplicate_of=prev;decisions[cid]=('excluded',f'Q4 duplicate of {prev}; symmetric rigid mean {d:.6f} mm');break
            if duplicate_of is None:accepted.append(cid);meshes.append(mesh);decisions[cid]=('included','Q1-Q2 passed; Q4 unique')
        return accepted,decisions
    females=primary[:];accepted,decisions=unique_females(females)
    ext_used=[]
    for cid in ext_order:
        if len(accepted)>=30:break
        fetch(cid);ext_used.append(cid);females.append(cid);accepted,decisions=unique_females(females)
    # Male control cases remain the fixed random sample; report pelvic quality independently.
    for cid in males:
        if cid not in qc:fetch(cid)
    for cid in females:
        q=qc[cid];inc,reason=decisions.get(cid,('excluded','not retained after Q4'))
        for r in rows:
            if r['id']==cid:
                r['included']=inc;r['reason']=reason
                r['split']='pending_dev_val' if inc=='included' else 'not_applicable'
                r['femur_qc']=json.dumps(q.get('Q3',{}),ensure_ascii=False,separators=(',',':'));break
    for cid in males:
        q=qc[cid]
        for r in rows:
            if r['id']==cid:
                r['included']='included' if q['Q1'] and q['Q2'] else 'excluded'
                r['reason']='male control Q1-Q2 passed' if q['Q1'] and q['Q2'] else '; '.join(q['reason'])
                r['split']='control' if r['included']=='included' else 'not_applicable'
                r['femur_qc']=json.dumps(q.get('Q3',{}),ensure_ascii=False,separators=(',',':'));break
    fields=list(rows[0].keys())+['femur_qc'] if rows else []
    with (HERE/'casos.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    info={'zip_url':URL,'zip_size_bytes':rf.size,'transfer_cap_bytes':rf.limit,'range_bytes_transferred':rf.baixado,
          'members_requested':len(manifest),'extracted_total_bytes':sum(x['extracted_bytes'] for x in manifest),'masks':manifest,
          'selected_primary_female':len(primary),'selected_male':len(males),'extension_downloaded_in_random_order':ext_used,
          'female_Q1_Q2_Q4_unique':accepted,'female_unique_count':len(accepted),'male_Q1_Q2_count':sum(qc[x]['Q1'] and qc[x]['Q2'] for x in males),
          'qc':qc,'q4':{'definition':'symmetric mean surface distance after rigid ICP, no scale, 12% trim, tolerance 1e-7, max 200; <1.0mm deduplicated retaining lexicographically first ID','samples_fit':5000,'samples_distance_each_direction':10000,'threshold_mm':DUP_THRESH_MM}}
    (HERE/'download_manifest.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in info.items() if k not in ('masks','qc')},ensure_ascii=False))
if __name__=='__main__':main()
