import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import test, { before, after } from 'node:test';
import { PGlite } from '@electric-sql/pglite';
import { criarSessaoAtiva, definirClaims, limparClaims } from './sessao_helper.mjs';

const pasta=dirname(fileURLToPath(import.meta.url));
const db=new PGlite();
const cardio='20000000-0000-4000-8000-000000000002';
const obstetricia='20000000-0000-4000-8000-000000000004';
const maria='30000000-0000-4000-8000-000000000001';

async function como(usuario,sessao,fn){
  await db.exec('SET ROLE authenticated');
  await definirClaims(db,usuario,sessao);
  try{return await fn();}
  finally{await db.exec('RESET ROLE');await limparClaims(db);}
}
async function comoService(fn){
  await db.exec('SET ROLE service_role');
  try{return await fn();}
  finally{await db.exec('RESET ROLE');}
}

before(async()=>{
  await db.exec(await readFile(resolve(pasta,'shim_auth.sql'),'utf8'));
  await db.exec(await readFile(resolve(pasta,'../migrations/0001_fundacao.sql'),'utf8'));
  await db.exec(await readFile(resolve(pasta,'../seed.sql'),'utf8'));
  for(const file of ['0002_cid10.sql','0003_achados.sql','0004_gestacao.sql','0005_fhir.sql',
    '0006_bodysite_leitura.sql','0007_endurecimento.sql','0008_endurecimento_piloto.sql','0009_sessao_inatividade.sql','0010_vista_achado.sql','0011_vista_up_consistencia.sql'])
    await db.exec(await readFile(resolve(pasta,'../migrations',file),'utf8'));
});
after(async()=>db.close());

test('authenticated e anon não registram atividade nem leem a tabela',async()=>{
  const sessao=randomUUID();
  await db.query('INSERT INTO auth.sessions(id,user_id) VALUES($1,$2)',[sessao,cardio]);
  for(const role of ['authenticated','anon']){
    await db.exec(`SET ROLE ${role}`);
    await definirClaims(db,role==='authenticated'?cardio:null,sessao);
    await assert.rejects(db.query('SELECT public.registrar_atividade_sessao($1,$2)',[sessao,cardio]));
    await assert.rejects(db.query('SELECT * FROM public.sessoes_atividade'));
    await db.exec('RESET ROLE');
    await limparClaims(db);
  }
  await comoService(async()=>{
    await assert.rejects(db.query('INSERT INTO public.sessoes_atividade(sessao_id,usuario_id) VALUES($1,$2)',[sessao,cardio]));
  });
});

test('sem linha de atividade, as leituras de paciente retornam vazio/null',async()=>{
  const sessao=randomUUID();
  await db.query('INSERT INTO auth.sessions(id,user_id) VALUES($1,$2)',[sessao,cardio]);
  await como(cardio,sessao,async()=>{
    assert.equal((await db.query('SELECT public.sessao_ativa() AS ativa')).rows[0].ativa,false);
    assert.deepEqual((await db.query('SELECT id FROM public.perfis WHERE id=$1',[cardio])).rows,[]);
    assert.equal((await db.query('SELECT (public.abrir_prontuario($1)).id AS id',[maria])).rows[0].id,null);
    assert.deepEqual((await db.query('SELECT * FROM public.listar_achados($1)',[maria])).rows,[]);
    assert.deepEqual((await db.query('SELECT * FROM public.buscar_pacientes()')).rows,[]);
  });
  assert.equal((await db.query('SELECT count(*)::int AS n FROM public.sessoes_atividade WHERE sessao_id=$1',[sessao])).rows[0].n,0);
});

test('atividade recente libera abrir_prontuario, listar_achados e buscar_pacientes',async()=>{
  const sessao=await criarSessaoAtiva(db,cardio);
  await como(cardio,sessao,async()=>{
    assert.equal((await db.query('SELECT public.sessao_ativa() AS ativa')).rows[0].ativa,true);
    assert.equal((await db.query('SELECT id FROM public.perfis WHERE id=$1',[cardio])).rows[0].id,cardio);
    assert.equal((await db.query('SELECT (public.abrir_prontuario($1)).id AS id',[maria])).rows[0].id,maria);
    const registrado=await db.query("SELECT public.registrar_achado($1,NULL,'I10','doenca','nao_se_aplica','ativo',CURRENT_DATE,'sessão ativa',NULL) AS id",[maria]);
    assert.ok(registrado.rows[0].id);
    assert.equal((await db.query('SELECT * FROM public.listar_achados($1)',[maria])).rows.length,1);
    assert.ok((await db.query('SELECT * FROM public.buscar_pacientes() WHERE id=$1',[maria])).rows.length===1);
  });
});

test('atividade com 33 minutos não é renovada e sessão inativa não recupera acesso',async()=>{
  const sessao=await criarSessaoAtiva(db,cardio);
  await db.query("UPDATE public.sessoes_atividade SET ultima_atividade=now()-interval '33 minutes' WHERE sessao_id=$1",[sessao]);
  await como(cardio,sessao,async()=>{
    assert.equal((await db.query('SELECT public.sessao_ativa() AS ativa')).rows[0].ativa,false);
    assert.deepEqual((await db.query('SELECT id FROM public.perfis WHERE id=$1',[cardio])).rows,[]);
    assert.equal((await db.query('SELECT (public.abrir_prontuario($1)).id AS id',[maria])).rows[0].id,null);
    assert.deepEqual((await db.query('SELECT * FROM public.listar_achados($1)',[maria])).rows,[]);
    assert.deepEqual((await db.query('SELECT * FROM public.buscar_pacientes()')).rows,[]);
  });
  const renovada=await comoService(()=>db.query('SELECT public.registrar_atividade_sessao($1,$2) AS ok',[sessao,cardio]));
  assert.equal(renovada.rows[0].ok,false);
  assert.equal((await db.query("SELECT ultima_atividade<=now()-interval '32 minutes' AS expirada FROM public.sessoes_atividade WHERE sessao_id=$1",[sessao])).rows[0].expirada,true);
});

test('atividade recusa sessão de outro usuário, sessão ausente e not_after vencido',async()=>{
  const outra=randomUUID();
  await db.query('INSERT INTO auth.sessions(id,user_id) VALUES($1,$2)',[outra,cardio]);
  const expirada=randomUUID();
  await db.query("INSERT INTO auth.sessions(id,user_id,not_after) VALUES($1,$2,now()-interval '1 second')",[expirada,obstetricia]);
  const ausente=randomUUID();
  const results=await comoService(async()=>[
    await db.query('SELECT public.registrar_atividade_sessao($1,$2) AS ok',[outra,obstetricia]),
    await db.query('SELECT public.registrar_atividade_sessao($1,$2) AS ok',[ausente,cardio]),
    await db.query('SELECT public.registrar_atividade_sessao($1,$2) AS ok',[expirada,obstetricia]),
  ]);
  assert.deepEqual(results.map((r)=>r.rows[0].ok),[false,false,false]);
  assert.equal((await db.query('SELECT count(*)::int AS n FROM public.sessoes_atividade WHERE sessao_id IN ($1,$2,$3)',[outra,ausente,expirada])).rows[0].n,0);
});

test('claim session_id ausente ou inválido falha fechado sem erro de conversão',async()=>{
  await db.exec('SET ROLE authenticated');
  await definirClaims(db,cardio,null);
  assert.equal((await db.query('SELECT public.sessao_ativa() AS ativa')).rows[0].ativa,false);
  await db.query("SELECT set_config('request.jwt.claims',$1,false)",[JSON.stringify({sub:cardio,session_id:'not-a-uuid'})]);
  assert.equal((await db.query('SELECT public.sessao_ativa() AS ativa')).rows[0].ativa,false);
  await db.exec('RESET ROLE');
  await limparClaims(db);
});
