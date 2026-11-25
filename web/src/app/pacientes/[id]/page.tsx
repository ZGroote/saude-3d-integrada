import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, CalendarDays, CircleUserRound, FileLock2 } from "lucide-react";
import { Prontuario3D } from "@/components/anatomia/prontuario-3d";
import { Topbar } from "@/components/topbar";
import { Card } from "@/components/ui/card";
import { createClient } from "@/lib/supabase/server";
import type { Paciente } from "@/lib/banco";

export const metadata: Metadata = { title: "Prontuário do paciente" };
export const dynamic = "force-dynamic";
export const revalidate = 0;

// ponytail: "criança" = menor de 12 anos (ECA); a SPEC §5.1 não fixa a idade
const IDADE_MINIMA_ATLAS_ADULTO = 12;

function calcularIdade(nascimento: string) {
  const hoje = new Date();
  const data = new Date(`${nascimento}T12:00:00Z`);
  let idade = hoje.getUTCFullYear() - data.getUTCFullYear();
  if (hoje.getUTCMonth() < data.getUTCMonth() || (hoje.getUTCMonth() === data.getUTCMonth() && hoje.getUTCDate() < data.getUTCDate())) idade--;
  return idade;
}

function nomeSexo(sexo: Paciente["sexo"]) {
  return ({ feminino: "Feminino", masculino: "Masculino", indeterminado: "Indeterminado" } as const)[sexo] ?? "Indeterminado";
}

export default async function ProntuarioPage({ params }: PageProps<"/pacientes/[id]">) {
  const { id } = await params;
  const supabase = await createClient();
  const { data, error } = await supabase.rpc("abrir_prontuario", { p_paciente: id });

  if (error?.code === "42501" || (!error && !data)) {
    return <div className="min-h-screen"><Topbar /><main className="mx-auto max-w-3xl px-5 py-16 sm:px-8"><Card className="px-6 py-12 text-center"><span className="mx-auto grid size-12 place-items-center rounded-full bg-amber-50 text-amber-800"><FileLock2 className="size-5" aria-hidden="true" /></span><h1 className="mt-4 text-2xl font-semibold tracking-tight text-slate-950">Sem acesso a este paciente</h1><p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-600">Este paciente não está disponível para sua unidade ou seu vínculo não está ativo.</p><Link href="/pacientes" className="mt-6 inline-flex h-10 items-center justify-center rounded-md bg-teal-800 px-4 text-sm font-semibold text-white hover:bg-teal-900">Voltar à lista</Link></Card></main></div>;
  }

  if (error) {
    return <div className="min-h-screen"><Topbar /><main className="mx-auto max-w-3xl px-5 py-16 sm:px-8"><Card className="px-6 py-12 text-center"><h1 className="text-xl font-semibold text-slate-950">Não foi possível abrir o prontuário</h1><p className="mt-3 text-sm text-slate-600">O serviço está indisponível. Tente novamente.</p><Link href="/pacientes" className="mt-6 inline-flex h-10 items-center justify-center rounded-md bg-teal-800 px-4 text-sm font-semibold text-white hover:bg-teal-900">Voltar à lista</Link></Card></main></div>;
  }

  const paciente = data as Paciente;
  return <div className="min-h-screen"><Topbar /><main className="mx-auto max-w-6xl px-5 py-8 sm:px-8"><Link href="/pacientes" className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-teal-800"><ArrowLeft className="size-4" aria-hidden="true" />Voltar aos pacientes</Link>
    <div className="mt-6 flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between"><div><p className="text-sm font-medium text-teal-800">Prontuário individual</p><h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">{paciente.nome}</h1></div><div className="inline-flex items-center gap-2 self-start rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-900"><span className="size-2 rounded-full bg-emerald-600" />Acesso autorizado e registrado</div></div>
    <Card className="mt-6 grid gap-0 divide-y divide-slate-100 sm:grid-cols-3 sm:divide-x sm:divide-y-0"><div className="px-5 py-4"><p className="text-xs font-medium uppercase tracking-wide text-slate-500">CNS</p><p className="mt-2 text-sm font-semibold text-slate-900">{paciente.cns}</p></div><div className="px-5 py-4"><p className="text-xs font-medium uppercase tracking-wide text-slate-500">Sexo</p><p className="mt-2 inline-flex items-center gap-2 text-sm font-semibold text-slate-900"><CircleUserRound className="size-4 text-teal-700" aria-hidden="true" />{nomeSexo(paciente.sexo)}</p></div><div className="px-5 py-4"><p className="text-xs font-medium uppercase tracking-wide text-slate-500">Idade</p><p className="mt-2 inline-flex items-center gap-2 text-sm font-semibold text-slate-900"><CalendarDays className="size-4 text-teal-700" aria-hidden="true" />{calcularIdade(paciente.data_nascimento)} anos</p></div></Card>
    <section className="mt-8"><div className="mb-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-teal-800">Visualização clínica</p><h2 className="mt-1 text-xl font-semibold text-slate-950">Prontuário 3D</h2></div>
      {/* SPEC §5.1: nunca um corpo adulto no prontuário de criança; idade desconhecida também não abre o 3D */}
      {calcularIdade(paciente.data_nascimento) >= IDADE_MINIMA_ATLAS_ADULTO
        ? <Prontuario3D sexo={paciente.sexo} />
        : <Card className="px-6 py-10 text-center text-sm leading-6 text-slate-600">Corpo em 3D indisponível. Não há atlas pediátrico: prontuário de criança, ou sem data de nascimento, não usa corpo adulto.</Card>}
    </section>
  </main></div>;
}
