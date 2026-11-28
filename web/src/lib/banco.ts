import type { Ancora } from "@saude3d/motor-anatomico";
import type { Achado, Categoria, Lado, Status } from "@/lib/achados";
import type { Evento } from "@/lib/eventos";
import type { Mapeamento } from "@/lib/fhir/ancora";
import type { ErroImportacao } from "@/lib/fhir/importar";
import type { Desfecho, Gestacao, RecorteGestacional } from "@/lib/gestacao";

export type Sexo = "feminino" | "masculino" | "indeterminado";

export type PacienteBusca = {
  id: string;
  nome: string;
  sexo: Sexo;
  data_nascimento: string;
  cns_final: string;
};

export type Paciente = {
  id: string;
  nome: string;
  cns: string;
  cpf_hash: string;
  sexo: Sexo;
  data_nascimento: string;
  municipio_ibge: string;
};

export type Cid10 = { codigo: string; descricao: string };

export type Database = {
  public: {
    Tables: {
      pacientes: {
        Row: Paciente;
        Insert: Omit<Paciente, "id"> & { id?: string };
        Update: Partial<Omit<Paciente, "id">>;
        Relationships: [];
      };
      perfis: {
        Row: {
          id: string;
          nome: string;
          unidade_id: string;
          especialidade: string | null;
          papel: "profissional" | "admin";
        };
        Insert: { id: string; nome: string; unidade_id: string; especialidade?: string | null; papel?: "profissional" | "admin" };
        Update: Partial<{ nome: string; unidade_id: string; especialidade: string | null; papel: "profissional" | "admin" }>;
        Relationships: [];
      };
      unidades: {
        Row: { id: string; nome: string; cnes: string; municipio_ibge: string };
        Insert: { id?: string; nome: string; cnes: string; municipio_ibge: string };
        Update: Partial<{ nome: string; cnes: string; municipio_ibge: string }>;
        Relationships: [];
      };
      vinculos: {
        Row: { id: string; paciente_id: string; unidade_id: string; motivo: string | null; desde: string; ate: string | null };
        Insert: { id?: string; paciente_id: string; unidade_id: string; motivo?: string | null; desde: string; ate?: string | null };
        Update: Partial<{ motivo: string | null; desde: string; ate: string | null }>;
        Relationships: [];
      };
      achados: {
        Row: {
          id: string; paciente_id: string; autor_id: string; unidade_id: string; especialidade: string;
          sistema: string | null; estrutura: string | null; ancora: Json | null; cid10: string | null;
          categoria: string; lado: string | null; status: string; inicio: string | null; observacao: string | null;
          origem: "manual" | "fhir"; fhir_id: string | null; criado_em: string;
        };
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
        Relationships: [];
      };
      auditoria: {
        Row: { id: string; autor_id: string; paciente_id: string; acao: string; criado_em: string };
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
        Relationships: [];
      };
      gestacoes: {
        Row: { id: string; mae_id: string; dum: string | null; dpp: string | null; inicio_pre_natal: string | null; desfecho: string };
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
        Relationships: [];
      };
      condicoes_gestacao: {
        Row: { id: string; gestacao_id: string; cid10: string; semana: number | null };
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
        Relationships: [];
      };
      nascimentos: {
        Row: { id: string; gestacao_id: string; crianca_id: string; data: string; peso_g: number | null; idade_gestacional_sem: number | null; apgar_5: number | null };
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
        Relationships: [];
      };
      importacoes_fhir: {
        Row: { id: string; autor_id: string; arquivo: string; recursos: number; erros: Json; criado_em: string };
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
        Relationships: [];
      };
      bodysite_estrutura: {
        Row: Mapeamento;
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
        Relationships: [];
      };
      cid10: {
        Row: { codigo: string; descricao: string };
        Insert: { codigo: string; descricao: string };
        Update: Partial<{ descricao: string }>;
        Relationships: [];
      };
    };
    Views: Record<string, never>;
    Functions: {
      minha_unidade: { Args: Record<string, never>; Returns: string | null };
      eh_admin: { Args: Record<string, never>; Returns: boolean };
      registrar_atividade_sessao: { Args: { p_sessao: string; p_usuario: string }; Returns: boolean };
      abrir_prontuario: { Args: { p_paciente: string }; Returns: Paciente | null };
      buscar_pacientes: { Args: { p_texto: string }; Returns: PacienteBusca[] };
      buscar_cid10: { Args: { p_texto: string; p_limite?: number }; Returns: Cid10[] };
      registrar_achado: {
        Args: {
          p_paciente: string; p_ancora: Ancora | null; p_cid10: string; p_categoria: Categoria; p_lado: Lado;
          p_status: Status; p_inicio: string | null; p_observacao: string | null; p_substitui?: string | null;
          p_vista?: import("@saude3d/motor-anatomico").VistaCamera | null;
        };
        Returns: string;
      };
      listar_achados: { Args: { p_paciente: string }; Returns: Achado[] };
      historico_achado: { Args: { p_achado: string }; Returns: Achado[] };
      registrar_gestacao: { Args: { p_mae: string; p_dum: string; p_inicio_pre_natal: string | null }; Returns: string };
      registrar_condicao_gestacao: { Args: { p_gestacao: string; p_cid10: string; p_semana: number }; Returns: string };
      encerrar_gestacao: { Args: { p_gestacao: string; p_desfecho: Desfecho }; Returns: null };
      registrar_nascimento: {
        Args: {
          p_gestacao: string; p_nome: string; p_sexo: Sexo; p_data: string; p_peso_g: number;
          p_idade_gestacional_sem: number; p_apgar_5: number;
        };
        Returns: string;
      };
      iniciar_importacao: { Args: { p_arquivo: string; p_recursos: number; p_sistema_origem: string }; Returns: string };
      importar_paciente_fhir: {
        Args: { p_importacao: string; p_fhir_id: string; p_cns: string; p_nome: string; p_sexo: Sexo; p_nascimento: string | null };
        Returns: string;
      };
      importar_condicao_fhir: {
        Args: {
          p_importacao: string; p_paciente: string; p_fhir_id: string; p_cid10: string; p_ancora: Ancora | null;
          p_status: Status; p_inicio: string | null;
        };
        Returns: string;
      };
      importar_evento_fhir: {
        Args: {
          p_importacao: string; p_paciente: string; p_fhir_id: string; p_tipo: Evento["tipo"]; p_data: string | null;
          p_codigo: string | null; p_descricao: string | null; p_valor: string | null;
        };
        Returns: null;
      };
      concluir_importacao: { Args: { p_importacao: string; p_erros: ErroImportacao[] }; Returns: null };
      listar_eventos: { Args: { p_paciente: string }; Returns: Evento[] };
      listar_gestacoes: { Args: { p_mae: string }; Returns: Gestacao[] };
      historico_gestacional_crianca: { Args: { p_crianca: string }; Returns: RecorteGestacional[] };
    };
    Enums: Record<string, never>;
    CompositeTypes: Record<string, never>;
  };
};

export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[];
