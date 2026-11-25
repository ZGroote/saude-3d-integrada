// Cores e enquadramento, vindos de bodyparts3d/visualizador.html.
import { MathUtils, Sphere, Vector3, type Box3 } from 'three';

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
