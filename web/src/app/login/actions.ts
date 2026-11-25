"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

// Ação de servidor: o formulário sai como POST mesmo antes de o JavaScript carregar (a senha nunca vai na URL).
export async function entrar(_anterior: { erro: string; email: string }, dados: FormData) {
  const email = String(dados.get("email"));
  try {
    const supabase = await createClient();
    const { error } = await supabase.auth.signInWithPassword({ email, password: String(dados.get("senha")) });
    if (error) return { erro: "Não foi possível entrar. Confira seu e-mail e sua senha.", email };
  } catch {
    return { erro: "Serviço de autenticação indisponível. Tente novamente mais tarde.", email };
  }
  // a marca de atividade de uma sessão anterior encerraria a nova no primeiro acesso (ver proxy.ts)
  (await cookies()).delete("saude3d-ultima-atividade");
  redirect("/pacientes");
}

export async function sair() {
  const supabase = await createClient();
  // só esta sessão: outros aparelhos do mesmo profissional continuam conectados
  await supabase.auth.signOut({ scope: "local" });
  redirect("/login");
}
