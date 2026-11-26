"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { Cid10 } from "@/lib/banco";
import { ROTULO } from "@/lib/formulario";
import { createClient } from "@/lib/supabase/client";

export function BuscaCid10({ escolhido, onEscolher }: { escolhido: Cid10 | null; onEscolher: (c: Cid10 | null) => void }) {
  const [texto, setTexto] = useState("");
  const [resposta, setResposta] = useState<{ termo: string; itens: Cid10[]; erro: boolean } | null>(null);
  const termo = texto.trim();

  useEffect(() => {
    if (termo.length < 2) return;
    let valido = true;
    const espera = setTimeout(async () => {
      const { data, error } = await createClient().rpc("buscar_cid10", { p_texto: termo, p_limite: 20 });
      // resposta de um termo antigo não sobrescreve a do atual
      if (valido) setResposta({ termo, itens: data ?? [], erro: !!error });
    }, 300);
    return () => { valido = false; clearTimeout(espera); };
  }, [termo]);

  if (escolhido) {
    return (
      <div className="space-y-1 text-sm">
        <p className="font-medium text-slate-800">CID-10</p>
        <div className="flex items-start justify-between gap-2 rounded-md border border-teal-200 bg-teal-50 px-3 py-2">
          <p data-cid-escolhido><strong className="font-mono">{escolhido.codigo}</strong> {escolhido.descricao}</p>
          <Button type="button" variant="ghost" className="h-7 px-2" onClick={() => onEscolher(null)}>Trocar</Button>
        </div>
      </div>
    );
  }
  const atual = termo.length >= 2 && resposta?.termo === termo ? resposta : null;
  return (
    <div className="space-y-1">
      <label className={ROTULO}>
        CID-10
        {/* Enter na busca não envia o formulário */}
        <Input type="search" autoComplete="off" value={texto} placeholder="Código ou descrição"
          onChange={(e) => setTexto(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") e.preventDefault(); }} />
      </label>
      <p role="status" className="text-xs text-slate-600">
        {termo.length < 2 ? "Digite ao menos 2 caracteres."
          : !atual ? "Buscando…"
            : atual.erro ? "Não foi possível buscar o CID-10. Altere o texto para tentar de novo."
              : atual.itens.length ? `${atual.itens.length} resultado(s).` : "Nenhum CID-10 encontrado."}
      </p>
      {!!atual?.itens.length && (
        <ul aria-label="Resultados do CID-10" className="max-h-48 divide-y divide-slate-100 overflow-y-auto rounded-md border border-slate-200">
          {atual.itens.map((item) => (
            <li key={item.codigo}>
              <button type="button" className="w-full px-3 py-2 text-left text-sm outline-none hover:bg-teal-50 focus-visible:bg-teal-100" onClick={() => onEscolher(item)}>
                <strong className="font-mono">{item.codigo}</strong> {item.descricao}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
