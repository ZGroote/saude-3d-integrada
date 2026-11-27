// Cores e enquadramento, vindos de bodyparts3d/visualizador.html.
import { MathUtils, Sphere, Vector3, type Box3 } from 'three';
import type { Ancora, NomeVista, Vetor3 } from './tipos';

export const CORES_SISTEMA: Record<string, string> = {
  esqueletico: '#e9e0c8', articular: '#9fc4c9', muscular: '#b5524a', fascia: '#cfc3b0', cardiaco: '#9e1b32',
  arterial: '#e0262b', venoso: '#2f5bd0', nervoso: '#f2cc39', respiratorio: '#7fb8d8', digestorio: '#d98b4a',
  urogenital: '#9a6fb0', endocrino: '#4fa96b', sensorial: '#3fb5a5', tegumentar: '#e3b095', linfatico: '#b7d65a',
};
export const COR_PADRAO = '#999999';

/** Distância da câmera, olhando de frente, para a caixa caber na tela. */
export function distanciaDeEnquadramento(caixa: Box3, fovVertical: number, aspecto: number): number {
  const tangente = Math.tan(MathUtils.degToRad(fovVertical / 2));
  if (aspecto < 1) {
    // retrato: a esfera deixaria o corpo pequeno; usa a caixa, a ~90% da altura (ou 95% da largura)
    const t = caixa.getSize(new Vector3());
    return Math.max(t.y / 0.9, t.x / (0.95 * aspecto)) / (2 * tangente);
  }
  return caixa.getBoundingSphere(new Sphere()).radius / Math.sin(Math.atan(tangente));
}

/** Posição, alvo e orientação de câmera por vista, nos eixos do atlas. */
export function calcularVista(vista: NomeVista, centro: Vetor3, distancia: number): {
  posicao: Vetor3; alvo: Vetor3; up: Vetor3;
} {
  const direcoes: Record<NomeVista, Vetor3> = {
    anterior: [0, 0, 1], posterior: [0, 0, -1], direita: [-1, 0, 0],
    esquerda: [1, 0, 0], superior: [0, 1, 0], inferior: [0, -1, 0],
  };
  const [dx, dy, dz] = direcoes[vista];
  const up: Vetor3 = vista === 'superior' ? [0, 0, 1] : vista === 'inferior' ? [0, 0, -1] : [0, 1, 0];
  return {
    posicao: [centro[0] + dx * distancia, centro[1] + dy * distancia, centro[2] + dz * distancia],
    alvo: [...centro],
    up,
  };
}

export type ProfundidadeMalha = { malha: string; profundidade: number };
export type CamadasMalhas = { total: number; porMalha: Record<string, number> };

/** Até dez faixas por quantis; índice zero é a camada mais superficial. */
export function binningCamadas(profundidades: ProfundidadeMalha[]): CamadasMalhas {
  const validas = profundidades.filter((p) => Number.isFinite(p.profundidade));
  if (!validas.length) return { total: 0, porMalha: {} };
  const ordenadas = [...validas].sort((a, b) => a.profundidade - b.profundidade || a.malha.localeCompare(b.malha));
  const total = Math.min(10, ordenadas.length);
  const porMalha: Record<string, number> = {};
  ordenadas.forEach(({ malha }, i) => { porMalha[malha] = Math.min(total - 1, Math.floor(i * total / ordenadas.length)); });
  return { total, porMalha };
}

/** Marcadores com mesmo ID estrutural; sem ID, a malha é a chave estável. */
export function filtrarMarcadoresNestaEstrutura<T extends { ancora: Pick<Ancora, 'estrutura' | 'malha'> }>(
  marcadores: T[], estrutura: string | null, malha: string,
): T[] {
  return marcadores.filter((m) => estrutura !== null
    ? m.ancora.estrutura === estrutura
    : m.ancora.estrutura === null && m.ancora.malha === malha);
}
