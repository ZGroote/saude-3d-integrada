// Só no servidor.
import type { Gestacao } from "@/lib/gestacao";
import type { createClient } from "@/lib/supabase/server";

/** `listar_gestacoes` mais a descrição dos CID-10 (a função só devolve o código; `cid10` é tabela de leitura). */
export async function listarGestacoes(supabase: Awaited<ReturnType<typeof createClient>>, maeId: string) {
  const { data, error } = await supabase.rpc("listar_gestacoes", { p_mae: maeId });
  const gestacoes: Gestacao[] = data ?? [];
  const codigos = [...new Set(gestacoes.flatMap((g) => g.condicoes ?? []).filter((c) => !c.cid10_descricao).map((c) => c.cid10))];
  if (codigos.length) {
    // sem a descrição a tela mostra o código: a falha daqui não esconde as gestações
    const { data: nomes } = await supabase.from("cid10").select("codigo, descricao").in("codigo", codigos);
    const descricao = new Map((nomes ?? []).map((n) => [n.codigo, n.descricao]));
    for (const c of gestacoes.flatMap((g) => g.condicoes ?? [])) c.cid10_descricao ||= descricao.get(c.cid10);
  }
  return { data: gestacoes, error };
}
