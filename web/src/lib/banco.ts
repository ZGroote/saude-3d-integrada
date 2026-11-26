import type { Ancora } from "@saude3d/motor-anatomico";
import type { Achado, Categoria, Lado, Status } from "@/lib/achados";

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
      abrir_prontuario: { Args: { p_paciente: string }; Returns: Paciente | null };
      buscar_pacientes: { Args: { p_texto: string }; Returns: PacienteBusca[] };
      buscar_cid10: { Args: { p_texto: string; p_limite?: number }; Returns: Cid10[] };
      registrar_achado: {
        Args: {
          p_paciente: string; p_ancora: Ancora | null; p_cid10: string; p_categoria: Categoria; p_lado: Lado;
          p_status: Status; p_inicio: string | null; p_observacao: string | null; p_substitui?: string | null;
        };
        Returns: string;
      };
      listar_achados: { Args: { p_paciente: string }; Returns: Achado[] };
    };
    Enums: Record<string, never>;
    CompositeTypes: Record<string, never>;
  };
};

export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[];
