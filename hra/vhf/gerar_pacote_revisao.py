"""Create a draft human-review atlas package from the EXP-0015 base meshes."""
from __future__ import annotations
import csv, hashlib, importlib.util, json, re, shutil, struct, subprocess, tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'atlas'/'hra-f'/'2.0-1'
DEST=ROOT/'atlas'/'vhf-f'/'0.1-0'
INDEX_NAME='indice.json'
MANIFEST_NAME='manifesto.json'
NPM_PACKAGE='@gltf-transform/cli@4.5.1'
TARGET_SKIN_TRIANGLES=40000

spec=importlib.util.spec_from_file_location('hra_publisher_model',ROOT/'hra'/'publicar_atlas_hra.py')
hra_model=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(hra_model)
SYSTEMS=sorted(hra_model.SISTEMAS_BP3D)
NPM=shutil.which('npx.cmd') or shutil.which('npx')
if not NPM:
    raise RuntimeError('npx is unavailable; package creation cannot compress meshopt without installing tools')

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest().upper()

def run_gltf(command,*args):
    cmd=[NPM,'--no-install',NPM_PACKAGE,command,*map(str,args)]
    p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    if p.returncode:
        raise RuntimeError(f'gltf-transform {command} failed:\n{p.stdout}\n{p.stderr}')

def system_for(name):
    if name=='body__skin': return 'tegumentar'
    if name.startswith('denver__'):
        if '__bone_' in name: return 'esqueletico'
        if '__muscle_' in name: return 'muscular'
        if '__cartilage_' in name or '__ligament_' in name: return 'articular'
        raise ValueError(f'Unmapped Denver class: {name}')
    raw=name.removeprefix('total__')
    if raw.startswith(('adrenal_gland','thyroid_gland')): return 'endocrino'
    if raw in {'heart'} or raw.startswith('atrial_appendage'): return 'cardiaco'
    if raw.startswith(('aorta','artery','trunk')) or raw.endswith('_trunk') or '_artery_' in raw: return 'arterial'
    if any(x in raw for x in ('vein','vena','portal')): return 'venoso'
    if raw.startswith(('brain','spinal_cord')): return 'nervoso'
    if raw.startswith(('lung','trachea','bronch')): return 'respiratorio'
    if raw.startswith(('kidney','urinary','uterus','ovary','prostate','testis')): return 'urogenital'
    if raw.startswith(('spleen','thymus','lymph')): return 'linfatico'
    if raw.startswith(('rib_','vertebrae_','clavicula','humerus','scapula','skull','sternum','hip_','sacrum','coccyx')): return 'esqueletico'
    if raw.startswith('costal_cartilages'): return 'articular'
    if raw.startswith(('autochthon',)): return 'muscular'
    if raw.startswith(('colon','duodenum','esophagus','gallbladder','liver','pancreas','small_bowel','stomach','rectum')): return 'digestorio'
    raise ValueError(f'No BP3D system mapping for {name}')

def laterality(name):
    if name in {'denver__bone_sacrum__left','denver__bone_coccyx__left'}: return None
    if name=='body__skin': return None
    m=re.search(r'(?:^|_)(left|right)(?:_|$)',name)
    return m.group(1) if m else None

def source_name(name):
    if name.startswith('denver__'):
        m=re.match(r'denver__(bone|muscle|cartilage|ligament)_(.+)__([a-z]+)$',name)
        if not m: return name
        kind,structure,side=m.groups()
        label=structure.replace('_',' ')
        fixes={'calcaneous':'calcaneus','illiacus':'iliacus','quadratis femoris':'quadratus femoris'}
        label=' '.join(fixes.get(w,w) for w in label.split())
        return f'{label.title()} {side.title()}'
    if name=='body__skin': return 'Skin'
    raw=name.removeprefix('total__')
    if raw.startswith('rib_'):
        m=re.match(r'rib_(left|right)_(\d+)',raw)
        if m:return f'Rib {m.group(2)} {m.group(1).title()}'
    if raw.startswith('vertebrae_'):
        return 'Vertebra '+raw.removeprefix('vertebrae_').upper()
    words=raw.replace('_',' ').split()
    substitutions={'clavicula':'clavicle','vena':'vein','autochthon':'autochthon muscle','small':'small'}
    words=[substitutions.get(w,w) for w in words]
    return ' '.join(words).title()

def triangles(mesh):
    return int(len(mesh.faces))

def make_scene(entries):
    scene=trimesh.Scene()
    for name,mesh in entries:
        scene.add_geometry(mesh,geom_name=name,node_name=name)
    return scene

def export_scene(entries,path):
    scene=make_scene(entries)
    path.write_bytes(scene.export(file_type='glb'))

def write_empty_glb(path):
    doc={'asset':{'version':'2.0','generator':'EXP-0015 VHF-F draft packager'},'scene':0,
         'scenes':[{'nodes':[]}],'nodes':[]}
    raw=json.dumps(doc,separators=(',',':')).encode('utf-8')
    raw+=b' '*((-len(raw))%4)
    path.write_bytes(struct.pack('<4sII',b'glTF',2,12+8+len(raw))+struct.pack('<II',len(raw),0x4E4F534A)+raw)

def read_glb(path):
    data=Path(path).read_bytes()
    magic,version,total=struct.unpack_from('<4sII',data,0)
    if magic!=b'glTF' or version!=2 or total!=len(data):raise ValueError(f'Invalid GLB header: {path}')
    jlen,jtype=struct.unpack_from('<II',data,12)
    if jtype!=0x4E4F534A:raise ValueError('GLB JSON chunk missing')
    return json.loads(data[20:20+jlen])

def node_triangles(doc):
    out={}
    for node in doc.get('nodes',[]):
        if 'mesh' not in node:continue
        n=0
        for prim in doc['meshes'][node['mesh']].get('primitives',[]):
            acc=prim.get('indices',prim['attributes']['POSITION'])
            n+=doc['accessors'][acc]['count']//3
        out[node.get('name')]=n
    return out

def publish():
    if DEST.exists():raise FileExistsError(f'Draft package already exists; preserving it: {DEST}')
    manifest=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
    records=manifest['meshes']
    if not all((SOURCE/f"{r['name']}.stl").is_file() for r in records):
        raise FileNotFoundError('At least one source STL referenced by the EXP-0015 manifest is missing')
    catalog={}
    with (ROOT/'hra'/'denver'/'catalogo_denver.csv').open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            catalog[(r['estrutura'].strip().lower().replace(' ','_'),r['lateralidade'].strip().lower())]=r['estrutura'].strip()
    groups={s:[] for s in SYSTEMS}
    index=[]
    source_hashes={}
    xform=np.array([[-0.001,0,0,0],[0,0,0.001,0],[0,0.001,0,0],[0,0,0,1]],dtype=float)
    for r in records:
        name=r['name']; system=system_for(name)
        if system not in groups:raise ValueError(f'Unknown system {system} for {name}')
        source='denver' if name.startswith('denver__') else 'totalsegmentator'
        mesh=trimesh.load_mesh(SOURCE/f'{name}.stl',process=False)
        if not isinstance(mesh,trimesh.Trimesh):raise TypeError(f'Not a mesh: {name}')
        expected=int(r['faces'])
        if len(mesh.faces)!=expected:raise ValueError(f'Triangle count changed on source STL {name}: {len(mesh.faces)} != {expected}')
        mesh.apply_transform(xform)
        groups[system].append((name,mesh))
        side=laterality(name)
        if source=='denver':
            bits=name.removeprefix('denver__').rsplit('__',1)
            key=bits[0].replace('_',' ')
            name_en=catalog.get((bits[0],bits[1]),key.title()+' '+(side.title() if side else ''))
            if name in {'denver__bone_sacrum__left','denver__bone_coccyx__left'}:
                name_en='Sacrum' if 'sacrum' in name else 'Coccyx'
        else:name_en=source_name(name)
        index.append({'malha':name,'estrutura':None,'nome_en':name_en,'nome_pt':None,'sistema':system,
                      'lateralidade':side,'glb':f'{system}.glb','triangulos':expected,'fonte':source})
        source_hashes[f'{name}.stl']=sha256(SOURCE/f'{name}.stl')
    unmapped=[r['name'] for r in records if not any(x['malha']==r['name'] for x in index)]
    if unmapped:raise ValueError(f'Unindexed source meshes: {unmapped}')
    if set(groups)!=set(SYSTEMS):raise AssertionError('System IDs differ from bp3d-m')
    if sum(len(v) for v in groups.values())!=len(records):raise AssertionError('Index count differs from manifest')

    DEST.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.tmp-vhf-f-0.1-0-',dir=DEST.parent))
    try:
        by_name={n:m for rows in groups.values() for n,m in rows}
        for sid,entries in sorted(groups.items()):
            out=stage/f'{sid}.glb'
            raw=stage/f'.{sid}.raw.glb'
            if entries:
                export_scene(entries,raw)
                run_gltf('meshopt',raw,out,'--level','high','--quantize-position','16','--quantization-volume','mesh')
                raw.unlink()
                doc=read_glb(out); counts=node_triangles(doc)
                expected={name:triangles(mesh) for name,mesh in entries}
                if counts!=expected:raise AssertionError(f'GLB nodes or triangle counts differ for {sid}')
                if 'EXT_meshopt_compression' not in doc.get('extensionsRequired',[]):
                    raise AssertionError(f'Meshopt extension not required in {sid}.glb')
            else:
                write_empty_glb(out)
            print(f'{sid}: {out.stat().st_size/1e6:.3f} MB; {len(entries)} meshes; {sum(triangles(m) for _,m in entries)} triangles',flush=True)

        skin_entries=groups['tegumentar']
        skin_name='body__skin'
        skin=by_name[skin_name]
        light=skin.simplify_quadric_decimation(face_count=TARGET_SKIN_TRIANGLES)
        if abs(len(light.faces)-TARGET_SKIN_TRIANGLES)>TARGET_SKIN_TRIANGLES*0.15:
            raise AssertionError(f'Skin LOD triangle target not met: {len(light.faces)}')
        leve=stage/'tegumentar_leve.glb'
        leve_raw=stage/'.tegumentar_leve.raw.glb'
        export_scene([(skin_name,light)],leve_raw)
        run_gltf('meshopt',leve_raw,leve,'--level','high','--quantize-position','16','--quantization-volume','mesh')
        leve_raw.unlink()
        leve_doc=read_glb(leve)
        if 'EXT_meshopt_compression' not in leve_doc.get('extensionsRequired',[]):
            raise AssertionError('Meshopt extension not required for skin LOD')
        if node_triangles(leve_doc)!={skin_name:len(light.faces)}:raise AssertionError('Skin LOD node/triangle validation failed')

        index_path=stage/INDEX_NAME
        index_path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        output_files=sorted([p for p in stage.iterdir() if p.is_file()])
        hashes={p.name:sha256(p) for p in output_files}
        system_rows=[]
        for sid,entries in sorted(groups.items()):
            item={'id':sid,'glb':f'{sid}.glb','estruturas':len(entries),
                  'triangulos':sum(triangles(m) for _,m in entries)}
            if sid=='tegumentar':
                item.update({'glb_leve':'tegumentar_leve.glb','triangulos_leve':len(light.faces)})
            system_rows.append(item)
        final_manifest={
            'atlas':'vhf-f','versao':'0.1-0','status':'rascunho, nao publicado, nao aceito',
            'publicado':False,'aceito':False,
            'fonte':'Base EXP-0015: TotalSegmentator total/body e Denver etapa A',
            'licencas':{'totalsegmentator':'Apache-2.0','denver':'CC BY 4.0','dados_tc':'NLM; atribuicao conforme origem'},
            'unidade':'m','eixos':'x esquerda do paciente, y cima, z frente',
            'transformacao_de_RAS_m':[[-0.001,0,0,0],[0,0,0.001,0],[0,0.001,0,0],[0,0,0,1]],
            'sha256':hashes,'fonte_malhas_sha256':source_hashes,
            'sistemas':system_rows,
            'observacao':'Pacote local de revisao humana F5; rascunho, nao publicado, nao aceito. nome_pt e estrutura intencionalmente null.'
        }
        (stage/MANIFEST_NAME).write_text(json.dumps(final_manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        # Integrated package consistency and hashes before atomic placement.
        assert len(index)==len(records)
        assert all((stage/f'{sid}.glb').is_file() for sid in SYSTEMS)
        assert all(sha256(stage/name)==digest for name,digest in hashes.items())
        for sid,entries in groups.items():
            doc=read_glb(stage/f'{sid}.glb')
            names=set(node_triangles(doc))
            assert names=={n for n,_ in entries},f'Node names mismatch in {sid}'
        stage.rename(DEST)
    except Exception:
        shutil.rmtree(stage,ignore_errors=True)
        raise
    total=sum((DEST/f'{sid}.glb').stat().st_size for sid in SYSTEMS)+(DEST/'tegumentar_leve.glb').stat().st_size
    print(f'PACKAGE {DEST}; {len(index)} entries; {total/1e6:.3f} MB total; skin LOD {len(light.faces)} triangles; SHA-256 verified')

if __name__=='__main__':
    publish()


