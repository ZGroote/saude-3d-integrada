"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { BuscaEstrutura } from "@/components/achados/busca-estrutura";
import { pontoDaEntrada, type AtlasPronto, type PontoNoCorpo } from "@/components/anatomia/visualizador-atlas";
import { BuscaCid10 } from "@/components/busca-cid10";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { CATEGORIAS, LADOS, STATUS, type Achado, type Categoria, type Lado, type Status } from "@/lib/achados";
import type { Cid10 } from "@/lib/banco";
import type { VistaCamera } from "@saude3d/motor-anatomico";
import { ancoraNaEntrada } from "@/lib/fhir/ancora";
import { CAMPO, hoje, ROTULO } from "@/lib/formulario";
import { createClient } from "@/lib/supabase/client";

const opcoes = (mapa: Record<string, string>) => Object.entries(mapa).map(([valor, rotulo]) => <option key={valor} value={valor}>{rotulo}</option>);

export function FormularioAchado({ pacienteId, ponto, corrigindo, atlas, comLocal, vista, onEscolherPonto, onSalvo, onCancelar }: {
  pacienteId: string;
  /** ponto clicado agora; null = nenhum (sem local, ou correção que mantém o local gravado) */
  ponto: PontoNoCorpo | null;
  /** achado que o novo substitui: os campos partem dele */
  corrigindo?: Achado;
  /** onde a busca por nome procura; null = sem corpo para marcar */
  atlas: AtlasPronto | null;
  /** aberto para marcar um local: o foco começa na busca de estrutura */
  comLocal?: boolean;
  /** Última câmera do mesmo atlas; nulo quando não há vista registrada nesta sessão. */
  vista?: VistaCamera | null;
  /** estrutura escolhida pela busca; null = tirar o local escolhido */
  onEscolherPonto: (ponto: PontoNoCorpo | null) => void;
  onSalvo: (id: string) => void;
  onCancelar: () => void;
}) {
  const [cid, setCid] = useState<Cid10 | null>(
    corrigindo ? { codigo: corrigindo.cid10, descricao: corrigindo.cid10_descricao } : null,
  );
  const ancora = ponto?.ancora ?? corrigindo?.ancora ?? null;
  const [erro, setErro] = useState("");
  const [salvando, setSalvando] = useState(false);
  const titulo = useRef<HTMLHeadingElement>(null);

  const busca = useRef<HTMLInputElement>(null);
  // o foco vai ao formulário quando ele abre e a cada toque no corpo; a escolha pela busca não o move
  const doCorpo = ponto?.daBusca ? "busca" : ponto;
  const temBusca = !!atlas;

  useEffect(() => {
    if (doCorpo === "busca") return;
    const alvo = comLocal && !doCorpo && temBusca ? busca.current : titulo.current;
    alvo?.focus({ preventScroll: true });
    alvo?.scrollIntoView({ block: "nearest" });
  }, [doCorpo, comLocal, temBusca]);

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (!cid) return setErro("Escolha um código CID-10 na busca.");
    const campos = new FormData(evento.currentTarget);
    const texto = (nome: string) => String(campos.get(nome) ?? "").trim();
    setErro("");
    setSalvando(true);
    const { data, error } = await createClient().rpc("registrar_achado", {
      p_paciente: pacienteId,
      p_ancora: ancora,
      p_cid10: cid.codigo,
      p_categoria: texto("categoria") as Categoria,
      p_lado: texto("lado") as Lado,
      p_status: texto("status") as Status,
      p_inicio: texto("inicio") || null,
      p_observacao: texto("observacao") || null,
      p_substitui: corrigindo?.id ?? null,
      p_vista: vista ?? null,
    });
    setSalvando(false);
    if (error || !data) return setErro("O achado não foi salvo. Confira os dados e o vínculo com o paciente e tente de novo.");
    onSalvo(data);
  }

  return (
    <Card className="px-5 py-4">
      <form onSubmit={salvar} className="space-y-3" aria-labelledby="titulo-novo-achado">
        <h3 id="titulo-novo-achado" ref={titulo} tabIndex={-1} className="text-sm font-semibold text-slate-950 outline-none">
          {corrigindo ? `Corrigir ${corrigindo.cid10}` : "Novo achado"}
        </h3>
        {corrigindo && <p className="text-xs text-slate-600">A correção registra um novo achado; o anterior fica no histórico.</p>}
        {ponto ? (
          <p className="text-sm text-slate-600" data-ancora>
            <strong className="text-slate-900">{ponto.nome}</strong> · {ponto.sistema} · <span className="font-mono">{ponto.ancora.estrutura ?? "sem identificador"}</span>
            {ponto.naoRevisado && <span className="block text-xs italic text-amber-800">tradução não revisada</span>}
          </p>
        ) : (
          <p className="text-sm text-slate-600">
            {ancora
              ? <>Local mantido: <span className="font-mono">{ancora.estrutura ?? ancora.malha}</span>. Clique no corpo para mudar.</>
              : "Sem local no corpo."}
          </p>
        )}
        {atlas && (
          <BuscaEstrutura ref={busca} indice={atlas.indice}
            onEscolher={({ entrada }) => onEscolherPonto({ ...pontoDaEntrada(ancoraNaEntrada(entrada, atlas), entrada), daBusca: true })} />
        )}
        {ponto && <Button type="button" variant="ghost" className="h-8 px-2" onClick={() => onEscolherPonto(null)}>Tirar este local</Button>}
        <BuscaCid10 escolhido={cid} onEscolher={(c) => { setCid(c); setErro(""); }} />
        <label className={ROTULO}>Categoria
          <select name="categoria" required className={CAMPO} defaultValue={corrigindo?.categoria ?? ""}>
            <option value="" disabled>Escolha…</option>{opcoes(CATEGORIAS)}
          </select>
        </label>
        <label className={ROTULO}>Lado
          {/* a key refaz o campo quando outro ponto é clicado, sem apagar o resto do formulário */}
          <select key={JSON.stringify(ancora)} name="lado" className={CAMPO} defaultValue={ponto?.lado ?? corrigindo?.lado ?? "nao_se_aplica"}>{opcoes(LADOS)}</select>
        </label>
        <label className={ROTULO}>Status<select name="status" className={CAMPO} defaultValue={corrigindo?.status ?? "ativo"}>{opcoes(STATUS)}</select></label>
        <label className={ROTULO}>Início<Input type="date" name="inicio" max={hoje()} defaultValue={corrigindo?.inicio ?? ""} /></label>
        <label className={ROTULO}>Observação<textarea name="observacao" rows={3} maxLength={2000} defaultValue={corrigindo?.observacao ?? ""} className={`${CAMPO} h-auto py-2`} /></label>
        {erro && <p role="alert" className="text-sm text-red-800">{erro}</p>}
        <div className="flex gap-2">
          <Button type="submit" disabled={salvando}>{salvando ? "Salvando…" : corrigindo ? "Salvar correção" : "Salvar achado"}</Button>
          <Button type="button" variant="outline" onClick={onCancelar} disabled={salvando}>Cancelar</Button>
        </div>
      </form>
    </Card>
  );
}
