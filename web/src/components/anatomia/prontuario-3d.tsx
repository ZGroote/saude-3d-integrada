"use client";

import dynamic from "next/dynamic";

const carregar = () => import("./visualizador-atlas");

/** Começa a baixar o código 3D antes de o visualizador ser montado. */
export function precarregar3D() {
  if (typeof window !== "undefined") void carregar();
}

// WebGL, fetch dos GLBs e workers só existem no navegador: nada disto é renderizado no servidor.
export const Prontuario3D = dynamic(carregar, {
  ssr: false,
  loading: () => <p role="status" className="text-sm text-slate-600">Carregando visualizador 3D…</p>,
});
