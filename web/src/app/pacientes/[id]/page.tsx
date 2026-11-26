import type { Metadata } from "next";
import { CalendarDays, CircleUserRound } from "lucide-react";
import { PainelAchados } from "@/components/achados/painel-achados";
import { Recorte } from "@/components/gestacao/recorte";
import { abrirPaciente, calcularIdade, PaginaPaciente, temAtlasAdulto } from "@/components/prontuario";
import { Card } from "@/components/ui/card";
import type { Paciente } from "@/lib/banco";

export const metadata: Metadata = { title: "Prontuário do paciente" };
export const dynamic = "force-dynamic";
export const revalidate = 0;

function nomeSexo(sexo: Paciente["sexo"]) {
  return ({ feminino: "Feminino", masculino: "Masculino", indeterminado: "Indeterminado" } as const)[sexo] ?? "Indeterminado";
}

export default async function ProntuarioPage({ params }: PageProps<"/pacientes/[id]">) {
  const { id } = await params;
  const aberto = await abrirPaciente(id);
  if ("recusa" in aberto) return aberto.recusa;
  const { supabase, paciente } = aberto;
  const com3d = temAtlasAdulto(paciente);
  // os achados vão prontos no HTML: lista e linha do tempo aparecem na primeira pintura. As consultas
  // da gestação correm junto, para não somar espera.
  const [achados, eventos, gestacoes, recorte] = await Promise.all([
    supabase.rpc("listar_achados", { p_paciente: paciente.id }),
    supabase.rpc("listar_eventos", { p_paciente: paciente.id }),
    com3d && paciente.sexo === "feminino" ? supabase.rpc("listar_gestacoes", { p_mae: paciente.id }) : null,
    com3d ? null : supabase.rpc("historico_gestacional_crianca", { p_crianca: paciente.id }),
  ]);

  return <PaginaPaciente paciente={paciente} aba="prontuario">
    <Card className="mt-6 grid gap-0 divide-y divide-slate-100 sm:grid-cols-3 sm:divide-x sm:divide-y-0"><div className="px-5 py-4"><p className="text-xs font-medium uppercase tracking-wide text-slate-500">CNS</p><p className="mt-2 text-sm font-semibold text-slate-900">{paciente.cns || "Não informado"}</p></div><div className="px-5 py-4"><p className="text-xs font-medium uppercase tracking-wide text-slate-500">Sexo</p><p className="mt-2 inline-flex items-center gap-2 text-sm font-semibold text-slate-900"><CircleUserRound className="size-4 text-teal-700" aria-hidden="true" />{nomeSexo(paciente.sexo)}</p></div><div className="px-5 py-4"><p className="text-xs font-medium uppercase tracking-wide text-slate-500">Idade</p><p className="mt-2 inline-flex items-center gap-2 text-sm font-semibold text-slate-900"><CalendarDays className="size-4 text-teal-700" aria-hidden="true" />{calcularIdade(paciente.data_nascimento)} anos</p></div></Card>
    {recorte && <Recorte linhas={recorte.error ? null : (recorte.data ?? [])} />}
    <section className="mt-8"><div className="mb-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-teal-800">Visualização clínica</p><h2 className="mt-1 text-xl font-semibold text-slate-950">{com3d ? "Prontuário 3D" : "Prontuário e linha do tempo"}</h2></div>
      <PainelAchados key={paciente.id} pacienteId={paciente.id} inicial={achados.error ? null : (achados.data ?? [])} sexo={paciente.sexo} com3d={com3d}
        eventos={eventos.error ? null : (eventos.data ?? [])}
        gestacaoEmCurso={!!gestacoes?.data?.some((g) => g.desfecho === "em_curso")} />
    </section>
  </PaginaPaciente>;
}
