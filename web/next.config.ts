import type { NextConfig } from "next";
import { PHASE_DEVELOPMENT_SERVER } from "next/constants";

const nextConfig: NextConfig = {
  /* config options here */
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
