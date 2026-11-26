import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import test, { before, after } from 'node:test';
import { PGlite } from '@electric-sql/pglite';

const pasta=dirname(fileURLToPath(import.meta.url));
const db=new PGlite();
const admin='20000000-0000-4000-8000-000000000001';
const adminCardio='20000000-0000-4000-8000-000000000005';
const profissional='20000000-0000-4000-8000-000000000002';
const maria='30000000-0000-4000-8000-000000000001';
const joao='30000000-0000-4000-8000-000000000002';
const unidadeUbs='10000000-0000-4000-8000-000000000001';
const unidadeCardio='10000000-0000-4000-8000-000000000002';
const ausente='90000000-0000-4000-8000-000000000099';
let importacao;
let importacaoCardio;
let pacienteNovo;
let pacienteCardioSemVinculo;
let pacienteSemVinculo;
let condicaoComAncora;
let condicaoSemAncora;

async function como(usuario,fn){
  await db.exec('SET ROLE authenticated');
  await db.query("SELECT set_config('request.jwt.claim.sub',$1,false)",[usuario]);
  try{return await fn();}
  finally{await db.exec('RESET ROLE');await db.query("SELECT set_config('request.jwt.claim.sub','',false)");}
}

before(async()=>{
  await db.exec(await readFile(resolve(pasta,'shim_auth.sql'),'utf8'));
  await db.exec(await readFile(resolve(pasta,'../migrations/0001_fundacao.sql'),'utf8'));
  await db.exec(await readFile(resolve(pasta,'../seed.sql'),'utf8'));
  for(const file of ['0002_cid10.sql','0003_achados.sql','0004_gestacao.sql','0005_fhir.sql','0006_bodysite_leitura.sql'])
    await db.exec(await readFile(resolve(pasta,'../migrations',file),'utf8'));
});
after(async()=>db.close());

test('admin importa paciente novo e CNS existente, com vínculo e sem duplicar',async()=>{
  importacao=(await como(admin,()=>db.query(
    "SELECT public.iniciar_importacao('bundle-sintetico.json',8) AS id",
  ))).rows[0].id;
  assert.ok(importacao);
  pacienteNovo=(await como(admin,()=>db.query(
    `SELECT public.importar_paciente_fhir($1,'Patient/sintetico-001','799999999999991',
      'Paciente Sintético Um','feminino','1995-04-03') AS id`,[importacao],
  ))).rows[0].id;
  assert.ok(pacienteNovo);
  const novoAgain=(await como(admin,()=>db.query(
    `SELECT public.importar_paciente_fhir($1,' Patient/sintetico-001 ','799999999999991',
      'Nome ignorado','feminino','1995-04-03') AS id`,[importacao],
  ))).rows[0].id;
  assert.equal(novoAgain,pacienteNovo);
  const existente=(await como(admin,()=>db.query(
    `SELECT public.importar_paciente_fhir($1,'Patient/maria-001','700000000000001',
      'Nome externo','feminino','1994-01-01') AS id`,[importacao],
  ))).rows[0].id;
  assert.equal(existente,maria);
  assert.equal((await db.query('SELECT count(*)::int AS n FROM public.pacientes WHERE cns=$1',['799999999999991'])).rows[0].n,1);
  assert.equal((await db.query('SELECT nome,cns FROM public.pacientes WHERE id=$1',[maria])).rows[0].nome,'Maria Fictícia');
  assert.equal((await db.query('SELECT count(*)::int AS n FROM public.paciente_fhir WHERE unidade_id=$1 AND fhir_id=$2 AND paciente_id=$3',
    [unidadeUbs,'Patient/sintetico-001',pacienteNovo])).rows[0].n,1);
  await assert.rejects(como(admin,()=>db.query(
    `SELECT public.importar_paciente_fhir($1,'Patient/sintetico-001','700000000000001',
      'Recurso divergente','feminino','1995-04-03')`,[importacao],
  )),(e)=>e.code==='22023' && !e.message.includes(maria));
  assert.equal((await db.query('SELECT unidade_id,origem FROM public.vinculos WHERE paciente_id=$1 AND unidade_id=$2',[pacienteNovo,unidadeUbs])).rows[0].origem,'importacao');
});

test('condições FHIR aceitam âncora e sem âncora, são idempotentes e respeitam sigilo CID',async()=>{
  const ancora={atlas:'bp3d-m',atlas_versao:'4.0-1',sistema:'esqueletico',estrutura:'FMA24475',malha:'FMA24475'};
  condicaoComAncora=(await como(admin,()=>db.query(
    `SELECT public.importar_condicao_fhir($1,$2,'Condition/001','I10',$3::jsonb,'ativo','2026-01-02') AS id`,
    [importacao,pacienteNovo,JSON.stringify(ancora)],
  ))).rows[0].id;
  const again=(await como(admin,()=>db.query(
    `SELECT public.importar_condicao_fhir($1,$2,'Condition/001','I10',$3::jsonb,'ativo','2026-01-02') AS id`,
    [importacao,pacienteNovo,JSON.stringify(ancora)],
  ))).rows[0].id;
  assert.equal(again,condicaoComAncora);
  condicaoSemAncora=(await como(admin,()=>db.query(
    `SELECT public.importar_condicao_fhir($1,$2,'Condition/002','F32.9',NULL,'ativo','2026-02-02') AS id`,
    [importacao,pacienteNovo],
  ))).rows[0].id;
  const recusada=como(admin,()=>db.query(
    `SELECT public.importar_condicao_fhir($1,$2,'Condition/cid-invalido','ZZZ99.9',NULL,'ativo',CURRENT_DATE)`,
    [importacao,pacienteNovo],
  ));
  await assert.rejects(recusada,(e)=>e.code==='22023');
  const rows=(await db.query('SELECT id,ancora,origem,fhir_id,nivel_sigilo FROM public.achados WHERE paciente_id=$1 ORDER BY fhir_id',[pacienteNovo])).rows;
  assert.equal(rows.length,2);
  assert.deepEqual(rows[0].ancora,ancora);
  assert.equal(rows[1].ancora,null);
  assert.equal(rows[0].origem,'fhir');
  assert.equal(rows[0].nivel_sigilo,'normal');
  assert.equal(rows[1].nivel_sigilo,'restrito');
  const collision=await como(admin,()=>db.query(
    `SELECT public.importar_condicao_fhir($1,$2,'Condition/001','I10',NULL,'ativo',CURRENT_DATE) AS id`,
    [importacao,maria],
  ));
  assert.equal(collision.rows[0].id,null);
  assert.equal((await db.query("SELECT count(*)::int AS n FROM public.achados WHERE unidade_id=$1 AND fhir_id='Condition/001'",[unidadeUbs])).rows[0].n,1);
});

test('eventos entram uma vez e aparecem na linha do tempo com vínculo ativo',async()=>{
  await como(admin,()=>db.query(
    `SELECT public.importar_evento_fhir($1,$2,'Observation/001','Observation',
      '2026-03-01T10:00:00Z','8867-4','Pressão arterial','120/80')`,[importacao,pacienteNovo],
  ));
  await como(admin,()=>db.query(
    `SELECT public.importar_evento_fhir($1,$2,'Observation/001','Observation',
      '2026-03-01T10:00:00Z','8867-4','Texto ignorado','valor ignorado')`,[importacao,pacienteNovo],
  ));
  const eventos=await como(admin,()=>db.query('SELECT * FROM public.listar_eventos($1)',[pacienteNovo]));
  assert.equal(eventos.rows.length,1);
  assert.equal(eventos.rows[0].fhir_id,'Observation/001');
  assert.equal(eventos.rows[0].codigo,'8867-4');
  assert.equal((await db.query('SELECT count(*)::int AS n FROM public.eventos_clinicos WHERE unidade_id=$1 AND fhir_id=$2',[unidadeUbs,'Observation/001'])).rows[0].n,1);
  await como(admin,()=>db.query(
    `SELECT public.importar_evento_fhir($1,$2,'Observation/001','Observation',CURRENT_TIMESTAMP,NULL,NULL,NULL)`,[importacao,maria],
  ));
  assert.equal((await db.query('SELECT count(*)::int AS n FROM public.eventos_clinicos WHERE unidade_id=$1 AND fhir_id=$2',[unidadeUbs,'Observation/001'])).rows[0].n,1);
});

test('fhir_id pode repetir entre unidades, mas não para outro paciente na mesma unidade',async()=>{
  importacaoCardio=(await como(adminCardio,()=>db.query(
    "SELECT public.iniciar_importacao('bundle-cardio-sintetico.json',4) AS id",
  ))).rows[0].id;
  const vinculado=(await como(adminCardio,()=>db.query(
    `SELECT public.importar_paciente_fhir($1,'Patient/sintetico-001','799999999999991',
      'Mesmo paciente','feminino','1995-04-03') AS id`,[importacaoCardio],
  ))).rows[0].id;
  assert.equal(vinculado,pacienteNovo);
  assert.equal((await db.query("SELECT count(*)::int AS n FROM public.paciente_fhir WHERE fhir_id='Patient/sintetico-001'",[])).rows[0].n,2);
  const cidOutraUnidade=(await como(adminCardio,()=>db.query(
    `SELECT public.importar_condicao_fhir($1,$2,'Condition/001','I10',NULL,'ativo',CURRENT_DATE) AS id`,
    [importacaoCardio,pacienteNovo],
  ))).rows[0].id;
  assert.ok(cidOutraUnidade);
  assert.equal((await db.query("SELECT count(*)::int AS n FROM public.achados WHERE fhir_id='Condition/001'",[])).rows[0].n,2);
  await como(adminCardio,()=>db.query(
    `SELECT public.importar_evento_fhir($1,$2,'Observation/001','Observation',CURRENT_TIMESTAMP,'8867-4','Evento cardio','120/80')`,
    [importacaoCardio,pacienteNovo],
  ));
  assert.equal((await db.query("SELECT count(*)::int AS n FROM public.eventos_clinicos WHERE fhir_id='Observation/001'",[])).rows[0].n,2);
  pacienteCardioSemVinculo=(await como(adminCardio,()=>db.query(
    `SELECT public.importar_paciente_fhir($1,'Patient/cardio-only','799999999999993',
      'Paciente só Cardiologia','masculino','1980-01-01') AS id`,[importacaoCardio],
  ))).rows[0].id;
  pacienteSemVinculo=(await db.query("INSERT INTO public.pacientes(nome,sexo) VALUES('Paciente sem vínculo','indeterminado') RETURNING id")).rows[0].id;
});

test('listar_eventos, condição e evento ocultam paciente sem vínculo e UUID ausente',async()=>{
  const noLink=await como(profissional,()=>db.query('SELECT * FROM public.listar_eventos($1)',[pacienteSemVinculo]));
  const missing=await como(profissional,()=>db.query('SELECT * FROM public.listar_eventos($1)',[ausente]));
  assert.deepEqual(noLink.rows,missing.rows);
  assert.deepEqual(noLink.rows,[]);
  assert.ok((await db.query("SELECT 1 FROM public.auditoria WHERE autor_id=$1 AND unidade_id=$2 AND acao='acesso_negado'",[profissional,unidadeCardio])).rows.length>=2);
  const condDenied=await como(admin,()=>db.query(
    `SELECT public.importar_condicao_fhir($1,$2,'Condition/no-link','I10',NULL,'ativo',CURRENT_DATE) AS id`,
    [importacao,pacienteSemVinculo],
  ));
  assert.equal(condDenied.rows[0].id,null);
  await como(admin,()=>db.query(
    `SELECT public.importar_evento_fhir($1,$2,'Observation/no-link','Observation',CURRENT_TIMESTAMP,NULL,NULL,NULL)`,
    [importacao,pacienteSemVinculo],
  ));
  assert.ok((await db.query("SELECT 1 FROM public.auditoria WHERE autor_id=$1 AND unidade_id=$2 AND acao='acesso_negado'",[admin,unidadeUbs])).rows.length>=2);
});

test('sem sessão não há retorno de dados nem auditoria nas seis RPCs',async()=>{
  const countBefore=(await db.query("SELECT count(*)::int AS n FROM public.auditoria WHERE acao='acesso_negado'")).rows[0].n;
  await db.exec('SET ROLE authenticated');
  await db.query("SELECT set_config('request.jwt.claim.sub','',false)");
  const iniciar=await db.query("SELECT public.iniciar_importacao('sem-sessao.json',1) AS id");
  const paciente=await db.query(`SELECT public.importar_paciente_fhir($1,'Patient/no-session',NULL,'Teste','feminino',CURRENT_DATE) AS id`,[importacao]);
  const condicao=await db.query(`SELECT public.importar_condicao_fhir($1,$2,'Condition/no-session','I10',NULL,'ativo',CURRENT_DATE) AS id`,[importacao,pacienteNovo]);
  const evento=await db.query(`SELECT public.importar_evento_fhir($1,$2,'Observation/no-session','Observation',CURRENT_TIMESTAMP,NULL,NULL,NULL) AS id`,[importacao,pacienteNovo]);
  const concluir=await db.query('SELECT public.concluir_importacao($1,$2::jsonb) AS id',[importacao,'[]']);
  const listar=await db.query('SELECT * FROM public.listar_eventos($1)',[pacienteNovo]);
  await db.exec('RESET ROLE');
  await db.query("SELECT set_config('request.jwt.claim.sub','',false)");
  assert.equal(iniciar.rows[0].id,null);
  assert.equal(paciente.rows[0].id,null);
  assert.equal(condicao.rows[0].id,null);
  assert.ok(evento.rows[0].id===null || evento.rows[0].id==='');
  assert.ok(concluir.rows[0].id===null || concluir.rows[0].id==='');
  assert.deepEqual(listar.rows,[]);
  assert.equal((await db.query("SELECT count(*)::int AS n FROM public.auditoria WHERE acao='acesso_negado'")).rows[0].n,countBefore);
});

test('profissional e anon não importam; erros persistidos contêm só id e motivo',async()=>{
  const before=(await db.query("SELECT count(*)::int AS n FROM public.pacientes WHERE cns='799999999999992'")).rows[0].n;
  const denied=await como(profissional,()=>db.query(
    `SELECT public.importar_paciente_fhir($1,'Patient/negado','799999999999992',
      'Não importar','feminino',CURRENT_DATE) AS id`,[importacao],
  ));
  assert.equal(denied.rows[0].id,null);
  const startDenied=await como(profissional,()=>db.query("SELECT public.iniciar_importacao('nao-importar.json',1) AS id"));
  assert.equal(startDenied.rows[0].id,null);
  const conditionDenied=await como(profissional,()=>db.query(
    `SELECT public.importar_condicao_fhir($1,$2,'Condition/deny','I10',NULL,'ativo',CURRENT_DATE) AS id`,
    [importacao,pacienteNovo],
  ));
  assert.equal(conditionDenied.rows[0].id,null);
  await como(profissional,()=>db.query(
    `SELECT public.importar_evento_fhir($1,$2,'Observation/deny','Observation',CURRENT_TIMESTAMP,NULL,NULL,NULL)`,
    [importacao,pacienteNovo],
  ));
  await como(profissional,()=>db.query('SELECT public.concluir_importacao($1,$2::jsonb)',[importacao,'[]']));
  assert.equal((await db.query("SELECT count(*)::int AS n FROM public.pacientes WHERE cns='799999999999992'")).rows[0].n,before);
  await db.exec('SET ROLE anon');
  await assert.rejects(db.query("SELECT public.iniciar_importacao('bundle.json',1)"));
  await assert.rejects(db.query(
    `SELECT public.importar_paciente_fhir($1,'Patient/anon',NULL,'Não importar','feminino',CURRENT_DATE)`,[importacao],
  ));
  await assert.rejects(db.query(`SELECT public.importar_condicao_fhir($1,$2,'Condition/anon','I10',NULL,'ativo',CURRENT_DATE)`,[importacao,pacienteNovo]));
  await assert.rejects(db.query(`SELECT public.importar_evento_fhir($1,$2,'Observation/anon','Observation',CURRENT_TIMESTAMP,NULL,NULL,NULL)`,[importacao,pacienteNovo]));
  await assert.rejects(db.query('SELECT * FROM public.listar_eventos($1)',[pacienteNovo]));
  await assert.rejects(db.query('SELECT public.concluir_importacao($1,$2::jsonb)',[importacao,'[]']));
  await db.exec('RESET ROLE');
  const crossImportPatient=await como(admin,()=>db.query(
    `SELECT public.importar_paciente_fhir($1,'Patient/other-import',NULL,'Não deve gravar','feminino',CURRENT_DATE) AS id`,[importacaoCardio],
  ));
  assert.equal(crossImportPatient.rows[0].id,null);
  const crossImportCondition=await como(adminCardio,()=>db.query(
    `SELECT public.importar_condicao_fhir($1,$2,'Condition/other-import','I10',NULL,'ativo',CURRENT_DATE) AS id`,[importacao,pacienteNovo],
  ));
  assert.equal(crossImportCondition.rows[0].id,null);
  await como(adminCardio,()=>db.query(
    `SELECT public.importar_evento_fhir($1,$2,'Observation/other-import','Observation',CURRENT_TIMESTAMP,NULL,NULL,NULL)`,[importacao,pacienteNovo],
  ));
  await como(adminCardio,()=>db.query('SELECT public.concluir_importacao($1,$2::jsonb)',[importacao,'[]']));
  const erros=[{id:'Condition/invalida-1',motivo:'CID-10 inexistente',nome:'Nome que não deve persistir',cns:'99999999999'}];
  await como(admin,()=>db.query('SELECT public.concluir_importacao($1,$2::jsonb)',[importacao,JSON.stringify(erros)]));
  const row=(await db.query('SELECT erros,erros_count,importados,concluido_em FROM public.importacoes_fhir WHERE id=$1',[importacao])).rows[0];
  assert.deepEqual(row.erros,[{id:'Condition/invalida-1',motivo:'CID-10 inexistente'}]);
  assert.equal(JSON.stringify(row.erros).includes('Nome que não deve persistir'),false);
  assert.equal(row.erros_count,1);
  assert.equal(row.importados,7);
  assert.ok(row.concluido_em);
  const pacienteDepoisDoFechamento=await como(admin,()=>db.query(
    `SELECT public.importar_paciente_fhir($1,'Patient/closed',NULL,'Não deve gravar','feminino',CURRENT_DATE) AS id`,[importacao],
  ));
  assert.equal(pacienteDepoisDoFechamento.rows[0].id,null);
  const condicaoDepoisDoFechamento=await como(admin,()=>db.query(
    `SELECT public.importar_condicao_fhir($1,$2,'Condition/closed','I10',NULL,'ativo',CURRENT_DATE) AS id`,[importacao,pacienteNovo],
  ));
  assert.equal(condicaoDepoisDoFechamento.rows[0].id,null);
  await como(admin,()=>db.query(
    `SELECT public.importar_evento_fhir($1,$2,'Observation/closed','Observation',CURRENT_TIMESTAMP,NULL,NULL,NULL)`,[importacao,pacienteNovo],
  ));
  await como(admin,()=>db.query('SELECT public.concluir_importacao($1,$2::jsonb)',[importacao,'[]']));
  await como(adminCardio,()=>db.query('SELECT public.concluir_importacao($1,$2::jsonb)',[importacaoCardio,'[]']));
  await como(profissional,async()=>{
    for(const table of ['importacoes_fhir','eventos_clinicos','paciente_fhir','bodysite_estrutura']){
      if(table!=='bodysite_estrutura') await assert.rejects(db.query(`SELECT * FROM public.${table}`)); // referência: leitura liberada (0006)
      await assert.rejects(db.query(`INSERT INTO public.${table} DEFAULT VALUES`));
      await assert.rejects(db.query(`UPDATE public.${table} SET id=id`));
      await assert.rejects(db.query(`DELETE FROM public.${table}`));
    }
  });
  assert.equal((await db.query('SELECT count(*)::int AS n FROM public.bodysite_estrutura WHERE verificado')).rows[0].n,12);
  assert.equal((await db.query("SELECT count(*)::int AS n FROM public.bodysite_estrutura WHERE snomed='52612000' AND fonte_url LIKE '%52612000'")).rows[0].n,1);
  assert.deepEqual((await db.query("SELECT estrutura_fma,estrutura_uberon FROM public.bodysite_estrutura WHERE snomed='6757004'")).rows[0],{estrutura_fma:'FMA24486',estrutura_uberon:null});
  assert.deepEqual((await db.query("SELECT estrutura_fma,estrutura_uberon FROM public.bodysite_estrutura WHERE snomed='35039007'")).rows[0],{estrutura_fma:null,estrutura_uberon:'UBERON:0009853'});
  const lateralidade=(await db.query(`SELECT count(*)::int AS total,
    count(*) FILTER (WHERE (descricao ILIKE '%right%' AND lado='direito')
      OR (descricao ILIKE '%left%' AND lado='esquerdo')
      OR (descricao NOT ILIKE '%right%' AND descricao NOT ILIKE '%left%' AND lado IS NULL))::int AS corretas
    FROM public.bodysite_estrutura`)).rows[0];
  assert.deepEqual(lateralidade,{total:12,corretas:12});
  assert.ok((await db.query("SELECT 1 FROM public.auditoria WHERE autor_id=$1 AND unidade_id=$2 AND acao='acesso_negado'",[profissional,unidadeCardio])).rows.length>0);
});

test('bodysite_estrutura é legível e não gravável por authenticated',async()=>{
  const n=(await como(profissional,()=>db.query('SELECT count(*)::int AS n FROM public.bodysite_estrutura'))).rows[0].n;
  assert.equal(n,12);
  await assert.rejects(como(admin,()=>db.query(
    "INSERT INTO public.bodysite_estrutura(snomed,descricao,estrutura_fma) VALUES ('1','x','FMA1')")));
});
