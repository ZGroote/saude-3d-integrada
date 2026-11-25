// Consultas ao indice.json. Sem three nem React: o servidor (importação FHIR) pode importar só isto.
import type { EntradaIndice } from './tipos';

/**
 * Malha que representa uma estrutura numa âncora sem clique (SPEC §5.4): a de mais triângulos;
 * no empate, o menor nome de malha (comparação de código, sem depender de locale).
 * null = estrutura não existe no índice. Erro = há várias malhas e falta `triangulos`:
 * escolher sem a contagem faria servidor e cliente divergirem.
 */
export function malhaPrincipal(indice: EntradaIndice[], estrutura: string): EntradaIndice | null {
  const todas = indice.filter((e) => e.estrutura === estrutura);
  if (todas.length > 1 && todas.some((e) => e.triangulos == null))
    throw new Error(`indice.json sem "triangulos": não dá para escolher entre as ${todas.length} malhas de ${estrutura}`);
  const [principal] = todas.sort((a, b) => (b.triangulos ?? 0) - (a.triangulos ?? 0) || (a.malha < b.malha ? -1 : 1));
  return principal ?? null;
}
