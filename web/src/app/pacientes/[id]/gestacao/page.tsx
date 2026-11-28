import type { Metadata } from "next";
import { Gestacoes } from "@/components/gestacao/gestacoes";
import { abrirPaciente, PaginaPaciente } from "@/components/prontuario";
import { Card } from "@/components/ui/card";
import { listarGestacoes } from "@/lib/gestacoes-servidor";

export const metadata: Metadata = { title: "Gestação" };
export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function GestacaoPage({ params }: PageProps<"/pacientes/[id]/gestacao">) {
  const { id } = await params;
  const aberto = await abrirPaciente(id);
  if ("recusa" in aberto) return aberto.recusa;
  const { supabase, paciente } = aberto;
  const resposta = paciente.sexo === "feminino" ? await listarGestacoes(supabase, paciente.id) : null;

  return <PaginaPaciente paciente={paciente} aba="gestacao" titulo="Gestações">
    {!resposta ? <Card className="mt-4 p-6 text-sm text-slate-600">O registro de gestação é para pacientes do sexo feminino.</Card>
      : resposta.error ? <Card className="mt-4 p-6 text-sm text-red-800" role="alert">Não foi possível carregar as gestações. Tente novamente.</Card>
        : <Gestacoes maeId={paciente.id} gestacoes={resposta.data} />}
  </PaginaPaciente>;
}
