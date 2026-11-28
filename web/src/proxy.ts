import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import type { Database } from "@/lib/banco";
import { atividadeValida, assinarAtividade } from "@/lib/sessao";

const INATIVIDADE_MS = 30 * 60 * 1000;
const COOKIE_ATIVIDADE = "saude3d-ultima-atividade";

function copiarCookies(origem: NextResponse, destino: NextResponse) {
  origem.cookies.getAll().forEach((cookie) => destino.cookies.set(cookie));
}

function apagarCookieAtividade(response: NextResponse, request: NextRequest) {
  response.cookies.set(COOKIE_ATIVIDADE, "", {
    httpOnly: true, sameSite: "lax", secure: request.nextUrl.protocol === "https:", path: "/", maxAge: 0,
  });
}

function cachePrivado(response: NextResponse, protegido: boolean) {
  let origemSupabase = "";
  let hostSupabase = "";
  try {
    const supabaseUrl = new URL(process.env.NEXT_PUBLIC_SUPABASE_URL || "");
    origemSupabase = supabaseUrl.origin;
    hostSupabase = supabaseUrl.host;
  } catch { /* CSP continua restrito à própria origem */ }
  const conexoes = ["'self'", origemSupabase, hostSupabase ? `wss://${hostSupabase}` : ""].filter(Boolean);
  const script = ["'self'", "'unsafe-inline'", "'wasm-unsafe-eval'"];
  if (process.env.NODE_ENV !== "production") {
    script.push("'unsafe-eval'");
    conexoes.push("ws://localhost:*", "ws://127.0.0.1:*");
  }
  response.headers.set("Content-Security-Policy", [
    "default-src 'self'", `script-src ${script.join(" ")}`, "style-src 'self' 'unsafe-inline'",
    `connect-src ${conexoes.join(" ")}`, "img-src 'self' data: blob:", "worker-src 'self' blob:",
    "font-src 'self' data:", "frame-ancestors 'none'", "base-uri 'self'", "object-src 'none'", "form-action 'self'",
  ].join("; "));
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("Referrer-Policy", "no-referrer");
  response.headers.set("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
  if (process.env.NODE_ENV === "production") {
    response.headers.set("Strict-Transport-Security", "max-age=63072000; includeSubDomains");
  }
  if (protegido) response.headers.set("Cache-Control", "no-store, private");
  return response;
}

export async function proxy(request: NextRequest) {
  let response = NextResponse.next({ request });
  const rotaLogin = request.nextUrl.pathname === "/login";
  const rotaAtividade = request.nextUrl.pathname === "/api/sessao/atividade";
  const rotaProtegida = request.nextUrl.pathname.startsWith("/pacientes") || request.nextUrl.pathname.startsWith("/importar");
  const requerLogin = rotaProtegida || rotaAtividade;
  if (requerLogin && process.env.NODE_ENV === "production" && (!process.env.SESSAO_SEGREDO || !process.env.SUPABASE_SECRET_KEY)) {
    return cachePrivado(NextResponse.json(
      { erro: "Configuração de segurança ausente no servidor." }, { status: 500 },
    ), true);
  }
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const chave = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !chave) {
    if (requerLogin) {
      return cachePrivado(NextResponse.redirect(new URL("/login", request.url)), true);
    }
    return response;
  }

  const supabase = createServerClient<Database>(url, chave, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        cookiesToSet.forEach(({ name, value, options }) => response.cookies.set(name, value, options));
      },
    },
  });

  const { data: { user } } = await supabase.auth.getUser();
  const agora = Date.now();
  const cookieAtividade = request.cookies.get(COOKIE_ATIVIDADE)?.value;
  const atividadeValidaAgora = user ? await atividadeValida(cookieAtividade, agora) : false;
  const expirouPorInatividade = Boolean(user && (requerLogin || rotaLogin) && (
    !atividadeValidaAgora || agora - Number(cookieAtividade?.split(".")[0]) >= INATIVIDADE_MS
  ));

  if (expirouPorInatividade) {
    try { await supabase.auth.signOut({ scope: "local" }); } catch { /* cookie inválido continua bloqueando as próximas requisições */ }
    if (rotaProtegida) {
      const destino = NextResponse.redirect(new URL("/login?motivo=sessao-expirada", request.url));
      copiarCookies(response, destino);
      apagarCookieAtividade(destino, request);
      return cachePrivado(destino, true);
    }
    if (rotaAtividade || rotaLogin) {
      const destino = rotaAtividade
        ? NextResponse.json({ erro: "sessao_expirada" }, { status: 401 })
        : NextResponse.redirect(new URL("/login?motivo=sessao-expirada", request.url));
      copiarCookies(response, destino);
      apagarCookieAtividade(destino, request);
      return cachePrivado(destino, rotaAtividade);
    }
  } else if (requerLogin && !user) {
    if (rotaAtividade) return cachePrivado(NextResponse.json({ erro: "sem_sessao" }, { status: 401 }), true);
    const destino = NextResponse.redirect(new URL("/login", request.url));
    copiarCookies(response, destino);
    return cachePrivado(destino, true);
  } else if (rotaLogin && user) {
    const destino = NextResponse.redirect(new URL("/pacientes", request.url));
    copiarCookies(response, destino);
    return cachePrivado(destino, true);
  }

  if (user && requerLogin) {
    response.cookies.set(COOKIE_ATIVIDADE, await assinarAtividade(agora), {
      httpOnly: true, sameSite: "lax", secure: request.nextUrl.protocol === "https:", path: "/", maxAge: INATIVIDADE_MS / 1000,
    });
  }
  return cachePrivado(response, requerLogin);
}

export const config = { matcher: ["/login", "/pacientes/:path*", "/importar", "/importar/:path*", "/api/sessao/atividade"] };
