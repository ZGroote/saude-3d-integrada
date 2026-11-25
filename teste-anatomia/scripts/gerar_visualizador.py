"""Gera visualizador.html autossuficiente (GLBs embutidos), que abre com dois cliques, sem servidor.

Uso: python gerar_visualizador.py <pasta_modelos> <arquivo_html>
"""
import base64
import json
import sys
from pathlib import Path

CAMADAS = [("ossos", "Ossos"), ("musculos", "Músculos"), ("coracao", "Coração"), ("vasos", "Vasos"), ("orgaos", "Órgãos")]

HTML = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Teste anatomia 3D</title>
<style>
 :root{--bg:#f4f2ee;--fg:#1d1d1b;--painel:#fffffff0;--borda:#d8d4cc}
 @media (prefers-color-scheme:dark){:root{--bg:#16171a;--fg:#ecebe8;--painel:#22242af0;--borda:#3a3d44}}
 html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);font:14px system-ui,sans-serif;overflow:hidden}
 #painel{position:fixed;top:16px;left:16px;background:var(--painel);border:1px solid var(--borda);border-radius:10px;padding:12px 14px;max-width:calc(100vw - 64px)}
 #painel h1{font-size:15px;margin:0 0 8px} label{display:block;margin:4px 0;cursor:pointer}
 #info{margin-top:10px;font-weight:600;min-height:1.2em} small{opacity:.7;display:block;margin-top:8px;max-width:260px}
</style>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
</head><body>
<div id="painel"><h1>Camadas</h1><div id="camadas"></div><div id="info">Clique numa estrutura</div>
<small>Dados: TotalSegmentator (CC BY 4.0), caso s1371. Teste interno.</small></div>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const MODELOS = __MODELOS__, CAMADAS = __CAMADAS__;
const CORES = {ossos: 0xe9e0c8, musculos: 0xbe463c, coracao: 0xc81e2d, vasos: 0x3c5ac8, orgaos: 0xd29678};
const renderer = new THREE.WebGLRenderer({antialias:true, alpha:true, preserveDrawingBuffer:true});
renderer.setPixelRatio(devicePixelRatio); renderer.setSize(innerWidth, innerHeight); document.body.appendChild(renderer.domElement);
const cena = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(35, innerWidth/innerHeight, 0.01, 20); cam.position.set(0, 0, 3.2);
const ctl = new OrbitControls(cam, renderer.domElement); ctl.enableDamping = true;
cena.add(new THREE.HemisphereLight(0xffffff, 0x444444, 2.2));
const sol = new THREE.DirectionalLight(0xffffff, 1.6); sol.position.set(1, 2, 3); cena.add(sol);
const grupos = {}, loader = new GLTFLoader(), caixa = document.getElementById('camadas');
for (const [id, rotulo] of CAMADAS) {
  if (!MODELOS[id]) continue;
  const gltf = await loader.loadAsync('data:model/gltf-binary;base64,' + MODELOS[id]);
  const material = new THREE.MeshStandardMaterial({color: CORES[id], roughness: .55, metalness: 0});
  gltf.scene.traverse(o => { if (o.isMesh) {
    o.geometry.deleteAttribute('color');
    if (!o.geometry.getAttribute('normal')) o.geometry.computeVertexNormals();
    o.material = material;
    o.userData.camada = rotulo; } });
  grupos[id] = gltf.scene; cena.add(gltf.scene);
  const l = document.createElement('label');
  l.innerHTML = `<input type="checkbox" checked> ${rotulo}`;
  l.firstChild.onchange = e => { gltf.scene.visible = e.target.checked; };
  caixa.appendChild(l);
}
const ray = new THREE.Raycaster(), info = document.getElementById('info');
renderer.domElement.addEventListener('pointerup', e => {
  ray.setFromCamera(new THREE.Vector2(e.clientX/innerWidth*2-1, -e.clientY/innerHeight*2+1), cam);
  const hit = ray.intersectObjects(Object.values(grupos).filter(g => g.visible), true)[0];
  info.textContent = hit ? `${hit.object.name} · ${hit.object.userData.camada}` : 'Clique numa estrutura';
});
addEventListener('resize', () => { cam.aspect = innerWidth/innerHeight; cam.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });
renderer.setAnimationLoop(() => { ctl.update(); renderer.render(cena, cam); });
document.body.dataset.pronto = '1';
</script></body></html>"""


def main():
    pasta, destino = Path(sys.argv[1]), Path(sys.argv[2])
    modelos = {c: base64.b64encode((pasta / f"{c}.glb").read_bytes()).decode()
               for c, _ in CAMADAS if (pasta / f"{c}.glb").exists()}
    html = HTML.replace("__MODELOS__", json.dumps(modelos)).replace("__CAMADAS__", json.dumps(CAMADAS, ensure_ascii=False))
    destino.write_text(html, encoding="utf-8")
    print(destino, round(destino.stat().st_size / 1e6, 1), "MB")


if __name__ == "__main__":
    main()
