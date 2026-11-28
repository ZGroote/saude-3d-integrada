export type Vetor3 = [number, number, number];

export type NomeVista = 'anterior' | 'posterior' | 'direita' | 'esquerda' | 'superior' | 'inferior';

/** Estado de câmera no espaço do mundo do atlas (metros); só vale para atlas/versão iguais. */
export type VistaCamera = {
  atlas: string;
  atlas_versao: string;
  posicao: Vetor3;
  alvo: Vetor3;
  up?: Vetor3;
  sistemas: string[];
};

export type ComandoCamera =
  | { seq: number; acao: 'enquadrar' }
  | { seq: number; acao: 'focar' }
  | { seq: number; acao: 'vista'; vista: NomeVista }
  | { seq: number; acao: 'restaurar'; vista: VistaCamera };

/** SPEC §5.4. "Espaço da malha" = metros, nos eixos do atlas, já sem a transformação de nó do GLB (ver pacote.ts). */
export type Ancora = {
  atlas: string;
  atlas_versao: string;
  /** do indice.json */
  sistema: string;
  /** ID de ontologia; null = malha sem ID */
  estrutura: string | null;
  /** nó clicado */
  malha: string;
  // geometria: null numa âncora só estrutural (ex.: importação FHIR, sem clique)
  /** fonte da verdade */
  posicao_local: Vetor3 | null;
  normal_local: Vetor3 | null;
  /** triângulo e baricêntricas só valem nesta atlas_versao */
  triangulo: number | null;
  baricentricas: Vetor3 | null;
};

export type Marcador = {
  id: string;
  ancora: Ancora;
  /** Vista persistida com o achado, quando presente; o motor só encaminha o valor. */
  vista?: VistaCamera | null;
  cor: string;
  /** raio da esfera, em metros (ex.: 0.01) */
  tamanho: number;
};

export type Manifesto = {
  atlas: string;
  versao: string;
  fonte: string;
  licenca: string;
  atribuicao: string;
  unidade: string;
  eixos: string;
  /** `glb_leve`: mesmas malhas e nomes de nó, simplificadas (SPEC §5.3) */
  sistemas: { id: string; glb: string; glb_leve?: string; estruturas: number }[];
};

export type EntradaIndice = {
  malha: string;
  estrutura: string | null;
  nome_en: string;
  nome_pt: string;
  validacao: string;
  sistema: string;
  lateralidade: string | null;
  glb: string;
  /** usado por malhaPrincipal */
  triangulos: number;
};
