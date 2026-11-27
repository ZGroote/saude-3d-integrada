"""Write honest EXP-0024 status artifacts when remote masks cannot be fetched."""
from pathlib import Path
import csv,json,hashlib,struct,zlib,sys,site,platform
sys.path.append(site.getusersitepackages())
import numpy as np, scipy, trimesh, nibabel

ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

FONT={
'A':['01110','10001','10001','11111','10001','10001','10001'],'B':['11110','10001','10001','11110','10001','10001','11110'],
'C':['01111','10000','10000','10000','10000','10000','01111'],'D':['11110','10001','10001','10001','10001','10001','11110'],
'E':['11111','10000','10000','11110','10000','10000','11111'],'F':['11111','10000','10000','11110','10000','10000','10000'],
'G':['01111','10000','10000','10111','10001','10001','01111'],'H':['10001','10001','10001','11111','10001','10001','10001'],
'I':['11111','00100','00100','00100','00100','00100','11111'],'J':['00111','00010','00010','00010','10010','10010','01100'],
'K':['10001','10010','10100','11000','10100','10010','10001'],'L':['10000','10000','10000','10000','10000','10000','11111'],
'M':['10001','11011','10101','10101','10001','10001','10001'],'N':['10001','11001','10101','10011','10001','10001','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],'P':['11110','10001','10001','11110','10000','10000','10000'],
'Q':['01110','10001','10001','10001','10101','10010','01101'],'R':['11110','10001','10001','11110','10100','10010','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],'T':['11111','00100','00100','00100','00100','00100','00100'],
'U':['10001','10001','10001','10001','10001','10001','01110'],'V':['10001','10001','10001','10001','10001','01010','00100'],
'W':['10001','10001','10001','10101','10101','10101','01010'],'X':['10001','10001','01010','00100','01010','10001','10001'],
'Y':['10001','10001','01010','00100','00100','00100','00100'],'Z':['11111','00001','00010','00100','01000','10000','11111'],
'0':['01110','10001','10011','10101','11001','10001','01110'],'1':['00100','01100','00100','00100','00100','00100','01110'],
'2':['01110','10001','00001','00010','00100','01000','11111'],'3':['11110','00001','00001','01110','00001','00001','11110'],
'4':['00010','00110','01010','10010','11111','00010','00010'],'5':['11111','10000','10000','11110','00001','00001','11110'],
'6':['01110','10000','10000','11110','10001','10001','01110'],'7':['11111','00001','00010','00100','01000','01000','01000'],
'8':['01110','10001','10001','01110','10001','10001','01110'],'9':['01110','10001','10001','01111','00001','00001','01110'],
'-':['00000','00000','00000','11111','00000','00000','00000'],':':['00000','00100','00100','00000','00100','00100','00000'],'/':['00001','00010','00010','00100','01000','01000','10000'],' ':['00000']*7}
def png_placeholder(path,title,lines):
    w,h=1200,650;pix=bytearray([255,255,255]*(w*h))
    def rect(x,y,ww,hh,color):
        for yy in range(max(0,y),min(h,y+hh)):
            for xx in range(max(0,x),min(w,x+ww)):
                k=(yy*w+xx)*3;pix[k:k+3]=bytes(color)
    def line(x0,y0,x1,y1,color=(80,90,100)):
        dx=abs(x1-x0);sx=1 if x0<x1 else -1;dy=-abs(y1-y0);sy=1 if y0<y1 else -1;err=dx+dy
        while True:
            rect(x0,y0,2,2,color)
            if x0==x1 and y0==y1:break
            e2=2*err
            if e2>=dy:err+=dy;x0+=sx
            if e2<=dx:err+=dx;y0+=sy
    def txt(x,y,s,scale=3,color=(25,45,65)):
        for ch in s.upper():
            pat=FONT.get(ch,FONT[' '])
            for yy,row in enumerate(pat):
                for xx,v in enumerate(row):
                    if v=='1':rect(x+xx*scale,y+yy*scale,scale,scale,color)
            x+=6*scale
    txt(70,45,title,4)
    rect(65,125,1070,2,(210,220,230))
    # Empty axes are explicitly identified as non-data placeholders.
    line(130,515,1070,515);line(130,205,130,515)
    for i in range(1,5):line(125,515-i*62,1070,515-i*62,(225,230,235))
    txt(175,250,'NO MEDIDO',7,(160,40,35))
    y=385
    for s in lines:txt(90,y,s,3,(55,70,85));y+=35
    raw=bytearray()
    stride=w*3
    for yy in range(h):raw.append(0);raw.extend(pix[yy*stride:(yy+1)*stride])
    def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(bytes(raw),9))+chunk(b'IEND',b'')
    Path(path).write_bytes(data)

def main():
    cases=list(csv.DictReader((HERE/'casos.csv').open(encoding='utf-8-sig',newline='')))
    # Ensure every member of both protocol pools is accounted for in the CSV.
    for r in cases:
        if r['pool']=='female_primary':
            r['included']='not_assessed';r['reason']='Q1-Q4 not assessable: remote mask download failed before transfer (0 bytes)';r['split']='not_assigned'
        elif r['pool']=='female_extension' and r['selection']=='reserve_random_order':
            r['included']='not_assessed';r['reason']='reserved by seed; not downloaded because masks were inaccessible; primary QC could not be assessed';r['split']='not_assigned'
        elif r['pool']=='male_control' and r['selection']=='selected':
            r['included']='not_assessed';r['reason']='Q1-Q4 not assessable: remote mask download failed before transfer (0 bytes)';r['split']='not_assigned'
    fields=list(cases[0].keys())
    with (HERE/'casos.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(cases)
    sel=json.loads((HERE/'selecao.json').read_text(encoding='utf-8'))
    block=json.loads((HERE/'download_manifest.json').read_text(encoding='utf-8'))
    metrics=[
      {'measure':'eligible_female_pool','value':200,'unit':'cases','status':'observed','reason':'Protocol literal filters; metadata count'},
      {'measure':'female_primary_pool','value':58,'unit':'cases','status':'observed','reason':'pathology=no_pathology'},
      {'measure':'female_extension_raw_pool','value':142,'unit':'cases','status':'observed','reason':'Remaining eligible-female pool before extension exclusions'},
      {'measure':'female_extension_after_exclusions','value':67,'unit':'cases','status':'observed','reason':'Blank/unclear pathology and pelvis/bones/extremity locations excluded'},
      {'measure':'male_control_pool','value':77,'unit':'cases','status':'observed','reason':'Protocol literal filters and pathology=no_pathology'},
      {'measure':'female_QC_included','value':'','unit':'cases','status':'not_measured','reason':'NIfTI masks unavailable'},
      {'measure':'male_QC_included','value':'','unit':'cases','status':'not_measured','reason':'NIfTI masks unavailable'},
      {'measure':'M1_female_LOO','value':'','unit':'mm','status':'not_measured','reason':'No pelvic masks downloaded'},
      {'measure':'M1_male_vs_female','value':'','unit':'mm','status':'not_measured','reason':'No pelvic masks downloaded'},
      {'measure':'M2_pelvis_size','value':'','unit':'mm','status':'not_measured','reason':'No pelvic surfaces available'},
      {'measure':'M3_pelvis_proportions','value':'','unit':'dimensionless','status':'not_measured','reason':'No masks/template available'},
      {'measure':'M1_proximal_femur','value':'','unit':'mm','status':'not_measured','reason':'No femur masks downloaded'}]
    with (HERE/'metricas.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(metrics[0]));w.writeheader();w.writerows(metrics)
    bands={'status':'not_measurable','reason':'No TotalSegmentator masks were available; network connection to Zenodo was refused before the first HTTP Range transfer.','n_female_validation':None,
           'M1_mean_mm':{'p2_5':None,'p97_5':None},'M2_size_mm':{'p2_5':None,'p97_5':None},
           'M3':{'width_height':{'p2_5':None,'p97_5':None},'width_depth':{'p2_5':None,'p97_5':None},'femoral_head_distance_width':{'p2_5':None,'p97_5':None}},
           'auc':{'status':'not_measured','value':None,'reason':'No validation cohort measurements.'}}
    (HERE/'faixas_femininas.json').write_text(json.dumps(bands,ensure_ascii=False,indent=2),encoding='utf-8')
    auc={'status':'not_measured','value':None,'positive_class':'male','score':'M1 mean distance to female validation cases','reason':bands['auc']['reason']}
    (HERE/'auc.json').write_text(json.dumps(auc,ensure_ascii=False,indent=2),encoding='utf-8')
    criteria={
      'V0':{'status':'not_verifiable','criterion':'>=30 QC-passing women, >=20 validation women, and 20 men','observed_counts':{'QC_passing_female':None,'validation_female':None,'QC_passing_male':None},'reason':'Masks unavailable; QC could not run.'},
      'V1':{'status':'inconclusive','criterion':'AUC >=0.80','auc':None,'reason':'M1 distributions and AUC not measurable without masks.'},
      'V2':{'status':'not_evaluable','criterion':'hra-f M1 <= female p97.5 and each M3 proportion within p2.5-p97.5','reason':'Female validation bands not measurable.'},
      'V3':{'status':'not_evaluable','criterion':'bp3d-m M1 > female p97.5','reason':'Female validation band and atlas comparison not measurable.'}}
    results={'experiment':'EXP-0024','protocol':'pesquisa/experimentos/EXP-0024-variabilidade-ossea-feminina.md','protocol_modified':False,
      'hypothesis_verdict':'inconclusive','criteria':criteria,'auc':auc,'pool_counts':sel['literal_filter_counts'],
      'transfer':block,'deviations':[{'label':'DESVIO','description':'Nenhuma transferência HTTP Range ocorreu: a conexão ao Zenodo foi recusada no HEAD (WinError 10061); 0 bytes transferidos. Sem as máscaras, QC, divisão dev/val, M1-M3, AUC, faixas e comparadores não podem ser medidos.'}],
      'limitations':['No CT data were downloaded or used.','No geometry metric, AUC, or atlas verdict is inferred from metadata-only pool counts.','Figures are explicit placeholders, not data plots.','RNG is Python random.Random with seed 240024; protocol specifies the seed but not RNG implementation.'],
      'reproducibility':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'trimesh':trimesh.__version__,'nibabel':nibabel.__version__,'seed':240024,
        'scripts':{p.name:sha(p) for p in sorted(HERE.glob('*.py'))},'metadata_sha256':sel['metadata_sha256'],'range_bytes_transferred':0}}
    (HERE/'resultados.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    png_placeholder(HERE/'distribuicao_m1.png','M1: MULHERES VS HOMENS',['DISTRIBUICAO NAO DISPONIVEL','Zenodo Range bloqueado antes da transferencia','hra-f e bp3d-m nao avaliados'])
    png_placeholder(HERE/'pelve_tipica.png','PELVIS TIPICA: NAO AVALIADA',['Sem mascaras NIfTI locais','Acesso ao Zenodo recusado antes de 0 bytes','Imagem ilustrativa ausente: sem geometria medida'])
    print(json.dumps({'cases':len(cases),'metric_rows':len(metrics),'V0':criteria['V0']['status'],'V1':criteria['V1']['status'],'V2':criteria['V2']['status'],'V3':criteria['V3']['status'],'range_bytes':0}))
if __name__=='__main__':main()
