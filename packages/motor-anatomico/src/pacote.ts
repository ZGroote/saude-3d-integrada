// Leitura do pacote de atlas (SPEC §5.3).
import { BufferAttribute, BufferGeometry, Group, Mesh, type Material, type Object3D } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { acceleratedRaycast } from 'three-mesh-bvh';
import { criarBVH } from './ancora';
import type { EntradaIndice, Manifesto } from './tipos';

export type Pacote = { manifesto: Manifesto; indice: EntradaIndice[] };
export type Sistema = { grupo: Group; malhas: Map<string, Mesh> };

export const urlDoPacote = (baseUrl: string, atlas: string, versao: string) =>
  `${baseUrl.replace(/\/+$/, '')}/${atlas}/${versao}`;

async function lerJson(url: string, signal?: AbortSignal) {
  const resposta = await fetch(url, { signal });
  if (!resposta.ok) throw new Error(`${url}: HTTP ${resposta.status}`);
  return resposta.json();
}

export async function carregarPacote(
  baseUrl: string,
  atlas: string,
  versao: string,
  signal?: AbortSignal,
): Promise<Pacote> {
  const url = urlDoPacote(baseUrl, atlas, versao);
  const [manifesto, indice] = await Promise.all([
    lerJson(`${url}/manifesto.json`, signal),
    lerJson(`${url}/indice.json`, signal),
  ]);
  // pacote trocado de pasta gravaria âncoras com atlas/versão errados
  if (manifesto?.atlas !== atlas || manifesto?.versao !== versao || !Array.isArray(manifesto.sistemas))
    throw new Error(`manifesto em ${url} não é de ${atlas} ${versao}`);
  if (!Array.isArray(indice)) throw new Error(`indice.json em ${url} não é uma lista`);
  return { manifesto, indice };
}

/**
 * Leva a geometria de um nó para o "espaço da malha" da âncora: metros, nos eixos do atlas.
 * No GLB comprimido as posições são inteiros quantizados e a transformação do nó as devolve a metros.
 * Se a âncora usasse o espaço quantizado, recomprimir o atlas mudaria o significado de posicao_local.
 * Várias primitivas do mesmo nó viram uma só, na ordem do GLB, para `triangulo` ser único.
 */
export function geometriaDaMalha(partes: Mesh[]): BufferGeometry {
  const geometrias = partes.map((parte) => {
    const origem = parte.geometry.getAttribute('position');
    const posicoes = new Float32Array(origem.count * 3);
    for (let i = 0; i < origem.count; i++) posicoes.set([origem.getX(i), origem.getY(i), origem.getZ(i)], i * 3);
    const geometria = new BufferGeometry().setAttribute('position', new BufferAttribute(posicoes, 3));
    const indice = parte.geometry.index;
    const indices = Uint32Array.from({ length: indice?.count ?? origem.count }, (_, i) => indice?.getX(i) ?? i);
    // nó espelhado: inverte a ordem dos vértices para a normal continuar apontando para fora
    if (parte.matrixWorld.determinant() < 0)
      for (let i = 0; i < indices.length; i += 3) [indices[i + 1], indices[i + 2]] = [indices[i + 2]!, indices[i + 1]!];
    return geometria.setIndex(new BufferAttribute(indices, 1)).applyMatrix4(parte.matrixWorld);
  });
  const unica = geometrias.length === 1 ? geometrias[0]! : mergeGeometries(geometrias);
  unica.computeVertexNormals();
  return unica;
}

/** Transforma a cena de um GLB em uma malha por nó do índice, com BVH. */
export function montarSistema(cena: Object3D, porMalha: Map<string, EntradaIndice>, material: Material): Sistema {
  cena.updateMatrixWorld(true);
  const partes = new Map<string, Mesh[]>();
  cena.traverse((objeto) => {
    if (!(objeto instanceof Mesh)) return;
    for (let no: Object3D | null = objeto; no; no = no.parent) {
      const nome: string = no.userData.name ?? no.name;
      if (!porMalha.has(nome)) continue;
      if (!partes.has(nome)) partes.set(nome, []);
      partes.get(nome)!.push(objeto);
      return;
    }
  });
  if (!partes.size) throw new Error('nenhum nó do GLB está no índice');
  const grupo = new Group();
  const malhas = new Map<string, Mesh>();
  for (const [nome, lista] of partes) {
    const geometria = geometriaDaMalha(lista);
    // ponytail: BVH montado na carga, na thread principal; mover para worker se travar no tablet
    geometria.boundsTree = criarBVH(geometria);
    const malha = new Mesh(geometria, material);
    malha.name = nome;
    const { sistema, estrutura } = porMalha.get(nome)!;
    malha.userData = { sistema, estrutura };
    malha.raycast = acceleratedRaycast;
    malhas.set(nome, malha);
    grupo.add(malha);
    for (const parte of lista) parte.geometry.dispose();
  }
  return { grupo, malhas };
}

export async function carregarSistema(url: string, porMalha: Map<string, EntradaIndice>, material: Material) {
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync(url);
  return montarSistema(gltf.scene, porMalha, material);
}

export function descartarSistema({ malhas }: Sistema) {
  for (const malha of malhas.values()) {
    malha.geometry.dispose();
    (malha.material as Material).dispose();
  }
}
