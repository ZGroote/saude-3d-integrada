"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Activity, ArrowRight, LoaderCircle } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function LoginForm({ sessaoExpirada }: { sessaoExpirada: boolean }) {
  const router = useRouter();
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  async function entrar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErro("");
    setCarregando(true);
    const dados = new FormData(event.currentTarget);
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.signInWithPassword({ email: String(dados.get("email")), password: String(dados.get("senha")) });
      if (error) setErro("Não foi possível entrar. Confira seu e-mail e sua senha.");
      else { router.push("/pacientes"); router.refresh(); }
    } catch {
      setErro("Serviço de autenticação indisponível. Tente novamente mais tarde.");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <form className="mt-8 space-y-5" onSubmit={entrar}>
      {sessaoExpirada && <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">Sua sessão terminou após 30 minutos sem atividade. Entre novamente.</p>}
      <div className="space-y-2"><label className="text-sm font-medium text-slate-800" htmlFor="email">E-mail profissional</label><Input id="email" name="email" type="email" autoComplete="username" placeholder="nome@unidade.saude.br" required /></div>
      <div className="space-y-2"><label className="text-sm font-medium text-slate-800" htmlFor="senha">Senha</label><Input id="senha" name="senha" type="password" autoComplete="current-password" required /></div>
      {erro && <p className="text-sm text-red-700" role="alert">{erro}</p>}
      <Button className="w-full" type="submit" disabled={carregando}>{carregando ? <LoaderCircle className="size-4 animate-spin" aria-hidden="true" /> : null}Entrar com segurança <ArrowRight className="size-4" aria-hidden="true" /></Button>
      <p className="text-center text-xs leading-5 text-slate-500">Acesso exclusivo para profissionais autorizados da rede de saúde.</p>
    </form>
  );
}

export function MarcaSaude() {
  return <div className="flex items-center gap-3"><span className="grid size-10 place-items-center rounded-md bg-teal-800 text-white"><Activity className="size-5" aria-hidden="true" /></span><span className="text-sm font-semibold tracking-tight text-slate-900">Saúde <span className="text-teal-800">3D</span></span></div>;
}
