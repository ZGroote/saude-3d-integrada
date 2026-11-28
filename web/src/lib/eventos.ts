import { diaDe, type Filtro } from "@/lib/achados";

/** Linha de `listar_eventos` (supabase/migrations/0005); só as colunas que o app usa. */
export type Evento = {
  id: string;
  tipo: "Observation" | "Encounter";
  data: string | null;
  codigo: string | null;
  descricao: string | null;
  valor: string | null;
};

/** Eventos não têm especialidade nem status: só o período os filtra. Sem data não entra num período. */
export function filtrarEventos(eventos: Evento[], { de, ate }: Filtro) {
  return eventos
    .filter((e) => (!de && !ate) || (!!e.data && (!de || diaDe(e.data) >= de) && (!ate || diaDe(e.data) <= ate)))
    .toSorted((a, b) => (a.data ?? "9").localeCompare(b.data ?? "9"));
}
