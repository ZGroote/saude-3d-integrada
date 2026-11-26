import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const pasta = new URL('./', import.meta.url);
const lerEnv = (url) => Object.fromEntries(readFileSync(url, 'utf8').split(/\r?\n/)
  .filter((linha) => linha && !linha.startsWith('#') && linha.includes('='))
  .map((linha) => { const i = linha.indexOf('='); return [linha.slice(0,i), linha.slice(i+1)]; }));
const env = lerEnv(new URL('../web/.env.local', import.meta.url));
const senhas = lerEnv(new URL('./.env.demo', import.meta.url));
if (!env.NEXT_PUBLIC_SUPABASE_URL || !env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY)
  throw new Error('web/.env.local precisa de URL e publishable key');
const require = createRequire(new URL('../web/package.json', import.meta.url));
export const { createClient } = require('@supabase/supabase-js');
export const clientes = {};
export const emails = {
  cardiologia: 'cardiologia@saude3d.invalid',
  ortopedia: 'ortopedia@saude3d.invalid',
  obstetricia: 'obstetricia@saude3d.invalid',
  adminCardio: 'admin-cardiologia@saude3d.invalid',
};
export async function login(email) {
  if (clientes[email]) return clientes[email];
  const senha = senhas[email];
  if (!senha) throw new Error(`Senha fictícia ausente para ${email} em supabase/.env.demo`);
  const cliente = createClient(env.NEXT_PUBLIC_SUPABASE_URL, env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
    { auth: { persistSession: false, autoRefreshToken: false } });
  const { error } = await cliente.auth.signInWithPassword({ email, password: senha });
  if (error) throw new Error(`Login de ${email} falhou: ${error.message}`);
  clientes[email] = cliente;
  return cliente;
}
export async function rpc(cliente, nome, args) {
  const { data, error } = await cliente.rpc(nome, args);
  if (error) throw new Error(`${nome}: ${error.message} (${error.code ?? 'sem código'})`);
  return data;
}
export function raiz(...partes) {
  return fileURLToPath(new URL(`../${partes.join('/')}`, import.meta.url));
}
