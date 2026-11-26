"""Diagn?stico geom?trico do EXP-0015 sem alterar m?scaras ou malhas."""
from __future__ import annotations
import json
from collections import OrderedDict
from pathlib import Path
import nibabel as nib
import numpy as np
import trimesh
from scipy import ndimage
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'atlas/hra-f/2.0-1'
REPORT=BASE/'diagnostico_EXP-0015.json'
TOTAL=ROOT/'hra/nlm/bruto/saida/segmentacao.nii.gz'
BODY=ROOT/'hra/nlm/bruto/body/segmentacao.nii.gz'
EVAL=json.loads((BASE/'avaliacao_F1-F4.json').read_text(encoding='utf-8'))
MAN=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
def mesh(n): return trimesh.load_mesh(BASE/f'{n}.stl',process=True)
def surf_samples(m,n,seed): return np.asarray(trimesh.sample.sample_surface(m,n,seed=seed)[0],dtype=float)
def read_labels(img):
 from xml.etree import ElementTree as ET
 for ext in img.header.extensions:
  try:
   root=ET.fromstring(ext.get_content()); return {int(q.attrib['Key']):q.text.strip() for q in root.findall('.//LabelTable/Label') if q.attrib.get('Key') and q.text}
  except Exception: pass
 raise ValueError('No label table')
def body_boundary():
 im=nib.load(str(BODY)); mask=np.asanyarray(im.dataobj)>0
 shape=np.asarray(mask.shape); zoom=np.asarray(im.header.get_zooms()[:3],float)
 mins=im.affine[:3,3]-zoom/2; maxs=(im.affine@np.r_[shape-1,1])[:3]+zoom/2
 # Exact face contact is directly observable from the voxel mask.
 faces={}
 for axis in range(3):
  for idx in (0,mask.shape[axis]-1):
   sl=[slice(None)]*3;sl[axis]=idx;faces[f'axis{axis}_index{idx}']=int(mask[tuple(sl)].sum())
 skin=mesh('body__skin'); points=surf_samples(skin,300000,15026)
 edge_dist=np.min(np.minimum(points-mins,maxs-points),axis=1)
 near=edge_dist<=1.5
 regions={'head':points[:,2]>-250,'hand_left':(points[:,0]>160)&(points[:,2]>-1200)&(points[:,2]<-700),
  'hand_right':(points[:,0]<-160)&(points[:,2]>-1200)&(points[:,2]<-700),
  'arm_left':(points[:,0]>100)&(points[:,2]>=-700)&(points[:,2]<-250),
  'arm_right':(points[:,0]<-100)&(points[:,2]>=-700)&(points[:,2]<-250),'foot':points[:,2]<-1500}
 result={'volume_shape_vox':shape.tolist(),'volume_edge_ras_mm':[mins.tolist(),maxs.tolist()],
  'surface_samples':len(points),'surface_samples_near_volume_edge':int(near.sum()),'fraction_sampled_surface_near_edge':float(near.mean()),
  'face_contacts_voxels':faces,'regions':{}}
 for name,sel in regions.items():result['regions'][name]={'surface_samples':int(sel.sum()),'near_edge_samples':int((sel&near).sum()),'fraction_region_surface_near_edge':float((sel&near).sum()/sel.sum()) if sel.any() else 0.0}
 # Associate outliers with scan edges by direct lookup in the original body mask.
 inv=np.linalg.inv(im.affine); f1=EVAL['F1']['structures_with_outside_vertices']; associations={}
 for name,row in f1.items():
  v=np.asarray(mesh(name).vertices); ij=np.rint((np.c_[v,np.ones(len(v))]@inv.T)[:,:3]).astype(int)
  valid=np.all((ij>=0)&(ij<shape),axis=1); inside=np.zeros(len(v),bool); q=ij[valid];inside[valid]=mask[q[:,0],q[:,1],q[:,2]]
  outside=~inside; edge=np.min(np.minimum(v-mins,maxs-v),axis=1)<=3.0
  bins={'head':v[:,2]>-250,'hands':(np.abs(v[:,0])>160)&(v[:,2]>-1200)&(v[:,2]<-700),
   'arms':(np.abs(v[:,0])>100)&(v[:,2]>=-700)&(v[:,2]<-250),'feet':v[:,2]<-1500}
  associations[name]={'outside_vertices_sampled_by_nearest_body_voxel':int(outside.sum()),'all_vertices_within_3mm_volume_edge':int(edge.sum()),
   'outside_vertices_within_3mm_volume_edge':int((outside&edge).sum()),'outside_fraction_near_edge':float((outside&edge).sum()/outside.sum()) if outside.any() else 0,
   'outside_vertices_by_region':{k:int((outside&sel).sum()) for k,sel in bins.items()}}
 result['f1_outlier_association']=associations
 result['f1_association_note']='Outside status here is nearest original body-mask voxel lookup (not filled 3 mm skin grid); use as regional attribution, not replacement F1 score.'
 return result

def f3_depth():
 rows=[r for r in EVAL['F3']['overlap_pairs'] if not r['criterion_both_below_0_02']]; records={r['name']:r for r in MAN['meshes']}; ordered=[r['name'] for r in MAN['meshes'] if r['name']!='body__skin']; index={n:i for i,n in enumerate(ordered)}
 point_cache={}; mesh_cache=OrderedDict(); grid_cache=OrderedDict(); depth_cache=OrderedDict()
 def get_points(n):
  if n not in point_cache:
   m=mesh(n);v=m.voxelized(pitch=2.0,method='subdivide');v.fill(method='holes');pts=np.asarray(v.points,dtype=float)
   if len(pts)>2000:
    rng=np.random.default_rng(15026+index[n]);pts=pts[rng.choice(len(pts),2000,replace=False)]
   point_cache[n]=pts
  return point_cache[n]
 def get_mesh(n):
  if n not in mesh_cache:
   mesh_cache[n]=mesh(n)
   if len(mesh_cache)>6:mesh_cache.popitem(last=False)
  else:mesh_cache.move_to_end(n)
  return mesh_cache[n]
 def get_grid(n):
  if n not in grid_cache:
   v=get_mesh(n).voxelized(pitch=2.0,method='subdivide');v.fill(method='holes');grid_cache[n]=v
   if len(grid_cache)>6:grid_cache.popitem(last=False)
  else:grid_cache.move_to_end(n)
  return grid_cache[n]
 def get_depth(n):
  if n not in depth_cache:
   g=get_grid(n);depth_cache[n]=ndimage.distance_transform_edt(np.asarray(g.matrix))*2.0
   if len(depth_cache)>2:depth_cache.popitem(last=False)
  else:depth_cache.move_to_end(n)
  return depth_cache[n]
 enriched=[];counts={'contact_le_1_5mm':0,'intermediate_1_5_to_3mm':0,'penetration_gt_3mm':0}
 for k,row in enumerate(rows,1):
  a,b=row['a'],row['b'];pa,pb=get_points(a),get_points(b);ga,gb=get_grid(a),get_grid(b)
  def inside(points,g):
   ix=np.asarray(g.points_to_indices(points),int);mat=np.asarray(g.matrix);ok=np.all((ix>=0)&(ix<mat.shape),axis=1);z=np.zeros(len(ix),bool);q=ix[ok];z[ok]=mat[q[:,0],q[:,1],q[:,2]];return z
  ain=inside(pa,gb);bin_=inside(pb,ga)
  da=np.array([]);db=np.array([])
  if ain.any():
   ix=np.asarray(gb.points_to_indices(pa[ain]),int);dt=get_depth(b);da=dt[ix[:,0],ix[:,1],ix[:,2]]
  if bin_.any():
   ix=np.asarray(ga.points_to_indices(pb[bin_]),int);dt=get_depth(a);db=dt[ix[:,0],ix[:,1],ix[:,2]]
  depth=float(max(da.max(initial=0),db.max(initial=0)))
  cls='contact_le_1_5mm' if depth<=1.5 else ('penetration_gt_3mm' if depth>3 else 'intermediate_1_5_to_3mm');counts[cls]+=1
  va=records[a]['volume_mm3']*float(ain.mean());vb=records[b]['volume_mm3']*float(bin_.mean())
  enriched.append({**row,'estimated_overlap_cm3_direction_a_in_b':va/1000,'estimated_overlap_cm3_direction_b_in_a':vb/1000,
   'estimated_overlap_cm3_mean_directional':(va+vb)/2000,'max_sampled_penetration_depth_mm_voxel_edt':depth,'classification':cls,
   'sampled_a_points_inside_b':int(ain.sum()),'sampled_b_points_inside_a':int(bin_.sum())})
  if k%25==0:print('F3 diagnostic',k,'/',len(rows),flush=True)
 return {'method':'2 mm filled-grid membership and up to 2,000 deterministic interior points per structure; estimated volume is directional sampled fraction ? exact mesh volume. Penetration depth is Euclidean distance-transform from interior voxel centers to target-grid boundary, quantized at 2 mm; classify as a voxel-scale estimate, not exact triangle distance.',
  'pair_count':len(rows),'counts_by_max_sampled_depth':counts,
  'top20_by_estimated_overlap_cm3':sorted(enriched,key=lambda r:r['estimated_overlap_cm3_mean_directional'],reverse=True)[:20],
  'top20_by_percent':sorted(enriched,key=lambda r:max(r['a_interior_fraction_inside_b'],r['b_interior_fraction_inside_a']),reverse=True)[:20],
  'all_pairs':enriched}

def ribs():
 # Diagnose segmentation inclusion and nearest transverse-process proxy from meshes.
 out=[]; samples_n=30000
 for side in ('left','right'):
  for i in range(1,13):
   rn=f'total__rib_{side}_{i}'; rp=BASE/f'{rn}.stl'
   if not rp.exists():continue
   rib=mesh(rn); rs=surf_samples(rib,samples_n,15026+i+(0 if side=='left' else 100))
   levels=[i] if i==1 else [i-1,i]
   for lv in levels:
    vn=f'total__vertebrae_t{lv}'; vert=mesh(vn); vs=surf_samples(vert,samples_n,15100+i+lv+(0 if side=='left' else 100))
    center=np.asarray(vert.centroid); dx=np.abs(vs[:,0]-center[0]); cut=np.quantile(dx,.75); proc=vs[dx>=cut]
    d_body=cKDTree(vs).query(rs,k=1,workers=-1)[0].min()
    d_proc=cKDTree(proc).query(rs,k=1,workers=-1)[0].min() if len(proc) else None
    # nearest distance from nominal rib head region to vertebral surface; infer head proxy by closest rib points.
    nearest=cKDTree(vs).query(rs,k=1,workers=-1)[0]; head=rs[nearest<=20]
    out.append({'side':side,'rib':i,'vertebra':f'T{lv}','rib_to_whole_vertebra_surface_mm':float(d_body),
     'rib_to_lateral_process_proxy_mm':float(d_proc) if d_proc is not None else None,'process_proxy_definition':'vertebral surface-sample points in outer quartile of absolute RAS-X distance from mesh centroid',
     'rib_samples_within_5mm_of_vertebra':int((nearest<=5).sum()),'rib_samples_within_10mm':int((nearest<=10).sum()),
     'rib_samples_within_20mm':int((nearest<=20).sum()),'nearest_region_ras_mean':np.mean(head,axis=0).round(2).tolist() if len(head) else None,
     'vertebra_bounds_ras_mm':np.asarray(vert.bounds).round(1).tolist()})
 return {'method':'30,000 deterministic rib and vertebra surface samples; transverse-process proxy uses lateral outer quartile of vertebral surface samples in |RAS-X minus vertebral centroid|.',
  'limitation':'TotalSegmentator vertebrae labels have no separate vertebral-body/transverse-process sublabels; this is a geometric lateral-process proxy, not a semantic segmentation.',
  'comparisons':out}

if __name__=='__main__':
 result={'volume_border_and_f1':body_boundary(),'f3_depth_and_rankings':f3_depth(),'costovertebral':ribs()}
 REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print('wrote',REPORT)


