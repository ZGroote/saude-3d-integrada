import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import test, { before, after } from 'node:test';
import { PGlite } from '@electric-sql/pglite';

const pasta = dirname(fileURLToPath(import.meta.url));
const db = new PGlite();
const obstetricia = '20000000-0000-4000-8000-000000000004';
const cardiologia = '20000000-0000-4000-8000-000000000002';
const adminUbs = '20000000-0000-4000-8000-000000000001';
const pediatriaAdmin = '20000000-0000-4000-8000-000000000008';
const pediatra = '20000000-0000-4000-8000-000000000009';
const maria = '30000000-0000-4000-8000-000000000001';
const unidadeMaternidade = '10000000-0000-4000-8000-000000000003';
const ausente = '90000000-0000-4000-8000-000000000099';
let gestacao;
let crianca;

async function como(usuario, fn) {
  await db.exec('SET ROLE authenticated');
  await db.query("SELECT set_config('request.jwt.claim.sub', $1, false)", [usuario]);
  try { return await fn(); }
  finally {
    await db.exec('RESET ROLE');
    await db.query("SELECT set_config('request.jwt.claim.sub', '', false)");
  }
}

before(async () => {
  await db.exec(await readFile(resolve(pasta, 'shim_auth.sql'), 'utf8'));
  await db.exec(await readFile(resolve(pasta, '../migrations/0001_fundacao.sql'), 'utf8'));
  await db.exec(await readFile(resolve(pasta, '../seed.sql'), 'utf8'));
  await db.exec(await readFile(resolve(pasta, '../migrations/0002_cid10.sql'), 'utf8'));
  await db.exec(await readFile(resolve(pasta, '../migrations/0003_achados.sql'), 'utf8'));
  await db.exec(await readFile(resolve(pasta, '../migrations/0004_gestacao.sql'), 'utf8'));
});
after(async () => db.close());

test('obstetrícia registra gestação, condições e nascimento com DPP calculada', async () => {
  const dum = '2026-01-01';
  gestacao = (await como(obstetricia, async () => (await db.query(
    'SELECT public.registrar_gestacao($1,$2::date,$3::date) AS id', [maria,dum,'2026-01-15'],
  )).rows[0].id));
  assert.ok(gestacao);
  const row = (await db.query('SELECT dum,dpp,desfecho FROM public.gestacoes WHERE id=$1',[gestacao])).rows[0];
  assert.equal(row.dpp.toISOString().slice(0,10), '2026-10-08');
  assert.equal(row.desfecho, 'em_curso');
  await como(obstetricia, async () => {
    await db.query("SELECT public.registrar_condicao_gestacao($1,'O24.4',28)",[gestacao]);
    await db.query("SELECT public.registrar_condicao_gestacao($1,'O98.7',30)",[gestacao]);
    await assert.rejects(db.query(
      'SELECT public.registrar_gestacao($1,$2::date,NULL) AS id',[maria,'2026-02-01'],
    ));
  });
  const sigilos = (await db.query('SELECT cid10,nivel_sigilo FROM public.condicoes_gestacao ORDER BY cid10')).rows;
  assert.deepEqual(sigilos,[{cid10:'O24.4',nivel_sigilo:'normal'},{cid10:'O98.7',nivel_sigilo:'restrito'}]);
  crianca = await como(obstetricia, async () => (await db.query(
    `SELECT public.registrar_nascimento($1,'Bebê Fictício','feminino','2026-10-08',3200,40,9) AS id`,[gestacao],
  )).rows[0].id);
  assert.ok(crianca);
  assert.equal((await db.query('SELECT desfecho FROM public.gestacoes WHERE id=$1',[gestacao])).rows[0].desfecho,'nascido_vivo');
  assert.equal((await db.query('SELECT crianca_id FROM public.nascimentos WHERE gestacao_id=$1',[gestacao])).rows[0].crianca_id,crianca);
  const vinculo = (await db.query('SELECT unidade_id FROM public.vinculos WHERE paciente_id=$1',[crianca])).rows[0];
  assert.equal(vinculo.unidade_id,unidadeMaternidade);
  const listed = await como(obstetricia,()=>db.query('SELECT * FROM public.listar_gestacoes($1)',[maria]));
  assert.equal(listed.rows[0].dpp.toISOString().slice(0,10),'2026-10-08');
  assert.equal(listed.rows[0].condicoes.length,2);
  assert.equal(listed.rows[0].condicoes.find((c)=>c.cid10==='O24.4').cid10_descricao.length>0,true);
  assert.equal(listed.rows[0].nascimentos[0].crianca_nome,'Bebê Fictício');
  const cardiologyList = await como(cardiologia,()=>db.query('SELECT * FROM public.listar_gestacoes($1)',[maria]));
  assert.deepEqual(cardiologyList.rows[0].condicoes.map((c)=>c.cid10),['O24.4']);
  const childCns = (await db.query('SELECT cns FROM public.pacientes WHERE id=$1',[crianca])).rows[0].cns;
  assert.equal(childCns,null);
  await assert.rejects(como(obstetricia,()=>db.query(
    "SELECT public.registrar_nascimento($1,'Nascimento inválido','feminino','2025-12-31',3000,40,8)",[gestacao],
  )),(e)=>e.code==='22023');
  await assert.rejects(como(obstetricia,()=>db.query(
    "SELECT public.registrar_nascimento($1,'Nascimento futuro','feminino',CURRENT_DATE+1,3000,40,8)",[gestacao],
  )),(e)=>e.code==='22023');
  await assert.rejects(como(obstetricia,()=>db.query(
    "SELECT public.encerrar_gestacao($1,'nascido_vivo')",[gestacao],
  )),(e)=>e.code==='22023');
  const gemeo = await como(obstetricia,async()=> (await db.query(
    "SELECT public.registrar_nascimento($1,'Gêmeo Fictício','masculino','2026-10-08',3100,40,8)",[gestacao],
  )).rows[0].registrar_nascimento);
  assert.ok(gemeo);
  assert.notEqual(gemeo,crianca);
  assert.equal((await db.query('SELECT count(*)::int AS n FROM public.nascimentos WHERE gestacao_id=$1',[gestacao])).rows[0].n,2);
});

test('Pediatria vê apenas recorte não restrito da criança e não acessa a mãe', async () => {
  await como(pediatriaAdmin,()=>db.query("SELECT public.vincular_paciente($1,'Acompanhamento pediátrico','encaminhamento')",[crianca]));
  const history = await como(pediatra,()=>db.query('SELECT * FROM public.historico_gestacional_crianca($1)',[crianca]));
  assert.equal(history.rows.length,1);
  assert.equal(history.rows[0].nome_mae,'Maria Fictícia');
  assert.equal(history.rows[0].mae_id,maria);
  assert.equal(history.rows[0].cid10,'O24.4');
  assert.equal(history.rows[0].idade_gestacional_sem,40);
  assert.equal(history.rows[0].peso_g,3200);
  assert.equal(history.rows[0].apgar_5,9);
  assert.equal(JSON.stringify(history.rows).includes('O98.7'),false);
  const prontuarioMae=await como(pediatra,()=>db.query('SELECT (public.abrir_prontuario($1)).id AS id',[history.rows[0].mae_id]));
  assert.equal(prontuarioMae.rows[0].id,null);
  assert.ok((await db.query("SELECT 1 FROM public.auditoria WHERE autor_id=$1 AND paciente_id=$2 AND acao='acesso_negado'",[pediatra,maria])).rows.length>0);
  assert.equal((await como(pediatra,()=>db.query('SELECT * FROM public.listar_achados($1)',[maria]))).rows.length,0);
  assert.equal((await como(pediatra,()=>db.query('SELECT * FROM public.listar_gestacoes($1)',[maria]))).rows.length,0);
  assert.equal((await db.query(`SELECT count(*)::int AS n FROM public.auditoria WHERE autor_id=$1 AND acao='acesso_negado'`,[pediatra])).rows[0].n,3);
  assert.equal((await db.query('SELECT especialidade FROM public.perfis WHERE id=$1',[pediatra])).rows[0].especialidade,'pediatria');
  const vinculo = (await db.query('SELECT unidade_id FROM public.vinculos WHERE paciente_id=$1 AND unidade_id=(SELECT unidade_id FROM public.perfis WHERE id=$2)',[crianca,pediatriaAdmin])).rows[0];
  assert.equal(vinculo.unidade_id,(await db.query('SELECT unidade_id FROM public.perfis WHERE id=$1',[pediatriaAdmin])).rows[0].unidade_id);
});

test('sem vínculo com a criança nada é exibido e tentativa sem vínculo com mãe devolve null auditado', async () => {
  const semVinculo = await como(cardiologia,()=>db.query('SELECT * FROM public.historico_gestacional_crianca($1)',[crianca]));
  assert.deepEqual(semVinculo.rows,[]);
  assert.ok((await db.query("SELECT 1 FROM public.auditoria WHERE autor_id=$1 AND paciente_id IS NULL AND acao='acesso_negado'",[cardiologia])).rows.length>0);
  const negado = await como(pediatra,()=>db.query(
    `SELECT public.registrar_nascimento($1,'Não deve nascer','feminino',CURRENT_DATE,3000,39,8) AS id`,[gestacao],
  ));
  assert.equal(negado.rows[0].id,null);
  assert.ok((await db.query("SELECT 1 FROM public.auditoria WHERE autor_id=$1 AND unidade_id=$2 AND acao='acesso_negado'",
    [pediatra,(await db.query('SELECT unidade_id FROM public.perfis WHERE id=$1',[pediatra])).rows[0].unidade_id])).rows.length>0);
});

test('gestação masculina, CID inválido e semana fora do intervalo são recusados', async () => {
  const masculino = await como(adminUbs,()=>db.query(
    "SELECT public.registrar_gestacao('30000000-0000-4000-8000-000000000002',CURRENT_DATE,NULL) AS id",
  ));
  assert.equal(masculino.rows[0].id,null);
  const segunda = await como(adminUbs,async()=> (await db.query(
    'SELECT public.registrar_gestacao($1,$2::date,NULL) AS id',[maria,'2026-02-01'],
  )).rows[0].id);
  await assert.rejects(como(adminUbs,()=>db.query(
    "SELECT public.registrar_condicao_gestacao($1,'O24.4',46)",[segunda],
  )),(e)=>e.code==='22023');
  await assert.rejects(como(adminUbs,()=>db.query(
    "SELECT public.registrar_condicao_gestacao($1,'ZZZ99.9',20)",[segunda],
  )),(e)=>e.code==='22023');
  await como(adminUbs,()=>db.query("SELECT public.encerrar_gestacao($1,'obito_fetal')",[segunda]));
  assert.equal((await db.query('SELECT desfecho FROM public.gestacoes WHERE id=$1',[segunda])).rows[0].desfecho,'obito_fetal');
  const terceira = await como(adminUbs,async()=> (await db.query(
    'SELECT public.registrar_gestacao($1,$2::date,NULL) AS id',[maria,'2026-03-01'],
  )).rows[0].id);
  await como(adminUbs,()=>db.query("SELECT public.encerrar_gestacao($1,'aborto')",[terceira]));
  assert.equal((await db.query('SELECT desfecho FROM public.gestacoes WHERE id=$1',[terceira])).rows[0].desfecho,'aborto');
});

test('as seis RPCs ocultam UUIDs ausentes como pacientes sem vínculo e auditam a tentativa', async () => {
  const gestacaoMaria=gestacao;
  const semVinculoGestacao=(await db.query('SELECT id FROM public.gestacoes WHERE mae_id=$1 ORDER BY criado_em LIMIT 1',[maria])).rows[0].id;
  const casos=[
    {usuario:obstetricia,acao:'registrar_gestacao',ausente:"SELECT public.registrar_gestacao($1,CURRENT_DATE,NULL) AS valor",sem:"SELECT public.registrar_gestacao($1,CURRENT_DATE,NULL) AS valor",a:[ausente],s:['30000000-0000-4000-8000-000000000002']},
    {usuario:pediatra,acao:'registrar_condicao_gestacao',ausente:"SELECT public.registrar_condicao_gestacao($1,'O24.4',20) AS valor",sem:"SELECT public.registrar_condicao_gestacao($1,'O24.4',20) AS valor",a:[ausente],s:[semVinculoGestacao]},
    {usuario:pediatra,acao:'encerrar_gestacao',ausente:"SELECT public.encerrar_gestacao($1,'aborto') AS valor",sem:"SELECT public.encerrar_gestacao($1,'aborto') AS valor",a:[ausente],s:[semVinculoGestacao]},
    {usuario:pediatra,acao:'registrar_nascimento',ausente:"SELECT public.registrar_nascimento($1,'Teste','feminino',CURRENT_DATE,3000,39,8) AS valor",sem:"SELECT public.registrar_nascimento($1,'Teste','feminino',CURRENT_DATE,3000,39,8) AS valor",a:[ausente],s:[semVinculoGestacao]},
    {usuario:obstetricia,acao:'listar_gestacoes',ausente:'SELECT * FROM public.listar_gestacoes($1)',sem:'SELECT * FROM public.listar_gestacoes($1)',a:[ausente],s:['30000000-0000-4000-8000-000000000002']},
    {usuario:cardiologia,acao:'historico_gestacional_crianca',ausente:'SELECT * FROM public.historico_gestacional_crianca($1)',sem:'SELECT * FROM public.historico_gestacional_crianca($1)',a:[ausente],s:[crianca]},
  ];
  for (const c of casos) {
    const antes=(await db.query("SELECT count(*)::int AS n FROM public.auditoria WHERE autor_id=$1 AND acao='acesso_negado'",[c.usuario])).rows[0].n;
    const a=await como(c.usuario,()=>db.query(c.ausente,c.a));
    const s=await como(c.usuario,()=>db.query(c.sem,c.s));
    assert.deepEqual(a.rows,s.rows,`${c.acao}: resposta para UUID ausente vs sem vínculo`);
    const depois=(await db.query("SELECT count(*)::int AS n FROM public.auditoria WHERE autor_id=$1 AND acao='acesso_negado'",[c.usuario])).rows[0].n;
    assert.equal(depois,antes+2,`${c.acao}: ambas as tentativas devem ser auditadas`);
  }
  assert.ok(gestacaoMaria);
});

test('anon e authenticated sem sub não obtêm dados nem deixam auditoria de prontuário', async () => {
  const chamadas=[
    "SELECT public.registrar_gestacao($1,CURRENT_DATE,NULL)",
    "SELECT public.registrar_condicao_gestacao($1,'O24.4',20)",
    "SELECT public.encerrar_gestacao($1,'aborto')",
    "SELECT public.registrar_nascimento($1,'Teste','feminino',CURRENT_DATE,3000,39,8)",
    'SELECT * FROM public.listar_gestacoes($1)',
    'SELECT * FROM public.historico_gestacional_crianca($1)',
  ];
  const beforeCount=(await db.query("SELECT count(*)::int AS n FROM public.auditoria WHERE acao='acesso_negado'")).rows[0].n;
  await db.exec('SET ROLE anon');
  for (const sql of chamadas) await assert.rejects(db.query(sql,[ausente]));
  await db.exec('RESET ROLE');
  await db.exec('SET ROLE authenticated');
  await db.query("SELECT set_config('request.jwt.claim.sub','',false)");
  const semSessao=[];
  for (const sql of chamadas) semSessao.push(await db.query(sql,[ausente]));
  await db.exec('RESET ROLE');
  await db.query("SELECT set_config('request.jwt.claim.sub','',false)");
  assert.equal(semSessao[0].rows[0].registrar_gestacao,null);
  assert.equal(semSessao[1].rows[0].registrar_condicao_gestacao,null);
  assert.ok([null,''].includes(semSessao[2].rows[0].encerrar_gestacao));
  assert.equal(semSessao[3].rows[0].registrar_nascimento,null);
  assert.deepEqual(semSessao[4].rows,[]);
  assert.deepEqual(semSessao[5].rows,[]);
  assert.equal((await db.query("SELECT count(*)::int AS n FROM public.auditoria WHERE acao='acesso_negado'")).rows[0].n,beforeCount);
});

test('achados expõem unidade_id e tabelas gestacionais não aceitam DML direto', async () => {
  await como(obstetricia,async()=>{
    const achado=(await db.query("SELECT public.registrar_achado($1,NULL,'Z34.0','doenca','nao_se_aplica','ativo',CURRENT_DATE,NULL,NULL) AS id",[maria])).rows[0].id;
    const lista=await db.query('SELECT unidade_id FROM public.listar_achados($1)',[maria]);
    assert.equal(lista.rows[0].unidade_id,unidadeMaternidade);
    const historico=await db.query('SELECT unidade_id FROM public.historico_achado($1)',[achado]);
    assert.equal(historico.rows[0].unidade_id,unidadeMaternidade);
    await assert.rejects(db.query('SELECT * FROM public.gestacoes'));
    await assert.rejects(db.query('INSERT INTO public.gestacoes(mae_id,dum,autor_id,unidade_id) VALUES($1,CURRENT_DATE,$2,$3)',[maria,obstetricia,unidadeMaternidade]));
    await assert.rejects(db.query('UPDATE public.gestacoes SET dum=CURRENT_DATE'));
    await assert.rejects(db.query('DELETE FROM public.gestacoes'));
    await assert.rejects(db.query('SELECT * FROM public.condicoes_gestacao'));
    await assert.rejects(db.query("INSERT INTO public.condicoes_gestacao(gestacao_id,cid10,semana,autor_id,unidade_id) VALUES($1,'O24.4',1,$2,$3)",[gestacao,obstetricia,unidadeMaternidade]));
    await assert.rejects(db.query('UPDATE public.condicoes_gestacao SET semana=2'));
    await assert.rejects(db.query('DELETE FROM public.condicoes_gestacao'));
    await assert.rejects(db.query('SELECT * FROM public.nascimentos'));
    await assert.rejects(db.query("INSERT INTO public.nascimentos(gestacao_id,crianca_id,data,peso_g,idade_gestacional_sem,apgar_5,autor_id,unidade_id) VALUES($1,$2,CURRENT_DATE,3000,39,8,$3,$4)",[gestacao,crianca,obstetricia,unidadeMaternidade]));
    await assert.rejects(db.query('UPDATE public.nascimentos SET peso_g=3100'));
    await assert.rejects(db.query('DELETE FROM public.nascimentos'));
  });
});
