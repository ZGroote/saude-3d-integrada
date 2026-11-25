"use client";

import { useEffect, useState } from "react";
import {
  carregarPacote, COR_PADRAO, CORES_SISTEMA, MotorAnatomico, type Ancora, type Pacote,
} from "@saude3d/motor-anatomico";
import { Card } from "@/components/ui/card";
import type { Sexo } from "@/lib/banco";

const BASE = process.env.NEXT_PUBLIC_ATLAS_URL || "/atlas";
const ATLAS = {
  "bp3d-m": { versao: "4.0-1", rotulo: "Masculino (BodyParts3D)" },
  "hra-f": { versao: "1.10-1", rotulo: "Feminino (HRA)" },
} as const;
type Atlas = keyof typeof ATLAS;

// SPEC §7: o atlas segue o sexo; indeterminado → o profissional escolhe
const ATLAS_DO_SEXO: Record<Sexo, Atlas | null> = { feminino: "hra-f", masculino: "bp3d-m", indeterminado: null };

const NOMES_SISTEMA: Record<string, string> = {
  tegumentar: "Pele", esqueletico: "Esquelético", articular: "Articular", muscular: "Muscular", fascia: "Fáscia",
  cardiaco: "Cardíaco", arterial: "Arterial", venoso: "Venoso", linfatico: "Linfático", nervoso: "Nervoso",
  respiratorio: "Respiratório", digestorio: "Digestório", urogenital: "Urogenital", endocrino: "Endócrino",
  sensorial: "Sensorial",
};
const nomeSistema = (id: string) => NOMES_SISTEMA[id] ?? id;
const LADOS: Record<string, string> = { left: "Esquerdo", right: "Direito" };

export default function VisualizadorAtlas({ sexo }: { sexo: Sexo }) {
  const [pedido, setPedido] = useState<Atlas | null>(ATLAS_DO_SEXO[sexo] ?? null);
  // null = ainda verificando se o atlas feminino já foi publicado
  const [temFeminino, setTemFeminino] = useState<boolean | null>(null);

  useEffect(() => {
    if (pedido !== "hra-f") return;
    const cancelar = new AbortController();
    fetch(`${BASE}/hra-f/${ATLAS["hra-f"].versao}/manifesto.json`, { method: "HEAD", signal: cancelar.signal }).then(
      // só 404 significa "ainda não existe"; outros erros aparecem no próprio motor
      (resposta) => setTemFeminino(resposta.status !== 404),
      () => { if (!cancelar.signal.aborted) setTemFeminino(true); },
    );
    return () => cancelar.abort();
  }, [pedido]);

  const verificando = pedido === "hra-f" && temFeminino === null;
  const provisorio = pedido === "hra-f" && temFeminino === false;
  const atlas = provisorio ? "bp3d-m" : pedido;

  return (
    <div className="space-y-4">
      {!ATLAS_DO_SEXO[sexo] && (
        <label className="flex flex-wrap items-center gap-2 text-sm font-medium text-slate-800">
          Atlas anatômico
          <select
            className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm"
            value={pedido ?? ""}
            onChange={(e) => setPedido((e.target.value || null) as Atlas | null)}
          >
            <option value="">Escolha…</option>
            {Object.entries(ATLAS).map(([id, { rotulo }]) => <option key={id} value={id}>{rotulo}</option>)}
          </select>
        </label>
      )}
      {provisorio && (
        <p role="alert" className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <strong>Atlas feminino em preparação.</strong> O corpo exibido é o masculino (BodyParts3D), apenas como
          referência provisória.
        </p>
      )}
      {!atlas ? (
        <p className="text-sm text-slate-600">Sexo indeterminado: escolha o atlas para ver o corpo em 3D.</p>
      ) : verificando ? (
        <p role="status" className="text-sm text-slate-600">Verificando o atlas…</p>
      ) : (
        // trocar de atlas zera a seleção de sistemas e o ponto escolhido
        <Corpo key={atlas} atlas={atlas} />
      )}
    </div>
  );
}

function Corpo({ atlas }: { atlas: Atlas }) {
  const { versao } = ATLAS[atlas];
  const [pacote, setPacote] = useState<Pacote | null>(null);
  const [sistemas, setSistemas] = useState(["tegumentar"]); // abre na pele
  const [ancora, setAncora] = useState<Ancora | null>(null);

  // ponytail: o motor também lê o índice (o navegador reaproveita o cache); expor o pacote pelo motor se pesar
  useEffect(() => {
    const cancelar = new AbortController();
    // a falha já é mostrada pelo motor, por cima do 3D
    carregarPacote(BASE, atlas, versao, cancelar.signal).then(setPacote, () => {});
    return () => cancelar.abort();
  }, [atlas, versao]);

  const entrada = ancora && pacote?.indice.find((e) => e.malha === ancora.malha);

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]" data-atlas={atlas}>
      <Card className="h-[60svh] min-h-96 overflow-hidden lg:h-[75svh]">
        <MotorAnatomico
          atlas={atlas}
          versao={versao}
          baseUrl={BASE}
          sistemasVisiveis={sistemas}
          onEscolherPonto={setAncora}
        />
      </Card>
      <div className="space-y-4">
        <Card className="px-5 py-4" aria-live="polite">
          <h3 className="text-sm font-semibold text-slate-950">Ponto selecionado</h3>
          {!ancora || !entrada ? (
            <p className="mt-2 text-sm text-slate-600">Clique no corpo para identificar uma estrutura.</p>
          ) : (
            <dl className="mt-3 space-y-3 text-sm" data-ancora>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Nome</dt>
                <dd className="font-semibold text-slate-900">{entrada.nome_pt || entrada.nome_en}</dd>
                {entrada.nome_pt && (!entrada.validacao || entrada.validacao === "pendente") && (
                  <dd className="text-xs italic text-amber-800">tradução não revisada</dd>
                )}
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Estrutura</dt>
                <dd className="font-mono text-slate-900">{ancora.estrutura ?? "sem identificador"}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Lado</dt>
                <dd className="text-slate-900">{LADOS[entrada.lateralidade ?? ""] ?? "Não se aplica"}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Sistema</dt>
                <dd className="text-slate-900">{nomeSistema(ancora.sistema)}</dd>
              </div>
            </dl>
          )}
        </Card>
        <Card className="px-5 py-4">
          <fieldset>
            <legend className="text-sm font-semibold text-slate-950">Sistemas</legend>
            {!pacote && <p className="mt-2 text-sm text-slate-600">Carregando lista…</p>}
            <div className="mt-2 grid grid-cols-2 gap-x-3 lg:grid-cols-1">
              {/* SPEC §5.1: a camada gestacional só é ligada no contexto de gestação (Etapa 5) */}
              {pacote?.manifesto.sistemas
                .filter(({ id }) => id !== "gestacional")
                .toSorted((a, b) => nomeSistema(a.id).localeCompare(nomeSistema(b.id), "pt-BR"))
                .map(({ id }) => (
                  <label key={id} className="flex min-h-9 cursor-pointer items-center gap-2 text-sm text-slate-800">
                    <input
                      type="checkbox"
                      className="size-4 accent-teal-800"
                      value={id}
                      checked={sistemas.includes(id)}
                      onChange={(e) =>
                        setSistemas((atuais) => (e.target.checked ? [...atuais, id] : atuais.filter((s) => s !== id)))}
                    />
                    <span
                      aria-hidden="true"
                      className="size-3 rounded-sm"
                      style={{ background: CORES_SISTEMA[id] ?? COR_PADRAO }}
                    />
                    {nomeSistema(id)}
                  </label>
                ))}
            </div>
          </fieldset>
        </Card>
      </div>
    </div>
  );
}
