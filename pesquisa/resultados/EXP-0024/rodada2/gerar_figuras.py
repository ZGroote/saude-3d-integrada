"""Round-2 M1 distribution and typical-pelvis figures using saved data."""
from pathlib import Path
import json,sys,site
sys.path.append(site.getusersitepackages())
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent;R1=HERE.parent
r=json.loads((HERE/'resultados.json').read_text(encoding='utf-8'))
base=json.loads((R1/'resultados.json').read_text(encoding='utf-8'))
fem=list(base['female_scores'].values());men=[x['mean_mm'] for x in r['male_replacement']['m1'].values()]
lim=base['bands']['M1_mean_mm']['p97_5'];h=r['published_atlases']['hra-f']['metrics'];b=r['published_atlases']['bp3d-m']['metrics']
fig,ax=plt.subplots(figsize=(10,6));ax.hist(fem,bins=12,alpha=.65,label='Mulheres (val; M1 LOO)',color='#bb6688');ax.hist(men,bins=12,alpha=.58,label='Homens (20 controles; M1)',color='#5577aa')
ax.axvline(lim,color='black',linestyle='--',label=f'p97,5 feminino: {lim:.2f} mm')
ax.axvline(h['M1_mean_mm'],color='#df852d',linewidth=2,label=f"hra-f publicado: {h['M1_mean_mm']:.2f} mm (V2 não avaliável)")
ax.axvline(b['M1_mean_mm'],color='#278c68',linewidth=2,label=f"bp3d-m publicado: {b['M1_mean_mm']:.2f} mm")
ax.set(xlabel='M1 médio — distância simétrica (mm)',ylabel='Casos',title='EXP-0024 — rodada 2: M1 feminino, controle e atlas publicados');ax.grid(alpha=.2);ax.legend();fig.tight_layout();fig.savefig(HERE/'distribuicao_m1.png',dpi=170);plt.close(fig)
# Register the typical validation pelvis and both atlas pelvises into the fixed dev template frame.
spec=__import__('importlib.util').util.spec_from_file_location('exp24_r1',R1/'analisar_local.py');mod=__import__('importlib.util').util.module_from_spec(spec);spec.loader.exec_module(mod)
z=np.load(R1/'surface_samples.npz');template=z[f"p_{base['development']['template_case_id']}"];cid=base['typical_validation_case'];st,typ=mod.symmetric_after_rigid(z[f'p_{cid}'],template)
atlas=np.load(HERE/'atlas_surface_samples.npz');fig=plt.figure(figsize=(10,8));ax=fig.add_subplot(111,projection='3d')
for name,points,color in [('Validação '+cid,typ,'#aa4466'),('hra-f publicado',atlas['hra_pelvis'],'#e38730'),('bp3d-m publicado',atlas['bp3d_m_pelvis'],'#278866')]:
 if name.startswith('hra-f'):q=points@np.asarray(h['rigid_alignment_to_development_template']['rotation']).T+np.asarray(h['rigid_alignment_to_development_template']['translation_mm'])
 elif name.startswith('bp3d-m'):q=points@np.asarray(b['rigid_alignment_to_development_template']['rotation']).T+np.asarray(b['rigid_alignment_to_development_template']['translation_mm'])
 else:q=points
 step=max(1,len(q)//5000);q=q[::step];ax.scatter(q[:,0],q[:,1],q[:,2],s=1,alpha=.24,c=color,label=name)
ax.set_xlabel('RAS X (mm)');ax.set_ylabel('RAS Y (mm)');ax.set_zlabel('RAS Z (mm)');ax.set_title(f'Pelve típica da validação — {cid}; registro rígido ao template dev');ax.legend();fig.tight_layout();fig.savefig(HERE/'pelve_tipica.png',dpi=170);plt.close(fig)
print('wrote round-2 M1 distribution and aligned pelvis figures')
