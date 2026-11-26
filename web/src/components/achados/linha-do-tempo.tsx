"use client";

import { useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { corDaEspecialidade, dataDoAchado, formatarData, SEM_FILTRO, STATUS, type Achado, type Filtro, type Status } from "@/lib/achados";

const CAMPO = "h-10 w-full rounded-md border border-slate-300 bg-white px-2 text-sm text-slate-900 outline-none focus-visible:ring-2 focus-visible:ring-teal-700";
const ROTULO = "block space-y-1 text-xs font-medium text-slate-700";

/** Filtros e linha do tempo escrevem no mesmo `filtro`: os campos de data e os deslizantes são o mesmo intervalo. */
export function LinhaDoTempo({ achados, visiveis, filtro, onFiltrar }: {
  achados: Achado[];
  visiveis: Achado[];
  filtro: Filtro;
  onFiltrar: (filtro: Filtro) => void;
}) {
  const especialidades = useMemo(() => [...new Set(achados.map((a) => a.especialidade ?? ""))].sort((a, b) => a.localeCompare(b, "pt-BR")), [achados]);
  // dias com achado, em ordem: as paradas dos deslizantes
  const dias = useMemo(() => [...new Set(achados.map(dataDoAchado))].sort(), [achados]);
  const marcados = useMemo(() => new Set(visiveis.map((a) => a.id)), [visiveis]);
  const ultimo = dias.length - 1;
  // posição de cada deslizante a partir das datas, que também podem ser digitadas
  const inicio = filtro.de ? Math.min(ultimo, dias.filter((d) => d < filtro.de).length) : 0;
  const fim = filtro.ate ? Math.max(0, dias.filter((d) => d <= filtro.ate).length - 1) : ultimo;
  const primeiroDia = Date.parse(dias[0]!);
  const duracao = Date.parse(dias[ultimo]!) - primeiroDia;
  const posicao = (dia: string) => (duracao ? ((Date.parse(dia) - primeiroDia) / duracao) * 100 : 50);
  // nas pontas o filtro fica aberto, para não esconder o que for registrado depois
  const intervalo = (i: number, f: number) => onFiltrar({ ...filtro, de: i ? dias[i]! : "", ate: f < ultimo ? dias[f]! : "" });

  return (
    <Card className="px-5 py-4">
      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-slate-950">Filtros e linha do tempo</legend>
        <div className="grid grid-cols-2 gap-2">
          <label className={ROTULO}>Especialidade
            <select name="filtro-especialidade" className={CAMPO} value={filtro.especialidade === null ? "*" : filtro.especialidade}
              onChange={(e) => onFiltrar({ ...filtro, especialidade: e.target.value === "*" ? null : e.target.value })}>
              <option value="*">Todas</option>
              {especialidades.map((e) => <option key={e} value={e}>{e || "Sem especialidade"}</option>)}
            </select>
          </label>
          <label className={ROTULO}>Status
            <select name="filtro-status" className={CAMPO} value={filtro.status} onChange={(e) => onFiltrar({ ...filtro, status: e.target.value as Status | "" })}>
              <option value="">Todos</option>
              {Object.entries(STATUS).map(([valor, rotulo]) => <option key={valor} value={valor}>{rotulo}</option>)}
            </select>
          </label>
          <label className={ROTULO}>De
            <Input type="date" name="filtro-de" className="px-2" value={filtro.de} max={filtro.ate || undefined} onChange={(e) => onFiltrar({ ...filtro, de: e.target.value })} />
          </label>
          <label className={ROTULO}>Até
            <Input type="date" name="filtro-ate" className="px-2" value={filtro.ate} min={filtro.de || undefined} onChange={(e) => onFiltrar({ ...filtro, ate: e.target.value })} />
          </label>
        </div>
        {/* desenho de apoio: os mesmos achados estão nas listas, em ordem de data */}
        <div aria-hidden="true" data-linha-do-tempo className="relative mx-1 h-6">
          <span className="absolute inset-x-0 top-1/2 h-px bg-slate-300" />
          {achados.map((a) => (
            <span key={a.id} title={`${formatarData(dataDoAchado(a))} · ${a.cid10}`}
              className={`absolute top-1/2 size-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full ${marcados.has(a.id) ? "" : "opacity-20"}`}
              style={{ left: `${posicao(dataDoAchado(a))}%`, background: corDaEspecialidade(a.especialidade) }} />
          ))}
        </div>
        <p className="flex justify-between text-xs text-slate-500"><span>{formatarData(dias[0]!)}</span><span>{formatarData(dias[ultimo]!)}</span></p>
        {ultimo > 0 && (
          <>
            <label className={ROTULO}>Início do intervalo
              <input type="range" name="intervalo-inicio" className="w-full accent-teal-800" min={0} max={ultimo} value={inicio}
                aria-valuetext={formatarData(dias[inicio]!)} onChange={(e) => { const i = Number(e.target.value); intervalo(i, Math.max(i, fim)); }} />
            </label>
            <label className={ROTULO}>Fim do intervalo
              <input type="range" name="intervalo-fim" className="w-full accent-teal-800" min={0} max={ultimo} value={fim}
                aria-valuetext={formatarData(dias[fim]!)} onChange={(e) => { const f = Number(e.target.value); intervalo(Math.min(inicio, f), f); }} />
            </label>
          </>
        )}
        <Button type="button" variant="outline" className="w-full" onClick={() => onFiltrar(SEM_FILTRO)}>Limpar filtros</Button>
      </fieldset>
    </Card>
  );
}
