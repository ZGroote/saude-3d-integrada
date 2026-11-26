import type { Metadata } from "next";
import Link from "next/link";
import { abrirPaciente, PaginaPaciente } from "@/components/prontuario";
import { Card } from "@/components/ui/card";
import { formatarData } from "@/lib/achados";
import { nomeDaCrianca } from "@/lib/gestacao";

export const metadata: Metadata = { title: "Família" };
export const dynamic = "force-dynamic";
export const revalidate = 0;

const ATALHO = "alvo font-semibold text-teal-800 underline";

export default async function FamiliaPage({ params }: PageProps<"/pacientes/[id]/familia">) {
  const { id } = await params;
  const aberto = await abrirPaciente(id);
  if ("recusa" in aberto) return aberto.recusa;
  const { supabase, paciente } = aberto;
  const [origem, gestacoes] = await Promise.all([
    supabase.rpc("historico_gestacional_crianca", { p_crianca: paciente.id }),
    paciente.sexo === "feminino" ? supabase.rpc("listar_gestacoes", { p_mae: paciente.id }) : null,
  ]);
  const mae = origem.data?.[0];
  const filhos = (gestacoes?.data ?? []).flatMap((g) => g.nascimentos ?? []).toSorted((a, b) => a.data.localeCompare(b.data));
  const falhou = origem.error || gestacoes?.error;

  return <PaginaPaciente paciente={paciente} aba="familia" titulo="Família">
    {falhou && <Card className="mt-4 p-6 text-sm text-red-800" role="alert">Não foi possível carregar todos os vínculos familiares. Tente novamente.</Card>}
    {!falhou && !mae && !filhos.length && <Card className="mt-4 p-6 text-sm text-slate-600">Nenhum vínculo de mãe ou filho registrado.</Card>}
    {mae && (
      <Card className="mt-4 px-5 py-4">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-600">Mãe</h3>
        <p className="mt-1 text-sm">
          {mae.mae_id ? <Link prefetch={false} href={`/pacientes/${mae.mae_id}`} className={ATALHO}>{mae.nome_mae}</Link> : <span className="font-semibold text-slate-900">{mae.nome_mae}</span>}
        </p>
      </Card>
    )}
    {!!filhos.length && (
      <Card className="mt-4 px-5 py-4">
        <h3 id="titulo-filhos" className="text-xs font-semibold uppercase tracking-wide text-slate-600">Filhos</h3>
        <ul aria-labelledby="titulo-filhos" className="mt-1 space-y-1 text-sm">
          {filhos.map((f) => <li key={f.crianca_id}><Link prefetch={false} href={`/pacientes/${f.crianca_id}`} className={ATALHO}>{nomeDaCrianca(f)}</Link><span className="text-slate-600"> · nascimento em {formatarData(f.data)}</span></li>)}
        </ul>
      </Card>
    )}
    <p className="mt-4 text-xs leading-5 text-slate-600">Abrir o prontuário de um familiar exige vínculo da sua unidade com ele, e o acesso é registrado.</p>
  </PaginaPaciente>;
}
