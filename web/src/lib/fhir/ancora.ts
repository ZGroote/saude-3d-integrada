// bodySite SNOMED → âncora estrutural (SPEC §9). Funções puras: usadas só no servidor.
import { malhaPrincipal } from "@saude3d/motor-anatomico/indice";
import type { Ancora, EntradaIndice } from "@saude3d/motor-anatomico";

/** Linha de `bodysite_estrutura` (supabase/migrations/0005). */
export type Mapeamento = {
  snomed: string;
  estrutura_fma: string | null;
  estrutura_uberon: string | null;
  /** desempata quando o mesmo ID cobre os dois lados (rim, mama no hra-f) */
  lado: "direito" | "esquerdo" | null;
};
export type AtlasDeImportacao = { atlas: "bp3d-m" | "hra-f"; versao: string; coluna: "estrutura_fma" | "estrutura_uberon" };

export const ATLAS_DO_SEXO: Record<"feminino" | "masculino" | "indeterminado", AtlasDeImportacao | null> = {
  feminino: { atlas: "hra-f", versao: "1.10-1", coluna: "estrutura_uberon" },
  masculino: { atlas: "bp3d-m", versao: "4.0-1", coluna: "estrutura_fma" },
  indeterminado: null,
};

const LATERALIDADE = { direito: "right", esquerdo: "left" } as const;

/** Malha que representa estas entradas de uma mesma estrutura: `malhaPrincipal` (sem ID, só há a própria malha). */
export function entradaPrincipal(entradas: EntradaIndice[]): EntradaIndice | null {
  const [primeira] = entradas;
  return primeira?.estrutura ? malhaPrincipal(entradas, primeira.estrutura) : primeira ?? null;
}

/** Âncora só estrutural: o motor desenha o marcador no centro da caixa da malha (SPEC §5.4). */
export function ancoraNaEntrada(entrada: EntradaIndice, { atlas, versao }: { atlas: string; versao: string }): Ancora {
  return {
    atlas, atlas_versao: versao, sistema: entrada.sistema, estrutura: entrada.estrutura, malha: entrada.malha,
    posicao_local: null, normal_local: null, triangulo: null, baricentricas: null,
  };
}

/**
 * Âncora no centro da estrutura mapeada, ou null quando não há certeza: nunca adivinha. Entre as malhas da
 * estrutura (do lado pedido) vale `malhaPrincipal`; sem lado, só se todas forem do mesmo lado.
 */
export function ancoraEstrutural(mapeamento: Mapeamento, atlas: AtlasDeImportacao, indice: EntradaIndice[]): Ancora | null {
  const id = mapeamento[atlas.coluna]?.trim();
  if (!id) return null;
  // o bp3d-m escreve FMA24475; o hra-f, FMA:24475
  const formas = id.startsWith("FMA") ? [id.replace(":", ""), id.replace(/^FMA:?/, "FMA:")] : [id];
  let candidatas = indice.filter((e) => e.estrutura && formas.includes(e.estrutura));
  const { lado } = mapeamento;
  if (lado) candidatas = candidatas.filter((e) => e.lateralidade === LATERALIDADE[lado]);
  else if (new Set(candidatas.map((e) => e.lateralidade)).size > 1) return null;
  const entrada = entradaPrincipal(candidatas);
  return entrada && ancoraNaEntrada(entrada, atlas);
}
