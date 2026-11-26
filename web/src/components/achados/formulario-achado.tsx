"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import type { PontoNoCorpo } from "@/components/anatomia/visualizador-atlas";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { CATEGORIAS, LADOS, STATUS, type Achado, type Categoria, type Lado, type Status } from "@/lib/achados";
import type { Cid10 } from "@/lib/banco";
import { createClient } from "@/lib/supabase/client";

const CAMPO = "h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none focus-visible:ring-2 focus-visible:ring-teal-700";
const ROTULO = "block space-y-1 text-sm font-medium text-slate-800";

const opcoes = (mapa: Record<string, string>) => Object.entries(mapa).map(([valor, rotulo]) => <option key={valor} value={valor}>{rotulo}</option>);

function hoje() {
  const agora = new Date();
  return new Date(agora.getTime() - agora.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
}

function BuscaCid10({ escolhido, onEscolher }: { escolhido: Cid10 | null; onEscolher: (c: Cid10 | null) => void }) {
  const [texto, setTexto] = useState("");
  const [resposta, setResposta] = useState<{ termo: string; itens: Cid10[]; erro: boolean } | null>(null);
  const termo = texto.trim();

  useEffect(() => {
    if (termo.length < 2) return;
    let valido = true;
    const espera = setTimeout(async () => {
      const { data, error } = await createClient().rpc("buscar_cid10", { p_texto: termo, p_limite: 20 });
      // resposta de um termo antigo não sobrescreve a do atual
      if (valido) setResposta({ termo, itens: data ?? [], erro: !!error });
    }, 300);
    return () => { valido = false; clearTimeout(espera); };
  }, [termo]);

  if (escolhido) {
    return (
      <div className="space-y-1 text-sm">
        <p className="font-medium text-slate-800">CID-10</p>
        <div className="flex items-start justify-between gap-2 rounded-md border border-teal-200 bg-teal-50 px-3 py-2">
          <p data-cid-escolhido><strong className="font-mono">{escolhido.codigo}</strong> {escolhido.descricao}</p>
          <Button type="button" variant="ghost" className="h-7 px-2" onClick={() => onEscolher(null)}>Trocar</Button>
        </div>
      </div>
    );
  }
  const atual = termo.length >= 2 && resposta?.termo === termo ? resposta : null;
  return (
    <div className="space-y-1">
      <label className={ROTULO}>
        CID-10
        {/* Enter na busca não envia o formulário */}
        <Input type="search" autoComplete="off" value={texto} placeholder="Código ou descrição"
          onChange={(e) => setTexto(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") e.preventDefault(); }} />
      </label>
      <p role="status" className="text-xs text-slate-600">
        {termo.length < 2 ? "Digite ao menos 2 caracteres."
          : !atual ? "Buscando…"
            : atual.erro ? "Não foi possível buscar o CID-10. Altere o texto para tentar de novo."
              : atual.itens.length ? `${atual.itens.length} resultado(s).` : "Nenhum CID-10 encontrado."}
      </p>
      {!!atual?.itens.length && (
        <ul aria-label="Resultados do CID-10" className="max-h-48 divide-y divide-slate-100 overflow-y-auto rounded-md border border-slate-200">
          {atual.itens.map((item) => (
            <li key={item.codigo}>
              <button type="button" className="w-full px-3 py-2 text-left text-sm outline-none hover:bg-teal-50 focus-visible:bg-teal-100" onClick={() => onEscolher(item)}>
                <strong className="font-mono">{item.codigo}</strong> {item.descricao}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function FormularioAchado({ pacienteId, ponto, corrigindo, onSalvo, onCancelar }: {
  pacienteId: string;
  /** ponto clicado agora; null = nenhum (sem local, ou correção que mantém o local gravado) */
  ponto: PontoNoCorpo | null;
  /** achado que o novo substitui: os campos partem dele */
  corrigindo?: Achado;
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

  useEffect(() => {
    titulo.current?.focus({ preventScroll: true });
    titulo.current?.scrollIntoView({ block: "nearest" });
  }, [ponto]);

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
