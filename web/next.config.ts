import type { NextConfig } from "next";
import { PHASE_DEVELOPMENT_SERVER } from "next/constants";

function cabecalhosSeguranca() {
  let origemSupabase = "";
  let hostSupabase = "";
  try {
    const url = new URL(process.env.NEXT_PUBLIC_SUPABASE_URL || "");
    origemSupabase = url.origin;
    hostSupabase = url.host;
  } catch { /* build sem configuração local: mantém connect-src restrito à própria origem */ }
  const conexoes = ["'self'", origemSupabase, hostSupabase ? `wss://${hostSupabase}` : ""]
    .filter(Boolean);
  if (process.env.NODE_ENV !== "production") conexoes.push("ws://localhost:*", "ws://127.0.0.1:*");
  const script = ["'self'", "'unsafe-inline'", "'wasm-unsafe-eval'"];
  if (process.env.NODE_ENV !== "production") script.push("'unsafe-eval'");
  const csp = [
    "default-src 'self'",
    `script-src ${script.join(" ")}`,
    "style-src 'self' 'unsafe-inline'",
    `connect-src ${conexoes.join(" ")}`,
    "img-src 'self' data: blob:",
    "worker-src 'self' blob:",
    "font-src 'self' data:",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "object-src 'none'",
    "form-action 'self'",
  ].join("; ");
  const cabecalhos = [
    { key: "Content-Security-Policy", value: csp },
    { key: "X-Content-Type-Options", value: "nosniff" },
    { key: "Referrer-Policy", value: "no-referrer" },
    { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  ];
  if (process.env.NODE_ENV === "production") {
    cabecalhos.push({ key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains" });
  }
  return cabecalhos;
}

const nextConfig: NextConfig = {
  // um segundo build (teste ao lado de um servidor no ar) vai para outra pasta: NEXT_DIST_DIR=.next-etapa7
  distDir: process.env.NEXT_DIST_DIR || ".next",
  // o Bundle FHIR tem até 10 MB; o padrão das ações de servidor é 1 MB. A folga é do envelope multipart.
  experimental: { serverActions: { bodySizeLimit: "11mb" }, proxyClientMaxBodySize: "12mb" },
  // o `next dev` registraria os argumentos das ações no terminal: nada de dado pessoal em log
  logging: { serverFunctions: false },
  async headers() {
    const seguranca = cabecalhosSeguranca();
    return [
      { source: "/:path*", headers: seguranca },
      { source: "/pacientes", headers: [{ key: "Cache-Control", value: "no-store, private" }] },
      { source: "/pacientes/:path*", headers: [{ key: "Cache-Control", value: "no-store, private" }] },
      { source: "/importar", headers: [{ key: "Cache-Control", value: "no-store, private" }] },
      { source: "/importar/:path*", headers: [{ key: "Cache-Control", value: "no-store, private" }] },
      { source: "/api/sessao/atividade", headers: [{ key: "Cache-Control", value: "no-store, private" }] },
    ];
  },
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
