"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { registrarAtividadeSessao } from "@/lib/supabase/admin";
import { assinarAtividade } from "@/lib/sessao";
import { z } from "zod";

const credenciaisSchema = z.object({
  email: z.string().trim().min(1).max(254).email(),
  senha: z.string().min(1).max(1024),
});
const COOKIE_ATIVIDADE = "saude3d-ultima-atividade";

// Ação de servidor: o formulário sai como POST mesmo antes de o JavaScript carregar (a senha nunca vai na URL).
export async function entrar(_anterior: { erro: string; email: string }, dados: FormData) {
  const emailEntrada = dados.get("email");
  const senhaEntrada = dados.get("senha");
  const email = typeof emailEntrada === "string" ? emailEntrada.trim().slice(0, 254) : "";
  const validacao = credenciaisSchema.safeParse({ email: emailEntrada, senha: senhaEntrada });
  if (!validacao.success) return { erro: "Informe um e-mail válido e uma senha.", email };
  if (!process.env.SESSAO_SEGREDO) {
    return { erro: "Configuração de segurança ausente: defina SESSAO_SEGREDO no servidor.", email };
  }
  if (!process.env.SUPABASE_SECRET_KEY) {
    return { erro: "Configuração de segurança ausente: defina SUPABASE_SECRET_KEY no servidor.", email };
  }
  try {
    const supabase = await createClient();
    const { error } = await supabase.auth.signInWithPassword({ email: validacao.data.email, password: validacao.data.senha });
    // 429: limite de tentativas do Supabase Auth (hoje contado pelo IP do servidor, ver SPEC §12)
    if (error?.status === 429) return { erro: "Muitas tentativas de entrada. Aguarde alguns minutos e tente de novo.", email };
    if (error) return { erro: "Não foi possível entrar. Confira seu e-mail e sua senha.", email };
    if (!await registrarAtividadeSessao(supabase)) {
      await supabase.auth.signOut({ scope: "local" });
      return { erro: "Serviço de autenticação indisponível. Tente novamente mais tarde.", email };
    }
    (await cookies()).set(COOKIE_ATIVIDADE, await assinarAtividade(Date.now()), {
      httpOnly: true, sameSite: "lax", secure: process.env.NODE_ENV === "production", path: "/", maxAge: 30 * 60,
    });
  } catch {
    return { erro: "Serviço de autenticação indisponível. Tente novamente mais tarde.", email };
  }
  redirect("/pacientes");
}

export async function sair() {
  (await cookies()).set(COOKIE_ATIVIDADE, "", {
    httpOnly: true, sameSite: "lax", secure: process.env.NODE_ENV === "production", path: "/", maxAge: 0,
  });
  const supabase = await createClient();
  // só esta sessão: outros aparelhos do mesmo profissional continuam conectados
  await supabase.auth.signOut({ scope: "local" });
  redirect("/login");
}
