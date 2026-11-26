"use client";

import { useState, useTransition } from "react";
import { analisar, confirmar } from "@/app/importar/actions";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { LIMITE_BYTES, type Previa, type Relatorio } from "@/lib/fhir/tipos";
import type { ErroImportacao } from "@/lib/fhir/importar";
import { useHidratado } from "@/lib/hidratacao";

function Numeros({ itens }: { itens: [string, string | number][] }) {
  return (
    <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-3">
      {itens.map(([nome, valor]) => (
        <div key={nome}>
          <dt className="text-xs font-medium uppercase tracking-wide text-slate-600">{nome}</dt>
          <dd className="text-lg font-semibold text-slate-900">{valor}</dd>
        </div>
      ))}
    </dl>
  );
}

function Erros({ erros }: { erros: ErroImportacao[] }) {
  if (!erros.length) return <p className="mt-3 text-sm text-slate-600">Nenhum erro.</p>;
  return (
    <div className="mt-4">
      <h3 id="titulo-erros" className="text-xs font-semibold uppercase tracking-wide text-slate-600">Recursos com erro ({erros.length})</h3>
      <ul aria-labelledby="titulo-erros" className="mt-1 max-h-72 space-y-1 overflow-y-auto text-sm">
        {erros.map((e, i) => <li key={i} className="break-words"><span className="font-mono">{e.id}</span> — {e.motivo}</li>)}
      </ul>
    </div>
  );
}

export function FormularioImportacao() {
  const hidratado = useHidratado();
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [previa, setPrevia] = useState<Previa | null>(null);
  const [relatorio, setRelatorio] = useState<Relatorio | null>(null);
  const [erro, setErro] = useState("");
  const [ocupado, iniciar] = useTransition();

  const escolher = (novo: File | null) => {
    setPrevia(null);
    setRelatorio(null);
    setArquivo(novo);
    setErro(novo && novo.size > LIMITE_BYTES ? "O arquivo passa de 10 MB." : "");
  };

  function enviar(hash?: string) {
    if (!arquivo || arquivo.size > LIMITE_BYTES) return;
    const dados = new FormData();
    dados.set("arquivo", arquivo);
    if (hash) dados.set("hash", hash);
    setErro("");
    iniciar(async () => {
      try {
        const resposta = await (hash ? confirmar(dados) : analisar(dados));
        if ("erro" in resposta) return setErro(resposta.erro);
        if ("previa" in resposta) setPrevia(resposta.previa);
        else { setPrevia(null); setRelatorio(resposta.relatorio); }
      } catch {
        setErro(hash
          ? "A importação foi interrompida. Parte pode ter sido gravada: analise e confirme o mesmo arquivo de novo (nada é duplicado)."
          : "Não foi possível analisar o arquivo. Tente novamente.");
      }
    });
  }

  return (
    <div className="mt-6 space-y-4">
      <Card className="px-5 py-4">
        <fieldset disabled={!hidratado || ocupado} className="flex flex-wrap items-end gap-3">
          <label className="block space-y-1 text-sm font-medium text-slate-800">Bundle FHIR R4 (.json, até 10 MB)
            <input type="file" name="arquivo" accept=".json,application/json,application/fhir+json" className="block text-sm"
              onChange={(e) => escolher(e.target.files?.[0] ?? null)} />
          </label>
          <Button type="button" disabled={!arquivo || arquivo.size > LIMITE_BYTES} onClick={() => enviar()}>Analisar</Button>
        </fieldset>
        <p role="status" className="mt-2 text-sm text-slate-600 empty:hidden">
          {ocupado ? (previa ? "Importando… não feche esta página." : "Analisando…") : ""}
        </p>
        {erro && <p role="alert" className="mt-2 text-sm text-red-800">{erro}</p>}
      </Card>

      {previa && (
        <Card className="px-5 py-4">
          <h2 className="text-lg font-semibold text-slate-950">Prévia: nada foi gravado ainda</h2>
          <Numeros itens={[
            ["Pacientes", previa.pacientes],
            ["Já vinculados à sua unidade", previa.vinculados ?? "não foi possível saber"],
            ["Demais (novos ou a vincular)", previa.vinculados === null ? "—" : previa.pacientes - previa.vinculados],
            ["Condições com local no corpo", previa.condicoesComLocal],
            ["Condições sem local", previa.condicoesSemLocal],
            ["Eventos (linha do tempo)", previa.eventos],
          ]} />
          {previa.naoMapeadas > 0 && <p className="mt-2 text-sm text-slate-600">{previa.naoMapeadas} condições citam uma parte do corpo sem mapeamento: entram sem local.</p>}
          <Erros erros={previa.erros} />
          {previa.bloqueio && <p role="alert" className="mt-3 text-sm text-red-800">{previa.bloqueio}</p>}
          <div className="mt-4 flex gap-2">
            <Button type="button" disabled={ocupado || !!previa.bloqueio} onClick={() => enviar(previa.hash)}>Confirmar importação</Button>
            <Button type="button" variant="outline" disabled={ocupado} onClick={() => setPrevia(null)}>Cancelar</Button>
          </div>
        </Card>
      )}

      {relatorio && (
        <Card className="px-5 py-4" data-relatorio>
          <h2 className="text-lg font-semibold text-slate-950">Relatório da importação</h2>
          {/* o banco devolve o mesmo id para o que já existia: aqui se conta o que o banco aceitou, não só o novo */}
          <Numeros itens={[
            ["Pacientes (novos + já existentes)", relatorio.pacientes], ["Condições (novas + já existentes)", relatorio.condicoes],
            ["Eventos (novos + já existentes)", relatorio.eventos],
          ]} />
          <p className="mt-2 text-sm text-slate-600">O que já tinha sido importado não é criado de novo. Registro: <span className="font-mono">{relatorio.importacao}</span></p>
          {!relatorio.concluida && <p role="alert" className="mt-2 text-sm text-red-800">Os recursos foram processados, mas o registro da importação não foi fechado.</p>}
          <Erros erros={relatorio.erros} />
        </Card>
      )}
    </div>
  );
}
