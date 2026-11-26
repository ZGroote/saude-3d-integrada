"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { Marcador } from "@saude3d/motor-anatomico";
import { FormularioAchado } from "@/components/achados/formulario-achado";
import { Prontuario3D } from "@/components/anatomia/prontuario-3d";
import type { PontoNoCorpo } from "@/components/anatomia/visualizador-atlas";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CATEGORIAS, corDaEspecialidade, LADOS, STATUS, TAMANHO_DO_STATUS, type Achado } from "@/lib/achados";
import type { Sexo } from "@/lib/banco";
import { createClient } from "@/lib/supabase/client";

// data pura (início) é lida em UTC para não voltar um dia; carimbo de hora usa o fuso do navegador
function data(iso: string) {
  const soData = iso.length === 10;
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium", timeZone: soData ? "UTC" : undefined })
    .format(new Date(soData ? `${iso}T12:00:00Z` : iso));
}

export function PainelAchados({ pacienteId, sexo, com3d }: { pacienteId: string; sexo: Sexo; com3d: boolean }) {
  const [achados, setAchados] = useState<Achado[] | null>(null);
  const [falha, setFalha] = useState(false);
  const [revisao, setRevisao] = useState(0);
  const [selecionado, setSelecionado] = useState<string | null>(null);
  // undefined = formulário fechado; ponto null = sem local no corpo
  const [novo, setNovo] = useState<{ ponto: PontoNoCorpo | null } | undefined>();
  const [semPosicao, setSemPosicao] = useState<string[]>([]);
  const [aviso, setAviso] = useState("");

  useEffect(() => {
    let valido = true;
    createClient().rpc("listar_achados", { p_paciente: pacienteId }).then(({ data, error }) => {
      if (!valido) return;
      setFalha(!!error);
      // sem resposta boa não fica lista antiga na tela
      setAchados(error ? null : (data ?? []));
    });
    return () => { valido = false; };
  }, [pacienteId, revisao]);

  const marcadores = useMemo<Marcador[]>(
    () => (achados ?? []).flatMap((a) => a.ancora
      ? [{ id: a.id, ancora: a.ancora, cor: corDaEspecialidade(a.especialidade), tamanho: TAMANHO_DO_STATUS[a.status] }]
      : []),
    [achados],
  );
  const aberto = achados?.find((a) => a.id === selecionado);
  const abrir = (id: string) => { setNovo(undefined); setSelecionado(id); };
  const registrar = (ponto: PontoNoCorpo | null) => { setSelecionado(null); setAviso(""); setNovo({ ponto }); };

  const lateral = (
    <>
      <Button type="button" className="w-full" onClick={() => registrar(null)}>Achado sem local no corpo</Button>
      <p role="status" className="text-sm text-teal-900 empty:hidden">{aviso}</p>
      {novo && (
        <FormularioAchado
          pacienteId={pacienteId}
          ponto={novo.ponto}
          onCancelar={() => setNovo(undefined)}
          onSalvo={(id) => { setNovo(undefined); setSelecionado(id); setAviso("Achado registrado."); setRevisao((n) => n + 1); }}
        />
      )}
      {aberto && <Cartao key={aberto.id} achado={aberto} onFechar={() => setSelecionado(null)} />}
      <Card className="px-5 py-4">
        <h3 id="titulo-achados" className="text-sm font-semibold text-slate-950">Achados{achados ? ` (${achados.length})` : ""}</h3>
        {falha ? (
          <div role="alert" className="mt-2 space-y-2 text-sm text-red-800">
            <p>Não foi possível carregar os achados.</p>
            <Button type="button" variant="outline" onClick={() => { setFalha(false); setRevisao((n) => n + 1); }}>Tentar de novo</Button>
          </div>
        ) : !achados ? <p role="status" className="mt-2 text-sm text-slate-600">Carregando achados…</p>
          : !achados.length ? <p className="mt-2 text-sm text-slate-600">Nenhum achado registrado.</p>
            : (
              <ul aria-labelledby="titulo-achados" className="mt-2 divide-y divide-slate-100">
                {achados.map((a) => (
                  <li key={a.id}>
                    <button type="button" data-achado={a.id} aria-pressed={a.id === selecionado} onClick={() => abrir(a.id)}
                      className="flex w-full gap-2 rounded-md px-1 py-2 text-left text-sm outline-none hover:bg-teal-50 focus-visible:ring-2 focus-visible:ring-teal-700 aria-pressed:bg-teal-50">
                      <span aria-hidden="true" className="mt-1 size-3 shrink-0 rounded-full" style={{ background: corDaEspecialidade(a.especialidade) }} />
                      <span className="min-w-0">
                        <span className="block text-slate-900"><strong className="font-mono">{a.cid10}</strong> {a.descricao}</span>
                        <span className="block text-xs text-slate-600">{a.autor_nome} · {a.unidade_nome} · {data(a.criado_em)}</span>
                        <span className="block text-xs text-slate-500">
                          {a.especialidade ?? "Sem especialidade"} · {STATUS[a.status]}
                          {!a.ancora ? " · sem local no corpo" : com3d && semPosicao.includes(a.id) ? " · não exibido neste corpo" : ""}
                        </span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
      </Card>
    </>
  );

  if (!com3d) {
    return (
      <div className="space-y-4">
        {/* SPEC §5.1: nunca um corpo adulto no prontuário de criança; idade desconhecida também não abre o 3D */}
        <Card className="px-6 py-10 text-center text-sm leading-6 text-slate-600">Corpo em 3D indisponível. Não há atlas pediátrico: prontuário de criança, ou sem data de nascimento, não usa corpo adulto.</Card>
        {lateral}
      </div>
    );
  }
  return (
    <Prontuario3D
      sexo={sexo}
      prontuario={{
        marcadores, selecionado, lateral,
        onEscolherPonto: registrar,
        onSelecionarMarcador: abrir,
        onMarcadoresSemPosicao: setSemPosicao,
      }}
    />
  );
}

function Cartao({ achado: a, onFechar }: { achado: Achado; onFechar: () => void }) {
  const titulo = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    titulo.current?.focus({ preventScroll: true });
    titulo.current?.scrollIntoView({ block: "nearest" });
  }, []);
  const campos: [string, string][] = [
    ["Categoria", CATEGORIAS[a.categoria]], ["Status", STATUS[a.status]], ["Lado", LADOS[a.lado]],
    ["Início", a.inicio ? data(a.inicio) : "Não informado"], ["Autor", a.autor_nome],
    ["Especialidade", a.especialidade ?? "Não informada"], ["Unidade", a.unidade_nome], ["Registrado em", data(a.criado_em)],
    ["Observação", a.observacao || "Sem observação"],
  ];
  return (
    <Card className="px-5 py-4" data-cartao={a.id} onKeyDown={(e) => { if (e.key === "Escape") onFechar(); }}>
      <div className="flex items-start justify-between gap-2">
        <h3 ref={titulo} tabIndex={-1} className="text-sm font-semibold text-slate-950 outline-none"><span className="font-mono">{a.cid10}</span> {a.descricao}</h3>
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
    </Card>
  );
}
