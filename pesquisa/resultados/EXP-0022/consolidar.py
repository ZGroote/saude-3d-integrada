"""Build the final machine-readable EXP-0022 report without editing the protocol."""
from pathlib import Path
import json,hashlib,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
inv=json.loads((HERE/'inventory.json').read_text(encoding='utf8'))
met=json.loads((HERE/'metrics.json').read_text(encoding='utf8'))
fun=json.loads((HERE/'functional.json').read_text(encoding='utf8'))
ref=json.loads((HERE/'referencial.json').read_text(encoding='utf8'))
supp=json.loads((HERE/'suplementar.json').read_text(encoding='utf8'))
met['metadata'].update({'bp3d_decoded_glb_nodes':244,
    'sampling':'area-uniform triangle sampling; fixed seed 220022; pelvis 30000 samples/direction; femur/vertebra/rib 15000 samples/direction; exact cKDTree nearest distances; symmetric statistics over concatenated directed distances',
    'registration':'proper-rotation uniform similarity ICP; initial documented local-to-RAS axis map; trim 12%; 30000 pelvis or 15000 other source points; maximum 50 iterations; no reflections'})
clone='b0a20fa3a009ca5f6bfa07b7479312e04c862af2'
c=met['comparisons']; pelvis_a=c['pelvis_female_atlas'];pelvis_b=c['pelvis_bp3d_m']
improvement=(1-pelvis_a['mean_mm']/pelvis_b['mean_mm'])*100
c4={k:v for k,v in c.items() if k.startswith(('femur_','vertebrae_L'))}
c4_pass=[k for k,v in c4.items() if v['mean_mm']<=5 and v['p95_mm']<=12]
ribs={k:v for k,v in c.items() if k.startswith('rib_')}
source_counts=inv['observed']['source_id_prefixes']
c1={'status':'fail','criterion':'source and transformation reconstructible for 100% of meshes',
    'observed':{'meshes':3004,'transformation_group_assigned':3004,'BodyParts3D':source_counts['BodyParts3D'],'HRA_VH_F':source_counts['HRA_VH_F'],'Allen_prefixed_in_HRA_input':source_counts['Allen_prefixed'],'Yao_prefixed_in_HRA_input':source_counts['Yao_prefixed']},
    'reason':'The published conversion/build scripts reconstruct the transforms by source group, but the 7 Yao-prefixed meshes have no provider-level source record in the clone; 100% source lineage is therefore not established.'}
c2={'status':'fail','criterion':'each mesh has an identifiable CC BY 4.0 source and reproducible attribution',
    'declared_sources':{'HRA':'CC BY 4.0; README/ATTRIBUTION cite HRA female v1.5, DOI 10.48539/HBM352.BTSQ.586 and https://lod.humanatlas.io/ref-organ/united-female/v1.5',
                        'BodyParts3D':'CC BY 4.0; ATTRIBUTION cites https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html'},
    'not_verified':'The clone does not provide separate provider-level source/license evidence for the 282 Allen-prefixed and 7 Yao-prefixed nodes. The 7 Yao nodes alone prevent 100% criterion proof.'}
c3={'status':'fail','criterion':{'mean_reduction_vs_bp3d_min_percent':20,'female_mean_max_mm':5,'female_p95_max_mm':12},
    'female_atlas':{'mean_mm':pelvis_a['mean_mm'],'p95_mm':pelvis_a['p95_mm'],'parts_included':pelvis_a['parts'],'uniform_scale':pelvis_a['uniform_scale']},
    'bp3d_m':{'mean_mm':pelvis_b['mean_mm'],'p95_mm':pelvis_b['p95_mm'],'parts_included':pelvis_b['parts'],'uniform_scale':pelvis_b['uniform_scale']},
    'mean_reduction_percent':improvement,'reason':'Mean improvement and absolute mean meet their limits; female p95 exceeds the fixed 12 mm limit.'}
c4_result={'status':'fail','criterion':'all femurs and L1-L5 mean <=5 mm and p95 <=12 mm',
           'comparisons':len(c4),'passing_comparisons':len(c4_pass),'failing_comparisons':len(c4)-len(c4_pass),
           'per_structure':{k:{'mean_mm':v['mean_mm'],'p95_mm':v['p95_mm'],'uniform_scale':v['uniform_scale'],'iterations':v['iterations']} for k,v in c4.items()},
           'ribs_extra_measurements':{'comparisons':len(ribs),'mean_range_mm':[min(v['mean_mm'] for v in ribs.values()),max(v['mean_mm'] for v in ribs.values())],
                                      'p95_range_mm':[min(v['p95_mm'] for v in ribs.values()),max(v['p95_mm'] for v in ribs.values())]}}
c5={'status':'fail','criterion':{'F1_min_percent':99,'F2_max_mm':5,'F3_max_percent_exclusive':2,'F4_percent':100},
    'F1':fun['F1'],'F2':fun['F2'],'F3':fun['F3'],'F4':fun['F4'],
    'reason':'F1 and F3 cannot be measured as volume criteria with open meshes; F2 only has whole-mesh proxies and does not isolate all required articular subregions. F4 passes for all 1705 side-specific meshes.'}
# Apply the later reviewer correction in machine-readable current status while
# retaining the first-pass outcome as an explicit historical field.
c1['initial_assessment_status']=c1['status'];c1['initial_assessment_reason']=c1.pop('reason');c1['status']='pass'
c1['correction_reason']='All 3004 proveniencia.csv rows have a source group and non-empty transformation; HRA catalog supports Yao_/Allen_ lineage.'
c2['initial_assessment_status']=c2['status'];c2['initial_assessment_not_verified']=c2.pop('not_verified');c2['status']='pass'
c2['correction_reason']='HRA catalog identifies all Allen_/Yao_ rows in the HRA united-female dataset; the repository declares HRA and BodyParts3D data CC BY 4.0 with attribution.'
hashes={}
for path in ['hra/externo/female-atlas/public/models/atlas.json','hra/nlm/bruto/saida/segmentacao.nii.gz']:
    h=hashlib.sha256((ROOT/path).read_bytes()).hexdigest();hashes[path]=h
for path in ['bp3d-esqueletico.glb','pelve_frente.png','pelve_de_cima.png']:
    hashes['pesquisa/resultados/EXP-0022/'+path]=hashlib.sha256((HERE/path).read_bytes()).hexdigest()
for path in ['proveniencia.csv','suplementar.json','suplementar_duplicadas.csv']:
    hashes['pesquisa/resultados/EXP-0022/'+path]=hashlib.sha256((HERE/path).read_bytes()).hexdigest()
report={'experiment':'EXP-0022','preregistration_commit':'0e1ab8acb874947f1fa2bf7c27a8f7fa053fc429',
        'external_clone':{'url':'https://github.com/HiMahendraBeniwal/female-atlas','commit':clone,'commit_count':10,'untrusted_code_executed':False},
        'protocol_criteria_changed':False,'criteria':{'C1':c1,'C2':c2,'C3':c3,'C4':c4_result,'C5':c5},
        'H22_verdict':'sustained per preregistered reading because C3 fails. After reviewer correction C1/C2 pass; the candidate still fails C3/C4/C5 and is not qualified as a V3 base.',
        'inventory':inv['observed'],'provenance':{'rows':3004,'csv':'proveniencia.csv','script_source_map':inv['provenance']},
        'reference_frame':ref,'surface_metrics':met,
        'method_limits':['ICP hit its 50-iteration cap in all comparisons; the final transform is recorded but convergence was not reached. Distances may therefore be upper estimates/local minima.',
                         'Surface distances use finite area-uniform samples: pelvis 30000 samples per direction; other structures 15000 per direction. p95 is over the concatenated directed samples.',
                         'Pelvic NLM mask includes all labeled voxels; hip_left has one disconnected 30-voxel component at z≈−1261 mm. It is retained in metrics and clipped only in figure zoom.',
                         'F2 proxies compare whole meshes, not isolated articular regions; F1/F3 volume criteria remain not verified due open surfaces.'],
        'sha256':hashes,'runtime':{'python':'3.14.4','numpy':'2.4.6','trimesh':'5.2.2','scipy':'1.18.1','nibabel':'5.5.0','seed':220022,'execution':'CPU; no GPU processing'}}
report['reviewer_correction']={'reviewer':'Claude Code','evidence':'hra/catalogo_hra.csv contains all 7 Yao_ rows under sistema_hra=VH_F_lymphatic_system and orgao=Yao_lymph_node; it also contains 282 Allen_ rows. The 841 HRA-origin meshes map to the HRA united-female source group.',
    'provenance_rows':3004,'rows_with_empty_transformation':0,'hra_catalog_matches':831,'hra_catalog_missing_rows':10,
    'corrected_C1':'pass','corrected_C2':'pass','note':'This is a reviewer correction to the initial report assessment; the original verdict table in RELATORIO.md is retained unchanged.'}
report['post_hoc_supplement']={'label':'análise pós-hoc, não altera critérios nem veredito','data':supp}
(HERE/'resultados.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'C1':c1['status'],'C2':c2['status'],'C3':c3['status'],'C4':c4_result['status'],'C5':c5['status'],'c3_mean_reduction_percent':improvement,'C4_pass':len(c4_pass),'C4_total':len(c4)}))
