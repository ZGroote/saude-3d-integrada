"use client";

import { useActionState } from "react";
import { Activity, ArrowRight, LoaderCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { entrar } from "./actions";

export function LoginForm({ sessaoExpirada }: { sessaoExpirada: boolean }) {
  const [estado, enviar, carregando] = useActionState(entrar, { erro: "", email: "" });

  return (
    <form className="mt-8 space-y-5" action={enviar}>
      {sessaoExpirada && <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">Sua sessão terminou após 30 minutos sem atividade. Entre novamente.</p>}
      <div className="space-y-2"><label className="text-sm font-medium text-slate-800" htmlFor="email">E-mail profissional</label><Input id="email" name="email" type="email" autoComplete="username" placeholder="nome@unidade.saude.br" defaultValue={estado.email} required /></div>
      <div className="space-y-2"><label className="text-sm font-medium text-slate-800" htmlFor="senha">Senha</label><Input id="senha" name="senha" type="password" autoComplete="current-password" required /></div>
      {estado.erro && <p className="text-sm text-red-700" role="alert">{estado.erro}</p>}
      <Button className="w-full" type="submit" disabled={carregando}>{carregando ? <LoaderCircle className="size-4 animate-spin" aria-hidden="true" /> : null}Entrar com segurança <ArrowRight className="size-4" aria-hidden="true" /></Button>
      <p className="text-center text-xs leading-5 text-slate-600">Acesso exclusivo para profissionais autorizados da rede de saúde.</p>
    </form>
  );
}

export function MarcaSaude({ clara = false }: { clara?: boolean }) {
  return <div className="flex items-center gap-3"><span className="grid size-10 place-items-center rounded-md bg-teal-800 text-white"><Activity className="size-5" aria-hidden="true" /></span><span className={`text-sm font-semibold tracking-tight ${clara ? "text-white" : "text-slate-900"}`}>Saúde <span className={clara ? "text-teal-200" : "text-teal-800"}>3D</span></span></div>;
}
