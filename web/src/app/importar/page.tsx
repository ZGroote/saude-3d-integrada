import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { FormularioImportacao } from "@/app/importar/formulario";
import { Topbar } from "@/components/topbar";
import { Card } from "@/components/ui/card";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = { title: "Importar FHIR" };
export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function ImportarPage() {
  const supabase = await createClient();
  // o proxy já barra o anônimo; a página confere de novo
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");
  const { data: admin } = await supabase.rpc("eh_admin");

  return <div className="min-h-screen"><Topbar /><main className="mx-auto max-w-4xl px-5 py-10 sm:px-8">
    {admin !== true ? (
      <Card className="px-6 py-12 text-center"><h1 className="text-2xl font-semibold text-slate-950">Acesso negado</h1><p className="mt-3 text-sm text-slate-600">Só o administrador da unidade importa dados.</p></Card>
    ) : (
      <>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Importar FHIR</h1>
        <p className="mt-2 text-sm text-slate-600">Os pacientes importados ficam vinculados à sua unidade. Nesta fase, só dados fictícios.</p>
        <FormularioImportacao />
      </>
    )}
  </main></div>;
}
