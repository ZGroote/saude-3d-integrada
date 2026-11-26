// Testes de ponta a ponta contra o Supabase de HOMOLOGAÇÃO (login real, JWT, PostgREST).
// Uso (na raiz):  node supabase/testes_homologacao.mjs
// Lê supabase/.env (URL e chave publishable) e supabase/.env.demo (senhas fictícias); ambos fora do git.
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import assert from 'node:assert/strict';

const { createClient } = createRequire(new URL('../web/package.json', import.meta.url))('@supabase/supabase-js');
const ler = (f) => Object.fromEntries(readFileSync(new URL(f, import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1)]));
const env = ler('./.env');
let envApp = {};
try {
  envApp = Object.fromEntries(readFileSync(new URL('../web/.env.local', import.meta.url), 'utf8')
    .split(/\r?\n/).filter((l) => l.includes('='))
    .map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1)]));
} catch (e) { if (e.code !== 'ENOENT') throw e; }
const URL_ = 'https://zmrxskzokpbedmvikrvc.supabase.co';
const CHAVE = env.SUPABASE_PUBLISHABLE_KEY ?? 'sb_publishable_flRzSCRnQhQ1ptqC3KFzdA_ePN2J6N0';
if (!envApp.SUPABASE_SECRET_KEY)
  throw new Error('SUPABASE_SECRET_KEY ausente em web/.env.local; os testes exigem registrar a atividade da sessão.');
const senhas = ler('./.env.demo');
const adminRpc = createClient(URL_, envApp.SUPABASE_SECRET_KEY,
  { auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false } });
const MARIA = '30000000-0000-4000-8000-000000000001';
const JOAO = '30000000-0000-4000-8000-000000000002';

async function como(email) {
  const c = createClient(URL_, CHAVE, { auth: { persistSession: false } });
  const { error } = await c.auth.signInWithPassword({ email, password: senhas[email] });
  assert.equal(error, null, `login de ${email}: ${error?.message}`);
  const { data: claimsData, error: claimsError } = await c.auth.getClaims();
  const claims = claimsData?.claims;
  assert.equal(claimsError, null, 'não foi possível obter os claims da sessão');
  assert.equal(typeof claims?.session_id, 'string', 'JWT sem session_id');
  assert.equal(typeof claims?.sub, 'string', 'JWT sem sub');
  const { data: registrado, error: atividadeError } = await adminRpc.rpc('registrar_atividade_sessao', {
    p_sessao: claims.session_id, p_usuario: claims.sub,
  });
  assert.equal(atividadeError, null, `registro de atividade falhou${atividadeError?.code ? ` (${atividadeError.code})` : ''}`);
  assert.equal(registrado, true, 'banco recusou registrar atividade da sessão');
  return c;
}
const ok = (nome) => console.log('✔', nome);

const anon = createClient(URL_, CHAVE, { auth: { persistSession: false } });
assert.equal((await anon.rpc('buscar_pacientes', { p_texto: null })).data?.length ?? 0, 0);
assert.ok((await anon.from('pacientes').select('id')).error || (await anon.from('pacientes').select('id')).data.length === 0);
ok('sem login: nada de pacientes');

const cardio = await como('cardiologia@saude3d.invalid');
const lista = await cardio.rpc('buscar_pacientes', { p_texto: null });
assert.equal(lista.error, null);
// a cardiologia também tem a paciente de carga da Etapa 4; o que importa: Maria sim, João não
const ids = lista.data.map((p) => p.id);
assert.ok(ids.includes(MARIA) && !ids.includes(JOAO), JSON.stringify(ids));
assert.ok(!('cns' in lista.data[0]) && /^\d{4}$/.test(lista.data[0].cns_final));
ok('cardiologia: lista a Maria e não o João, CNS mascarado');

const direto = await cardio.from('pacientes').select('*');
assert.ok(direto.error, 'select direto em pacientes deveria falhar');
assert.ok((await cardio.from('vinculos').select('*')).error);
assert.ok((await cardio.from('auditoria').select('*')).error || (await cardio.from('auditoria').select('*')).data.length === 0);
ok('cardiologia: select direto em pacientes/vínculos/auditoria negado');

const maria = await cardio.rpc('abrir_prontuario', { p_paciente: MARIA });
assert.equal(maria.error, null);
assert.equal(maria.data?.id, MARIA);
const joao = await cardio.rpc('abrir_prontuario', { p_paciente: JOAO });
assert.equal(joao.error, null);
assert.ok(joao.data === null || joao.data?.id === null);
ok('cardiologia: abre a Maria; João sem vínculo devolve null');

assert.ok((await cardio.rpc('vincular_paciente', { p_paciente: JOAO, p_motivo: 'bisbilhotar', p_origem: 'atendimento' })).error);
ok('cardiologia: não se autovincula ao João');

const admin = await como('admin-cardiologia@saude3d.invalid');
const aud = await admin.from('auditoria').select('acao, paciente_id').order('criado_em', { ascending: false }).limit(5);
assert.equal(aud.error, null);
assert.ok(aud.data.some((a) => a.acao === 'abrir_prontuario' && a.paciente_id === MARIA));
assert.ok(aud.data.some((a) => a.acao === 'acesso_negado' && a.paciente_id === JOAO));
ok('admin da Cardiologia vê a auditoria: abertura da Maria e tentativa negada no João');

await cardio.auth.signOut();
assert.equal((await cardio.rpc('buscar_pacientes', { p_texto: null })).data?.length ?? 0, 0);
ok('depois do logout: nada de pacientes');
console.log('homologação: todos os testes passaram');
