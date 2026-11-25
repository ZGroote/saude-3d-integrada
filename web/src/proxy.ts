import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import type { Database } from "@/lib/banco";

const INATIVIDADE_MS = 30 * 60 * 1000;
const COOKIE_ATIVIDADE = "saude3d-ultima-atividade";

export async function proxy(request: NextRequest) {
  let response = NextResponse.next({ request });
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const chave = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !chave) {
    if (request.nextUrl.pathname.startsWith("/pacientes")) {
      return NextResponse.redirect(new URL("/login", request.url));
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
  const rotaLogin = request.nextUrl.pathname === "/login";
  const rotaAtividade = request.nextUrl.pathname === "/api/sessao/atividade";
  const requerLogin = request.nextUrl.pathname.startsWith("/pacientes") || rotaAtividade;
  const ultimaAtividade = Number(request.cookies.get(COOKIE_ATIVIDADE)?.value ?? 0);
  const expirouPorInatividade = user && ultimaAtividade > 0 && Date.now() - ultimaAtividade >= INATIVIDADE_MS;

  if (expirouPorInatividade) {
    await supabase.auth.signOut();
    response.cookies.delete(COOKIE_ATIVIDADE);
    if (request.nextUrl.pathname.startsWith("/pacientes")) return NextResponse.redirect(new URL("/login?motivo=sessao-expirada", request.url));
    if (rotaAtividade) return NextResponse.json({ erro: "sessao_expirada" }, { status: 401 });
  } else if (requerLogin && !user) {
    if (rotaAtividade) return NextResponse.json({ erro: "sem_sessao" }, { status: 401 });
    const destino = NextResponse.redirect(new URL("/login", request.url));
    response.cookies.getAll().forEach((cookie) => destino.cookies.set(cookie));
    return destino;
  } else if (rotaLogin && user) {
    return NextResponse.redirect(new URL("/pacientes", request.url));
  }

  if (user && !expirouPorInatividade) {
    response.cookies.set(COOKIE_ATIVIDADE, String(Date.now()), {
      httpOnly: true, sameSite: "lax", secure: request.nextUrl.protocol === "https:", path: "/", maxAge: 60 * 60,
    });
  }
  return response;
}

export const config = { matcher: ["/login", "/pacientes/:path*", "/api/sessao/atividade"] };
