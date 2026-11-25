"use client";

import dynamic from "next/dynamic";

// WebGL, fetch dos GLBs e workers só existem no navegador: nada disto é renderizado no servidor.
export const Prontuario3D = dynamic(() => import("./visualizador-atlas"), {
  ssr: false,
  loading: () => <p role="status" className="text-sm text-slate-600">Carregando visualizador 3D…</p>,
});
