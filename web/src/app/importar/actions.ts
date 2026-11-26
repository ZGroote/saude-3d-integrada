"use server";

import { gravar, montarPrevia, preparar } from "@/lib/fhir/servidor";
import type { Previa, Relatorio } from "@/lib/fhir/tipos";
import { createClient } from "@/lib/supabase/server";
import { z } from "zod";

const NEGADO = { erro: "Acesso negado: só o administrador da unidade importa." } as const;

// uma ação de servidor pode ser chamada sem passar pela página: o papel é conferido aqui também
async function comoAdmin() {
  const supabase = await createClient();
  const { data, error } = await supabase.rpc("eh_admin");
  return !error && data === true ? supabase : null;
}

export async function analisar(dados: FormData): Promise<{ previa: Previa } | { erro: string }> {
  const supabase = await comoAdmin();
  if (!supabase) return NEGADO;
  const sistemaOrigem = z.string().trim().min(1).max(200).safeParse(dados.get("sistemaOrigem"));
  if (!sistemaOrigem.success) return { erro: "Informe o sistema de origem (1 a 200 caracteres)." };
  const preparado = await preparar(supabase, dados.get("arquivo"), sistemaOrigem.data);
  return typeof preparado === "string" ? { erro: preparado } : { previa: await montarPrevia(supabase, preparado) };
}

export async function confirmar(dados: FormData): Promise<{ relatorio: Relatorio } | { erro: string }> {
  const supabase = await comoAdmin();
  if (!supabase) return NEGADO;
  const sistemaOrigem = z.string().trim().min(1).max(200).safeParse(dados.get("sistemaOrigem"));
  if (!sistemaOrigem.success) return { erro: "Informe o sistema de origem (1 a 200 caracteres)." };
  // o arquivo vem de novo e é planejado de novo: o navegador não decide o que é gravado
  const preparado = await preparar(supabase, dados.get("arquivo"), sistemaOrigem.data);
  if (typeof preparado === "string") return { erro: preparado };
  if (preparado.hash !== dados.get("hash") || preparado.sistemaOrigem !== sistemaOrigem.data) return { erro: "O arquivo ou sistema de origem mudou depois da prévia. Analise de novo." };
  if (preparado.semMapeamento || !preparado.pacientes.length) return { erro: "A importação está bloqueada. Analise o arquivo de novo." };
  const relatorio = await gravar(supabase, preparado);
  return typeof relatorio === "string" ? { erro: relatorio } : { relatorio };
}
