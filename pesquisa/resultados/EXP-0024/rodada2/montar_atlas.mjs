// Reconstruct published atlas meshes with the same node selection and world
// transform rule as packages/motor-anatomico/src/pacote.ts::montarSistema.
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Matrix4, Vector3 } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const root = process.cwd();
const outDir = path.join(root, 'pesquisa/resultados/EXP-0024/rodada2');
const definitions = [
  {key:'hra-f', version:'1.10-1', glb:path.join(root,'hra/externo/atlas_extraido/hra-f_esqueletico.glb'), names:['VH_F_ilium_compact_bone_R','VH_F_ilium_compact_bone_L','VH_F_sacrum','VH_F_femur_R','VH_F_femur_L']},
  {key:'bp3d-m', version:'4.0-1', glb:path.join(root,'hra/externo/atlas_extraido/bp3d-m_esqueletico.glb'), names:['FJ3152','FJ3288','FJ3393','FJ3259','FJ3365']},
];
const loader = new GLTFLoader();
const chunks=[]; const meshes=[]; let offset=0;
for (const atlas of definitions) {
  const pub=path.join(root,'web/public/atlas',atlas.key,atlas.version);
  const manifest=JSON.parse(fs.readFileSync(path.join(pub,'manifesto.json'),'utf8'));
  const index=JSON.parse(fs.readFileSync(path.join(pub,'indice.json'),'utf8'));
  if (manifest.atlas!==atlas.key || manifest.versao!==atlas.version || manifest.unidade!=='m') throw new Error(`Manifesto inválido ${atlas.key}`);
  const indexMap=new Map(index.map(x=>[x.malha,x]));
  for (const name of atlas.names) if (!indexMap.has(name)) throw new Error(`Malha ausente no índice: ${name}`);
  const buf=fs.readFileSync(atlas.glb);
  const gltf=await new Promise((resolve,reject)=>loader.parse(buf.buffer.slice(buf.byteOffset,buf.byteOffset+buf.byteLength),'',resolve,reject));
  gltf.scene.updateMatrixWorld(true);
  const pieces=new Map(atlas.names.map(n=>[n,[]]));
  gltf.scene.traverse(obj=>{
    if (!obj.isMesh) return;
    for (let node=obj; node; node=node.parent) {
      const n=node.userData?.name ?? node.name;
      if (pieces.has(n)) { pieces.get(n).push(obj); break; }
    }
  });
  for (const name of atlas.names) {
    const parts=pieces.get(name); if (!parts.length) throw new Error(`GLTF sem nó indexado: ${atlas.key}/${name}`);
    const verts=[]; const faces=[];
    for (const part of parts) {
      const pos=part.geometry.getAttribute('position');
      const base=verts.length/3; const v=new Vector3();
      for(let i=0;i<pos.count;i++) { v.set(pos.getX(i),pos.getY(i),pos.getZ(i)).applyMatrix4(part.matrixWorld); verts.push(v.x,v.y,v.z); }
      const attr=part.geometry.index; const ic=attr?.count??pos.count; const local=[];
      for(let i=0;i<ic;i++) local.push(attr?.getX(i)??i);
      if(part.matrixWorld.determinant()<0) for(let i=0;i<local.length;i+=3) [local[i+1],local[i+2]]=[local[i+2],local[i+1]];
      for(const ix of local) faces.push(base+ix);
    }
    if (faces.length/3 !== indexMap.get(name).triangulos)
      throw new Error(`Triângulos divergem do índice para ${atlas.key}/${name}: ${faces.length/3} != ${indexMap.get(name).triangulos}`);
    const vb=Buffer.from(new Float64Array(verts).buffer); const fb=Buffer.from(new Uint32Array(faces).buffer);
    chunks.push(vb,fb);
    meshes.push({atlas:atlas.key,version:atlas.version,name,structure:indexMap.get(name).estrutura,laterality:indexMap.get(name).lateralidade,
      triangles:faces.length/3,vertices:verts.length/3,vertex_offset:offset,vertex_bytes:vb.length,index_offset:offset+vb.length,index_bytes:fb.length});
    offset+=vb.length+fb.length;
  }
}
fs.writeFileSync(path.join(outDir,'malhas_publicadas.bin'),Buffer.concat(chunks));
fs.writeFileSync(path.join(outDir,'malhas_publicadas.json'),JSON.stringify({rule:'GLTFLoader attributes (including normalized/quantized accessor decoding); exact ancestor match node.userData.name ?? node.name from indice; scene.updateMatrixWorld(true); vertex.applyMatrix4(part.matrixWorld); reverse triangle winding for negative determinant; published metres',meshes},null,2));
console.log(JSON.stringify(meshes.map(({atlas,name,triangles,vertices})=>({atlas,name,triangles,vertices}))));
