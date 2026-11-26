import { formatarData } from "@/lib/achados";
import type { Evento } from "@/lib/eventos";

const TIPOS = { Observation: "Observação", Encounter: "Atendimento" } as const;

/** Eventos importados na linha do tempo: não são pontos no corpo. */
export function ListaEventos({ eventos }: { eventos: Evento[] }) {
  return (
    <div className="mt-3">
      <h4 id="eventos-clinicos" className="text-xs font-semibold uppercase tracking-wide text-slate-600">Eventos clínicos ({eventos.length})</h4>
      {!eventos.length ? <p className="mt-1 text-sm text-slate-600">Nenhum no período.</p> : (
        <ul aria-labelledby="eventos-clinicos" className="mt-1 max-h-96 divide-y divide-slate-100 overflow-y-auto">
          {eventos.map((e) => (
            <li key={e.id} data-evento={e.tipo} className="px-1 py-2 text-sm [contain-intrinsic-size:auto_4rem] [content-visibility:auto]">
              <span className="block text-xs font-semibold text-teal-800">{e.data ? formatarData(e.data) : "Sem data"} · {TIPOS[e.tipo]}</span>
              <span className="block text-slate-900">{e.descricao || e.codigo || "Sem descrição"}</span>
              {e.valor && <span className="block text-xs text-slate-600">{e.valor}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
