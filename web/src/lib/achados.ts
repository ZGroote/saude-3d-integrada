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
  unidade_nome: string;
  criado_em: string;
};

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
