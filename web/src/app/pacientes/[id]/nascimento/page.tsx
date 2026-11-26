import type { Metadata } from "next";
import Link from "next/link";
import { FormularioNascimento } from "@/components/gestacao/formulario-nascimento";
import { abrirPaciente, PaginaPaciente } from "@/components/prontuario";
import { Card } from "@/components/ui/card";
import { formatarData } from "@/lib/achados";

export const metadata: Metadata = { title: "Registrar nascimento" };
export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function NascimentoPage({ params, searchParams }: PageProps<"/pacientes/[id]/nascimento">) {
  const { id } = await params;
  const { gestacao: pedida } = await searchParams;
  const aberto = await abrirPaciente(id);
  if ("recusa" in aberto) return aberto.recusa;
  const { supabase, paciente } = aberto;
  const { data, error } = await supabase.rpc("listar_gestacoes", { p_mae: paciente.id });
  // a gestação em curso; uma já com nascido vivo só quando pedida (gêmeos: outro recém-nascido da mesma gestação)
  const gestacao = (data ?? []).find((g) => pedida
    ? g.gestacao_id === pedida && (g.desfecho === "em_curso" || g.desfecho === "nascido_vivo")
    : g.desfecho === "em_curso");

  return <PaginaPaciente paciente={paciente} aba="nascimento" titulo="Registrar nascimento">
    {error ? <Card className="mt-4 p-6 text-sm text-red-800" role="alert">Não foi possível carregar as gestações. Tente novamente.</Card>
      : !gestacao ? <Card className="mt-4 p-6 text-sm text-slate-600">Não há gestação em curso. <Link prefetch={false} href={`/pacientes/${paciente.id}/gestacao`} className="font-medium text-teal-800 underline">Ver gestações</Link></Card>
        : <>
          <p className="mt-2 text-sm text-slate-600">
            Mãe: {paciente.nome} · DUM {gestacao.dum ? formatarData(gestacao.dum) : "não informada"}
            {gestacao.desfecho === "nascido_vivo" && " · outro recém-nascido de uma gestação que já tem nascimento"}
          </p>
          <p className="mt-1 text-sm text-slate-600">A criança será cadastrada sem CNS (o administrador atribui depois) e vinculada à sua unidade.</p>
          <FormularioNascimento key={gestacao.gestacao_id} gestacaoId={gestacao.gestacao_id} dum={gestacao.dum} />
        </>}
  </PaginaPaciente>;
}
