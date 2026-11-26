import type { Metadata } from "next";
import Link from "next/link";
import { Topbar } from "@/components/topbar";
import { BuscaPacientes, type EstadoBuscaPacientes } from "@/components/busca-pacientes";
import { createClient } from "@/lib/supabase/server";
import type { PacienteBusca } from "@/lib/banco";
import { z } from "zod";

export const metadata: Metadata = { title: "Pacientes" };
export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function PacientesPage() {
  async function pesquisarPacientes(_estado: EstadoBuscaPacientes, formData: FormData): Promise<EstadoBuscaPacientes> {
    "use server";
    const resultado = z.string().trim().max(120).safeParse(formData.get("busca"));
    if (!resultado.success) return { pacientes: [], busca: "", erro: true };
    const supabase = await createClient();
    const { data, error } = await supabase.rpc("buscar_pacientes", { p_texto: resultado.data });
    return { pacientes: (data ?? []) as PacienteBusca[], busca: resultado.data, erro: Boolean(error) };
  }

  const supabase = await createClient();
  const { data, error } = await supabase.rpc("buscar_pacientes", { p_texto: "" });
  const pacientes = (data ?? []) as PacienteBusca[];
  const { data: admin } = await supabase.rpc("eh_admin");

  return <div className="min-h-screen"><Topbar /><main className="mx-auto max-w-6xl px-5 py-10 sm:px-8">
    <div className="mb-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
      <div><p className="text-sm font-medium text-teal-800">Atendimento</p><h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Pacientes</h1><p className="mt-2 text-sm text-slate-600">Consulte pessoas com vínculo ativo com sua unidade.</p></div>
      {admin === true && <Link href="/importar" className="alvo self-start text-sm font-semibold text-teal-800 underline sm:ml-auto sm:self-auto">Importar FHIR</Link>}
    </div>
    <BuscaPacientes initialState={{ pacientes, busca: "", erro: Boolean(error) }} action={pesquisarPacientes} />
  </main></div>;
}
