import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Search, UsersRound } from "lucide-react";
import { Topbar } from "@/components/topbar";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createClient } from "@/lib/supabase/server";
import type { PacienteBusca } from "@/lib/banco";

export const metadata: Metadata = { title: "Pacientes" };
export const dynamic = "force-dynamic";
export const revalidate = 0;

function formatarData(data: string) {
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(`${data}T12:00:00Z`));
}

export default async function PacientesPage({ searchParams }: PageProps<"/pacientes">) {
  const params = await searchParams;
  const valorBusca = Array.isArray(params.busca) ? params.busca[0] : params.busca;
  const busca = valorBusca?.trim() ?? "";
  const supabase = await createClient();
  const { data, error } = await supabase.rpc("buscar_pacientes", { p_texto: busca });
  const pacientes = (data ?? []) as PacienteBusca[];

  return <div className="min-h-screen"><Topbar /><main className="mx-auto max-w-6xl px-5 py-10 sm:px-8">
    <div className="mb-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><p className="text-sm font-medium text-teal-800">Atendimento</p><h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Pacientes</h1><p className="mt-2 text-sm text-slate-600">Consulte pessoas com vínculo ativo com sua unidade.</p></div><div className="inline-flex items-center gap-2 self-start rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 sm:self-auto"><UsersRound className="size-4 text-teal-700" aria-hidden="true" />{pacientes.length} pacientes</div></div>
    <Card className="mb-5 p-4 sm:p-5"><form action="/pacientes" method="get" className="flex flex-col gap-3 sm:flex-row"><div className="relative flex-1"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" aria-hidden="true" /><Input className="pl-10" type="search" name="busca" defaultValue={busca} placeholder="Buscar por nome ou CNS" aria-label="Buscar pacientes por nome ou CNS" /></div><button className="h-11 rounded-md bg-teal-800 px-5 text-sm font-semibold text-white hover:bg-teal-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700 focus-visible:ring-offset-2" type="submit">Buscar</button></form></Card>
    {error ? <Card className="p-6 text-sm text-red-800" role="alert">Não foi possível carregar a lista de pacientes. Tente novamente.</Card> : pacientes.length === 0 ? <Card className="flex flex-col items-center px-6 py-14 text-center"><span className="grid size-12 place-items-center rounded-full bg-slate-100 text-slate-500"><UsersRound className="size-5" aria-hidden="true" /></span><h2 className="mt-4 font-semibold text-slate-900">Nenhum paciente encontrado</h2><p className="mt-2 max-w-sm text-sm leading-6 text-slate-600">{busca ? "Revise o nome ou o CNS informado." : "Pacientes vinculados à unidade aparecerão aqui."}</p></Card> : <Card className="overflow-hidden"><div className="hidden grid-cols-[minmax(0,1.6fr)_minmax(140px,1fr)_minmax(120px,0.8fr)_40px] gap-4 border-b border-slate-200 bg-slate-50 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 sm:grid"><span>Nome</span><span>CNS</span><span>Nascimento</span><span /></div><ul aria-label="Pacientes vinculados" className="divide-y divide-slate-100">{pacientes.map((paciente) => <li key={paciente.id}><Link href={`/pacientes/${paciente.id}`} className="grid grid-cols-1 gap-2 px-5 py-4 outline-none transition-colors hover:bg-teal-50/50 focus-visible:bg-teal-50 sm:grid-cols-[minmax(0,1.6fr)_minmax(140px,1fr)_minmax(120px,0.8fr)_40px] sm:items-center sm:gap-4"><span className="font-medium text-slate-900">{paciente.nome}</span><span className="text-sm text-slate-600"><span className="mr-2 text-xs text-slate-400 sm:hidden">CNS</span>•••• {paciente.cns_final}</span><span className="text-sm text-slate-600"><span className="mr-2 text-xs text-slate-400 sm:hidden">Nascimento</span>{formatarData(paciente.data_nascimento)}</span><span className="hidden justify-self-end text-teal-800 sm:block"><ArrowRight className="size-4" aria-hidden="true" /></span></Link></li>)}</ul></Card>}
    <p className="mt-5 text-xs leading-5 text-slate-500">A lista é filtrada pelo vínculo ativo da sua unidade. A abertura de cada prontuário é registrada para auditoria.</p>
  </main></div>;
}
