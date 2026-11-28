import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const pasta = new URL('./', import.meta.url);
const lerEnv = (url) => Object.fromEntries(readFileSync(url, 'utf8').split(/\r?\n/)
  .filter((linha) => linha && !linha.startsWith('#') && linha.includes('='))
  .map((linha) => { const i = linha.indexOf('='); return [linha.slice(0,i), linha.slice(i+1)]; }));
const lerEnvOpcional = (url) => { try { return lerEnv(url); } catch (e) { if (e.code === 'ENOENT') return {}; throw e; } };
const env = lerEnvOpcional(new URL('../web/.env.local', import.meta.url));
if (!env.SUPABASE_SECRET_KEY)
  throw new Error('SUPABASE_SECRET_KEY ausente em web/.env.local; registre a atividade da sessão exige a chave secreta do servidor.');
if (!env.NEXT_PUBLIC_SUPABASE_URL || !env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY)
  throw new Error('web/.env.local precisa de URL e publishable key');
const senhas = lerEnv(new URL('./.env.demo', import.meta.url));
const require = createRequire(new URL('../web/package.json', import.meta.url));
export const { createClient } = require('@supabase/supabase-js');
export const servico = createClient(env.NEXT_PUBLIC_SUPABASE_URL, env.SUPABASE_SECRET_KEY,
  { auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false } });
export const clientes = {};
export const emails = {
  mfc: 'mfc@saude3d.invalid',
  cardiologia: 'cardiologia@saude3d.invalid',
  ortopedia: 'ortopedia@saude3d.invalid',
  obstetricia: 'obstetricia@saude3d.invalid',
  pediatria: 'pediatria@saude3d.invalid',
  adminUbs: 'admin@saude3d.invalid',
  adminCardio: 'admin-cardiologia@saude3d.invalid',
  adminMaternidade: 'admin-maternidade@saude3d.invalid',
  adminUbsSubstituto: 'admin-ubs-substituto@saude3d.invalid',
  adminPediatria: 'admin-pediatria@saude3d.invalid',
};
export async function login(email) {
  if (clientes[email]) return clientes[email];
  const senha = senhas[email];
  if (!senha) throw new Error(`Senha fictícia ausente para ${email} em supabase/.env.demo`);
  const cliente = createClient(env.NEXT_PUBLIC_SUPABASE_URL, env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
    { auth: { persistSession: false, autoRefreshToken: false } });
  const { error } = await cliente.auth.signInWithPassword({ email, password: senha });
  if (error) throw new Error(`Login de ${email} falhou: ${error.message}`);
  const { data: claimsData, error: claimsError } = await cliente.auth.getClaims();
  const claims = claimsData?.claims;
  if (claimsError || typeof claims?.session_id !== 'string' || typeof claims?.sub !== 'string')
    throw new Error('Não foi possível obter session_id/sub do JWT após login; atividade não registrada.');
  const { data: registrado, error: atividadeError } = await servico.rpc('registrar_atividade_sessao', {
    p_sessao: claims.session_id, p_usuario: claims.sub,
  });
  if (atividadeError || registrado !== true)
    throw new Error(`Registro de atividade da sessão falhou${atividadeError?.code ? ` (${atividadeError.code})` : ''}; verifique a migração 0009 e as permissões service_role.`);
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
