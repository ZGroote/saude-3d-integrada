// Critérios registrados antes da execução (SPEC-MVP.md §12, “Homologação antes de dado real”):
// Cada tentativa abaixo deve ser negada, ou devolver vazio/null/false sem revelar dados.
// Qualquer resposta bem-sucedida com dados ou qualquer gravação é uma falha a reportar.
// Testes limitados à API pública PostgREST/Auth/Storage; sem SQL privilegiado ou migrações.
// Toda informação enviada é sintética; nunca imprimir credenciais, tokens ou corpos de resposta.
// Inventário conferido em supabase/migrations/0001_fundacao.sql a 0005_fhir.sql:
// RPC: minha_unidade, eh_admin, abrir_prontuario, buscar_pacientes, cadastrar_paciente,
// vincular_paciente, encerrar_vinculo, buscar_cid10, registrar_achado, listar_achados,
// historico_achado, calcular_sigilo_condicao_gestacao, registrar_gestacao,
// registrar_condicao_gestacao, encerrar_gestacao, registrar_nascimento, listar_gestacoes,
// historico_gestacional_crianca, iniciar_importacao, importar_paciente_fhir,
// importar_condicao_fhir, importar_evento_fhir, concluir_importacao, listar_eventos.
// Tabelas (15): unidades, perfis, pacientes, vinculos, auditoria, cid10, cid10_sigilo, achados,
// gestacoes, condicoes_gestacao, nascimentos, importacoes_fhir, eventos_clinicos,
// paciente_fhir, bodysite_estrutura.

import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { randomUUID } from 'node:crypto';

const { createClient } = createRequire(new URL('../web/package.json', import.meta.url))('@supabase/supabase-js');
const ler = (f) => Object.fromEntries(readFileSync(new URL(f, import.meta.url), 'utf8')
  .split(/\r?\n/).filter((l) => l.includes('='))
  .map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1)]));
const env = ler('./.env');
const senhas = ler('./.env.demo');
const BASE = 'https://zmrxskzokpbedmvikrvc.supabase.co';
const KEY = env.SUPABASE_PUBLISHABLE_KEY ?? 'sb_publishable_flRzSCRnQhQ1ptqC3KFzdA_ePN2J6N0';
const MARIA = '30000000-0000-4000-8000-000000000001';
const AUSENTE = 'ffffffff-ffff-4fff-8fff-ffffffffffff';
const TABELAS = ['unidades','perfis','pacientes','vinculos','auditoria','cid10','cid10_sigilo','achados',
  'gestacoes','condicoes_gestacao','nascimentos','importacoes_fhir','eventos_clinicos','paciente_fhir','bodysite_estrutura'];
const RPC_ANON = {
  minha_unidade: {}, eh_admin: {}, abrir_prontuario: { p_paciente: MARIA },
  buscar_pacientes: { p_texto: null },
  cadastrar_paciente: { p_nome: null, p_cns: null, p_sexo: null, p_data_nascimento: null, p_motivo: null, p_origem: null },
  vincular_paciente: { p_paciente: AUSENTE, p_motivo: 'teste adversarial', p_origem: 'atendimento' },
  encerrar_vinculo: { p_vinculo: AUSENTE }, buscar_cid10: { p_texto: 'I10', p_limite: 1 },
  registrar_achado: { p_paciente: MARIA, p_ancora: null, p_cid10: 'I10', p_categoria: 'doenca', p_lado: 'nao_se_aplica', p_status: 'ativo', p_inicio: '2026-01-01', p_observacao: 'teste adversarial (dado fictício)', p_substitui: null },
  listar_achados: { p_paciente: MARIA }, historico_achado: { p_achado: AUSENTE },
  calcular_sigilo_condicao_gestacao: {}, registrar_gestacao: { p_mae: MARIA, p_dum: '2099-01-01', p_inicio_pre_natal: null },
  registrar_condicao_gestacao: { p_gestacao: AUSENTE, p_cid10: 'O24.4', p_semana: 10 },
  encerrar_gestacao: { p_gestacao: AUSENTE, p_desfecho: 'aborto' },
  registrar_nascimento: { p_gestacao: AUSENTE, p_nome: 'RN Teste', p_sexo: 'feminino', p_data: '2026-01-01', p_peso_g: 3000, p_idade_gestacional_sem: 38, p_apgar_5: 9 },
  listar_gestacoes: { p_mae: MARIA }, historico_gestacional_crianca: { p_crianca: AUSENTE },
  iniciar_importacao: { p_arquivo: 'teste-ficticio.json', p_recursos: 0, p_sistema_origem: 'teste-adversarial' },
  importar_paciente_fhir: { p_importacao: AUSENTE, p_fhir_id: 'probe-paciente', p_cns: null, p_nome: 'RN Teste', p_sexo: 'feminino', p_nascimento: '2026-01-01' },
  importar_condicao_fhir: { p_importacao: AUSENTE, p_paciente: AUSENTE, p_fhir_id: 'probe-condicao', p_cid10: 'I10', p_ancora: null, p_status: 'ativo', p_inicio: '2026-01-01' },
  importar_evento_fhir: { p_importacao: AUSENTE, p_paciente: AUSENTE, p_fhir_id: 'probe-evento', p_tipo: 'Observation', p_data: null, p_codigo: null, p_descricao: null, p_valor: null },
  concluir_importacao: { p_importacao: AUSENTE, p_erros: [] }, listar_eventos: { p_paciente: MARIA },
};
const tentativas = [];
const falhas = [];
const registrar = (cenario, status, ok, detalhe = '') => {
  tentativas.push({ cenario, status });
  if (!ok) falhas.push({ cenario, status, detalhe });
};
const vazio = (v) => v == null || v === false || (Array.isArray(v) && (v.length === 0 || v.every(vazio))) ||
  (typeof v === 'object' && !Array.isArray(v) && Object.values(v).every(vazio));
const api = (token) => createClient(BASE, KEY, {
  auth: { persistSession: false, autoRefreshToken: false },
  global: token ? { headers: { Authorization: `Bearer ${token}` } } : undefined,
});
async function login(email) {
  const c = api();
  const { data, error } = await c.auth.signInWithPassword({ email, password: senhas[email] });
  if (error || !data?.session?.access_token) throw new Error('login de teste indisponível');
  return { client: c, token: data.session.access_token };
}
function b64url(obj) { return Buffer.from(JSON.stringify(obj)).toString('base64url'); }
async function raw(path, { token, method = 'GET', body, headers = {} } = {}) {
  const h = { apikey: KEY, ...headers };
  if (token) h.Authorization = `Bearer ${token}`;
  if (body !== undefined) h['Content-Type'] = 'application/json';
  return fetch(`${BASE}${path}`, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
}

// 1. Todas as funções públicas da série de migrações, como anônimo.
const anon = api();
for (const [fn, args] of Object.entries(RPC_ANON)) {
  try {
    const { data, error } = await anon.rpc(fn, args);
    registrar(`anon RPC ${fn}`, error ? 'erro' : '2xx', Boolean(error) || vazio(data), error ? 'chamada recusada' : vazio(data) ? '' : 'retornou dado');
  } catch { registrar(`anon RPC ${fn}`, 'exceção', true); }
}

// Login profissional sintético de outra unidade (Pediatria), sem exibir credenciais.
let prof;
try { prof = await login('pediatria@saude3d.invalid'); }
catch { console.error('Não foi possível autenticar o usuário sintético de Pediatria; testes dependentes não executados.'); }

const unidadeProf = prof ? (await api(prof.token).rpc('minha_unidade')).data : null;
const ESCOPO_LEITURA = {
  unidades: (l) => l.id === unidadeProf,
  perfis: (l) => l.unidade_id === unidadeProf,
  cid10: () => true,
  bodysite_estrutura: () => true,
};

// 2. CRUD direto em cada tabela, anon e profissional.
for (const [papel, token] of [['anon', null], ...(prof ? [['profissional', prof.token]] : [])]) {
  for (const tabela of TABELAS) {
    // leituras previstas (0001/0002/0006): referência aberta a authenticated; unidades e perfis só da própria unidade
    if (papel === 'profissional' && tabela in ESCOPO_LEITURA) {
      try {
        const r = await raw(`/rest/v1/${tabela}?select=*`, { token });
        const data = r.ok ? await r.json().catch(() => null) : null;
        const ok = r.ok && Array.isArray(data) && data.every((linha) => ESCOPO_LEITURA[tabela](linha));
        registrar(`${papel} SELECT ${tabela} (escopo)`, r.status, ok, ok ? '' : 'linha fora do escopo previsto');
      } catch { registrar(`${papel} SELECT ${tabela} (escopo)`, 'exceção', false, 'falha ao conferir escopo'); }
    } else try {
      const r = await raw(`/rest/v1/${tabela}?select=*&limit=1`, { token });
      const data = r.ok ? await r.json().catch(() => null) : null;
      registrar(`${papel} SELECT ${tabela}`, r.status, !r.ok || (Array.isArray(data) && data.length === 0), r.ok && !vazio(data) ? 'retornou linhas' : '');
    } catch { registrar(`${papel} SELECT ${tabela}`, 'exceção', true); }
    try {
      const r = await raw(`/rest/v1/${tabela}`, { token, method: 'POST', body: {}, headers: { Prefer: 'return=representation' } });
      const data = r.ok ? await r.json().catch(() => null) : null;
      registrar(`${papel} INSERT ${tabela}`, r.status, !r.ok, r.ok ? 'resposta 2xx; possível gravação' : '');
    } catch { registrar(`${papel} INSERT ${tabela}`, 'exceção', true); }
    const filtro = tabela === 'bodysite_estrutura' ? 'snomed=eq.999999999' :
      tabela === 'paciente_fhir' ? 'fhir_id=eq.__probe__' : 'id=eq.ffffffff-ffff-4fff-8fff-ffffffffffff';
    for (const [acao, method, body] of [['UPDATE','PATCH',{}], ['DELETE','DELETE',undefined]]) {
      try {
        const r = await raw(`/rest/v1/${tabela}?${filtro}`, { token, method, body, headers: { Prefer: 'return=representation' } });
        const data = r.ok ? await r.json().catch(() => null) : null;
        registrar(`${papel} ${acao} ${tabela}`, r.status, !r.ok || vazio(data), r.ok && !vazio(data) ? 'alterou/removeu linha' : '');
      } catch { registrar(`${papel} ${acao} ${tabela}`, 'exceção', true); }
    }
  }
}

// 3. JWTs malformados: Auth /user deve rejeitar todos; nunca registrar token/resposta.
if (prof) {
  const token = prof.token;
  const [head, payload, sig = ''] = token.split('.');
  const primeiro = sig[0] === 'A' ? 'B' : 'A';
  const alterada = `${head}.${payload}.${primeiro}${sig.slice(1)}`;
  let claim = {};
  try { claim = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8')); } catch {}
  const expirada = `${head}.${b64url({ ...claim, exp: 1 })}.${sig}`;
  const outroSub = `${head}.${b64url({ ...claim, sub: AUSENTE })}.${sig}`;
  const jwtNone = `${b64url({ alg: 'none', typ: 'JWT' })}.${payload}.`;
  for (const [nome, jwt] of [['assinatura trocada', alterada], ['alg none', jwtNone], ['expiração passada', expirada], ['sub de outro usuário + assinatura inválida', outroSub]]) {
    try {
      const r = await raw('/auth/v1/user', { token: jwt });
      const body = r.ok ? await r.json().catch(() => null) : null;
      registrar(`JWT forjado: ${nome}`, r.status, !r.ok || vazio(body), r.ok && !vazio(body) ? 'Auth aceitou token forjado' : '');
    } catch { registrar(`JWT forjado: ${nome}`, 'exceção', true); }
  }
}

// 4. RPCs de leitura/escrita contra Maria e importação por profissional não-admin.
if (prof) {
  const outsiderCalls = {
    abrir_prontuario: { p_paciente: MARIA }, listar_achados: { p_paciente: MARIA },
    historico_achado: { p_achado: AUSENTE }, listar_gestacoes: { p_mae: MARIA },
    listar_eventos: { p_paciente: MARIA }, historico_gestacional_crianca: { p_crianca: AUSENTE },
    registrar_achado: { ...RPC_ANON.registrar_achado },
    registrar_gestacao: { p_mae: MARIA, p_dum: '2099-01-01', p_inicio_pre_natal: null },
    registrar_nascimento: { ...RPC_ANON.registrar_nascimento },
    vincular_paciente: { p_paciente: MARIA, p_motivo: 'teste adversarial', p_origem: 'atendimento' },
    iniciar_importacao: RPC_ANON.iniciar_importacao,
    importar_paciente_fhir: RPC_ANON.importar_paciente_fhir,
    importar_condicao_fhir: RPC_ANON.importar_condicao_fhir,
    importar_evento_fhir: RPC_ANON.importar_evento_fhir,
    concluir_importacao: RPC_ANON.concluir_importacao,
  };
  for (const [fn, args] of Object.entries(outsiderCalls)) {
    try {
      const { data, error } = await prof.client.rpc(fn, args);
      const safe = Boolean(error) || vazio(data);
      registrar(`Pediatria RPC ${fn}`, error ? 'erro' : '2xx', safe, safe ? '' : 'resposta não vazia; verificar possível gravação');
    } catch { registrar(`Pediatria RPC ${fn}`, 'exceção', true); }
  }
}

// 5. Storage: buckets e listagem de objetos não devem revelar conteúdo; upload anônimo falha.
let buckets = [];
for (const [papel, token] of [['anon', null], ...(prof ? [['profissional', prof.token]] : [])]) {
  try {
    const r = await raw('/storage/v1/bucket', { token });
    const body = r.ok ? await r.json().catch(() => null) : null;
    const lista = Array.isArray(body) ? body : [];
    if (papel === 'anon') buckets = lista;
    registrar(`${papel} Storage listar buckets`, r.status, !r.ok || lista.length === 0, lista.length ? `${lista.length} bucket(s) retornados` : '');
    for (const b of lista) {
      const objetos = await raw(`/storage/v1/object/list/${encodeURIComponent(b.id ?? b.name)}`, { token, method: 'POST', body: { prefix: '', limit: 1, offset: 0, sortBy: { column: 'name', order: 'asc' } } });
      const items = objetos.ok ? await objetos.json().catch(() => null) : null;
      registrar(`${papel} Storage objetos`, objetos.status, !objetos.ok || vazio(items), objetos.ok && !vazio(items) ? 'objetos visíveis' : '');
    }
    if (lista.length === 0) {
      const objetos = await raw('/storage/v1/object/list/probe-bucket-inexistente', { token, method: 'POST', body: { prefix: '', limit: 1, offset: 0, sortBy: { column: 'name', order: 'asc' } } });
      const items = objetos.ok ? await objetos.json().catch(() => null) : null;
      registrar(`${papel} Storage objetos (sonda)`, objetos.status, !objetos.ok || vazio(items), objetos.ok && !vazio(items) ? 'objetos visíveis' : '');
    }
  } catch { registrar(`${papel} Storage listar buckets`, 'exceção', true); }
}
const bucketAlvo = buckets.find((b) => b.public === false)?.id ?? 'probe-bucket-inexistente';
const caminhoProbe = `__probe_adversarial__/${randomUUID()}.txt`;
try {
  const r = await raw(`/storage/v1/object/${encodeURIComponent(bucketAlvo)}/${caminhoProbe}`, { method: 'POST', body: 'x', headers: { 'Content-Type': 'text/plain', 'x-upsert': 'false' } });
  if (r.ok) {
    // Remove imediatamente qualquer objeto sintético criado por uma falha de política.
    const del = await raw(`/storage/v1/object/${encodeURIComponent(bucketAlvo)}/${caminhoProbe}`, { method: 'DELETE' });
    registrar('anon Storage upload', r.status, false, del.ok ? 'upload aceito; objeto sintético removido' : 'upload aceito; remoção automática falhou');
  } else registrar('anon Storage upload', r.status, true);
} catch { registrar('anon Storage upload', 'exceção', true); }

// 6. OpenAPI é informativo: registrar somente nomes/contagens de schema, sem dados.
try {
  const r = await raw('/rest/v1/');
  const body = r.ok ? await r.json().catch(() => null) : null;
  const paths = body?.paths ? Object.keys(body.paths) : [];
  const informativo = paths.map((p) => p.replace(/^\//, '')).filter((p) => p && p !== 'rpc');
  console.log(`OpenAPI informativo: HTTP ${r.status}; recursos publicados (${informativo.length}): ${informativo.join(', ') || 'nenhum nome extraível'}`);
  tentativas.push({ cenario: 'OpenAPI informativo', status: r.status });
} catch { console.log('OpenAPI informativo: indisponível'); tentativas.push({ cenario: 'OpenAPI informativo', status: 'exceção' }); }

console.log(`Tentativas totais: ${tentativas.length}`);
console.log(`Negadas/vazias: ${tentativas.length - falhas.length - 1}`); // OpenAPI não é teste de bloqueio.
console.log(`Falhas: ${falhas.length}`);
for (const f of falhas) console.log(`FALHA | ${f.cenario} | HTTP ${f.status} | ${f.detalhe}`);
if (falhas.some((f) => f.detalhe.includes('gravação') || f.detalhe.includes('upload aceito'))) {
  console.log('Atenção: houve indício de gravação sintética; verificar e executar a limpeza prevista antes de encerrar.');
}
