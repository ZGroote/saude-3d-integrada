// O que a tela de importação recebe do servidor: contagens e erros, sem dado pessoal.
import type { ErroImportacao } from "@/lib/fhir/importar";

export const LIMITE_BYTES = 10 * 1024 * 1024;

export type Previa = {
  /** impressão digital do arquivo analisado: a confirmação só vale para ele */
  hash: string;
  pacientes: number;
  /** quantos já têm vínculo ativo com a unidade; null = não foi possível saber */
  vinculados: number | null;
  condicoesComLocal: number;
  condicoesSemLocal: number;
  /** têm bodySite, mas sem mapeamento seguro: entram sem local */
  naoMapeadas: number;
  eventos: number;
  erros: ErroImportacao[];
  /** motivo que impede confirmar */
  bloqueio: string | null;
};

export type Relatorio = {
  importacao: string;
  pacientes: number;
  condicoes: number;
  eventos: number;
  erros: ErroImportacao[];
  concluida: boolean;
};
