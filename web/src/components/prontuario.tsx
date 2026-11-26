// Partes comuns às páginas de um paciente. Só no servidor.
import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowLeft, FileLock2 } from "lucide-react";
import { Topbar } from "@/components/topbar";
import { Card } from "@/components/ui/card";
import type { Paciente } from "@/lib/banco";
import { createClient } from "@/lib/supabase/server";
import { z } from "zod";

// ponytail: "criança" = menor de 12 anos (ECA); a SPEC §5.1 não fixa a idade
export const IDADE_MINIMA_ATLAS_ADULTO = 12;

export function calcularIdade(nascimento: string) {
  const hoje = new Date();
  const data = new Date(`${nascimento}T12:00:00Z`);
  let idade = hoje.getUTCFullYear() - data.getUTCFullYear();
  if (hoje.getUTCMonth() < data.getUTCMonth() || (hoje.getUTCMonth() === data.getUTCMonth() && hoje.getUTCDate() < data.getUTCDate())) idade--;
  return idade;
}

/** Adulto = pode ver o atlas. Data desconhecida conta como criança (SPEC §5.1). */
export const temAtlasAdulto = (paciente: Paciente) => calcularIdade(paciente.data_nascimento) >= IDADE_MINIMA_ATLAS_ADULTO;

const BOTAO_VOLTAR = "alvo mt-6 inline-flex h-10 items-center justify-center rounded-md bg-teal-800 px-4 text-sm font-semibold text-white hover:bg-teal-900";

function Aviso({ children }: { children: ReactNode }) {
  return <div className="min-h-screen"><Topbar /><main className="mx-auto max-w-3xl px-5 py-16 sm:px-8"><Card className="px-6 py-12 text-center">{children}<Link href="/pacientes" className={BOTAO_VOLTAR}>Voltar à lista</Link></Card></main></div>;
}

function semAcesso() {
  return { recusa: <Aviso><span className="mx-auto grid size-12 place-items-center rounded-full bg-amber-50 text-amber-800"><FileLock2 className="size-5" aria-hidden="true" /></span><h1 className="mt-4 text-2xl font-semibold tracking-tight text-slate-950">Sem acesso a este paciente</h1><p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-600">Este paciente não está disponível para sua unidade ou seu vínculo não está ativo.</p></Aviso> };
}

/**
 * Porta única de leitura (SPEC §6): toda página de paciente passa por `abrir_prontuario`, que confere o
 * vínculo e audita. Devolve o paciente ou a tela de recusa.
 */
export async function abrirPaciente(id: string) {
  if (!z.string().uuid().safeParse(id).success) return semAcesso();
  const supabase = await createClient();
  const { data, error } = await supabase.rpc("abrir_prontuario", { p_paciente: id });

  // sem vínculo a função devolve NULL, que o PostgREST entrega como objeto com todos os campos nulos
  if (error?.code === "42501" || (!error && !data?.id)) {
    return semAcesso();
  }
  if (error || !data) {
    return { recusa: <Aviso><h1 className="text-xl font-semibold text-slate-950">Não foi possível abrir o prontuário</h1><p className="mt-3 text-sm text-slate-600">O serviço está indisponível. Tente novamente.</p></Aviso> };
  }
  return { supabase, paciente: data };
}

const ABAS = { prontuario: "Prontuário", gestacao: "Gestação", familia: "Família" } as const;

/** Cabeçalho, nome do paciente e navegação entre as páginas dele. */
export function PaginaPaciente({ paciente, aba, titulo, children }: {
  paciente: Paciente;
  aba: keyof typeof ABAS | "nascimento";
  /** subtítulo das páginas que não são o prontuário */
  titulo?: string;
  children: ReactNode;
}) {
  const base = `/pacientes/${paciente.id}`;
  // ponytail: a aba aparece a partir dos 10 anos (início da adolescência pela OMS), para não surgir num bebê;
  // a SPEC não fixa idade e a rota /gestacao continua valendo para qualquer paciente do sexo feminino
  const mostraGestacao = paciente.sexo === "feminino" && calcularIdade(paciente.data_nascimento) >= 10;
  const abas = (Object.keys(ABAS) as (keyof typeof ABAS)[]).filter((a) => a !== "gestacao" || mostraGestacao);
  return <div className="min-h-screen"><Topbar /><main className="mx-auto max-w-6xl px-5 py-8 sm:px-8"><Link href="/pacientes" className="alvo inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-teal-800"><ArrowLeft className="size-4" aria-hidden="true" />Voltar aos pacientes</Link>
    <div className="mt-6 flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between"><div><p className="text-sm font-medium text-teal-800">Prontuário individual</p><h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">{paciente.nome}</h1></div><div className="inline-flex items-center gap-2 self-start rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-900"><span className="size-2 rounded-full bg-emerald-600" />Acesso autorizado e registrado</div></div>
    <nav aria-label="Páginas do paciente" className="mt-4 flex gap-1 border-b border-slate-200">
      {abas.map((a) => (
        // sem pré-carga: abrir uma página do paciente é um acesso auditado
        <Link key={a} prefetch={false} href={a === "prontuario" ? base : `${base}/${a}`} aria-current={a === aba ? "page" : undefined}
          className="alvo -mb-px border-b-2 border-transparent px-3 py-2 text-sm font-medium text-slate-600 hover:text-teal-800 aria-[current=page]:border-teal-800 aria-[current=page]:text-teal-800">{ABAS[a]}</Link>
      ))}
    </nav>
    {titulo && <h2 className="mt-6 text-xl font-semibold text-slate-950">{titulo}</h2>}
    {children}
  </main></div>;
}
