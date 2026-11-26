"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CATEGORIAS, formatarData, LADOS, STATUS, type Achado } from "@/lib/achados";
import { createClient } from "@/lib/supabase/client";

export function CartaoAchado({ achado: a, podeCorrigir, onCorrigir, onFechar }: {
  achado: Achado;
  podeCorrigir: boolean;
  onCorrigir: () => void;
  onFechar: () => void;
}) {
  const titulo = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    titulo.current?.focus({ preventScroll: true });
    titulo.current?.scrollIntoView({ block: "nearest" });
  }, []);
  const campos: [string, string][] = [
    ["Categoria", CATEGORIAS[a.categoria]], ["Status", STATUS[a.status]], ["Lado", LADOS[a.lado]],
    ["Início", a.inicio ? formatarData(a.inicio) : "Não informado"], ["Autor", a.autor_nome],
    ["Especialidade", a.especialidade ?? "Não informada"], ["Unidade", a.unidade_nome], ["Registrado em", formatarData(a.criado_em)],
    ["Observação", a.observacao || "Sem observação"],
  ];
  return (
    <Card className="px-5 py-4" data-cartao={a.id} onKeyDown={(e) => { if (e.key === "Escape") onFechar(); }}>
      <div className="flex items-start justify-between gap-2">
        <h3 ref={titulo} tabIndex={-1} className="text-sm font-semibold text-slate-950 outline-none"><span className="font-mono">{a.cid10}</span> {a.cid10_descricao}</h3>
        <Button type="button" variant="ghost" className="h-7 px-2" onClick={onFechar}>Fechar</Button>
      </div>
      <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
        {campos.map(([nome, valor]) => (
          <div key={nome} className={nome === "Observação" ? "col-span-2" : undefined}>
            <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{nome}</dt>
            <dd className="whitespace-pre-wrap break-words text-slate-900">{valor}</dd>
          </div>
        ))}
      </dl>
      <section className="mt-4 border-t border-slate-100 pt-3">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Histórico de correções</h4>
        {a.substitui_id ? <Historico id={a.id} /> : <p className="mt-1 text-sm text-slate-600">Este achado não foi corrigido.</p>}
      </section>
      {podeCorrigir && <Button type="button" variant="outline" className="mt-3 w-full" onClick={onCorrigir}>Corrigir</Button>}
    </Card>
  );
}

/** Versões do achado, da mais antiga para a atual. Só é pedido quando houve correção (a consulta é auditada). */
function Historico({ id }: { id: string }) {
  const [resposta, setResposta] = useState<{ versoes: Achado[]; erro: boolean } | null>(null);
  useEffect(() => {
    let valido = true;
    createClient().rpc("historico_achado", { p_achado: id }).then(({ data, error }) => {
      if (valido) setResposta({ versoes: data ?? [], erro: !!error || !data?.length });
    });
    return () => { valido = false; };
  }, [id]);

  if (!resposta) return <p role="status" className="mt-1 text-sm text-slate-600">Carregando histórico…</p>;
  if (resposta.erro) return <p role="alert" className="mt-1 text-sm text-red-800">Não foi possível carregar o histórico.</p>;
  return (
    <ol aria-label="Versões do achado" className="mt-1 space-y-2 text-sm">
      {resposta.versoes.map((v) => (
        <li key={v.id} data-versao={v.id} className="border-l-2 border-slate-200 pl-2">
          <p className="text-slate-900"><strong className="font-mono">{v.cid10}</strong> {v.cid10_descricao}{v.id === id && <em> (atual)</em>}</p>
          <p className="text-xs text-slate-600">
            {formatarData(v.criado_em)} · {v.autor_nome} · {v.unidade_nome} · {STATUS[v.status]} · {LADOS[v.lado]}
            {v.observacao && ` · ${v.observacao}`}
          </p>
        </li>
      ))}
    </ol>
  );
}
