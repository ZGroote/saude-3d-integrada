import { BufferGeometry, Float32BufferAttribute, Mesh, Raycaster, SphereGeometry, Vector3 } from 'three';
import { acceleratedRaycast } from 'three-mesh-bvh';
import { describe, expect, it } from 'vitest';
import { ancoraDeIntersecao, candidatas, criarBVH, posicionarMarcador, reprojetar, situarMarcador } from './ancora';
import { malhaPrincipal } from './indice';
import type { Ancora, EntradaIndice, Vetor3 } from './tipos';

const contexto = { atlas: 'bp3d-m', atlas_versao: '4.0-1', sistema: 'esqueletico', malha: 'FJ1', estrutura: 'FMA24475' };
const triangulo = (z = 0) =>
  new BufferGeometry().setAttribute('position', new Float32BufferAttribute([0, 0, z, 1, 0, z, 0, 1, z], 3));
const perto = (a: number[], b: number[], casas = 5) => a.forEach((v, i) => expect(v).toBeCloseTo(b[i]!, casas));
const ancora = (extra: Partial<Ancora> = {}): Ancora => ({
  ...contexto, posicao_local: [0.25, 0.5, 0.3], normal_local: [0, 0, 1], triangulo: 0, baricentricas: [1, 0, 0], ...extra,
});
const estrutural = (extra: Partial<Ancora> = {}) =>
  ancora({ posicao_local: null, normal_local: null, triangulo: null, baricentricas: null, ...extra });
const entradas = (...lista: [string, string | null, number?][]) =>
  lista.map(([malha, estrutura, triangulos]) => ({ malha, estrutura, triangulos })) as unknown as EntradaIndice[];

function atirar(malha: Mesh, origem: Vector3, direcao: Vector3) {
  malha.updateMatrixWorld(true);
  const [hit] = new Raycaster(origem, direcao.normalize()).intersectObject(malha);
  if (!hit) throw new Error('raio não acertou');
  return hit;
}

describe('ancoraDeIntersecao', () => {
  it('devolve a âncora no espaço da malha, não no do mundo', () => {
    const malha = new Mesh(triangulo());
    malha.position.set(10, 20, 30);
    malha.scale.setScalar(2);
    const a = ancoraDeIntersecao(atirar(malha, new Vector3(10.5, 21, 40), new Vector3(0, 0, -1)), contexto);
    expect(a).toMatchObject({ ...contexto, triangulo: 0 });
    perto(a.posicao_local, [0.25, 0.5, 0]);
    perto(a.normal_local, [0, 0, 1]);
    perto(a.baricentricas, [0.25, 0.25, 0.5]);
    expect(JSON.parse(JSON.stringify(a))).toEqual(a); // vai para uma coluna jsonb
  });

  it('com BVH, o triângulo continua sendo o da geometria original', () => {
    const geometria = new SphereGeometry(1, 32, 24);
    const indiceOriginal = Array.from(geometria.index!.array);
    const lenta = new Mesh(geometria.clone());
    const rapida = new Mesh(geometria);
    geometria.boundsTree = criarBVH(geometria);
    rapida.raycast = acceleratedRaycast;
    expect(Array.from(geometria.index!.array)).toEqual(indiceOriginal);
    for (const d of [new Vector3(1, 0.3, 0.2), new Vector3(-0.2, -1, 0.4), new Vector3(0.1, 0.5, -1)]) {
      const origem = d.clone().setLength(5);
      const a = ancoraDeIntersecao(atirar(rapida, origem, d.clone().negate()), contexto);
      const b = ancoraDeIntersecao(atirar(lenta, origem, d.clone().negate()), contexto);
      expect(a.triangulo).toBe(b.triangulo);
      perto(a.posicao_local, b.posicao_local);
    }
  });

  it('recusa interseção sem triângulo', () => {
    expect(() => ancoraDeIntersecao({ object: new Mesh(triangulo()), point: new Vector3() }, contexto)).toThrow();
  });
});

describe('reprojetar', () => {
  it('leva ao ponto mais próximo e não altera a âncora original', () => {
    const original = ancora();
    const copia = structuredClone(original);
    const p = reprojetar(original, triangulo(0.1));
    perto(p.posicao_local, [0.25, 0.5, 0.1]);
    perto(p.baricentricas, [0.25, 0.25, 0.5]);
    expect(p.distancia).toBeCloseTo(0.2);
    expect(original).toEqual(copia);
  });

  it('prende à borda quando o ponto cai fora da malha', () => {
    perto(reprojetar(ancora({ posicao_local: [-1, -1, 0] }), triangulo()).posicao_local, [0, 0, 0]);
  });

  it('numa malha refeita, acha o triângulo novo e bate com as baricêntricas', () => {
    const geometria = new SphereGeometry(1, 40, 30);
    const posicao_local: Vetor3 = [0.8, 0.7, 0.6];
    const p = reprojetar(ancora({ posicao_local }), geometria);
    expect(new Vector3(...p.posicao_local).length()).toBeCloseTo(1, 2);
    const canto = (i: number) =>
      new Vector3().fromBufferAttribute(geometria.getAttribute('position'), geometria.index!.getX(p.triangulo * 3 + i));
    const refeito = new Vector3();
    p.baricentricas.forEach((peso, i) => refeito.addScaledVector(canto(i), peso));
    perto(refeito.toArray(), p.posicao_local);
  });
});

describe('marcadores', () => {
  it('mesma versão usa a posição gravada, sem precisar de geometria', () => {
    expect(posicionarMarcador(ancora(), 'bp3d-m', '4.0-1', [])).toEqual([0.25, 0.5, 0.3]);
  });
  it('outro atlas nunca é desenhado', () => {
    expect(posicionarMarcador(ancora(), 'hra-f', '4.0-1', [triangulo()])).toBeNull();
  });
  it('outra versão reprojeta na geometria candidata mais próxima, ou espera por ela', () => {
    expect(posicionarMarcador(ancora(), 'bp3d-m', '4.0-2', [])).toBeNull();
    perto(posicionarMarcador(ancora(), 'bp3d-m', '4.0-2', [triangulo(-1), triangulo(0.2)])!, [0.25, 0.5, 0.2]);
  });
  it('procura pela estrutura mesmo que a malha tenha mudado de nome', () => {
    const indice = entradas(['FJ1', 'FMA1'], ['NOVA', 'FMA24475']);
    expect(candidatas(ancora(), indice).map((e) => e.malha)).toEqual(['NOVA']);
    expect(candidatas(ancora({ estrutura: null }), indice).map((e) => e.malha)).toEqual(['FJ1']);
  });
});

describe('âncora só estrutural', () => {
  it('vai para o centro da caixa da malha, em qualquer versão', () => {
    for (const versao of ['4.0-1', '4.0-2'])
      perto(posicionarMarcador(estrutural(), 'bp3d-m', versao, [triangulo(0.2)])!, [0.5, 0.5, 0.2]);
    expect(posicionarMarcador(estrutural(), 'bp3d-m', '4.0-1', [])).toBeNull(); // geometria não carregada
    expect(posicionarMarcador(estrutural(), 'hra-f', '4.0-1', [triangulo()])).toBeNull();
  });
  it('usa a malha indicada, mesmo não sendo a maior', () => {
    const indice = entradas(['FJ1', 'FMA24475', 10], ['FJ2', 'FMA24475', 99]);
    expect(candidatas(estrutural(), indice).map((e) => e.malha)).toEqual(['FJ1']);
  });
  it('se a malha sumiu na versão nova, usa a principal da estrutura', () => {
    const indice = entradas(['A', 'FMA24475', 10], ['B', 'FMA24475', 99]);
    expect(candidatas(estrutural(), indice).map((e) => e.malha)).toEqual(['B']);
    expect(candidatas(estrutural({ estrutura: null }), indice)).toEqual([]);
  });
  it('malha sem ID é achada pelo nome', () => {
    const indice = entradas(['FJ1', null], ['FJ2', null]);
    expect(candidatas(estrutural({ estrutura: null }), indice).map((e) => e.malha)).toEqual(['FJ1']);
  });
  it('não tem o que reprojetar', () => {
    expect(() => reprojetar(estrutural(), triangulo())).toThrow(/estrutural/);
  });
});

describe('situarMarcador', () => {
  const [a, b] = entradas(['A', 'FMA24475'], ['B', 'FMA24475']) as [EntradaIndice, EntradaIndice];
  const situar = (
    alvo: Ancora, lista: EntradaIndice[] | undefined, geometrias: Record<string, BufferGeometry | null> = {},
  ) => situarMarcador(alvo, 'bp3d-m', '4.0-1', lista, (e) => geometrias[e.malha]);

  it('ponto desta versão não espera nada; outro atlas nunca tem posição', () => {
    expect(situar(ancora(), undefined)).toEqual([0.25, 0.5, 0.3]);
    expect(situar(ancora({ atlas: 'hra-f' }), undefined)).toBeNull();
  });
  it('espera o índice e todas as malhas candidatas', () => {
    const antiga = ancora({ atlas_versao: '4.0-0' });
    expect(situar(antiga, undefined)).toBe('pendente');
    expect(situar(antiga, [a, b], { A: triangulo(0.2) })).toBe('pendente');
    perto(situar(antiga, [a, b], { A: triangulo(-1), B: triangulo(0.2) }) as number[], [0.25, 0.5, 0.2]);
  });
  it('usa as candidatas que vieram se outra falhou', () => {
    perto(situar(estrutural(), [a, b], { A: null, B: triangulo() }) as number[], [0.5, 0.5, 0]);
  });
  it('sem candidata, ou com todas falhadas, não tem posição', () => {
    expect(situar(estrutural(), [])).toBeNull();
    expect(situar(estrutural(), [a], { A: null })).toBeNull();
  });
});

describe('malhaPrincipal', () => {
  const indice = entradas(['FJ9', 'FMA1', 5], ['FJ3', 'FMA1', 8], ['FJ2', 'FMA1', 8], ['FJ0', 'FMA2', 100]);
  it('escolhe a de mais triângulos; no empate, o menor nome, em qualquer ordem', () => {
    expect(malhaPrincipal(indice, 'FMA1')?.malha).toBe('FJ2');
    expect(malhaPrincipal([...indice].reverse(), 'FMA1')?.malha).toBe('FJ2');
  });
  it('não reordena o índice recebido', () => {
    const copia = structuredClone(indice);
    malhaPrincipal(indice, 'FMA1');
    expect(indice).toEqual(copia);
  });
  it('com uma malha só, dispensa a contagem', () => {
    expect(malhaPrincipal(entradas(['FJ7', 'FMA7']), 'FMA7')?.malha).toBe('FJ7');
  });
  it('sem contagem para desempatar, falha em vez de escolher no chute', () => {
    expect(() => malhaPrincipal(entradas(['A', 'FMA1', 3], ['B', 'FMA1']), 'FMA1')).toThrow(/triangulos/);
  });
  it('estrutura inexistente dá null', () => {
    expect(malhaPrincipal(indice, 'FMA404')).toBeNull();
  });
});
