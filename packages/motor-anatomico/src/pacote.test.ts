import { existsSync, readFileSync } from 'node:fs';
import {
  Box3, BufferAttribute, BufferGeometry, DoubleSide, Group, Mesh, MeshBasicMaterial, Raycaster, Vector3,
} from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { describe, expect, it } from 'vitest';
import { ancoraDeIntersecao, reprojetar } from './ancora';
import { malhaPrincipal } from './indice';
import { geometriaDaMalha, montarSistema, urlDoPacote } from './pacote';
import type { EntradaIndice } from './tipos';
import { distanciaDeEnquadramento } from './visual';

const quantizada = () => {
  const g = new BufferGeometry();
  g.setAttribute('position', new BufferAttribute(new Int16Array([-32767, -32767, 0, 32767, -32767, 0, -32767, 32767, 0]), 3, true));
  return new Mesh(g);
};

describe('geometriaDaMalha', () => {
  it('converte posições quantizadas para metros usando a transformação do nó', () => {
    const parte = quantizada();
    parte.position.set(0.5, 1, 0);
    parte.scale.setScalar(2);
    parte.updateMatrixWorld(true);
    const p = geometriaDaMalha([parte]).getAttribute('position');
    expect([p.getX(0), p.getY(0), p.getX(1), p.getY(2)]).toEqual([-1.5, -1, 2.5, 3]); // fora de [-1, 1]: não estourou
  });

  it('junta as primitivas de um nó numa geometria só, na ordem', () => {
    const [a, b] = [quantizada(), quantizada()];
    b.position.z = 1;
    b.updateMatrixWorld(true);
    const g = geometriaDaMalha([a, b]);
    expect(g.index!.count).toBe(6);
    expect(g.getAttribute('position').getZ(g.index!.getX(3))).toBe(1);
  });

  it('nó espelhado continua com a normal para fora', () => {
    const parte = quantizada();
    parte.scale.x = -1;
    parte.updateMatrixWorld(true);
    expect(geometriaDaMalha([parte]).getAttribute('normal').getZ(0)).toBeCloseTo(1);
  });
});

it('monta a URL do pacote', () => {
  expect(urlDoPacote('', 'bp3d-m', '4.0-1')).toBe('/bp3d-m/4.0-1');
  expect(urlDoPacote('/atlas/', 'bp3d-m', '4.0-1')).toBe('/atlas/bp3d-m/4.0-1');
});

it('enquadramento em retrato: a caixa ocupa 90% da altura', () => {
  const caixa = new Box3(new Vector3(-0.3, -0.9, -0.15), new Vector3(0.3, 0.9, 0.15));
  const d = distanciaDeEnquadramento(caixa, 35, 0.52);
  expect(1.8 / (2 * d * Math.tan((17.5 * Math.PI) / 180))).toBeCloseTo(0.9);
  expect(distanciaDeEnquadramento(caixa, 35, 1.6)).toBeGreaterThan(2.5);
});

// atlas real: gerado por bodyparts3d/publicar_atlas.py e fora do git
const pasta = new URL('../../../atlas/bp3d-m/4.0-1/', import.meta.url);

describe.skipIf(!existsSync(pasta))('atlas bp3d-m 4.0-1 real', () => {
  it('um raio no fêmur esquerdo devolve FMA24475', async () => {
    const indice: EntradaIndice[] = JSON.parse(readFileSync(new URL('indice.json', pasta), 'utf8'));
    const porMalha = new Map(indice.filter((e) => e.glb === 'esqueletico.glb').map((e) => [e.malha, e]));
    const bytes = readFileSync(new URL('esqueletico.glb', pasta));
    const gltf = await new GLTFLoader()
      .setMeshoptDecoder(MeshoptDecoder)
      .parseAsync(new Uint8Array(bytes).buffer, '');
    const { grupo, malhas } = montarSistema(gltf.scene, porMalha, new MeshBasicMaterial({ side: DoubleSide }));
    expect(malhas.size).toBe(porMalha.size);

    const entrada = indice.find((e) => e.estrutura === 'FMA24475')!;
    const femur = malhas.get(entrada.malha)!;
    const caixa = new Box3().setFromObject(femur);
    expect(caixa.max.y - caixa.min.y).toBeGreaterThan(0.35); // metros
    expect(caixa.getCenter(new Vector3()).x).toBeGreaterThan(0); // +x = esquerda do paciente

    // de frente, no meio da diáfise
    const alvo = caixa.getCenter(new Vector3());
    let hit;
    for (let x = caixa.min.x; !hit && x <= caixa.max.x; x += 0.005) {
      const [primeiro] = new Raycaster(new Vector3(x, alvo.y, 2), new Vector3(0, 0, -1)).intersectObject(grupo);
      if (primeiro?.object === femur) hit = primeiro;
    }
    expect(hit).toBeDefined();
    const a = ancoraDeIntersecao(hit!, {
      atlas: 'bp3d-m', atlas_versao: '4.0-1', malha: hit!.object.name,
      sistema: hit!.object.userData.sistema, estrutura: hit!.object.userData.estrutura,
    });
    expect(a).toMatchObject({ sistema: 'esqueletico', estrutura: 'FMA24475' });
    // malhaPrincipal depende disto: contagem do índice = contagem da geometria
    const erradas = [...malhas].filter(([nome, m]) => porMalha.get(nome)!.triangulos !== m.geometry.index!.count / 3);
    expect(erradas.map(([nome]) => nome)).toEqual([]);
    expect(malhaPrincipal(indice, 'FMA24475')?.malha).toBe(entrada.malha);
    expect(a.triangulo).toBeLessThan(femur.geometry.index!.count / 3);
    expect(a.baricentricas.reduce((s, v) => s + v)).toBeCloseTo(1);
    expect(a.normal_local[2]).toBeGreaterThan(0); // superfície voltada para quem olha
    const volta = reprojetar(a, femur.geometry);
    expect(volta.distancia).toBeLessThan(1e-6);
    expect(grupo).toBeInstanceOf(Group);
  }, 60_000);
});
