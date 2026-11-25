export type Vetor3 = [number, number, number];

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
  sistemas: { id: string; glb: string; estruturas: number }[];
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
