"use client";

import { useMemo, useState, type KeyboardEvent, type Ref } from "react";
import type { EntradaIndice } from "@saude3d/motor-anatomico";
import { Input } from "@/components/ui/input";
import { LADO_DA_ESTRUTURA, listarEstruturas, procurarEstruturas, type Estrutura } from "@/lib/estruturas";
import { ROTULO } from "@/lib/formulario";

const MAXIMO = 30;

/** Combobox de estrutura anatômica (padrão ARIA 1.2): setas percorrem, Enter escolhe, Esc fecha. */
export function BuscaEstrutura({ indice, onEscolher, ref }: {
  indice: EntradaIndice[];
  onEscolher: (estrutura: Estrutura) => void;
  ref?: Ref<HTMLInputElement>;
}) {
  const estruturas = useMemo(() => listarEstruturas(indice), [indice]);
  const [texto, setTexto] = useState("");
  const [aberto, setAberto] = useState(false);
  const [ativo, setAtivo] = useState(0);
  const achadas = useMemo(() => procurarEstruturas(estruturas, texto), [estruturas, texto]);
  const visiveis = achadas.slice(0, MAXIMO);
  const mostrar = aberto && visiveis.length > 0;

  function escolher(e: Estrutura) {
    onEscolher(e);
    setTexto("");
    setAberto(false);
  }

  function mover(para: number) {
    const indiceNovo = (para + visiveis.length) % visiveis.length;
    setAtivo(indiceNovo);
    document.getElementById(`estrutura-${indiceNovo}`)?.scrollIntoView({ block: "nearest" });
  }

  function teclas(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault(); // a busca nunca envia o formulário
      if (mostrar) escolher(visiveis[ativo]!);
    } else if (e.key === "Escape" && (mostrar || texto)) {
      e.preventDefault();
      e.stopPropagation();
      if (mostrar) setAberto(false);
      else setTexto("");
    } else if ((e.key === "ArrowDown" || e.key === "ArrowUp") && visiveis.length) {
      e.preventDefault();
      if (!mostrar) setAberto(true);
      else mover(ativo + (e.key === "ArrowDown" ? 1 : -1));
    }
  }

  return (
    <div className="space-y-1">
      <label className={ROTULO} htmlFor="busca-estrutura">Buscar estrutura do corpo</label>
      <Input id="busca-estrutura" ref={ref} role="combobox" autoComplete="off" value={texto} placeholder="Nome em português ou inglês"
        aria-expanded={mostrar} aria-controls="lista-estruturas" aria-autocomplete="list" aria-activedescendant={mostrar ? `estrutura-${ativo}` : undefined}
        onChange={(e) => { setTexto(e.target.value); setAberto(true); setAtivo(0); }} onKeyDown={teclas} onBlur={() => setAberto(false)} />
      <p role="status" className="text-xs text-slate-600">
        {texto.trim().length < 2 ? "Digite ao menos 2 caracteres."
          : !achadas.length ? "Nenhuma estrutura encontrada."
            : achadas.length > MAXIMO ? `${achadas.length} estruturas; as primeiras ${MAXIMO} na lista. Digite mais para refinar.`
              : `${achadas.length} estrutura(s).`}
      </p>
      <ul id="lista-estruturas" role="listbox" aria-label="Estruturas encontradas" hidden={!mostrar}
        className="max-h-60 divide-y divide-slate-100 overflow-y-auto rounded-md border border-slate-200">
        {visiveis.map((e, i) => (
          <li key={e.chave} id={`estrutura-${i}`} role="option" aria-selected={i === ativo}
            className="flex min-h-11 cursor-pointer flex-col justify-center px-3 py-1 text-sm text-slate-900 aria-selected:bg-teal-100"
            // o clique não pode tirar o foco do campo antes de escolher
            onMouseDown={(ev) => ev.preventDefault()} onClick={() => escolher(e)}>
            <span>{e.nome}{LADO_DA_ESTRUTURA[e.lateralidade ?? ""] && <strong> · lado {LADO_DA_ESTRUTURA[e.lateralidade!]}</strong>}</span>
            {e.nomeIngles !== e.nome && <span lang="en" className="text-xs text-slate-600">{e.nomeIngles}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
