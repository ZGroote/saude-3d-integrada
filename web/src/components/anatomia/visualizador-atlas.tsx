"use client";

import { useCallback, useEffect, useState } from "react";
import {
  carregarPacote, COR_PADRAO, CORES_SISTEMA, MotorAnatomico, type Ancora, type Marcador, type Pacote,
} from "@saude3d/motor-anatomico";
import { Card } from "@/components/ui/card";
import { ladoDaLateralidade, LADOS, type Lado } from "@/lib/achados";
import type { Sexo } from "@/lib/banco";
import { useHidratado } from "@/lib/hidratacao";

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
  sensorial: "Sensorial", gestacional: "Gestacional",
};
const nomeSistema = (id: string) => NOMES_SISTEMA[id] ?? id;

export type PontoNoCorpo = { ancora: Ancora; nome: string; sistema: string; lado: Lado; naoRevisado: boolean };

/** O que o prontuário liga ao 3D; sem isso (rota /dev/motor) o painel só identifica o ponto clicado. */
type Prontuario = {
  marcadores: Marcador[];
  /** os achados ainda não chegaram: o corpo é baixado depois dos marcadores */
  carregando: boolean;
  /** libera a camada gestacional (SPEC §5.1: só no contexto de gestação) */
  gestacaoEmCurso: boolean;
  selecionado: string | null;
  onEscolherPonto: (ponto: PontoNoCorpo) => void;
  onSelecionarMarcador: (id: string) => void;
  onMarcadoresSemPosicao: (ids: string[]) => void;
  onMarcadoresDesenhados: () => void;
};
const naoRevisado = (e: { nome_pt: string; validacao: string }) => !!e.nome_pt && (!e.validacao || e.validacao === "pendente");

export default function VisualizadorAtlas({ sexo, prontuario, pacoteDeRevisao }: {
  sexo: Sexo;
  prontuario?: Prontuario;
  /** só a rota /dev/motor passa: abre um pacote fora da tabela, para revisão */
  pacoteDeRevisao?: { atlas: string; versao: string };
}) {
  const [pedido, setPedido] = useState<Atlas | null>(ATLAS_DO_SEXO[sexo] ?? null);
  // o atlas feminino é tido como publicado; só o 404 do manifesto leva ao corpo provisório
  const [semFeminino, setSemFeminino] = useState(false);
  const femininoAusente = useCallback(() => setSemFeminino(true), []);
  const hidratado = useHidratado();
  const provisorio = pedido === "hra-f" && semFeminino;
  const atlas = provisorio ? "bp3d-m" : pedido;

  if (pacoteDeRevisao) return <Corpo key={`${pacoteDeRevisao.atlas}/${pacoteDeRevisao.versao}`} {...pacoteDeRevisao} provisorio={false} />;

  return (
    <div className="space-y-4">
      {!ATLAS_DO_SEXO[sexo] && (
        <label className="flex flex-wrap items-center gap-2 text-sm font-medium text-slate-800">
          Atlas anatômico
          <select
            disabled={!hidratado}
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
          referência provisória.{prontuario && " Não é possível marcar achados nele: registre sem local no corpo."}
        </p>
      )}
      {!atlas ? (
        <p className="text-sm text-slate-600">Sexo indeterminado: escolha o atlas para ver o corpo em 3D.</p>
      ) : (
        // trocar de atlas zera a seleção de sistemas e o ponto escolhido
        <Corpo key={atlas} atlas={atlas} versao={ATLAS[atlas].versao} provisorio={provisorio} prontuario={prontuario}
          onAusente={atlas === "hra-f" ? femininoAusente : undefined} />
      )}
    </div>
  );
}

function Corpo({ atlas, versao, provisorio, prontuario, onAusente }: {
  atlas: string;
  versao: string;
  provisorio: boolean;
  prontuario?: Prontuario;
  /** o pacote deste atlas não foi publicado */
  onAusente?: () => void;
}) {
  const [pacote, setPacote] = useState<Pacote | null>(null);
  const [sistemas, setSistemas] = useState(["tegumentar"]); // abre na pele
  const [ancora, setAncora] = useState<Ancora | null>(null);

  // ponytail: o motor também lê o índice (o navegador reaproveita o cache); expor o pacote pelo motor se pesar
  useEffect(() => {
    const cancelar = new AbortController();
    // as outras falhas já são mostradas pelo motor, por cima do 3D
    carregarPacote(BASE, atlas, versao, cancelar.signal).then(setPacote, (erro: Error) => {
      if (/manifesto\.json: HTTP 404/.test(erro.message)) onAusente?.();
    });
    return () => cancelar.abort();
  }, [atlas, versao, onAusente]);

  const entradaDe = (a: Ancora) => pacote?.indice.find((e) => e.malha === a.malha);
  const entrada = ancora && entradaDe(ancora);

  function escolher(a: Ancora) {
    if (!prontuario) return setAncora(a);
    const e = entradaDe(a);
    // SPEC §6: no corpo provisório não se grava âncora. Sem o índice não há nome nem lado.
    if (provisorio || !e) return;
    prontuario.onEscolherPonto({
      ancora: a, nome: e.nome_pt || e.nome_en, sistema: nomeSistema(a.sistema),
      lado: ladoDaLateralidade(e.lateralidade), naoRevisado: naoRevisado(e),
    });
  }

  // achado num sistema desligado ficaria escondido sob a pele: selecioná-lo liga o sistema (uma vez por seleção)
  const doSelecionado = prontuario?.marcadores.find((m) => m.id === prontuario.selecionado && m.ancora.atlas === atlas);
  const [revelado, setRevelado] = useState<string | null>(null);
  if ((doSelecionado?.id ?? null) !== revelado) {
    setRevelado(doSelecionado?.id ?? null);
    const sistema = doSelecionado?.ancora.sistema;
    if (sistema && !sistemas.includes(sistema)) setSistemas([...sistemas, sistema]);
  }

  // no prontuário a coluna ao lado é a dos achados: aqui os sistemas vão para baixo do corpo
  return (
    <div className={prontuario ? "space-y-4" : "grid gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]"} data-atlas={atlas}>
      {/* o motor sobrepõe a atribuição ao 3D; aqui ela vai para baixo do canvas, para não cobrir os pés */}
      <Card className="h-[60svh] min-h-96 overflow-hidden lg:h-[75svh] [&_[data-motor]]:flex [&_[data-motor]]:flex-col [&_[data-motor]>small]:static! [&_[data-motor]>small]:shrink-0 [&_[data-motor]>small]:px-2 [&_[data-motor]>small]:py-1">
        <MotorAnatomico
          atlas={atlas}
          versao={versao}
          baseUrl={BASE}
          sistemasVisiveis={sistemas}
          marcadores={prontuario?.marcadores}
          marcadoresPendentes={prontuario?.carregando}
          selecionado={prontuario?.selecionado}
          onEscolherPonto={escolher}
          onSelecionarMarcador={prontuario?.onSelecionarMarcador}
          onMarcadoresSemPosicao={prontuario?.onMarcadoresSemPosicao}
          onMarcadoresDesenhados={prontuario?.onMarcadoresDesenhados}
        />
      </Card>
      <div className="space-y-4">
        {!prontuario && <Card className="px-5 py-4" aria-live="polite">
          <h3 className="text-sm font-semibold text-slate-950">Ponto selecionado</h3>
          {!ancora || !entrada ? (
            <p className="mt-2 text-sm text-slate-600">Clique no corpo para identificar uma estrutura.</p>
          ) : (
            <dl className="mt-3 space-y-3 text-sm" data-ancora>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Nome</dt>
                <dd className="font-semibold text-slate-900">{entrada.nome_pt || entrada.nome_en}</dd>
                {naoRevisado(entrada) && (
                  <dd className="text-xs italic text-amber-800">tradução não revisada</dd>
                )}
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Estrutura</dt>
                <dd className="font-mono text-slate-900">{ancora.estrutura ?? "sem identificador"}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Lado</dt>
                <dd className="text-slate-900">{LADOS[ladoDaLateralidade(entrada.lateralidade)]}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Sistema</dt>
                <dd className="text-slate-900">{nomeSistema(ancora.sistema)}</dd>
              </div>
            </dl>
          )}
        </Card>}
        <Card className="px-5 py-4">
          <fieldset>
            <legend className="text-sm font-semibold text-slate-950">Sistemas</legend>
            {!pacote && <p className="mt-2 text-sm text-slate-600">Carregando lista…</p>}
            <div className={`mt-2 grid grid-cols-2 gap-x-3 ${prontuario ? "sm:grid-cols-3 xl:grid-cols-5" : "lg:grid-cols-1"}`}>
              {/* SPEC §5.1: a camada gestacional só é ligada no contexto de gestação */}
              {pacote?.manifesto.sistemas
                .filter(({ id }) => id !== "gestacional" || prontuario?.gestacaoEmCurso)
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
            {prontuario?.gestacaoEmCurso && pacote?.manifesto.sistemas.some((s) => s.id === "gestacional") && (
              <p className="mt-2 text-xs text-slate-600">Camada gestacional: representação de referência (placenta, âmnio, cordão), não é a gestação desta paciente.</p>
            )}
          </fieldset>
        </Card>
      </div>
    </div>
  );
}
