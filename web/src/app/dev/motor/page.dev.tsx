// Só existe no `next dev`: a extensão .dev.tsx fica fora de pageExtensions no build (next.config.ts).
// Mesmo componente do prontuário, sem paciente, sem login e sem Supabase.
// ?atlas=vhf-f&versao=0.1-0 abre um pacote em revisão (copie antes com `npm run atlas -- --rascunho`).
// ?achados=1 mostra o painel de achados com paciente falso; testes/achados.py simula as rpc no navegador.
import type { Metadata } from "next";
import Link from "next/link";
import { PainelAchados } from "@/components/achados/painel-achados";
import { Prontuario3D } from "@/components/anatomia/prontuario-3d";
import type { Sexo } from "@/lib/banco";

export const metadata: Metadata = { title: "Demonstração do motor 3D", robots: { index: false } };

const SEXOS: Sexo[] = ["masculino", "feminino", "indeterminado"];

export default async function DemoMotor({ searchParams }: { searchParams: Promise<{ sexo?: string; achados?: string; atlas?: string; versao?: string }> }) {
  const { sexo, achados, atlas, versao } = await searchParams;
  // os dois viram caminho de arquivo: só nomes simples
  const nome = /^[a-z0-9][a-z0-9.-]*$/i;
  const revisao = atlas && versao && nome.test(atlas) && nome.test(versao) ? { atlas, versao } : undefined;
  const escolhido = SEXOS.find((s) => s === sexo) ?? "masculino";
  return (
    <main className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
      <h1 className="text-xl font-semibold text-slate-950">Motor 3D — demonstração de desenvolvimento</h1>
      <nav className="my-4 flex gap-4 text-sm font-medium text-teal-800" aria-label="Sexo simulado">
        {SEXOS.map((s) => (
          <Link key={s} href={`?sexo=${s}`} aria-current={s === escolhido ? "page" : undefined} className="aria-[current]:underline">
            {s}
          </Link>
        ))}
      </nav>
      {revisao ? (
        <>
          <p role="alert" className="mb-4 text-sm font-semibold text-amber-900">Pacote em revisão: {revisao.atlas} {revisao.versao}</p>
          <Prontuario3D sexo={escolhido} pacoteDeRevisao={revisao} />
        </>
      ) : achados
        ? <PainelAchados key={escolhido} pacienteId="00000000-0000-4000-8000-00000000fa15" sexo={escolhido} com3d />
        : <Prontuario3D key={escolhido} sexo={escolhido} />}
    </main>
  );
}
