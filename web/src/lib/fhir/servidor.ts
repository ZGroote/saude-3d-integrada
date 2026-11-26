// Importação FHIR no servidor: prepara a prévia e grava pelas rpc. Nada daqui vai para log: o Bundle tem
// dado pessoal, e as mensagens de erro são fixas (a do banco poderia repetir um valor).
import "server-only";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import path from "node:path";
import type { Ancora, EntradaIndice } from "@saude3d/motor-anatomico";
import type { Status } from "@/lib/achados";
import { ancoraEstrutural, ATLAS_DO_SEXO, type AtlasDeImportacao, type Mapeamento } from "@/lib/fhir/ancora";
import { planejarImportacaoFHIR, type CondicaoImportacao, type ErroImportacao, type EventoImportacao, type PacienteImportacao } from "@/lib/fhir/importar";
import { LIMITE_BYTES, type Previa, type Relatorio } from "@/lib/fhir/tipos";
import type { createClient } from "@/lib/supabase/server";

type Banco = Awaited<ReturnType<typeof createClient>>;

const STATUS_FHIR: Record<string, Status> = {
  active: "ativo", recurrence: "ativo", relapse: "ativo", resolved: "resolvido", inactive: "resolvido", remission: "resolvido",
};
const DATA = /^\d{4}-\d{2}-\d{2}$/;
const dataValida = (texto: string) => DATA.test(texto) && new Date(`${texto}T12:00:00Z`).toISOString().startsWith(texto);

type Preparado = {
  hash: string;
  recursos: number;
  pacientes: (PacienteImportacao & { nome: string })[];
  condicoes: (Omit<CondicaoImportacao, "status" | "inicio"> & { status: Status; inicio: string | null; ancora: Ancora | null })[];
  eventos: EventoImportacao[];
  erros: ErroImportacao[];
  /** há bodySite no Bundle e a tabela de mapeamento não pôde ser lida */
  semMapeamento: boolean;
};

async function lerIndice({ atlas, versao }: AtlasDeImportacao): Promise<EntradaIndice[]> {
  const base = process.env.NEXT_PUBLIC_ATLAS_URL || "/atlas";
  if (/^https?:/.test(base)) {
    const resposta = await fetch(`${base.replace(/\/+$/, "")}/${atlas}/${versao}/indice.json`);
    if (!resposta.ok) throw new Error("atlas indisponível");
    return resposta.json();
  }
  return JSON.parse(await readFile(path.join(process.cwd(), "public", base, atlas, versao, "indice.json"), "utf8"));
}

const emBlocos = <T,>(lista: T[], tamanho: number) =>
  Array.from({ length: Math.ceil(lista.length / tamanho) }, (_, i) => lista.slice(i * tamanho, (i + 1) * tamanho));

/** Lê, valida e resolve o Bundle. Erro de arquivo vira `string`. */
export async function preparar(supabase: Banco, arquivo: unknown): Promise<Preparado | string> {
  if (!(arquivo instanceof File) || !arquivo.size) return "Escolha um arquivo .json.";
  if (!/\.json$/i.test(arquivo.name)) return "O arquivo precisa ser .json.";
  if (arquivo.size > LIMITE_BYTES) return "O arquivo passa de 10 MB.";
  const texto = await arquivo.text();
  let bundle: unknown;
  try {
    bundle = JSON.parse(texto.replace(/^﻿/, ""));
  } catch {
    return "O arquivo não é um JSON válido.";
  }
  const plano = planejarImportacaoFHIR(bundle);
  if (plano.erros.some((e) => e.id === "Bundle")) return "O arquivo não é um Bundle FHIR válido.";
  const erros = [...plano.erros];
  const recursos = plano.pacientes.length + plano.condicoes.length + plano.eventos.length + plano.erros.length;

  const pacientes: Preparado["pacientes"] = [];
  for (const p of plano.pacientes) {
    if (!p.nome) erros.push({ id: p.fhir_id, motivo: "Patient sem nome." });
    else pacientes.push({ ...p, nome: p.nome, nascimento: p.nascimento && dataValida(p.nascimento) ? p.nascimento : null });
  }
  const porId = new Map(pacientes.map((p) => [p.fhir_id, p]));
  const semPaciente = (id: string) => erros.push({ id, motivo: "O Patient deste recurso não pode ser importado." });

  const codigos = [...new Set(plano.condicoes.map((c) => c.cid10))];
  const existentes = new Set<string>();
  for (const bloco of emBlocos(codigos, 200)) {
    const { data, error } = await supabase.from("cid10").select("codigo, descricao").in("codigo", bloco);
    if (error) return "Não foi possível conferir os códigos CID-10. Tente novamente.";
    for (const linha of data ?? []) existentes.add(linha.codigo);
  }

  const mapa = new Map<string, Mapeamento>();
  let semMapeamento = false;
  if (plano.condicoes.some((c) => c.bodySite.length)) {
    // a tabela é pequena: lida inteira, uma resposta vazia (RLS sem política) também conta como indisponível
    const { data, error } = await supabase.from("bodysite_estrutura").select("snomed, estrutura_fma, estrutura_uberon, lado");
    semMapeamento = !!error || !data?.length;
    for (const linha of data ?? []) mapa.set(linha.snomed, linha);
  }

  const indices = new Map<string, Promise<EntradaIndice[]>>();
  const condicoes: Preparado["condicoes"] = [];
  for (const c of plano.condicoes) {
    const paciente = porId.get(c.paciente_fhir_id);
    const status = STATUS_FHIR[(c.status ?? "").trim().toLowerCase()];
    if (!paciente) { semPaciente(c.fhir_id); continue; }
    if (!existentes.has(c.cid10)) { erros.push({ id: c.fhir_id, motivo: "CID-10 inexistente na tabela." }); continue; }
    if (!status) { erros.push({ id: c.fhir_id, motivo: "Condition sem status clínico reconhecido." }); continue; }
    const dia = c.inicio?.slice(0, 10) ?? "";
    let ancora: Ancora | null = null;
    const atlas = ATLAS_DO_SEXO[paciente.sexo];
    const mapeados = c.bodySite.flatMap((codigo) => mapa.get(codigo) ?? []);
    if (atlas && mapeados.length) {
      if (!indices.has(atlas.atlas)) indices.set(atlas.atlas, lerIndice(atlas));
      let indice: EntradaIndice[];
      try {
        indice = await indices.get(atlas.atlas)!;
      } catch {
        // sem o índice a âncora sairia nula para sempre (o fhir_id não é regravado): melhor não importar
        return "O índice do atlas não está disponível no servidor. Nada foi importado.";
      }
      for (const m of mapeados) {
        ancora = ancoraEstrutural(m, atlas, indice);
        if (ancora) break;
      }
    }
    condicoes.push({ ...c, status, inicio: dataValida(dia) ? dia : null, ancora });
  }

  const eventos: EventoImportacao[] = [];
  for (const e of plano.eventos) {
    if (!porId.has(e.paciente_fhir_id)) semPaciente(e.fhir_id);
    else if (e.data && Number.isNaN(Date.parse(e.data))) erros.push({ id: e.fhir_id, motivo: "Data do recurso inválida." });
    else eventos.push(e);
  }

  return { hash: createHash("sha256").update(texto).digest("hex"), recursos, pacientes, condicoes, eventos, erros, semMapeamento };
}

export async function montarPrevia(supabase: Banco, p: Preparado): Promise<Previa> {
  // só se sabe quem já é vinculado à própria unidade; o resto não é consultado (não revela cadastro de outras)
  let vinculados: number | null = 0;
  for (const bloco of emBlocos(p.pacientes, 8)) {
    const respostas = await Promise.all(bloco.map((x) => supabase.rpc("buscar_pacientes", { p_texto: x.cns })));
    if (respostas.some((r) => r.error)) { vinculados = null; break; }
    vinculados += respostas.filter((r) => r.data?.length).length;
  }
  const comLocal = p.condicoes.filter((c) => c.ancora).length;
  return {
    hash: p.hash,
    pacientes: p.pacientes.length,
    vinculados,
    condicoesComLocal: comLocal,
    condicoesSemLocal: p.condicoes.length - comLocal,
    naoMapeadas: p.condicoes.filter((c) => c.bodySite.length && !c.ancora).length,
    eventos: p.eventos.length,
    erros: p.erros,
    bloqueio: p.semMapeamento
      ? "A tabela de mapeamento de bodySite não pôde ser lida. Importar agora deixaria as condições sem local de forma definitiva."
      : !p.pacientes.length ? "Não há paciente válido para importar." : null,
  };
}

function motivo(error: { code?: string } | null) {
  if (!error || error.code === "42501") return "Recusado pelo banco: sem permissão ou vínculo.";
  return error.code?.startsWith("22") || error.code?.startsWith("23") ? "Dados recusados pelo banco." : "Falha ao gravar.";
}

export async function gravar(supabase: Banco, p: Preparado): Promise<Relatorio | string> {
  // o nome do arquivo pode conter o nome de alguém: grava-se só a impressão digital
  const { data: importacao, error } = await supabase.rpc("iniciar_importacao", { p_arquivo: `bundle-${p.hash.slice(0, 12)}.json`, p_recursos: p.recursos });
  if (error || !importacao) return "Não foi possível iniciar a importação. Nada foi gravado.";
  const erros = [...p.erros];
  const gravados = { pacientes: 0, condicoes: 0, eventos: 0 };
  const ids = new Map<string, string>();

  // um de cada vez: a falha de um recurso vira erro dele e não para os outros
  for (const x of p.pacientes) {
    const r = await supabase.rpc("importar_paciente_fhir", {
      p_importacao: importacao, p_fhir_id: x.fhir_id, p_cns: x.cns, p_nome: x.nome, p_sexo: x.sexo, p_nascimento: x.nascimento,
    });
    if (r.error || !r.data) erros.push({ id: x.fhir_id, motivo: motivo(r.error) });
    else { ids.set(x.fhir_id, r.data); gravados.pacientes++; }
  }
  const falta = (id: string) => erros.push({ id, motivo: "O paciente deste recurso não foi importado." });
  for (const c of p.condicoes) {
    const paciente = ids.get(c.paciente_fhir_id);
    if (!paciente) { falta(c.fhir_id); continue; }
    const r = await supabase.rpc("importar_condicao_fhir", {
      p_importacao: importacao, p_paciente: paciente, p_fhir_id: c.fhir_id, p_cid10: c.cid10, p_ancora: c.ancora, p_status: c.status, p_inicio: c.inicio,
    });
    if (r.error || !r.data) erros.push({ id: c.fhir_id, motivo: motivo(r.error) });
    else gravados.condicoes++;
  }
  for (const e of p.eventos) {
    const paciente = ids.get(e.paciente_fhir_id);
    if (!paciente) { falta(e.fhir_id); continue; }
    const r = await supabase.rpc("importar_evento_fhir", {
      // o banco exige fhir_id único por unidade, e em FHIR o id só é único dentro do tipo
      p_importacao: importacao, p_paciente: paciente, p_fhir_id: `${e.tipo}/${e.fhir_id}`, p_tipo: e.tipo,
      p_data: e.data, p_codigo: e.codigo, p_descricao: e.descricao, p_valor: e.valor,
    });
    if (r.error) erros.push({ id: e.fhir_id, motivo: motivo(r.error) });
    else gravados.eventos++;
  }
  const fim = await supabase.rpc("concluir_importacao", { p_importacao: importacao, p_erros: erros });
  return { importacao, ...gravados, erros, concluida: !fim.error };
}
