"""Write the source map and front/top comparison figures for EXP-0022."""
from pathlib import Path
import sys,site,json,csv,hashlib
sys.path.append(site.getusersitepackages())
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import medir as g

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def provenance():
    hra_catalog={r['no']:r for r in csv.DictReader((g.ROOT/'hra/catalogo_hra.csv').open(encoding='utf-8-sig'))}
    source_map=[]
    for p in g.AT['parts']:
        id=p['id']
        if id.startswith('BP3D_'):
            group='BodyParts3D'
            tx='OBJ/mm→m (x,z,-y), then scale X .95/Y .96335/Z .95 + Z −.052 m; piecewise female morphology; meshoptimizer simplification.'
            license='CC BY 4.0 declared in README/ATTRIBUTION'
            verification='source group traced by BP3D_ ID; per-mesh source CSV not embedded in clone output'
        elif id.startswith(('VH_F_','Allen_','Yao_')):
            group='Human Reference Atlas (united-female v1.5)'
            tx='HRA Y-up meter geometry; +0.794760942 m on Y; existing female skeletal knee/femur/tibia fragments and rectus femoris excluded by final builder.'
            license='CC BY 4.0 declared for HRA dataset'
            record=hra_catalog.get(id)
            verification=(f"catalog row: sistema_hra={record['sistema_hra']}; orgao={record['orgao']}" if record else
                          'HRA input GLB source group and transform identified in convert-female.py/build-perfect-female-atlas.mjs; no row in hra/catalogo_hra.csv')
        else:
            group='unmapped';tx='not verified';license='not verified';verification='not verified'
        source_map.append({'id':id,'name':p['name'],'system':p['system'],'conceptId':p.get('conceptId',''),
                           'source_group':group,'transformation':tx,'declared_license':license,'verification':verification})
    with (HERE/'proveniencia.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(source_map[0]));w.writeheader();w.writerows(source_map)
    return source_map

def figures():
    target,_=g.target_mesh(['hip_left','hip_right','sacrum'])
    ext=trimesh.load(str(HERE/'female_atlas_pelvis_aligned.ply'),force='mesh',process=False)
    bp=trimesh.load(str(HERE/'bp3d_m_pelvis_aligned.ply'),force='mesh',process=False)
    rng=np.random.default_rng(220022)
    pts={'Female Atlas':g.sample_surface(ext,35000,rng),'bp3d-m':g.sample_surface(bp,35000,rng),'NLM TotalSegmentator':g.sample_surface(target,35000,rng)}
    colors={'Female Atlas':'#007c91','bp3d-m':'#ee8b22','NLM TotalSegmentator':'#343a40'}
    for view,xy,labels,title in [('frente',(0,2),('RAS X (mm)','RAS Z (mm)'),'Pelve — vista frontal'),
                                 ('de_cima',(0,1),('RAS X (mm)','RAS Y (mm)'),'Pelve — vista superior')]:
        fig,ax=plt.subplots(figsize=(10,8),layout='constrained')
        for name,p in pts.items():
            ax.scatter(p[:,xy[0]],p[:,xy[1]],s=.55,alpha=.34,c=colors[name],label=name,rasterized=True,linewidths=0)
        ax.set_title(title+' · alinhamento à máscara NLM (ROI pélvica)')
        ax.set_xlabel(labels[0]);ax.set_ylabel(labels[1]);ax.set_aspect('equal',adjustable='box');ax.grid(alpha=.2);ax.legend(markerscale=8,loc='best')
        ax.set_xlim(-190,190)
        if view=='frente':ax.set_ylim(-1000,-700)
        else:ax.set_ylim(-150,110)
        fig.savefig(HERE/f'pelve_{view}.png',dpi=180);plt.close(fig)

if __name__=='__main__':
    rows=provenance();figures()
    hashes={p:sha(g.ROOT/p) for p in ['hra/externo/female-atlas/public/models/atlas.json','hra/nlm/bruto/saida/segmentacao.nii.gz']}
    hashes['pesquisa/resultados/EXP-0022/bp3d-esqueletico.glb']=sha(HERE/'bp3d-esqueletico.glb')
    # Body frame and label centroids establish the measured anatomical orientation.
    bp=g.bp3d_all();frames={}
    for id in ('FJ3152','FJ3288','FJ3393','FJ3259','FJ3365'):
        if id in bp:
            r,m=bp[id];frames[id]={'name':r.get('nome_en'),'bounds_m':m.bounds.tolist(),'centroid_m':m.centroid.tolist()}
    label_frames={}
    for name in ('hip_left','hip_right','sacrum','femur_left','femur_right','vertebrae_L1','vertebrae_L5'):
        lab_id=next(int(k) for k,v in g.LABELS.items() if v==name)
        ijk=np.argwhere(g.VOL==lab_id)
        w=trimesh.transform_points(ijk,g.AFF)
        label_frames[name]={'voxel_count':len(ijk),'bounds_RAS_mm':np.vstack((w.min(0),w.max(0))).tolist(),'centroid_RAS_mm':w.mean(0).tolist()}
    (HERE/'referencial.json').write_text(json.dumps({'HRA_local_frame':'x positive=left; y positive=up; z positive=front; metres, per project record and HRA source conversion.',
        'bp3d_m_local_frame':'x positive=left, y positive=up, z positive=front; metres, confirmed by BodyParts3D exporter and decoded node lateralities.',
        'TC_world_frame':'NIfTI affine coordinates labelled RAS mm by EXP-0010; x increases right, y increases anterior, z increases superior. Affine is diagonal +1.5 mm voxel spacing; negative world Z origin is a translation, not an axis reversal.',
        'HRA_to_RAS_axis_map':{'x_RAS_mm':'-1000*x_local_m','y_RAS_mm':'1000*z_local_m','z_RAS_mm':'1000*y_local_m'},
        'BP3D_representative_geometry':frames,'NLM_label_boxes':label_frames,
        'note':'30-voxel disconnected hip_left component at z≈−1261 mm is included in metric mask; the figure zooms the connected pelvic ROI and clips this tiny outlier.'},ensure_ascii=False,indent=2),encoding='utf8')
    catalog_ids={r['no'] for r in csv.DictReader((g.ROOT/'hra/catalogo_hra.csv').open(encoding='utf-8-sig'))}
    print(json.dumps({'provenance_rows':len(rows),'prefix_counts':{k:sum(r['source_group'].startswith(k) for r in rows) for k in ['BodyParts3D','Human Reference Atlas']},'hra_catalog_matches':sum(r['id'] in catalog_ids for r in rows if r['source_group'].startswith('Human Reference Atlas')),'sha256':hashes}))
