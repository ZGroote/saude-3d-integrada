"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  carregarPacote, COR_PADRAO, CORES_SISTEMA, filtrarMarcadoresNestaEstrutura, MotorAnatomico,
  type Ancora, type ComandoCamera, type EntradaIndice, type Marcador, type NomeVista, type Pacote, type VistaCamera,
} from "@saude3d/motor-anatomico";
import { Card } from "@/components/ui/card";
import { ladoDaLateralidade, LADOS, type Lado } from "@/lib/achados";
import type { Sexo } from "@/lib/banco";
import { useHidratado } from "@/lib/hidratacao";
import { LACUNAS, nomearIndiceLacunas } from "@/lib/lacunas";

const BASE = process.env.NEXT_PUBLIC_ATLAS_URL || "/atlas";
const ATLAS = {
  "bp3d-m": { versao: "4.0-1", rotulo: "Masculino (BodyParts3D)" },
  "hra-f": { versao: "1.10-1", rotulo: "Feminino (HRA)" },
} as const;
type Atlas = keyof typeof ATLAS;
type ComandoSemSeq = ComandoCamera extends infer C ? C extends { seq: number } ? Omit<C, "seq"> : never : never;

// SPEC §7: o atlas segue o sexo; indeterminado → o profissional escolhe
const ATLAS_DO_SEXO: Record<Sexo, Atlas | null> = { feminino: "hra-f", masculino: "bp3d-m", indeterminado: null };

const NOMES_SISTEMA: Record<string, string> = {
  tegumentar: "Pele", esqueletico: "Esquelético", articular: "Articular", muscular: "Muscular", fascia: "Fáscia",
  cardiaco: "Cardíaco", arterial: "Arterial", venoso: "Venoso", linfatico: "Linfático", nervoso: "Nervoso",
  respiratorio: "Respiratório", digestorio: "Digestório", urogenital: "Urogenital", endocrino: "Endócrino",
  sensorial: "Sensorial", gestacional: "Gestacional",
};
const nomeSistema = (id: string) => NOMES_SISTEMA[id] ?? id;

export type PontoNoCorpo = {
  ancora: Ancora; nome: string; sistema: string; lado: Lado; naoRevisado: boolean;
  /** escolhido pela busca por nome: o foco fica onde está */
  daBusca?: boolean;
};

/** O atlas em que dá para marcar agora, com o índice dele. */
export type AtlasPronto = { atlas: string; versao: string; indice: EntradaIndice[] };

export function pontoDaEntrada(ancora: Ancora, e: EntradaIndice): PontoNoCorpo {
  return {
    ancora, nome: e.nome_pt || e.nome_en, sistema: nomeSistema(ancora.sistema),
    lado: ladoDaLateralidade(e.lateralidade), naoRevisado: naoRevisado(e),
  };
}

/** O que o prontuário liga ao 3D; sem isso (rota /dev/motor) o painel só identifica o ponto clicado. */
type Prontuario = {
  marcadores: Marcador[];
  /** os achados ainda não chegaram: o corpo é baixado depois dos marcadores */
  carregando: boolean;
  /** libera a camada gestacional (SPEC §5.1: só no contexto de gestação) */
  gestacaoEmCurso: boolean;
  selecionado: string | null;
  rotulos?: Record<string, string>;
  onVistaCamera?: (vista: VistaCamera) => void;
  onEscolherPonto: (ponto: PontoNoCorpo) => void;
  onSelecionarMarcador: (id: string) => void;
  onMarcadoresSemPosicao: (ids: string[]) => void;
  onMarcadoresDesenhados: () => void;
  /** null = não há onde marcar (carregando ou corpo provisório) */
  onAtlasPronto: (atlas: AtlasPronto | null) => void;
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
  const [ocultas, setOcultas] = useState<string[]>([]);
  const [isoladas, setIsoladas] = useState<string[] | null>(null);
  const [transparencia, setTransparencia] = useState(false);
  const [camadasRemovidas, setCamadasRemovidas] = useState(0);
  const [totalCamadas, setTotalCamadas] = useState(0);
  const [comandoCamera, setComandoCamera] = useState<ComandoCamera>();
  const sequenciaCamera = useRef(0);
  const [vistaCamera, setVistaCamera] = useState<Omit<VistaCamera, "sistemas"> | null>(null);

  // ponytail: o motor também lê o índice (o navegador reaproveita o cache); expor o pacote pelo motor se pesar
  useEffect(() => {
    const cancelar = new AbortController();
    // as outras falhas já são mostradas pelo motor, por cima do 3D
    carregarPacote(BASE, atlas, versao, cancelar.signal).then(setPacote, (erro: Error) => {
      if (/manifesto\.json: HTTP 404/.test(erro.message)) onAusente?.();
    });
    return () => cancelar.abort();
  }, [atlas, versao, onAusente]);

  // Normaliza rótulos do índice uma única vez antes de entregá-lo à busca, ao formulário e aos cards.
  const indice = useMemo(() => pacote ? nomearIndiceLacunas(atlas, versao, pacote.indice) : [], [pacote, atlas, versao]);
  const entradaDe = (a: Ancora) => indice.find((e) => e.malha === a.malha);

  const onAtlasPronto = prontuario?.onAtlasPronto;
  useEffect(() => {
    // SPEC §6: no corpo provisório não se grava âncora, nem pela busca por nome
    if (!pacote || provisorio) return;
    onAtlasPronto?.({ atlas, versao, indice });
    return () => onAtlasPronto?.(null);
  }, [pacote, provisorio, atlas, versao, indice, onAtlasPronto]);

  function escolher(a: Ancora) {
    setAncora(a);
    if (!prontuario) return;
    const e = entradaDe(a);
    // SPEC §6: no corpo provisório não se grava âncora. Sem o índice não há nome nem lado.
    if (provisorio || !e) return;
    prontuario.onEscolherPonto(pontoDaEntrada(a, e));
  }

  const emitirComando = useCallback((comando: ComandoSemSeq) => {
    const seq = ++sequenciaCamera.current;
    setComandoCamera({ ...comando, seq } as ComandoCamera);
  }, []);
  const onVistaCamera = prontuario?.onVistaCamera;
  const registrarVista = useCallback((vista: Omit<VistaCamera, "sistemas">) => setVistaCamera(vista), []);
  useEffect(() => {
    if (vistaCamera) onVistaCamera?.({ ...vistaCamera, sistemas: [...sistemas] });
  }, [vistaCamera, sistemas, onVistaCamera]);
  const registrarCamadas = useCallback((total: number) => setTotalCamadas(total), []);
  const camadasAplicadas = sistemas.includes("muscular")
    ? Math.min(camadasRemovidas, totalCamadas)
    : 0;
  const entradaAtual = ancora ? entradaDe(ancora) : undefined;
  const malhasDaEstrutura = useMemo(() => {
    if (!ancora) return [];
    const encontradas = indice.filter((e) => ancora.estrutura !== null
      ? e.estrutura === ancora.estrutura
      : e.estrutura === null && e.malha === ancora.malha).map((e) => e.malha);
    return encontradas.length ? encontradas : [ancora.malha];
  }, [ancora, indice]);
  const achadosDaEstrutura = useMemo(() => ancora && prontuario
    ? filtrarMarcadoresNestaEstrutura(prontuario.marcadores, ancora.estrutura, ancora.malha)
    : [], [ancora, prontuario]);
  const mostrarTudo = () => { setOcultas([]); setIsoladas(null); setCamadasRemovidas(0); };

  const nomeVista: Record<NomeVista, string> = {
    anterior: "Vista anterior", posterior: "Vista posterior", direita: "Vista lateral direita",
    esquerda: "Vista lateral esquerda", superior: "Vista superior", inferior: "Vista inferior",
  };

  // achado num sistema desligado ficaria escondido sob a pele: selecioná-lo liga o sistema (uma vez por seleção)
  const doSelecionado = prontuario?.marcadores.find((m) => m.id === prontuario.selecionado && m.ancora.atlas === atlas);
  const ultimaSelecao = useRef<string | null>(null);
  useEffect(() => {
    if (!doSelecionado) {
      ultimaSelecao.current = null;
      return;
    }
    if (ultimaSelecao.current === doSelecionado.id) return;
    ultimaSelecao.current = doSelecionado.id;
    const salva = doSelecionado.vista;
    queueMicrotask(() => {
      if (ultimaSelecao.current !== doSelecionado.id) return;
      if (salva && salva.atlas === atlas && salva.atlas_versao === versao) {
        setSistemas([...new Set([...salva.sistemas, doSelecionado.ancora.sistema])]);
        emitirComando({ acao: "restaurar", vista: salva });
      } else {
        setSistemas((atuais) => atuais.includes(doSelecionado.ancora.sistema)
          ? atuais : [...atuais, doSelecionado.ancora.sistema]);
        emitirComando({ acao: "focar" });
      }
    });
  }, [doSelecionado, atlas, versao, emitirComando]);

  // no prontuário a coluna ao lado é a dos achados: aqui os sistemas vão para baixo do corpo
  return (
    <div className={prontuario ? "space-y-4" : "grid gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]"} data-atlas={atlas}>
      <div className="space-y-2">
      <div role="group" aria-label="Ferramentas do corpo" className="flex flex-wrap items-center gap-2 rounded-md border border-slate-300 bg-white p-2 text-xs shadow-sm">
        <div className="flex flex-wrap gap-1">
          <button type="button" className="min-h-9 rounded border px-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-800" onClick={() => emitirComando({ acao: "enquadrar" })}>Corpo inteiro</button>
          <button type="button" className="min-h-9 rounded border px-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-800" disabled={!prontuario?.selecionado} onClick={() => emitirComando({ acao: "focar" })}>Focar achado</button>
        </div>
        <fieldset className="flex flex-wrap items-center gap-1 border-l pl-2">
          <legend className="sr-only">Vista</legend>
          {(Object.keys(nomeVista) as NomeVista[]).map((vista) => (
            <button key={vista} type="button" aria-label={nomeVista[vista]} className="min-h-9 rounded border px-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-800" onClick={() => emitirComando({ acao: "vista", vista })}>{nomeVista[vista]}</button>
          ))}
        </fieldset>
        <button type="button" aria-pressed={transparencia} className="min-h-9 rounded border px-2 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-800" onClick={() => setTransparencia((v) => !v)}>Transparência: {transparencia ? "ligada" : "desligada"}</button>
        {sistemas.includes("muscular") && totalCamadas > 0 && (
          <div role="group" aria-label="Camadas musculares aproximadas" aria-describedby="descricao-camadas-musculares" className="flex flex-wrap items-center gap-1">
            <span className="mr-auto">Camadas musculares aproximadas</span>
            <button type="button" aria-label="Recolocar uma camada muscular" className="size-9 rounded border focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-800" disabled={camadasAplicadas <= 0} onClick={() => setCamadasRemovidas((n) => Math.max(0, n - 1))}>−</button>
            <span aria-live="polite" className="min-w-5 text-center">{camadasAplicadas}</span>
            <button type="button" aria-label="Remover uma camada muscular" className="size-9 rounded border focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-800" disabled={camadasAplicadas >= totalCamadas} onClick={() => setCamadasRemovidas((n) => Math.min(totalCamadas, n + 1))}>+</button>
            <span id="descricao-camadas-musculares" className="basis-full text-xs text-slate-600">Agrupadas pela distância até a pele; não são planos anatômicos.</span>
          </div>
        )}
        {(ocultas.length > 0 || isoladas !== null) && <button type="button" className="min-h-9 rounded border px-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-800" onClick={mostrarTudo}>Mostrar tudo</button>}
      </div>
      {!!(LACUNAS[`${atlas}/${versao}`]?.some((l) => !l.parcial)) && (
        <p role="note" className="text-sm text-amber-900">Faltam neste corpo: {LACUNAS[`${atlas}/${versao}`]!.filter((l) => !l.parcial).map((l) => l.nome).join(", ")}.</p>
      )}
      {/* A barra fica fora do canvas para não cobrir o corpo em telas estreitas. */}
      <Card className="h-[60svh] min-h-96 overflow-hidden lg:h-[75svh] [&_[data-motor]]:flex [&_[data-motor]]:flex-col [&_[data-motor]>small]:static! [&_[data-motor]>small]:shrink-0 [&_[data-motor]>small]:px-2 [&_[data-motor]>small]:py-1">
        <div className="h-full min-h-0" data-vista-camera={vistaCamera ? "registrada" : "nao-registrada"}>
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
          comandoCamera={comandoCamera}
          onVista={registrarVista}
          ocultas={ocultas}
          isoladas={isoladas}
          transparencia={transparencia}
          camadasRemovidas={camadasAplicadas}
          onCamadas={registrarCamadas}
        />
        </div>
      </Card>
      </div>
      <div className="space-y-4">
        {(!prontuario || ancora) && <Card className="px-5 py-4" aria-live="polite">
          <h3 className="text-sm font-semibold text-slate-950">{prontuario ? "Estrutura selecionada" : "Ponto selecionado"}</h3>
          {!ancora || !entradaAtual ? (
            <p className="mt-2 text-sm text-slate-600">Clique no corpo para identificar uma estrutura.</p>
          ) : (
            <dl className="mt-3 space-y-3 text-sm" data-ancora>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-600">Nome</dt>
                <dd className="font-semibold text-slate-900">{entradaAtual.nome_pt || entradaAtual.nome_en}</dd>
                {entradaAtual.nome_pt && entradaAtual.nome_en && entradaAtual.nome_pt !== entradaAtual.nome_en && <dd className="text-sm text-slate-600">{entradaAtual.nome_en}</dd>}
                {naoRevisado(entradaAtual) && (
                  <dd className="text-xs italic text-amber-800">tradução não revisada</dd>
                )}
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-600">Estrutura</dt>
                <dd className="font-mono text-slate-900">{ancora.estrutura ?? "sem identificador"}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-600">Lado</dt>
                <dd className="text-slate-900">{LADOS[ladoDaLateralidade(entradaAtual.lateralidade)]}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-600">Sistema</dt>
                <dd className="text-slate-900">{nomeSistema(ancora.sistema)}</dd>
              </div>
            </dl>
          )}
          {ancora && entradaAtual && <div className="mt-3 flex flex-wrap gap-2">
            <button type="button" className="min-h-9 rounded border px-3 focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-800" onClick={() => setOcultas((atual) => [...new Set([...atual, ...malhasDaEstrutura])])}>Ocultar estrutura</button>
            <button type="button" className="min-h-9 rounded border px-3 focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-800" onClick={() => setIsoladas(malhasDaEstrutura)}>Isolar estrutura</button>
          </div>}
          {prontuario && ancora && <section className="mt-4 border-t pt-3">
            <h4 className="text-sm font-semibold text-slate-900">Achados nesta estrutura</h4>
            {!achadosDaEstrutura.length ? <p className="mt-1 text-sm text-slate-600">Nenhum achado nesta estrutura.</p> : <ul className="mt-1 space-y-1">
              {achadosDaEstrutura.map((m) => <li key={m.id}><button type="button" className="min-h-9 text-left text-sm text-teal-900 underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-800" onClick={() => prontuario.onSelecionarMarcador(m.id)}>{prontuario.rotulos?.[m.id] ?? m.id}</button></li>)}
            </ul>}
          </section>}
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
