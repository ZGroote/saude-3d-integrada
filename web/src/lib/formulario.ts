export const CAMPO = "h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none focus-visible:ring-2 focus-visible:ring-teal-700";
export const ROTULO = "block space-y-1 text-sm font-medium text-slate-800";

/** Hoje no relógio do navegador (AAAA-MM-DD), para o `max` dos campos de data. */
export function hoje() {
  const agora = new Date();
  return new Date(agora.getTime() - agora.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
}
