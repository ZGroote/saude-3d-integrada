// Escolha da estrutura por nome (o caminho sem ponteiro para registrar um achado com local).
import type { EntradaIndice } from "@saude3d/motor-anatomico";
import { entradaPrincipal } from "./fhir/ancora";

export type Estrutura = {
  chave: string;
  nome: string;
  nomeIngles: string;
  lateralidade: string | null;
  /** a malha onde a âncora vai: a mesma regra da importação FHIR */
  entrada: EntradaIndice;
  /** texto normalizado em que a busca procura */
  busca: string;
};

export const normalizar = (texto: string) => texto.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
export const LADO_DA_ESTRUTURA: Record<string, string> = { left: "esquerdo", right: "direito" };

/** Uma opção por estrutura, lado e nome: o mesmo ID com os dois lados (ou com partes nomeadas) não se mistura. */
export function listarEstruturas(indice: EntradaIndice[]): Estrutura[] {
  const grupos = new Map<string, EntradaIndice[]>();
  for (const e of indice) {
    const chave = JSON.stringify([e.estrutura ?? e.malha, e.lateralidade, e.nome_pt || e.nome_en]);
    const grupo = grupos.get(chave);
    if (grupo) grupo.push(e);
    else grupos.set(chave, [e]);
  }
  return [...grupos].map(([chave, entradas]) => {
    const entrada = entradaPrincipal(entradas)!;
    const nome = entrada.nome_pt || entrada.nome_en;
    const lado = LADO_DA_ESTRUTURA[entrada.lateralidade ?? ""] ?? "";
    return { chave, nome, nomeIngles: entrada.nome_en, lateralidade: entrada.lateralidade, entrada, busca: normalizar(`${nome} ${entrada.nome_en} ${lado}`) };
  }).sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR") || (a.lateralidade ?? "").localeCompare(b.lateralidade ?? ""));
}

/** Todas as palavras digitadas, em qualquer ordem; nomes que começam pelo que foi digitado vêm primeiro. */
export function procurarEstruturas(estruturas: Estrutura[], texto: string) {
  const termo = normalizar(texto).trim();
  if (termo.length < 2) return [];
  const palavras = termo.split(/\s+/);
  return estruturas.filter((e) => palavras.every((p) => e.busca.includes(p)))
    .toSorted((a, b) => Number(!a.busca.startsWith(termo)) - Number(!b.busca.startsWith(termo)));
}
