// Regras puras dos achados (SPEC §5.4, §6 e §7). Só tipos do motor: nada de three no servidor.
import type { Ancora } from "@saude3d/motor-anatomico";

export const CATEGORIAS = { doenca: "Doença", sintoma: "Sintoma", lesao: "Lesão", cirurgia: "Cirurgia", dispositivo: "Dispositivo", alergia: "Alergia" } as const;
export const LADOS = { esquerdo: "Esquerdo", direito: "Direito", bilateral: "Bilateral", nao_se_aplica: "Não se aplica" } as const;
export const STATUS = { ativo: "Ativo", suspeito: "Suspeito", resolvido: "Resolvido" } as const;

export type Categoria = keyof typeof CATEGORIAS;
export type Lado = keyof typeof LADOS;
export type Status = keyof typeof STATUS;

/** Linha de `listar_achados` (supabase/migrations/0003); só as colunas que o app usa. */
export type Achado = {
  id: string;
  ancora: Ancora | null;
  cid10: string;
  cid10_descricao: string;
  categoria: Categoria;
  lado: Lado;
  status: Status;
  inicio: string | null;
  observacao: string | null;
  especialidade: string | null;
  autor_nome: string;
  /** vem na migração 0004; até lá a unidade só é identificada pelo nome */
  unidade_id?: string;
  unidade_nome: string;
  substitui_id: string | null;
  criado_em: string;
};

// um formatador de cada: criar um por linha pesa com 200 achados num tablet
const DATA_PURA = new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium", timeZone: "UTC" });
const CARIMBO = new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium" });
/** Data pura (início) é lida em UTC para não voltar um dia; carimbo de hora usa o fuso do navegador. */
export const formatarData = (iso: string) =>
  iso.length === 10 ? DATA_PURA.format(new Date(`${iso}T12:00:00Z`)) : CARIMBO.format(new Date(iso));

/** Dia (AAAA-MM-DD) do achado na linha do tempo: o início; sem ele, o dia local do registro. */
export function dataDoAchado(a: Pick<Achado, "inicio" | "criado_em">) {
  if (a.inicio) return a.inicio;
  const criado = new Date(a.criado_em);
  return new Date(criado.getTime() - criado.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
}

/** `especialidade` null = todas ("" é um valor: achados sem especialidade); nos outros, "" = sem filtro. Datas inclusivas. */
export type Filtro = { especialidade: string | null; status: Status | ""; de: string; ate: string };
export const SEM_FILTRO: Filtro = { especialidade: null, status: "", de: "", ate: "" };

export function filtrar(achados: Achado[], { especialidade, status, de, ate }: Filtro) {
  return achados.filter((a) => {
    const dia = dataDoAchado(a);
    return (especialidade === null || (a.especialidade ?? "") === especialidade)
      && (!status || a.status === status) && (!de || dia >= de) && (!ate || dia <= ate);
  });
}

export const ordenarPorData = (achados: Achado[]) =>
  achados.toSorted((a, b) => dataDoAchado(a).localeCompare(dataDoAchado(b)) || a.criado_em.localeCompare(b.criado_em));

export const ladoDaLateralidade = (lateralidade: string | null | undefined): Lado =>
  lateralidade === "left" ? "esquerdo" : lateralidade === "right" ? "direito" : "nao_se_aplica";

/** Raio do marcador em metros: o status se lê pelo tamanho. */
export const TAMANHO_DO_STATUS: Record<Status, number> = { ativo: 0.014, suspeito: 0.01, resolvido: 0.007 };

const CORES = ["#c2185b", "#1565c0", "#2e7d32", "#6a1b9a", "#e65100", "#00838f", "#4e342e", "#f9a825"];
// ponytail: cor pelo hash do nome; duas especialidades podem repetir a cor (o texto sempre acompanha).
// Tabela fixa de cores quando houver cadastro de especialidades.
export function corDaEspecialidade(especialidade: string | null) {
  let hash = 0;
  for (const letra of (especialidade ?? "").trim().toLowerCase()) hash = (hash * 31 + letra.charCodeAt(0)) >>> 0;
  return CORES[hash % CORES.length]!;
}
