"use client";

import { useEffect, useMemo, useState } from "react";
import type { Marcador } from "@saude3d/motor-anatomico";
import { CartaoAchado } from "@/components/achados/cartao-achado";
import { FormularioAchado } from "@/components/achados/formulario-achado";
import { LinhaDoTempo } from "@/components/achados/linha-do-tempo";
import { Prontuario3D } from "@/components/anatomia/prontuario-3d";
import type { PontoNoCorpo } from "@/components/anatomia/visualizador-atlas";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  corDaEspecialidade, dataDoAchado, filtrar, formatarData, ordenarPorData, SEM_FILTRO, STATUS, TAMANHO_DO_STATUS, type Achado,
} from "@/lib/achados";
import type { Sexo } from "@/lib/banco";
import { useHidratado } from "@/lib/hidratacao";
import { createClient } from "@/lib/supabase/client";

export function PainelAchados({ pacienteId, sexo, com3d, inicial }: {
  pacienteId: string;
  sexo: Sexo;
  com3d: boolean;
  /** achados buscados no servidor; null = a busca falhou; omitido = o navegador busca (rota de desenvolvimento) */
  inicial?: Achado[] | null;
}) {
  const [achados, setAchados] = useState<Achado[] | null>(inicial ?? null);
  const [falha, setFalha] = useState(inicial === null);
  const [revisao, setRevisao] = useState(0);
  const [selecionado, setSelecionado] = useState<string | null>(null);
  // undefined = formulário fechado; ponto null = nenhum ponto clicado
  const [novo, setNovo] = useState<{ ponto: PontoNoCorpo | null; corrigindo?: Achado } | undefined>();
  const [filtro, setFiltro] = useState(SEM_FILTRO);
  // unidade de quem está logado: só ela vê o botão de corrigir
  const [minhaUnidade, setMinhaUnidade] = useState<{ id: string; nome: string | null } | null>(null);
  const [semPosicao, setSemPosicao] = useState<string[]>([]);
  const [aviso, setAviso] = useState("");
  const veioDoServidor = inicial !== undefined;
  const hidratado = useHidratado();

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
    const banco = createClient();
    banco.rpc("minha_unidade").then(async ({ data: id }) => {
      if (!id) return;
      const { data } = await banco.from("unidades").select("nome").eq("id", id).maybeSingle();
      if (valido) setMinhaUnidade({ id, nome: data?.nome ?? null });
    });
    return () => { valido = false; };
  }, []);

  // um filtro só para o corpo e para as listas
  const visiveis = useMemo(() => ordenarPorData(filtrar(achados ?? [], filtro)), [achados, filtro]);
  const marcadores = useMemo<Marcador[]>(
    () => visiveis.flatMap((a) => a.ancora
      ? [{ id: a.id, ancora: a.ancora, cor: corDaEspecialidade(a.especialidade), tamanho: TAMANHO_DO_STATUS[a.status] }]
      : []),
    [visiveis],
  );
  const aberto = visiveis.find((a) => a.id === selecionado);
  // ponytail: sem unidade_id (antes da migração 0004) compara o nome; o banco confere o id ao salvar.
  // Apagar a reserva e a leitura do nome quando a 0004 estiver aplicada.
  const daMinhaUnidade = (a: Achado) =>
    !!minhaUnidade && (a.unidade_id ? a.unidade_id === minhaUnidade.id : a.unidade_nome === minhaUnidade.nome);
  const abrir = (id: string) => { setNovo(undefined); setSelecionado(id); };
  const registrar = (ponto: PontoNoCorpo | null) => { setSelecionado(null); setAviso(""); setNovo({ ponto }); };
  // clicar no corpo durante uma correção muda o local dela, sem virar achado novo
  const escolherPonto = (ponto: PontoNoCorpo) => {
    setSelecionado(null);
    setAviso("");
    setNovo((atual) => ({ ponto, corrigindo: atual?.corrigindo }));
  };

  function linha(a: Achado) {
    return (
      <li key={a.id}>
        <button type="button" data-achado={a.id} data-dia={dataDoAchado(a)} aria-pressed={a.id === selecionado} onClick={() => abrir(a.id)}
          className="flex w-full gap-2 rounded-md px-1 py-2 text-left text-sm outline-none hover:bg-teal-50 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-teal-700 aria-pressed:bg-teal-50">
          <span aria-hidden="true" className="mt-1 size-3 shrink-0 rounded-full" style={{ background: corDaEspecialidade(a.especialidade) }} />
          <span className="min-w-0">
            <span className="block text-xs font-semibold text-teal-800">{a.inicio ? "Início" : "Registro"} {formatarData(dataDoAchado(a))}</span>
            <span className="block text-slate-900"><strong className="font-mono">{a.cid10}</strong> {a.cid10_descricao}</span>
            <span className="block text-xs text-slate-600">{a.autor_nome} · {a.unidade_nome} · {formatarData(a.criado_em)}</span>
            <span className="block text-xs text-slate-500">
              {a.especialidade ?? "Sem especialidade"} · {STATUS[a.status]}
              {!a.ancora ? " · sem local no corpo" : com3d && semPosicao.includes(a.id) ? " · não exibido neste corpo" : ""}
            </span>
          </span>
        </button>
      </li>
    );
  }

  function lista(titulo: string, id: string, itens: Achado[]) {
    return (
      <div className="mt-3">
        <h4 id={id} className="text-xs font-semibold uppercase tracking-wide text-slate-500">{titulo} ({itens.length})</h4>
        {itens.length
          ? <ul aria-labelledby={id} className="mt-1 max-h-96 divide-y divide-slate-100 overflow-y-auto">{itens.map(linha)}</ul>
          : <p className="mt-1 text-sm text-slate-600">Nenhum.</p>}
      </div>
    );
  }

  const lateral = (
    <fieldset disabled={!hidratado} className="min-w-0 space-y-4">
      <Button type="button" className="w-full" onClick={() => registrar(null)}>Achado sem local no corpo</Button>
      <p role="status" className="text-sm text-teal-900 empty:hidden">{aviso}</p>
      {novo && (
        <FormularioAchado
          key={novo.corrigindo?.id ?? "novo"}
          pacienteId={pacienteId}
          ponto={novo.ponto}
          corrigindo={novo.corrigindo}
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
          podeCorrigir={daMinhaUnidade(aberto)}
          onCorrigir={() => { setSelecionado(null); setAviso(""); setNovo({ ponto: null, corrigindo: aberto }); }}
          onFechar={() => setSelecionado(null)}
        />
      )}
      {!!achados?.length && <LinhaDoTempo achados={achados} visiveis={visiveis} filtro={filtro} onFiltrar={setFiltro} />}
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
                {lista("No corpo", "achados-no-corpo", visiveis.filter((a) => a.ancora))}
                {lista("Sem local no corpo", "achados-sem-local", visiveis.filter((a) => !a.ancora))}
              </>
            )}
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
          marcadores, selecionado,
          carregando: !achados && !falha,
          onEscolherPonto: escolherPonto,
          onSelecionarMarcador: abrir,
          onMarcadoresSemPosicao: setSemPosicao,
        }}
      />
      {lateral}
    </div>
  );
}
