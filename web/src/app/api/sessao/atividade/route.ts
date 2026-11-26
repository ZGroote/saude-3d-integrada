import { registrarAtividadeSessao } from "@/lib/supabase/admin";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const origem = request.headers.get("origin");
  const host = request.headers.get("host");
  let origemHost = "";
  try { origemHost = origem ? new URL(origem).host : ""; } catch { /* origem inválida */ }
  if (!host || !origemHost || origemHost.toLowerCase() !== host.toLowerCase()) {
    return Response.json({ erro: "origem_invalida" }, {
      status: 403, headers: { "Cache-Control": "no-store, private" },
    });
  }
  const supabase = await createClient();
  if (!await registrarAtividadeSessao(supabase)) {
    return Response.json({ erro: "sessao_expirada" }, {
      status: 401, headers: { "Cache-Control": "no-store, private" },
    });
  }
  return Response.json({ ok: true }, { headers: { "Cache-Control": "no-store, private" } });
}
