"""C5 functional checks on the candidate atlas, using own code only."""
from pathlib import Path
import sys,site,json,csv,re
sys.path.append(site.getusersitepackages())
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import numpy as np
import trimesh
from scipy.spatial import cKDTree
import medir as g

def approx_min(a,b,n=40000):
    pa=g.sample_surface(a,n);pb=g.sample_surface(b,n)
    if not len(pa) or not len(pb):return None
    return float(cKDTree(pb).query(pa,k=1,workers=-1)[0].min()*1000)

def ordinal(n):return ['first','second','third','fourth','fifth','sixth','seventh','eighth','ninth','tenth','eleventh','twelfth'][n-1]

def main():
    ext=g.external_all();bp=g.bp3d_all(); cat={r['arquivo']:r for r in csv.DictReader((g.ROOT/'bodyparts3d/catalogo_bp3d.csv').open(encoding='utf-8-sig'))}
    skin=next((m for p,m in ext.values() if p['id']=='BP3D_FJ2810'),None)
    imported=[(p,m) for p,m in ext.values() if p['id'].startswith('BP3D_')]
    bone_muscle=[(p,m) for p,m in imported if p['system'] in ('skeletal','muscular')]
    skin_summary={'id':'BP3D_FJ2810','watertight':bool(skin.is_watertight),'winding_consistent':bool(skin.is_winding_consistent),
                  'vertices':len(skin.vertices),'triangles':len(skin.faces),'bounds_m':skin.bounds.tolist(),
                  'eligible_imported_bone_muscle_meshes':len(bone_muscle),
                  'closed_imported_bone_muscle_meshes':sum(m.is_watertight for _,m in bone_muscle)}
    # F2a: closest samples on complete femur and corresponding hip bone are only
    # a proxy for the specifically required femoral head/acetabulum subregions.
    f2={'femur_to_same_side_hip_bone_proxy':{},'rib_to_same_number_thoracic_vertebra':{},'skull_to_C1':{}}
    for side in ('left','right'):
        fem=next((m for p,m in ext.values() if p['id'].startswith('BP3D_') and p['system']=='skeletal' and side in p['name'].lower() and 'femur' in p['name'].lower()),None)
        hip=next((m for p,m in ext.values() if p['id'].startswith('BP3D_') and p['system']=='skeletal' and f'{side} hip bone'==p['name'].lower()),None)
        if fem is not None and hip is not None:f2['femur_to_same_side_hip_bone_proxy'][side]={'sampled_surface_min_mm':approx_min(fem,hip),'femur_id':next(p['id'] for p,m in ext.values() if m is fem),'hip_id':next(p['id'] for p,m in ext.values() if m is hip),'interpretation':'whole-mesh proxy; femoral-head-to-acetabulum subregions are not separately named.'}
    skull_terms=('ethmoid','frontal bone','maxilla','nasal bone','palatine bone','parietal bone','temporal bone','zygomatic bone','mandible','occipital bone','sphenoid bone','vomer')
    skulls=[m for p,m in ext.values() if p['system']=='skeletal' and any(t in p['name'].lower() for t in skull_terms)]
    c1=next((m for p,m in ext.values() if p['system']=='skeletal' and (p['id']=='VH_F_cervical_vertebra_1' or p['id'].endswith('FJ3176'))),None)
    if skulls and c1 is not None:
        skull=trimesh.util.concatenate(skulls)
        f2['skull_to_C1']={'sampled_surface_min_mm':approx_min(skull,c1),'skull_mesh_count':len(skulls),
                          'C1_id':next(p['id'] for p,m in ext.values() if m is c1),
                          'interpretation':'whole cranial bone group to whole C1 proxy; occipital condyle/articular facets are not separately named.'}
    else:f2['skull_to_C1']={'status':'not_verifiable','reason':'Skull bone group or C1 mesh absent.'}
    for side in ('left','right'):
        for i in range(1,13):
            word=ordinal(i);rib=next((m for p,m in ext.values() if p['id'].startswith('BP3D_') and p['system']=='skeletal' and 'rib' in p['name'].lower() and side in p['name'].lower() and word in p['name'].lower()),None)
            vertebra=next((m for p,m in ext.values() if p['id'].startswith('BP3D_') and p['system']=='skeletal' and p['name'].lower()==f'{word} thoracic vertebra'),None)
            if rib is not None and vertebra is not None:
                f2['rib_to_same_number_thoracic_vertebra'][f'{side}_{i}']={'sampled_surface_min_mm':approx_min(rib,vertebra),'pairing':'same-numbered T vertebra','rib_id':next(p['id'] for p,m in ext.values() if m is rib),'vertebra_id':next(p['id'] for p,m in ext.values() if m is vertebra)}
    # F3 needs enclosed-volume fractions. Determine whether watertight volumes are
    # available for the complete imported/HRA groups before attempting intersection.
    hras=[(p,m) for p,m in ext.values() if not p['id'].startswith('BP3D_')]
    f3={'status':'not_verifiable','definition':'volume fraction of each imported structure inside/intersecting HRA-origin organs or bones; limit <2%.',
        'imported_meshes':len(imported),'imported_watertight':sum(m.is_watertight for _,m in imported),
        'hra_origin_meshes':len(hras),'hra_origin_watertight':sum(m.is_watertight for _,m in hras),
        'reason':'The source meshes include open surfaces, so a watertight volume intersection denominator is unavailable; no volumetric result is inferred from surface proximity.'}
    # F4: compare source catalog laterality with the displayed final mesh name.
    checked=0;mismatches=[];no_source=[]
    for p,m in imported:
        sid=p['id'].removeprefix('BP3D_');r=cat.get(sid)
        if not r:no_source.append(p['id']);continue
        lat=r.get('lateralidade','').strip().lower()
        if lat not in ('left','right'):continue
        checked+=1;name=p['name'].lower()
        if lat not in name:mismatches.append({'id':p['id'],'name':p['name'],'catalog_laterality':lat})
    f4={'status':'pass' if checked>0 and not mismatches and not no_source else 'fail','side_specific_meshes_checked':checked,'mismatches':mismatches,'ids_without_catalog_record':no_source}
    out={'F1':{'status':'not_verifiable','criterion':'at least 99% of imported bones/muscles inside skin','skin':skin_summary,
               'reason':'Skin mesh is open (not watertight); point-in-volume containment is undefined for the required closed-surface test.'},
         'F2':f2,'F3':f3,'F4':f4,
         'mesh_integrity_summary':{'total_parts':len(ext),'imported_BP3D_parts':len(imported),'HRA_prefix_counts':{'VH_F':sum(p['id'].startswith('VH_F_') for p,m in ext.values()),'Allen':sum(p['id'].startswith('Allen_') for p,m in ext.values()),'Yao':sum(p['id'].startswith('Yao_') for p,m in ext.values())},
                                   'watertight_imported':sum(m.is_watertight for _,m in imported),'watertight_HRA_origin':sum(m.is_watertight for _,m in hras)}}
    (HERE/'functional.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'F1':out['F1']['status'],'F2_rib_pairs':len(f2['rib_to_same_number_thoracic_vertebra']),'F3':f3['status'],'F4':f4['status'],'F4_checked':checked,'F4_mismatches':len(mismatches)}))
if __name__=='__main__':main()
