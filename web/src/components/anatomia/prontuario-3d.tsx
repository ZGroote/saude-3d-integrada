"use client";

import dynamic from "next/dynamic";

// Separado em outro arquivo JS, mas renderizado também no servidor: assim o HTML já pede o código 3D
// (preload) e ele baixa junto com a página. WebGL e GLBs só rodam em efeitos, no navegador.
export const Prontuario3D = dynamic(() => import("./visualizador-atlas"), {
  loading: () => <p role="status" className="text-sm text-slate-600">Carregando visualizador 3D…</p>,
});
