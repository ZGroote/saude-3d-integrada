"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition, type FormEvent } from "react";
import { BuscaCid10 } from "@/components/busca-cid10";
import { Condicoes } from "@/components/gestacao/recorte";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { formatarData } from "@/lib/achados";
import type { Cid10 } from "@/lib/banco";
import { hoje, ROTULO } from "@/lib/formulario";
import { calcularDpp, DESFECHOS, nomeDaCrianca, type Gestacao } from "@/lib/gestacao";
import { useHidratado } from "@/lib/hidratacao";
import { createClient } from "@/lib/supabase/client";

/** Executa uma escrita e, se der certo, refaz a página no servidor. */
function useGravar() {
  const router = useRouter();
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [atualizando, iniciar] = useTransition();
  async function gravar(chamada: PromiseLike<{ error: unknown; data: unknown }>, falha: string, esperaId = true) {
    setErro("");
    setEnviando(true);
    const { data, error } = await chamada;
    setEnviando(false);
    // sem vínculo ativo as funções devolvem null, sem erro
    if (error || (esperaId && !data)) {
      setErro(falha);
      return false;
    }
    iniciar(() => router.refresh());
    return true;
  }
  return { gravar, erro, setErro, ocupado: enviando || atualizando };
}

export function Gestacoes({ maeId, gestacoes }: { maeId: string; gestacoes: Gestacao[] }) {
  const emCurso = gestacoes.some((g) => g.desfecho === "em_curso");
  return (
    <div className="mt-4 space-y-4">
      {emCurso
        ? <p className="text-sm text-slate-600">Há uma gestação em curso. Encerre-a, ou registre o nascimento, antes de abrir outra.</p>
        : <NovaGestacao maeId={maeId} />}
      {!gestacoes.length && <p className="text-sm text-slate-600">Nenhuma gestação registrada.</p>}
      {gestacoes.map((g) => <CartaoGestacao key={g.gestacao_id} maeId={maeId} gestacao={g} />)}
    </div>
  );
}

function NovaGestacao({ maeId }: { maeId: string }) {
  const hidratado = useHidratado();
  const { gravar, erro, ocupado } = useGravar();
  const [dum, setDum] = useState("");
  const dpp = calcularDpp(dum);

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const inicio = String(new FormData(evento.currentTarget).get("inicio_pre_natal") ?? "");
    await gravar(
      createClient().rpc("registrar_gestacao", { p_mae: maeId, p_dum: dum, p_inicio_pre_natal: inicio || null }),
      "A gestação não foi registrada. Confira as datas, o vínculo e se já não há outra em curso.",
    );
  }

  return (
    <Card className="px-5 py-4">
      <form onSubmit={salvar} aria-labelledby="titulo-nova-gestacao">
        <fieldset disabled={!hidratado || ocupado} className="space-y-3">
          <h3 id="titulo-nova-gestacao" className="text-sm font-semibold text-slate-950">Registrar gestação</h3>
          <div className="grid gap-3 sm:grid-cols-3">
            <label className={ROTULO}>Data da última menstruação (DUM)
              <Input type="date" name="dum" required max={hoje()} value={dum} onChange={(e) => setDum(e.target.value)} />
            </label>
            <label className={ROTULO}>Início do pré-natal
              <Input type="date" name="inicio_pre_natal" min={dum || undefined} max={hoje()} />
            </label>
            <p className={ROTULO}>Data provável do parto (DPP)
              <output className="block h-11 py-2.5 font-semibold text-slate-900">{dpp ? formatarData(dpp) : "informe a DUM"}</output>
            </p>
          </div>
          {erro && <p role="alert" className="text-sm text-red-800">{erro}</p>}
          <Button type="submit">Registrar gestação</Button>
        </fieldset>
      </form>
    </Card>
  );
}

function CartaoGestacao({ maeId, gestacao: g }: { maeId: string; gestacao: Gestacao }) {
  const titulo = `gestacao-${g.gestacao_id}`;
  const nascimento = `/pacientes/${maeId}/nascimento?gestacao=${g.gestacao_id}`;
  return (
    <Card className="px-5 py-4" data-gestacao={g.desfecho}>
      <article aria-labelledby={titulo} className="space-y-4">
        <div>
          <h3 id={titulo} className="text-sm font-semibold text-slate-950">Gestação: {DESFECHOS[g.desfecho]}</h3>
          <p className="mt-1 text-sm text-slate-600">
            DUM {g.dum ? formatarData(g.dum) : "não informada"} · DPP {g.dpp ? formatarData(g.dpp) : "não calculada"} ·
            pré-natal {g.inicio_pre_natal ? `desde ${formatarData(g.inicio_pre_natal)}` : "sem data de início"}
          </p>
        </div>
        <section>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-600">Condições</h4>
          <Condicoes condicoes={g.condicoes} />
          <NovaCondicao gestacaoId={g.gestacao_id} />
        </section>
        {!!g.nascimentos?.length && (
          <section>
            <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-600">Nascimentos</h4>
            <ul className="mt-1 space-y-1 text-sm">
              {g.nascimentos.map((n) => (
                <li key={n.crianca_id}>
                  <Link prefetch={false} href={`/pacientes/${n.crianca_id}`} className="alvo font-semibold text-teal-800 underline">{nomeDaCrianca(n)}</Link>
                  <span className="text-slate-600"> · {formatarData(n.data)}{n.peso_g == null ? "" : ` · ${n.peso_g.toLocaleString("pt-BR")} g`}</span>
                </li>
              ))}
            </ul>
          </section>
        )}
        {g.desfecho === "em_curso" && (
          <div className="flex flex-wrap items-center gap-3 border-t border-slate-100 pt-3">
            <Link prefetch={false} href={nascimento} className="alvo inline-flex h-10 items-center rounded-md bg-teal-800 px-4 text-sm font-semibold text-white hover:bg-teal-900">Registrar nascimento</Link>
            <Encerrar gestacaoId={g.gestacao_id} />
          </div>
        )}
        {g.desfecho === "nascido_vivo" && (
          <Link prefetch={false} href={nascimento} className="alvo inline-block text-sm font-medium text-teal-800 underline">Registrar outro recém-nascido desta gestação</Link>
        )}
      </article>
    </Card>
  );
}

function NovaCondicao({ gestacaoId }: { gestacaoId: string }) {
  const hidratado = useHidratado();
  const { gravar, erro, setErro, ocupado } = useGravar();
  const [cid, setCid] = useState<Cid10 | null>(null);

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (!cid) return setErro("Escolha um código CID-10 na busca.");
    const formulario = evento.currentTarget;
    const semana = Number(new FormData(formulario).get("semana"));
    const salvou = await gravar(
      createClient().rpc("registrar_condicao_gestacao", { p_gestacao: gestacaoId, p_cid10: cid.codigo, p_semana: semana }),
      "A condição não foi registrada. Confira os dados e o vínculo com a paciente.",
    );
    if (salvou) { setCid(null); formulario.reset(); }
  }

  return (
    <details className="mt-2">
      <summary className="cursor-pointer text-sm font-medium text-teal-800">Adicionar condição</summary>
      <form onSubmit={salvar} className="mt-2 max-w-xl">
        <fieldset disabled={!hidratado || ocupado} className="space-y-3">
          <BuscaCid10 escolhido={cid} onEscolher={(c) => { setCid(c); setErro(""); }} />
          <label className={ROTULO}>Semana da gestação (0 a 45)
            <Input type="number" name="semana" required min={0} max={45} step={1} inputMode="numeric" />
          </label>
          {erro && <p role="alert" className="text-sm text-red-800">{erro}</p>}
          <Button type="submit">Salvar condição</Button>
        </fieldset>
      </form>
    </details>
  );
}

/** Encerrar sem nascimento não tem volta: pede confirmação na própria tela. */
function Encerrar({ gestacaoId }: { gestacaoId: string }) {
  const hidratado = useHidratado();
  const { gravar, erro, ocupado } = useGravar();
  const [desfecho, setDesfecho] = useState<"obito_fetal" | "aborto" | null>(null);

  return (
    <fieldset disabled={!hidratado || ocupado} className="flex flex-wrap items-center gap-2">
      {!desfecho ? (
        (["obito_fetal", "aborto"] as const).map((d) => (
          <Button key={d} type="button" variant="outline" onClick={() => setDesfecho(d)}>Encerrar: {DESFECHOS[d].toLowerCase()}</Button>
        ))
      ) : (
        <>
          <p className="text-sm text-slate-900">Encerrar como <strong>{DESFECHOS[desfecho].toLowerCase()}</strong>? Não dá para desfazer.</p>
          <Button type="button" onClick={() => gravar(
            createClient().rpc("encerrar_gestacao", { p_gestacao: gestacaoId, p_desfecho: desfecho }),
            "A gestação não foi encerrada. Confira o vínculo com a paciente.", false,
          )}>Confirmar</Button>
          <Button type="button" variant="outline" onClick={() => setDesfecho(null)}>Cancelar</Button>
        </>
      )}
      {erro && <p role="alert" className="text-sm text-red-800">{erro}</p>}
    </fieldset>
  );
}
