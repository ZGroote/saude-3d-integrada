// Server-only module: do not import from any file marked "use client".
import { createClient as createSupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@/lib/banco";
import type { createClient } from "@/lib/supabase/server";

if (typeof window !== "undefined") throw new Error("Supabase admin client is server-only.");

type UsuarioSupabase = Awaited<ReturnType<typeof createClient>>;

function clienteAdmin() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const chave = process.env.SUPABASE_SECRET_KEY;
  if (!url || !chave) throw new Error("Configuração de segurança ausente.");
  return createSupabaseClient<Database>(url, chave, {
    auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
  });
}

/** Registra atividade da sessão autenticada sem expor a chave privilegiada ao navegador. */
export async function registrarAtividadeSessao(supabaseDoUsuario: UsuarioSupabase): Promise<boolean> {
  try {
    const { data, error } = await supabaseDoUsuario.auth.getClaims();
    if (error || !data?.claims) return false;
    const claims = data.claims as Record<string, unknown>;
    const sessao = claims.session_id;
    const usuario = claims.sub;
    if (typeof sessao !== "string" || !sessao || typeof usuario !== "string" || !usuario) return false;

    const admin = clienteAdmin();
    const { data: ativo, error: rpcError } = await admin.rpc("registrar_atividade_sessao", {
      p_sessao: sessao,
      p_usuario: usuario,
    });
    return !rpcError && ativo === true;
  } catch {
    return false;
  }
}
