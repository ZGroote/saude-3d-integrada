import { describe, expect, it } from 'vitest';
import { binningCamadas, calcularVista, filtrarMarcadoresNestaEstrutura } from './visual';

describe('calcularVista', () => {
  const centro: [number, number, number] = [1, 2, 3];
  it.each([
    ['anterior', [1, 2, 8], [0, 1, 0]], ['posterior', [1, 2, -2], [0, 1, 0]],
    ['direita', [-4, 2, 3], [0, 1, 0]], ['esquerda', [6, 2, 3], [0, 1, 0]],
    ['superior', [1, 7, 3], [0, 0, 1]], ['inferior', [1, -3, 3], [0, 0, -1]],
  ] as const)('%s posiciona câmera, alvo e up', (vista, posicao, up) => {
    expect(calcularVista(vista, centro, 5)).toEqual({ posicao, alvo: centro, up });
  });
  it('direita fica no lado direito do paciente (−X)', () => {
    const camera = calcularVista('direita', centro, 5).posicao;
    const femurDireito: [number, number, number] = [-1, 2, 3];
    const femurEsquerdo: [number, number, number] = [3, 2, 3];
    const dist = (p: number[]) => Math.hypot(...p.map((v, i) => v - camera[i]!));
    expect(dist(femurDireito)).toBeLessThan(dist(femurEsquerdo));
  });
});

describe('binningCamadas', () => {
  it('ordena do superficial para o profundo e limita a dez faixas', () => {
    const got = binningCamadas(Array.from({ length: 15 }, (_, i) => ({ malha: `m${i}`, profundidade: i })));
    expect(got.total).toBe(10);
    expect(got.porMalha.m0).toBe(0);
    expect(got.porMalha.m14).toBe(9);
    expect(got.porMalha.m1).toBe(0);
  });
  it('sem dados válidos retorna zero camadas', () => {
    expect(binningCamadas([{ malha: 'x', profundidade: Number.NaN }])).toEqual({ total: 0, porMalha: {} });
  });
});

describe('filtrarMarcadoresNestaEstrutura', () => {
  const ms = [
    { id: 'a', ancora: { estrutura: 'FMA1', malha: 'osso-a' } },
    { id: 'b', ancora: { estrutura: 'FMA1', malha: 'osso-b' } },
    { id: 'c', ancora: { estrutura: 'FMA2', malha: 'osso-c' } },
    { id: 'd', ancora: { estrutura: null, malha: 'sem-id' } },
  ];
  it('usa estrutura quando existe', () => {
    expect(filtrarMarcadoresNestaEstrutura(ms, 'FMA1', 'osso-a').map((m) => m.id)).toEqual(['a', 'b']);
  });
  it('usa malha quando a estrutura clicada é nula', () => {
    expect(filtrarMarcadoresNestaEstrutura(ms, null, 'sem-id').map((m) => m.id)).toEqual(['d']);
  });
});
