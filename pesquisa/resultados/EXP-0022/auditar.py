"""Own-code audit of the untrusted Female Atlas data. Invoke with python -I."""
from __future__ import annotations
import sys, site, json, struct, hashlib, gzip, re, math
from pathlib import Path
from collections import Counter, defaultdict

# The approved Python packages are installed in the current user's site directory.
# Isolated mode is retained; only this explicit trusted package directory is added.
sys.path.append(site.getusersitepackages())
import numpy as np
import nibabel as nib
import trimesh

ROOT = Path(__file__).resolve().parents[3]
EXT = ROOT / 'hra/externo/female-atlas'
OUT = Path(__file__).resolve().parent
ATLAS = json.loads((EXT/'public/models/atlas.json').read_text(encoding='utf8'))

def extract_part(part):
    raw=(EXT/'public/models'/f"female-{part['chunk']}.bin").read_bytes()
    n=part['vertexCount']; ni=part['indexCount']
    v=np.frombuffer(raw,dtype='<f4',count=n*3,offset=part['positions']).reshape(-1,3).copy()
    f=np.frombuffer(raw,dtype='<u4',count=ni,offset=part['indices']).reshape(-1,3).copy()
    return trimesh.Trimesh(vertices=v,faces=f,process=False)

def manifest_summary():
    parts=ATLAS['parts']; concepts=ATLAS['concepts']
    source=Counter('HRA_VH_F' if p['id'].startswith('VH_F_') else 'BodyParts3D' if p['id'].startswith('BP3D_') else 'Allen_prefixed' if p['id'].startswith('Allen_') else 'Yao_prefixed' if p['id'].startswith('Yao_') else 'unmapped' for p in parts)
    systems=Counter(p['system'] for p in parts)
    tri=sum(p['indexCount']//3 for p in parts)
    names=Counter(p['name'] for p in parts)
    result={'declared':{'meshes':3004,'concepts':2557,'systems':16},
            'observed':{'meshes':len(parts),'concepts':len(concepts),'systems':len(set(p['system'] for p in parts)),'triangles':tri,
                        'unique_mesh_names':len(names),'duplicate_mesh_names':sum(n-1 for n in names.values() if n>1),
                        'source_id_prefixes':dict(source),'system_mesh_counts':dict(sorted(systems.items()))},
            'concept_id_prefixes':dict(Counter('HRA' if c['id'].startswith('HRA:') else 'FMA' if c['id'].startswith('FMA:') else 'composite/other' for c in concepts))}
    pelvis=[]
    for p in parts:
        s=(p['name']+' '+p['id']+' '+str(p.get('conceptId',''))).lower()
        if p['system']=='skeletal' and any(k in s for k in ('hip bone','ilium','iliac','ischium','pubis','acetabul','sacrum','coccyx')):
            pelvis.append({'id':p['id'],'name':p['name'],'conceptId':p.get('conceptId'),'triangles':p['indexCount']//3,'bounds_m':p['bounds']})
    result['candidate_pelvis_parts']=pelvis
    # HRA and BodyParts3D source transforms read directly from the repository scripts.
    result['provenance']={
      'HRA':{'source':'HRA united-female v1.5 GLB','transform':'convert-female.py adds +0.794760942 m to Y; source has baked Y-up meter coordinates; no node matrix/transforms accepted.'},
      'BodyParts3D':{'source':'BodyParts3D 4.0 OBJ','transform':'convert-anatomy.py: (x,y,z) mm -> (0.001*x, 0.001*z+0.0781112, -0.001*y-0.1) m; build-perfect scales X=.95, Y=.96335, Z=.95 and adds Z=-.052 m, then applies piecewise height/region deformations (neck, shoulders, rib cage, waist/hips, lower back, glutes, arms; extra skin breast/groin edits).'},
      'postprocessing':{'source':'meshoptimizer','transform':'optimize-anatomy.mjs welds coincident HRA vertices/averages normals, simplifies each part toward 22% of original triangle count with error argument .002, compacts vertices; report README says .2% relative error but source passes .002 and target count is ~22%.'},
      'coverage':'The shipped atlas.json identifies all 3004 parts. The 841 HRA-origin parts include 552 VH_F_, 282 Allen_ and 7 Yao_ IDs; hra/catalogo_hra.csv contains all 289 Allen/Yao records (including Yao_lymph_node within VH_F_lymphatic_system). The HRA source-group conversion is documented; 10 HRA-origin nodes lack individual catalog rows but remain attributable to the HRA input GLB and converter.'}
    return result

def box(arr): return np.vstack((arr.min(0),arr.max(0))).round(6).tolist()

def axis_report():
    # Check representative named mesh bounds. Output coordinates are the composite local coordinates.
    keys=('skin','ilium','hip bone','sacrum','femur','lumbar vertebra')
    chosen=[]
    for p in ATLAS['parts']:
        s=p['name'].lower()
        if p['system'] in ('integumentary','skeletal') and any(k in s for k in keys):
            chosen.append({'id':p['id'],'name':p['name'],'bounds_m':p['bounds']})
    img=nib.load(str(ROOT/'hra/nlm/bruto/saida/segmentacao.nii.gz'))
    data=np.asanyarray(img.dataobj)
    labels={int(k):str(v) for k,v in img.header[' descrip'].__str__().encode().hex().items()} if False else None
    # The audited affine is also present in the checked EXP-0010 transform metadata.
    tr=json.loads((ROOT/'hra/alinhar/transformacoes.json').read_text(encoding='utf8'))['source_multilabel']
    return {'female_composite_representative_bounds_m':chosen[:30],
            'tc_nlm':{'shape_ijk':list(data.shape),'affine_ijk_to_RAS_mm':img.affine.round(6).tolist(),
                      'world_bbox_mm':box(nib.affines.apply_affine(img.affine,np.array([[0,0,0],*[np.array(data.shape)-1]]))),
                      'voxel_spacing_mm':[float(x) for x in img.header.get_zooms()[:3]],
                      'EXP0010_affine_matches_loaded':bool(np.allclose(img.affine,np.array(tr['affine_ijk_to_world_mm']),atol=1e-5))}}

if __name__=='__main__':
    r=manifest_summary(); r['axes']=axis_report()
    (OUT/'inventory.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'meshes':r['observed']['meshes'],'concepts':r['observed']['concepts'],'triangles':r['observed']['triangles'],'prefixes':r['observed']['source_id_prefixes'],'systems':r['observed']['systems'],'inventory':str(OUT/'inventory.json')},ensure_ascii=False))
