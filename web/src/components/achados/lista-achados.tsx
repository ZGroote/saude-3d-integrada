"use client";

import { memo, startTransition, useEffect, useRef, useState, type FocusEvent } from "react";
import { flushSync } from "react-dom";
import { corDaEspecialidade, dataDoAchado, formatarData, STATUS, type Achado } from "@/lib/achados";

/** Linhas na primeira pintura (mais do que cabe na tela) e em cada lote seguinte. */
const LOTE = 30;
/** Foco a esta distância do fim das linhas montadas monta o resto, antes que o teclado chegue lá. */
const FOLGA = 3;

function quandoOcioso(tarefa: () => void) {
  if (typeof requestIdleCallback === "function") {
    const id = requestIdleCallback(tarefa, { timeout: 500 });
    return () => cancelIdleCallback(id);
  }
  const id = setTimeout(tarefa, 50);
  return () => clearTimeout(id);
}

/**
 * Lista de achados montada aos poucos: o começo vem na primeira pintura e o resto em lotes, quando `liberar`.
 * Nenhuma linha fica inalcançável: foco perto do fim, o botão "Mostrar os outros", Ctrl/Cmd+F e um achado
 * selecionado montam o que falta na hora.
 */
export function ListaAchados({ titulo, id, itens, liberar, selecionado, semPosicao, onAbrir }: {
  titulo: string;
  id: string;
  itens: Achado[];
  liberar: boolean;
  selecionado: string | null;
  /** ids que o corpo atual não consegue desenhar */
  semPosicao: string[];
  onAbrir: (id: string) => void;
}) {
  const [montadas, setMontadas] = useState(LOTE);
  const lista = useRef<HTMLUListElement>(null);
  const faltam = Math.max(0, itens.length - montadas);

  // o achado selecionado (por um marcador, por exemplo) tem de existir na lista
  const indice = itens.findIndex((a) => a.id === selecionado);
  if (indice >= montadas) setMontadas(indice + LOTE);

  useEffect(() => {
    if (!liberar || !faltam) return;
    // em transição: um toque no meio da montagem passa na frente
    return quandoOcioso(() => startTransition(() => setMontadas((n) => n + LOTE)));
  }, [liberar, faltam]);

  const montarTudo = () => flushSync(() => setMontadas(Number.MAX_SAFE_INTEGER));

  useEffect(() => {
    if (!faltam) return;
    // a busca do navegador só acha o que está no documento
    const aoTeclar = (e: KeyboardEvent) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "f") montarTudo(); };
    window.addEventListener("keydown", aoTeclar);
    return () => window.removeEventListener("keydown", aoTeclar);
  }, [faltam]);

  const focar = (posicao: number) => lista.current?.querySelectorAll("button")[posicao]?.focus();
  const mostrarOutros = (posicao: number) => { montarTudo(); focar(posicao); };

  return (
    <div className="mt-3">
      <h4 id={id} className="text-xs font-semibold uppercase tracking-wide text-slate-600">{titulo} ({itens.length})</h4>
      {!itens.length ? <p className="mt-1 text-sm text-slate-600">Nenhum.</p> : (
        <div className="mt-1 max-h-96 overflow-y-auto">
          <ul ref={lista} aria-labelledby={id} aria-busy={faltam > 0} className="divide-y divide-slate-100"
            onFocus={(e) => {
              if (faltam && Number((e.target as HTMLElement).closest("li")?.ariaPosInSet) > montadas - FOLGA) montarTudo();
            }}>
            {itens.slice(0, montadas).map((a, i) => (
              <Linha key={a.id} achado={a} posicao={i + 1} total={itens.length} selecionada={a.id === selecionado}
                naoExibido={semPosicao.includes(a.id)} onAbrir={onAbrir} />
            ))}
          </ul>
          {faltam > 0 && (
            <button type="button" className="w-full rounded-md px-1 py-2 text-sm font-medium text-teal-800 outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-teal-700"
              // com o mouse, segue para a primeira linha nova; chegando pelo teclado de baixo para cima, para a última
              onMouseDown={(e) => e.preventDefault()} onClick={() => mostrarOutros(montadas)}
              onFocus={(e: FocusEvent) => mostrarOutros(e.relatedTarget && lista.current?.contains(e.relatedTarget) ? montadas : itens.length - 1)}>
              Mostrar os outros {faltam} achados
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/** Memorizada: um lote novo não redesenha as linhas que já estão na tela. */
const Linha = memo(function Linha({ achado: a, posicao, total, selecionada, naoExibido, onAbrir }: {
  achado: Achado;
  posicao: number;
  total: number;
  selecionada: boolean;
  naoExibido: boolean;
  onAbrir: (id: string) => void;
}) {
  return (
    // content-visibility: o navegador pula o layout e a pintura das linhas fora da tela
    <li aria-posinset={posicao} aria-setsize={total} className="[contain-intrinsic-size:auto_6rem] [content-visibility:auto]">
      <button type="button" data-achado={a.id} data-dia={dataDoAchado(a)} aria-pressed={selecionada} onClick={() => onAbrir(a.id)}
        className="flex w-full gap-2 rounded-md px-1 py-2 text-left text-sm outline-none hover:bg-teal-50 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-teal-700 aria-pressed:bg-teal-50">
        <span aria-hidden="true" className="mt-1 size-3 shrink-0 rounded-full" style={{ background: corDaEspecialidade(a.especialidade) }} />
        <span className="min-w-0">
          <span className="block text-xs font-semibold text-teal-800">{a.inicio ? "Início" : "Registro"} {formatarData(dataDoAchado(a))}</span>
          <span className="block text-slate-900"><strong className="font-mono">{a.cid10}</strong> {a.cid10_descricao}</span>
          <span className="block text-xs text-slate-600">{a.autor_nome} · {a.unidade_nome} · {formatarData(a.criado_em)}</span>
          <span className="block text-xs text-slate-600">
            {a.especialidade ?? "Sem especialidade"} · {STATUS[a.status]}
            {!a.ancora ? " · sem local no corpo" : naoExibido ? " · não exibido neste corpo" : ""}
          </span>
        </span>
      </button>
    </li>
  );
});
