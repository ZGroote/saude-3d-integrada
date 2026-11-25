// Funções puras de âncora: nada de React, DOM ou rede.
import { Box3, BufferAttribute, Mesh, Triangle, Vector3, type BufferGeometry, type Intersection } from 'three';
import { MeshBVH } from 'three-mesh-bvh';
import { malhaPrincipal } from './indice';
import type { Ancora, EntradaIndice, Vetor3 } from './tipos';

/** Parte da âncora que vem da geometria (um clique sempre a preenche). */
export type Projecao = { posicao_local: Vetor3; normal_local: Vetor3; triangulo: number; baricentricas: Vetor3 };

/**
 * BVH sempre "indirect": o modo padrão reordena o índice da geometria, e aí `triangulo`
 * deixaria de ser o triângulo do GLB.
 */
export const criarBVH = (geometria: BufferGeometry) => new MeshBVH(geometria, { indirect: true });

function projecao(geometria: BufferGeometry, triangulo: number, ponto: Vector3): Projecao {
  const posicao = geometria.getAttribute('position');
  const [a, b, c] = [0, 1, 2].map((canto) => {
    const i = triangulo * 3 + canto;
    return new Vector3().fromBufferAttribute(posicao, geometria.index ? geometria.index.getX(i) : i);
  }) as [Vector3, Vector3, Vector3];
  const face = new Triangle(a, b, c);
  const baricentricas = face.getBarycoord(ponto, new Vector3());
  if (!baricentricas) throw new Error(`triângulo ${triangulo} degenerado`);
  return {
    posicao_local: ponto.toArray() as Vetor3,
    // normal geométrica (pela ordem dos vértices): não depende das normais suavizadas do desenho
    normal_local: face.getNormal(new Vector3()).toArray() as Vetor3,
    triangulo,
    baricentricas: baricentricas.toArray() as Vetor3,
  };
}

export function ancoraDeIntersecao(
  intersecao: Pick<Intersection, 'object' | 'point' | 'faceIndex'>,
  contexto: Pick<Ancora, 'atlas' | 'atlas_versao' | 'sistema' | 'estrutura' | 'malha'>,
): Ancora & Projecao {
  const { object, point, faceIndex } = intersecao;
  if (!(object instanceof Mesh) || faceIndex == null) throw new Error('interseção sem malha ou sem triângulo');
  const local = object.worldToLocal(point.clone());
  const { atlas, atlas_versao, sistema, estrutura, malha } = contexto;
  return { atlas, atlas_versao, sistema, estrutura, malha, ...projecao(object.geometry, faceIndex, local) };
}

/** Ponto da geometria mais próximo de `posicao_local`. Não altera a âncora recebida. */
export function reprojetar(ancora: Ancora, geometriaNova: BufferGeometry): Projecao & { distancia: number } {
  if (!ancora.posicao_local) throw new Error('âncora só estrutural não tem ponto para reprojetar');
  const bvh = geometriaNova.boundsTree instanceof MeshBVH ? geometriaNova.boundsTree : criarBVH(geometriaNova);
  const perto = bvh.closestPointToPoint(new Vector3(...ancora.posicao_local));
  if (!perto) throw new Error('geometria vazia');
  return { ...projecao(geometriaNova, perto.faceIndex, perto.point), distancia: perto.distance };
}

export function centroDaMalha(geometria: BufferGeometry): Vetor3 {
  const posicao = geometria.getAttribute('position') as BufferAttribute;
  return new Box3().setFromBufferAttribute(posicao).getCenter(new Vector3()).toArray() as Vetor3;
}

/** Entradas do índice cuja geometria é necessária para desenhar a âncora nesta versão do atlas. */
export function candidatas(ancora: Ancora, indice: EntradaIndice[]): EntradaIndice[] {
  const { estrutura, malha } = ancora;
  if (ancora.posicao_local)
    // reprojeção: procura pela estrutura (permanente); o nome da malha só vale sem estrutura
    return indice.filter((e) => (estrutura ? e.estrutura === estrutura : e.malha === malha));
  // só estrutural: a malha indicada; se ela mudou de nome na versão nova, a principal da estrutura
  const indicada = indice.find((e) => e.malha === malha && e.estrutura === estrutura);
  if (indicada) return [indicada];
  const principal = estrutura ? malhaPrincipal(indice, estrutura) : null;
  return principal ? [principal] : [];
}

/** Ponto gravado nesta mesma versão se desenha sozinho; o resto depende da malha carregada. */
export const precisaDeGeometria = (ancora: Ancora, versao: string) =>
  !ancora.posicao_local || ancora.atlas_versao !== versao;

/**
 * Estado de um marcador enquanto os sistemas chegam. `entradas` são as de `candidatas` (undefined = índice
 * ainda não chegou); `obter` devolve a geometria, undefined (carregando) ou null (nunca virá).
 * Espera todas as candidatas antes de posicionar, para o marcador não pular de lugar.
 */
export function situarMarcador(
  ancora: Ancora,
  atlas: string,
  versao: string,
  entradas: EntradaIndice[] | undefined,
  obter: (entrada: EntradaIndice) => BufferGeometry | null | undefined,
): Vetor3 | 'pendente' | null {
  if (ancora.atlas !== atlas || !precisaDeGeometria(ancora, versao))
    return posicionarMarcador(ancora, atlas, versao, []);
  if (!entradas) return 'pendente';
  const geometrias = entradas.map(obter);
  if (geometrias.includes(undefined)) return 'pendente';
  return posicionarMarcador(ancora, atlas, versao, geometrias.filter((g) => g != null));
}

/**
 * Onde desenhar um marcador. null = não desenhar: outro atlas (atlas nunca são alinhados entre si)
 * ou a geometria necessária ainda não foi carregada.
 * `geometrias` são as das entradas devolvidas por `candidatas`.
 */
export function posicionarMarcador(
  ancora: Ancora,
  atlas: string,
  versao: string,
  geometrias: BufferGeometry[],
): Vetor3 | null {
  if (ancora.atlas !== atlas) return null;
  if (!ancora.posicao_local) return geometrias[0] ? centroDaMalha(geometrias[0]) : null;
  if (ancora.atlas_versao === versao) return ancora.posicao_local;
  const [melhor] = geometrias.map((g) => reprojetar(ancora, g)).sort((a, b) => a.distancia - b.distancia);
  return melhor?.posicao_local ?? null;
}
