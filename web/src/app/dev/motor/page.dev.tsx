// Só existe no `next dev`: a extensão .dev.tsx fica fora de pageExtensions no build (next.config.ts).
// Mesmo componente do prontuário, sem paciente, sem login e sem Supabase.
import type { Metadata } from "next";
import Link from "next/link";
import { Prontuario3D } from "@/components/anatomia/prontuario-3d";
import type { Sexo } from "@/lib/banco";

export const metadata: Metadata = { title: "Demonstração do motor 3D", robots: { index: false } };

const SEXOS: Sexo[] = ["masculino", "feminino", "indeterminado"];

export default async function DemoMotor({ searchParams }: { searchParams: Promise<{ sexo?: string }> }) {
  const { sexo } = await searchParams;
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
      <Prontuario3D key={escolhido} sexo={escolhido} />
    </main>
  );
}
