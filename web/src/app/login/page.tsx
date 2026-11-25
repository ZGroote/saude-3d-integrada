import type { Metadata } from "next";
import { LockKeyhole, ShieldCheck } from "lucide-react";
import { LoginForm, MarcaSaude } from "./login-form";

export const metadata: Metadata = { title: "Entrar" };

export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const params = await searchParams;
  return (
    <main className="grid min-h-screen bg-white lg:grid-cols-[1.05fr_0.95fr]">
      <section className="relative hidden overflow-hidden bg-[#153b35] px-12 py-10 text-white lg:flex lg:flex-col lg:justify-between xl:px-20">
        <div className="absolute -right-28 top-24 size-96 rounded-full border border-white/10" /><div className="absolute -right-12 top-40 size-64 rounded-full border border-white/10" />
        <MarcaSaude />
        <div className="relative max-w-xl py-20"><p className="mb-5 text-xs font-semibold uppercase tracking-[0.2em] text-teal-200">Cuidado conectado</p><h1 className="text-4xl font-semibold leading-tight tracking-tight xl:text-5xl">Um olhar integrado para cada pessoa.</h1><p className="mt-6 max-w-md text-base leading-7 text-teal-50/80">Informação clínica segura para apoiar o cuidado em toda a rede de saúde.</p></div>
        <p className="text-xs text-teal-100/70">Saúde 3D Integrada · Ambiente protegido</p>
      </section>
      <section className="flex items-center justify-center px-5 py-12 sm:px-10">
        <div className="w-full max-w-md"><div className="mb-12 lg:hidden"><MarcaSaude /></div><div className="mb-8 flex size-12 items-center justify-center rounded-lg bg-teal-50 text-teal-800"><LockKeyhole className="size-5" aria-hidden="true" /></div><p className="text-sm font-semibold text-teal-800">Área profissional</p><h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Acesse sua conta</h2><p className="mt-3 text-sm leading-6 text-slate-600">Entre com as credenciais da sua unidade para consultar pacientes vinculados.</p>
          <LoginForm sessaoExpirada={params.motivo === "sessao-expirada"} />
          <div className="mt-9 flex items-start gap-3 border-t border-slate-200 pt-5 text-xs leading-5 text-slate-500"><ShieldCheck className="mt-0.5 size-4 shrink-0 text-teal-700" aria-hidden="true" /><p>O acesso é registrado para proteger a privacidade e a continuidade do cuidado.</p></div>
        </div>
      </section>
    </main>
  );
}
