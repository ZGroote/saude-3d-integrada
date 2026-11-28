// Gestação e nascimento (SPEC §6 e "Contrato do banco — Etapa 5"). Formatos de supabase/migrations/0004.
// Os campos opcionais ainda não vêm do banco: o app os usa quando vierem.

export const DESFECHOS = { em_curso: "Em curso", nascido_vivo: "Nascido vivo", obito_fetal: "Óbito fetal", aborto: "Aborto" } as const;
export type Desfecho = keyof typeof DESFECHOS;

export type CondicaoGestacao = { cid10: string; semana: number | null; cid10_descricao?: string | null };

export type Nascimento = { crianca_id: string; data: string; peso_g: number | null; crianca_nome?: string | null };

/** Linha de `listar_gestacoes`. */
export type Gestacao = {
  gestacao_id: string;
  dum: string | null;
  dpp: string | null;
  inicio_pre_natal: string | null;
  desfecho: Desfecho;
  condicoes: CondicaoGestacao[] | null;
  nascimentos: Nascimento[] | null;
};

/**
 * Linha de `historico_gestacional_crianca`: o recorte, nunca o prontuário da mãe. Uma linha por condição,
 * repetindo os dados do parto; sem condição disponível, uma linha com `cid10` nulo.
 */
export type RecorteGestacional = {
  nome_mae: string;
  /** só com ele há atalho para a mãe; abrir o prontuário dela continua exigindo vínculo */
  mae_id?: string | null;
  cid10: string | null;
  cid10_descricao: string | null;
  semana: number | null;
  idade_gestacional_sem: number | null;
  peso_g: number | null;
  apgar_5: number | null;
  data: string;
};

export const nomeDaCrianca = (n: Nascimento) => n.crianca_nome || "Abrir prontuário da criança";

/** DPP = DUM + 280 dias. Só para mostrar antes de salvar: quem grava é o servidor. */
export function calcularDpp(dum: string) {
  const dia = new Date(`${dum}T12:00:00Z`);
  if (Number.isNaN(dia.getTime())) return "";
  dia.setUTCDate(dia.getUTCDate() + 280);
  return dia.toISOString().slice(0, 10);
}
