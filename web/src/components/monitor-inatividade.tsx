"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

const TEMPO_INATIVIDADE = 30 * 60 * 1000;
const INTERVALO_ATUALIZACAO = 60 * 1000;

export function MonitorInatividade() {
  const router = useRouter();

  useEffect(() => {
    let temporizador: number;
    let ultimaAtualizacao = 0;
    let encerrando = false;

    const expirar = () => {
      if (encerrando) return;
      encerrando = true;
      window.clearTimeout(temporizador);
      void createClient().auth.signOut({ scope: "local" })
        .catch(() => undefined)
        .finally(() => router.replace("/login?motivo=sessao-expirada"));
    };

    const renovar = () => {
      window.clearTimeout(temporizador);
      temporizador = window.setTimeout(async () => {
        expirar();
      }, TEMPO_INATIVIDADE);

      const agora = Date.now();
      if (agora - ultimaAtualizacao >= INTERVALO_ATUALIZACAO) {
        ultimaAtualizacao = agora;
        void fetch("/api/sessao/atividade", { method: "POST", cache: "no-store", keepalive: true })
          .then((resposta) => { if (resposta.status === 401) expirar(); });
      }
    };

    ["pointerdown", "keydown", "touchstart", "scroll"].forEach((evento) => window.addEventListener(evento, renovar, { passive: true }));
    renovar();
    return () => {
      window.clearTimeout(temporizador);
      ["pointerdown", "keydown", "touchstart", "scroll"].forEach((evento) => window.removeEventListener(evento, renovar));
    };
  }, [router]);

  return null;
}
