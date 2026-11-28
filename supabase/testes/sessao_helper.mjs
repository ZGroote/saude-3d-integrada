import { randomUUID } from 'node:crypto';

export async function criarSessaoAtiva(db, usuario, notAfter = null) {
  const sessao = randomUUID();
  await db.query('INSERT INTO auth.sessions(id,user_id,not_after) VALUES($1,$2,$3)', [sessao,usuario,notAfter]);
  await db.exec('SET ROLE service_role');
  try {
    const r = await db.query('SELECT public.registrar_atividade_sessao($1,$2) AS ok', [sessao,usuario]);
    if (r.rows[0]?.ok !== true) throw new Error('falha interna ao ativar sessão sintética PGlite');
  } finally {
    await db.exec('RESET ROLE');
  }
  return sessao;
}

export async function definirClaims(db, usuario, sessao = null) {
  const claims = usuario ? { sub: usuario, ...(sessao ? { session_id: sessao } : {}) } : {};
  await db.query("SELECT set_config('request.jwt.claims',$1,false)", [JSON.stringify(claims)]);
  await db.query("SELECT set_config('request.jwt.claim.sub',$1,false)", [usuario ?? '']);
}

export async function limparClaims(db) {
  await definirClaims(db, null, null);
}
