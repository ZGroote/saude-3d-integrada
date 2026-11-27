import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { Vector3 } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

const raizProjeto = fileURLToPath(new URL('../', import.meta.url));
const caminho = (...partes) => `${raizProjeto}/${partes.join('/')}`;

/** Carrega índice e geometrias locais e cria âncoras FHIR no referencial do atlas indicado. */
export function criarAncorasSeed(atlasNome = 'hra-f', atlasVersao = '1.10-1') {
  const indice = JSON.parse(readFileSync(caminho('atlas', atlasNome, atlasVersao, 'indice.json'), 'utf8'));
  const sistemas = new Map();
  const indicesPorGlb = new Map();
  for (const entry of indice) {
    if (!indicesPorGlb.has(entry.glb)) indicesPorGlb.set(entry.glb, []);
    indicesPorGlb.get(entry.glb).push(entry);
  }

  async function carregarGlb(glb) {
    if (sistemas.has(glb)) return sistemas.get(glb);
    const bytes = readFileSync(caminho('atlas', atlasNome, atlasVersao, glb));
    const ab = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const carregado = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(ab, '');
    carregado.scene.updateMatrixWorld(true);
    const permitidas = new Set((indicesPorGlb.get(glb) ?? []).map((entry) => entry.malha));
    const porMalha = new Map();
    carregado.scene.traverse((obj) => {
      if (!obj.isMesh) return;
      for (let no = obj; no; no = no.parent) {
        const nome = no.userData?.name || no.name;
        if (!permitidas.has(nome)) continue;
        if (!porMalha.has(nome)) porMalha.set(nome, []);
        porMalha.get(nome).push(obj);
        break;
      }
    });
    const sistema = { porMalha, cache: new Map() };
    sistemas.set(glb, sistema);
    return sistema;
  }

  function dadosMalha(entry, sistema) {
    if (!sistema) throw new Error(`GLB ainda não carregado para ${entry.malha}`);
    if (sistema.cache.has(entry.malha)) return sistema.cache.get(entry.malha);
    const objetos = sistema.porMalha.get(entry.malha);
    if (!objetos?.length) throw new Error(`Malha não encontrada no GLB: ${entry.malha}`);
    const partes = [];
    let trianguloBase = 0;
    for (const obj of objetos) {
      const pos = obj.geometry.getAttribute('position');
      const idx = obj.geometry.index;
      const indices = idx
        ? Uint32Array.from({ length: idx.count }, (_, i) => idx.getX(i))
        : Uint32Array.from({ length: pos.count }, (_, i) => i);
      if (obj.matrixWorld.determinant() < 0)
        for (let i = 0; i < indices.length; i += 3) [indices[i + 1], indices[i + 2]] = [indices[i + 2], indices[i + 1]];
      const vertices = new Float64Array(pos.count * 3);
      const v = new Vector3();
      for (let i = 0; i < pos.count; i++) {
        v.set(pos.getX(i), pos.getY(i), pos.getZ(i)).applyMatrix4(obj.matrixWorld);
        vertices.set([v.x, v.y, v.z], i * 3);
      }
      partes.push({ vertices, indices, trianguloBase });
      trianguloBase += indices.length / 3;
    }
    if (entry.triangulos && trianguloBase !== entry.triangulos)
      throw new Error(`Contagem de triângulos divergente em ${entry.malha}: índice=${entry.triangulos}, GLB=${trianguloBase}`);
    const dados = { partes, triangulos: trianguloBase };
    sistema.cache.set(entry.malha, dados);
    return dados;
  }

  function ancora(entry, modo = 'dispersa', sal = 0) {
    const sistema = sistemas.get(entry.glb);
    const dados = dadosMalha(entry, sistema);
    const caixas = [];
    for (const parte of dados.partes) {
      const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
      for (let i = 0; i < parte.vertices.length; i += 3) for (let eixo = 0; eixo < 3; eixo++) {
        min[eixo] = Math.min(min[eixo], parte.vertices[i + eixo]);
        max[eixo] = Math.max(max[eixo], parte.vertices[i + eixo]);
      }
      caixas.push({ min, max });
    }
    const min = [0, 1, 2].map((i) => Math.min(...caixas.map((b) => b.min[i])));
    const max = [0, 1, 2].map((i) => Math.max(...caixas.map((b) => b.max[i])));
    const centro = min.map((x, i) => (x + max[i]) / 2);
    const inicio = modo === 'dispersa' ? (Math.imul(sal + 1, 104729) >>> 0) % dados.triangulos : 0;
    let melhor = null;
    for (const parte of dados.partes) {
      const total = parte.indices.length / 3;
      for (let passo = 0; passo < total; passo++) {
        const local = modo === 'dispersa' ? (inicio + passo) % dados.triangulos - parte.trianguloBase : passo;
        if (local < 0 || local >= total) continue;
        const ids = [parte.indices[local * 3], parte.indices[local * 3 + 1], parte.indices[local * 3 + 2]];
        const pts = ids.map((id) => [parte.vertices[id * 3], parte.vertices[id * 3 + 1], parte.vertices[id * 3 + 2]]);
        const ab = new Vector3(...pts[1]).sub(new Vector3(...pts[0]));
        const ac = new Vector3(...pts[2]).sub(new Vector3(...pts[0]));
        const normal = ab.cross(ac);
        const area2 = normal.length();
        if (area2 < 1e-12) continue;
        normal.multiplyScalar(1 / area2);
        const faceCenter = [0, 1, 2].map((i) => (pts[0][i] + pts[1][i] + pts[2][i]) / 3);
        const score = modo === 'posterior'
          ? (normal.z < -0.15 ? faceCenter[2] : Infinity)
          : modo === 'centro'
            ? faceCenter.reduce((s, x, i) => s + (x - centro[i]) ** 2, 0)
            : 0;
        if (modo === 'posterior' && !Number.isFinite(score)) continue;
        const candidato = { score, ponto: pts[0], normal: normal.toArray(), triangulo: parte.trianguloBase + local };
        if (!melhor || score < melhor.score) melhor = candidato;
        if (modo === 'dispersa') break;
      }
      if (modo === 'dispersa' && melhor) break;
    }
    if (!melhor) throw new Error(`Não achei face válida (${modo}) em ${entry.malha}`);
    return {
      atlas: atlasNome, atlas_versao: atlasVersao, sistema: entry.sistema, estrutura: entry.estrutura,
      malha: entry.malha, posicao_local: melhor.ponto, normal_local: melhor.normal,
      triangulo: melhor.triangulo, baricentricas: [1, 0, 0],
    };
  }

  function lado(entry) {
    return entry.lateralidade === 'left' ? 'esquerdo' : entry.lateralidade === 'right' ? 'direito' : 'nao_se_aplica';
  }

  return { indice, atlas: atlasNome, versao: atlasVersao, sistemas, carregarGlb, dadosMalha, ancora, lado };
}
