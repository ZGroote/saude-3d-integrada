"""Select protocol pools without touching the preregistered protocol; Python -I."""
from pathlib import Path
import csv, json, hashlib, random

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
META=ROOT/'pesquisa/resultados/EXP-0023/metadados/S1_totalsegmentator/meta.csv'
SEED=240024

def fnum(x):
    try:return float(x)
    except (TypeError,ValueError):return None

def main():
    with META.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f,delimiter=';'))
    base=[r for r in rows if r.get('gender','').strip().lower() in ('f','m') and
          (fnum(r.get('age')) or 0)>=18 and
          any(x in r.get('study_type','').lower() for x in ('pelvis','lower limb','leg','polytrauma')) and
          (fnum(r.get('slice_thickness')) or 999)<=2]
    female=[r for r in base if r['gender'].strip().lower()=='f']
    male=[r for r in base if r['gender'].strip().lower()=='m' and r.get('pathology','').strip().lower()=='no_pathology']
    primary=sorted([r for r in female if r.get('pathology','').strip().lower()=='no_pathology'],key=lambda r:r['image_id'])
    extension_raw=[r for r in female if r.get('pathology','').strip().lower()!='no_pathology']
    extension=sorted([r for r in female if r.get('pathology','').strip().lower() not in ('','unclear') and
                      not any(x in r.get('pathology_location','').lower() for x in ('pelvis','bones','extremity')) and
                      r.get('pathology','').strip().lower()!='no_pathology'],key=lambda r:r['image_id'])
    rng=random.Random(SEED)
    male20=sorted(rng.sample(male,20),key=lambda r:r['image_id']) if len(male)>=20 else []
    extension_order=rng.sample(extension,len(extension))
    extension_by_id={r['image_id']:r for r in extension}
    raw_by_id={r['image_id']:r for r in extension_raw}
    out=[]
    for r in primary:out.append({'id':r['image_id'],'pool':'female_primary','selection':'download_initial','included':'pending_qc','reason':'no_pathology; protocol primary pool','split':'pending_qc','age':r.get('age',''),'gender':r.get('gender','')})
    for r in extension_order:out.append({'id':r['image_id'],'pool':'female_extension','selection':'reserve_random_order','included':'not_downloaded','reason':'eligible extension; downloaded only if QC leaves fewer than 30 unique women','split':'pending_qc','age':r.get('age',''),'gender':r.get('gender','')})
    for r in sorted(extension_raw,key=lambda x:x['image_id']):
        if r['image_id'] in extension_by_id:continue
        why=[]
        if r.get('pathology','').strip().lower() in ('','unclear'):why.append('pathology blank/unclear')
        if any(x in r.get('pathology_location','').lower() for x in ('pelvis','bones','extremity')):why.append('pathology_location contains pelvis/bones/extremity')
        out.append({'id':r['image_id'],'pool':'female_extension','selection':'excluded_by_extension_filter','included':'excluded','reason':'; '.join(why) or 'does not meet extension filter','split':'not_applicable','age':r.get('age',''),'gender':r.get('gender','')})
    for r in male:out.append({'id':r['image_id'],'pool':'male_control','selection':'selected' if r in male20 else 'not_selected','included':'pending_qc' if r in male20 else 'excluded','reason':'seed 240024 sample of 20' if r in male20 else 'not in seed 240024 sample of 20','split':'control' if r in male20 else 'not_applicable','age':r.get('age',''),'gender':r.get('gender','')})
    fields=['id','pool','selection','included','reason','split','age','gender']
    with (HERE/'casos.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
    counts={'metadata_sha256':hashlib.sha256(META.read_bytes()).hexdigest(),'seed':SEED,'rng':'Python random.Random (protocol specifies seed, not RNG implementation)',
            'literal_filter_counts':{'female_adult_study_slice':len(female),'female_no_pathology':len(primary),'female_extension_raw_remaining':len(extension_raw),'female_extension_eligible_after_exclusions':len(extension),'male_no_pathology':len(male),'male_selected':len(male20)},
            'protocol_expected_counts':{'female_total':200,'female_primary':58,'female_extension_raw_remaining':142,'male_control':77},
            'pool_count_mismatch':len(female)!=200 or len(primary)!=58 or len(extension_raw)!=142 or len(male)!=77,
            'filters':'gender f/m; age >=18; study_type contains pelvis/lower limb/leg/polytrauma; slice_thickness <=2; extension excludes blank/unclear pathology and pathology_location containing pelvis/bones/extremity'}
    (HERE/'selecao.json').write_text(json.dumps(counts,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(counts,ensure_ascii=False))
if __name__=='__main__':main()
