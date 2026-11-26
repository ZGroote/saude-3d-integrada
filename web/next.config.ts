import type { NextConfig } from "next";
import { PHASE_DEVELOPMENT_SERVER } from "next/constants";

const nextConfig: NextConfig = {
  // o Bundle FHIR tem até 10 MB; o padrão das ações de servidor é 1 MB. A folga é do envelope multipart.
  experimental: { serverActions: { bodySizeLimit: "11mb" }, proxyClientMaxBodySize: "12mb" },
  // o `next dev` registraria os argumentos das ações no terminal: nada de dado pessoal em log
  logging: { serverFunctions: false },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default function config(phase: string): NextConfig {
  // arquivos *.dev.tsx (rota /dev/motor) só viram rota no `next dev`; no build eles não existem
  const soDev = phase === PHASE_DEVELOPMENT_SERVER ? ["dev.tsx"] : [];
  return { ...nextConfig, pageExtensions: [...soDev, "tsx", "ts", "jsx", "js"] };
}
