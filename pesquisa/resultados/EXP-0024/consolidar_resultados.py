"""Add execution provenance and ICP convergence summaries to EXP-0024 JSON."""
from pathlib import Path
import json,csv,hashlib,collections,statistics
HERE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=HERE/'resultados.json';r=json.loads(p.read_text(encoding='utf-8'))
    groups=collections.defaultdict(list)
    for line in (HERE/'m1_pairs.jsonl').read_text(encoding='utf-8').splitlines():
        x=json.loads(line);groups[x['key'].split('::',1)[0]].append(x['stats'])
    convergence={}
    for name,items in groups.items():
        convergence[name]={'comparisons':len(items),'converged':sum(bool(x['converged']) for x in items),
            'not_converged':sum(not x['converged'] for x in items),'mean_iterations':statistics.mean(x['iterations'] for x in items),
            'max_iterations':max(x['iterations'] for x in items)}
    q4=json.loads((HERE/'q4.json').read_text(encoding='utf-8'))
    dl=json.loads((HERE/'download_manifest.json').read_text(encoding='utf-8'))
    with (HERE/'casos.csv').open(encoding='utf-8-sig',newline='') as f:case_rows=list(csv.DictReader(f))
    r['m1_convergence']=convergence
    q4conv={}
    for label,key in [('female','female_pairs'),('male','male_pairs')]:
        fits=[x for x in q4[key] if x['icp_run']]
        q4conv[label]={'icp_runs':len(fits),'converged':sum(bool(x.get('converged')) for x in fits),
            'not_converged':sum(not x.get('converged',False) for x in fits),'max_iterations':max((x.get('iterations',0) for x in fits),default=0)}
    r['q4_summary']={'female_pairs_considered':q4['female_pair_count'],'female_icp_runs':q4['female_icp_runs'],
        'female_prefiltered':q4['female_pair_count']-q4['female_icp_runs'],'male_pairs_considered':q4['male_pair_count'],
        'male_icp_runs':q4['male_icp_runs'],'male_prefiltered':q4['male_pair_count']-q4['male_icp_runs'],
        'centroid_size_prefilter_relative_difference_lt':q4['prefilter_relative_size'],'unchanged_duplicate_cutoff_mean_mm_lt':q4['criterion_distance_mm'],'convergence':q4conv}
    r['download_provenance']={'downloaded_by':'reviewer Claude Code','download_date':'2026-11-27','case_count':dl['case_count'],
        'mask_count':dl['mask_count'],'size_on_disk_total_bytes':dl['size_on_disk_total_bytes'],
        'range_transfer_bytes':'not recorded','no_ct_downloaded':True,'manifest_sha256':sha(HERE/'download_manifest.json'),
        'mask_set_sha256':dl['mask_set_sha256']}
    r['case_counts']={'total_ledger_rows':len(case_rows),'female_primary_included':sum(x['pool']=='female_primary' and x['included']=='included' for x in case_rows),
        'female_extension_not_downloaded':sum(x['pool']=='female_extension' and x['included']=='not_downloaded' for x in case_rows),
        'male_control_included':sum(x['pool']=='male_control' and x['included']=='included' for x in case_rows),
        'female_development':sum(x['gender']=='f' and x['split']=='dev' for x in case_rows),
        'female_validation':sum(x['gender']=='f' and x['split']=='val' for x in case_rows)}
    r['artifact_sha256']={name:sha(HERE/name) for name in ['analisar_local.py','preparar.py','baixar_mascaras.py','casos.csv','metricas.csv','faixas_femininas.json','auc.json','parametros_congelados.json','q4.json','qc.json','download_manifest.json','extension_needed.json','m1_pairs.jsonl','distribuicao_m1.png','pelve_tipica.png']}
    p.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'M1_convergence':convergence,'Q4':r['q4_summary'],'download':r['download_provenance'],'case_counts':r['case_counts']},ensure_ascii=False))
if __name__=='__main__':main()
