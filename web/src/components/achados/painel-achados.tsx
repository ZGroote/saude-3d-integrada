"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { Marcador, VistaCamera } from "@saude3d/motor-anatomico";
import { CartaoAchado } from "@/components/achados/cartao-achado";
import { ListaEventos } from "@/components/achados/eventos";
import { FormularioAchado } from "@/components/achados/formulario-achado";
import { LinhaDoTempo } from "@/components/achados/linha-do-tempo";
import { ListaAchados } from "@/components/achados/lista-achados";
import { Prontuario3D } from "@/components/anatomia/prontuario-3d";
import type { AtlasPronto, PontoNoCorpo } from "@/components/anatomia/visualizador-atlas";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { corDaEspecialidade, dataDoAchado, filtrar, formatarData, ordenarPorData, SEM_FILTRO, TAMANHO_DO_STATUS, type Achado } from "@/lib/achados";
import type { Sexo } from "@/lib/banco";
import { filtrarEventos, type Evento } from "@/lib/eventos";
import { useHidratado } from "@/lib/hidratacao";
import { createClient } from "@/lib/supabase/client";

const SEM_EVENTOS: Evento[] = [];

export function PainelAchados({ pacienteId, sexo, com3d, inicial, eventos = SEM_EVENTOS, gestacaoEmCurso = false }: {
  pacienteId: string;
  sexo: Sexo;
  com3d: boolean;
  /** eventos clínicos da linha do tempo; null = a busca falhou */
  eventos?: Evento[] | null;
  /** com gestação em curso o corpo oferece a camada gestacional */
  gestacaoEmCurso?: boolean;
  /** achados buscados no servidor; null = a busca falhou; omitido = o navegador busca (rota de desenvolvimento) */
  inicial?: Achado[] | null;
}) {
  const [achados, setAchados] = useState<Achado[] | null>(inicial ?? null);
  const [falha, setFalha] = useState(inicial === null);
  const [revisao, setRevisao] = useState(0);
  const [selecionado, setSelecionado] = useState<string | null>(null);
  // undefined = formulário fechado; ponto null = nenhum ponto clicado
  const [novo, setNovo] = useState<{ ponto: PontoNoCorpo | null; corrigindo?: Achado; comLocal?: boolean } | undefined>();
  const [atlasPronto, setAtlasPronto] = useState<AtlasPronto | null>(null);
  const [vistaCamera, setVistaCamera] = useState<VistaCamera | null>(null);
  const [filtro, setFiltro] = useState(SEM_FILTRO);
  // unidade de quem está logado: só ela vê o botão de corrigir
  const [minhaUnidade, setMinhaUnidade] = useState<string | null>(null);
  const [semPosicao, setSemPosicao] = useState<string[]>([]);
  const [aviso, setAviso] = useState("");
  const veioDoServidor = inicial !== undefined;
  const hidratado = useHidratado();
  // o resto das linhas da lista é montado depois que os marcadores aparecem no corpo
  const [marcadoresNaTela, setMarcadoresNaTela] = useState(!com3d);
  const aoDesenharMarcadores = useCallback(() => setMarcadoresNaTela(true), []);
  useEffect(() => {
    // sem 3D que avise (atlas não escolhido, WebGL indisponível), a lista se completa do mesmo jeito
    const prazo = setTimeout(aoDesenharMarcadores, 8000);
    return () => clearTimeout(prazo);
  }, [aoDesenharMarcadores]);

  useEffect(() => {
    // na abertura vale o que veio do servidor; o navegador só busca depois de salvar ou de tentar de novo
    if (veioDoServidor && !revisao) return;
    let valido = true;
    createClient().rpc("listar_achados", { p_paciente: pacienteId }).then(({ data, error }) => {
      if (!valido) return;
      setFalha(!!error);
      // sem resposta boa não fica lista antiga na tela
      setAchados(error ? null : (data ?? []));
    });
    return () => { valido = false; };
  }, [pacienteId, revisao, veioDoServidor]);

  useEffect(() => {
    let valido = true;
    createClient().rpc("minha_unidade").then(({ data }) => { if (valido) setMinhaUnidade(data); });
    return () => { valido = false; };
  }, []);

  // um filtro só para o corpo e para as listas
  const visiveis = useMemo(() => ordenarPorData(filtrar(achados ?? [], filtro)), [achados, filtro]);
  const marcadores = useMemo<Marcador[]>(
    () => visiveis.flatMap((a) => a.ancora
      ? [{ id: a.id, ancora: a.ancora, vista: a.vista, cor: corDaEspecialidade(a.especialidade), tamanho: TAMANHO_DO_STATUS[a.status] }]
      : []),
    [visiveis],
  );
  const rotulos = useMemo(() => Object.fromEntries(visiveis.map((a) => [
    a.id, `${a.cid10} — ${a.cid10_descricao.slice(0, 100)} — ${formatarData(dataDoAchado(a))}`,
  ])), [visiveis]);
  const aberto = visiveis.find((a) => a.id === selecionado);
  const abrir = useCallback((id: string) => { setNovo(undefined); setSelecionado(id); }, []);
  const registrar = (comLocal: boolean) => { setSelecionado(null); setAviso(""); setNovo({ ponto: null, comLocal }); };
  // SPEC §5.1: a camada gestacional só existe no contexto de gestação, também na busca
  const atlasDaBusca = useMemo(
    () => atlasPronto && (gestacaoEmCurso ? atlasPronto : { ...atlasPronto, indice: atlasPronto.indice.filter((e) => e.sistema !== "gestacional") }),
    [atlasPronto, gestacaoEmCurso],
  );
  const vistaParaSalvar = vistaCamera && vistaCamera.atlas === atlasDaBusca?.atlas
    && vistaCamera.atlas_versao === atlasDaBusca?.versao ? vistaCamera : null;
  // clicar no corpo durante uma correção muda o local dela, sem virar achado novo
  const escolherPonto = (ponto: PontoNoCorpo) => {
    setSelecionado(null);
    setAviso("");
    setNovo((atual) => ({ ponto, corrigindo: atual?.corrigindo }));
  };

  const lateral = (
    <fieldset disabled={!hidratado} className="min-w-0 space-y-4">
      {atlasDaBusca && <Button type="button" className="w-full" onClick={() => registrar(true)}>Achado com local no corpo</Button>}
      <Button type="button" variant={atlasDaBusca ? "outline" : "default"} className="w-full" onClick={() => registrar(false)}>Achado sem local no corpo</Button>
      <p role="status" className="text-sm text-teal-900 empty:hidden">{aviso}</p>
      {novo && (
        <FormularioAchado
          key={novo.corrigindo?.id ?? "novo"}
          pacienteId={pacienteId}
          ponto={novo.ponto}
          corrigindo={novo.corrigindo}
          atlas={atlasDaBusca}
          vista={vistaParaSalvar}
          comLocal={novo.comLocal}
          onEscolherPonto={(ponto) => setNovo((atual) => atual && { ...atual, ponto })}
          onCancelar={() => setNovo(undefined)}
          onSalvo={(id) => {
            setAviso(novo.corrigindo ? "Correção registrada." : "Achado registrado.");
            setNovo(undefined);
            setFiltro(SEM_FILTRO); // o que acabou de ser salvo não pode nascer escondido
            setSelecionado(id);
            setRevisao((n) => n + 1);
          }}
        />
      )}
      {aberto && (
        <CartaoAchado
          key={aberto.id}
          achado={aberto}
          podeCorrigir={!!minhaUnidade && aberto.unidade_id === minhaUnidade}
          onCorrigir={() => { setSelecionado(null); setAviso(""); setNovo({ ponto: null, corrigindo: aberto }); }}
          onFechar={() => setSelecionado(null)}
        />
      )}
      {!!(achados?.length || eventos?.length) && (
        <LinhaDoTempo achados={achados ?? []} eventos={eventos ?? SEM_EVENTOS} visiveis={visiveis} filtro={filtro} onFiltrar={setFiltro} />
      )}
      <Card className="px-5 py-4">
        <h3 className="text-sm font-semibold text-slate-950" aria-live="polite">
          Achados{!achados ? "" : visiveis.length === achados.length ? ` (${achados.length})` : ` (${visiveis.length} de ${achados.length})`}
        </h3>
        {falha ? (
          <div role="alert" className="mt-2 space-y-2 text-sm text-red-800">
            <p>Não foi possível carregar os achados.</p>
            <Button type="button" variant="outline" onClick={() => { setFalha(false); setRevisao((n) => n + 1); }}>Tentar de novo</Button>
          </div>
        ) : !achados ? <p role="status" className="mt-2 text-sm text-slate-600">Carregando achados…</p>
          : !achados.length ? <p className="mt-2 text-sm text-slate-600">Nenhum achado registrado.</p>
            : (
              <>
                {([["No corpo", "achados-no-corpo", true], ["Sem local no corpo", "achados-sem-local", false]] as const)
                  .map(([titulo, id, noCorpo]) => (
                    <ListaAchados key={id} titulo={titulo} id={id} itens={visiveis.filter((a) => !!a.ancora === noCorpo)}
                      liberar={marcadoresNaTela} selecionado={selecionado} semPosicao={com3d ? semPosicao : []} onAbrir={abrir} />
                  ))}
              </>
            )}
        {eventos === null
          ? <p role="alert" className="mt-3 text-sm text-red-800">Não foi possível carregar os eventos clínicos.</p>
          : !!eventos.length && <ListaEventos eventos={filtrarEventos(eventos, filtro)} />}
      </Card>
    </fieldset>
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
  // a lista fica fora do 3D: não espera o código dele para aparecer
  return (
    <div className="grid grid-cols-[minmax(0,1fr)] items-start gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <Prontuario3D
        sexo={sexo}
        prontuario={{
          marcadores, selecionado, rotulos, onVistaCamera: setVistaCamera,
          carregando: !achados && !falha,
          gestacaoEmCurso,
          onEscolherPonto: escolherPonto,
          onSelecionarMarcador: abrir,
          onMarcadoresSemPosicao: setSemPosicao,
          onMarcadoresDesenhados: aoDesenharMarcadores,
          onAtlasPronto: setAtlasPronto,
        }}
      />
      {lateral}
    </div>
  );
}
