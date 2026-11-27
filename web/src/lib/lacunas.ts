import type { EntradaIndice } from "@saude3d/motor-anatomico";
import { normalizar } from "./estruturas";

export type Lacuna = { nome: string; termos: string[]; parcial?: string; detalhe?: string };

export const LACUNAS: Record<string, Lacuna[]> = {
  "hra-f/1.10-1": [
    { nome: "Púbis", termos: ["pubis", "pube", "pubic"] },
    { nome: "Ísquio", termos: ["isquio", "ischium", "ischial"] },
    { nome: "Acetábulo", termos: ["acetabulo", "acetabulum"] },
    { nome: "Osso do quadril", termos: ["quadril", "coxal", "hip"], parcial: "só o ílio está no corpo", detalhe: "Púbis, ísquio e acetábulo não existem neste corpo." },
  ],
  "bp3d-m/4.0-1": [
    { nome: "Pulmão", termos: ["pulmao", "pulmoes", "lung"], parcial: "só a árvore brônquica está no corpo", detalhe: "Registre no brônquio ou sem local e descreva na observação." },
  ],
};

export function lacunasDaBusca(atlas: string, versao: string, texto: string): Lacuna[] {
  const palavras = normalizar(texto).trim().split(/\s+/).filter((palavra) => palavra.length >= 3);
  if (!palavras.length) return [];
  return (LACUNAS[`${atlas}/${versao}`] ?? []).filter((lacuna) =>
    palavras.some((palavra) => lacuna.termos.some((termo) => normalizar(termo).split(/\s+/).some((t) => t.startsWith(palavra)))),
  );
}

export const NOMES_MALHAS: Record<string, Record<string, Pick<EntradaIndice, "nome_pt" | "nome_en">>> = {
  "hra-f/1.10-1": {
    VH_F_ilium_compact_bone_R: { nome_pt: "Ílio (osso compacto)", nome_en: "Ilium (compact bone)" },
    VH_F_ilium_compact_bone_L: { nome_pt: "Ílio (osso compacto)", nome_en: "Ilium (compact bone)" },
    VH_F_ilium_spongy_bone_R: { nome_pt: "Ílio (osso trabecular)", nome_en: "Ilium (trabecular bone)" },
    VH_F_ilium_spongy_bone_L: { nome_pt: "Ílio (osso trabecular)", nome_en: "Ilium (trabecular bone)" },
  },
};

/** Corrige rótulos de superfície na única entrada do índice para a interface; a âncora continua intacta. */
export function nomearIndiceLacunas(atlas: string, versao: string, indice: EntradaIndice[]): EntradaIndice[] {
  const nomes = NOMES_MALHAS[`${atlas}/${versao}`];
  if (!nomes) return indice;
  return indice.map((entrada) => {
    const nome = nomes[entrada.malha];
    return nome ? { ...entrada, ...nome } : entrada;
  });
}
