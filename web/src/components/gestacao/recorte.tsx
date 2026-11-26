import { Card } from "@/components/ui/card";
import { formatarData } from "@/lib/achados";
import type { CondicaoGestacao, RecorteGestacional } from "@/lib/gestacao";

export function Condicoes({ condicoes }: { condicoes: CondicaoGestacao[] | null }) {
  if (!condicoes?.length) return <p className="mt-1 text-sm text-slate-600">Nenhuma condição disponível.</p>;
  return (
    <ul aria-label="Condições da gestação" className="mt-1 space-y-1 text-sm text-slate-900">
      {condicoes.map((c, i) => (
        <li key={`${c.cid10}-${i}`}>
          <strong className="font-mono">{c.cid10}</strong> {c.cid10_descricao}
          <span className="text-slate-600">{c.semana == null ? "" : ` · semana ${c.semana}`}</span>
        </li>
      ))}
    </ul>
  );
}

const medidas = (n: { peso_g: number | null; idade_gestacional_sem: number | null; apgar_5: number | null }): [string, string][] => [
  ["Peso ao nascer", n.peso_g == null ? "Não informado" : `${n.peso_g.toLocaleString("pt-BR")} g`],
  ["Idade gestacional", n.idade_gestacional_sem == null ? "Não informada" : `${n.idade_gestacional_sem} semanas`],
  ["Apgar no 5º minuto", n.apgar_5 == null ? "Não informado" : String(n.apgar_5)],
];

/** Prontuário de criança: só o que a gestação diz sobre ela (`historico_gestacional_crianca`). */
export function Recorte({ linhas }: { linhas: RecorteGestacional[] | null }) {
  const recorte = linhas?.[0];
  const condicoes = (linhas ?? []).flatMap((l) => (l.cid10 ? [{ cid10: l.cid10, cid10_descricao: l.cid10_descricao, semana: l.semana }] : []));
  return (
    <section className="mt-8" aria-labelledby="titulo-recorte">
      <h2 id="titulo-recorte" className="text-xl font-semibold text-slate-950">Gestação e nascimento</h2>
      <Card className="mt-3 px-5 py-4">
        {!linhas ? <p role="alert" className="text-sm text-red-800">Não foi possível carregar o histórico gestacional. Tente novamente.</p>
          : !recorte ? <p className="text-sm text-slate-600">Não há nascimento registrado para este paciente.</p> : (
            <>
              <dl className="grid gap-3 text-sm sm:grid-cols-5">
                {[["Mãe", recorte.nome_mae], ["Nascimento", formatarData(recorte.data)], ...medidas(recorte)].map(([nome, valor]) => (
                  <div key={nome}>
                    <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{nome}</dt>
                    <dd className="font-semibold text-slate-900">{valor}</dd>
                  </div>
                ))}
              </dl>
              <h3 className="mt-4 text-xs font-semibold uppercase tracking-wide text-slate-500">Condições na gestação</h3>
              <Condicoes condicoes={condicoes} />
            </>
          )}
      </Card>
    </section>
  );
}
