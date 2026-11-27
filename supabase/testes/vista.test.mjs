import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import test, { before, after } from 'node:test';
import { PGlite } from '@electric-sql/pglite';
import { criarSessaoAtiva, definirClaims, limparClaims } from './sessao_helper.mjs';

const pasta=dirname(fileURLToPath(import.meta.url));
const db=new PGlite();
const admin='20000000-0000-4000-8000-000000000001';
const cardio='20000000-0000-4000-8000-000000000002';
const maria='30000000-0000-4000-8000-000000000001';
const vista={atlas:'hra-f',atlas_versao:'1.10-1',posicao:[0,1.5,-10],alvo:[10,0,0.25],sistemas:['esqueleto','sistema_nervoso']};
const REGISTRAR="SELECT public.registrar_achado($1,$2::jsonb,'I10','doenca','nao_se_aplica','ativo',CURRENT_DATE,'vista',NULL";
let ancora;

async function como(usuario,fn){
  const sessao=await criarSessaoAtiva(db,usuario);
  await db.exec('SET ROLE authenticated');
  await definirClaims(db,usuario,sessao);
  try{return await fn();}
  finally{await db.exec('RESET ROLE');await limparClaims(db);}
}
const registrar=(v,a=ancora)=>como(cardio,async()=>(await db.query(`${REGISTRAR},$3::jsonb) AS id`,
  [maria,a&&JSON.stringify(a),JSON.stringify(v)])).rows[0].id);
const valida=async(json)=>(await db.query('SELECT public.vista_valida($1::jsonb) AS ok',[json])).rows[0].ok;
const total=async()=>(await db.query('SELECT count(*)::int AS n FROM public.achados')).rows[0].n;

before(async()=>{
  await db.exec(await readFile(resolve(pasta,'shim_auth.sql'),'utf8'));
  await db.exec(await readFile(resolve(pasta,'../migrations/0001_fundacao.sql'),'utf8'));
  await db.exec(await readFile(resolve(pasta,'../seed.sql'),'utf8'));
  for(const file of ['0002_cid10.sql','0003_achados.sql','0004_gestacao.sql','0005_fhir.sql','0006_bodysite_leitura.sql',
    '0007_endurecimento.sql','0008_endurecimento_piloto.sql','0009_sessao_inatividade.sql','0010_vista_achado.sql','0011_vista_up_consistencia.sql'])
    await db.exec(await readFile(resolve(pasta,'../migrations',file),'utf8'));
  ancora=(await db.query(`SELECT atlas,versao AS atlas_versao,malha FROM public.atlas_malhas
    WHERE atlas=$1 AND versao=$2 ORDER BY malha LIMIT 1`,[vista.atlas,vista.atlas_versao])).rows[0];
});
after(async()=>db.close());

test('vista válida é gravada e devolvida por listar_achados e historico_achado',async()=>{
  const id=await registrar(vista);
  await como(cardio,async()=>{
    for(const fn of ['listar_achados($1)','historico_achado($1)']){
      const {rows}=await db.query(`SELECT id,vista FROM public.${fn}`,[fn.startsWith('listar')?maria:id]);
      assert.deepEqual(rows.find((r)=>r.id===id).vista,vista);
    }
  });
  assert.ok(await registrar({...vista,sistemas:[]}));
  assert.ok(await registrar({...vista,sistemas:Array(20).fill('a'.repeat(40))}));
  // limites de texto: nenhum atlas catalogado chega a eles, então direto na validação
  assert.equal(await valida(JSON.stringify({...vista,atlas:'a'.repeat(40),atlas_versao:'v'.repeat(20)})),true);
});

test('up opcional válido é gravado e devolvido',async()=>{
  for(const up of [[0,1,0],[0,0,-1],[-1,0.5,1]]){
    const id=await registrar({...vista,up});
    assert.deepEqual((await db.query('SELECT vista FROM public.achados WHERE id=$1',[id])).rows[0].vista,{...vista,up});
  }
});

test('vista sem âncora ou de atlas/versão diferente da âncora é recusada com 22023 sem gravar',async()=>{
  const antes=await total();
  for(const [v,a] of [[vista,null],[{...vista,atlas:'bp3d-m'},ancora],[{...vista,atlas_versao:'1.10-2'},ancora]])
    await assert.rejects(registrar(v,a),(e)=>e.code==='22023' && /Vista incompatível/.test(e.message));
  assert.equal(await total(),antes);
});

test('vistas inválidas são recusadas sem gravar',async()=>{
  const semAlvo={...vista}; delete semAlvo.alvo;
  const invalidas=[
    'texto',1,true,[],{},null,semAlvo,{...vista,extra:1},{...semAlvo,extra:[0,0,0]},
    ...['atlas','atlas_versao'].flatMap((k)=>[1,null,'',['x']].map((v)=>({...vista,[k]:v}))),
    {...vista,atlas:'a'.repeat(41)},{...vista,atlas_versao:'v'.repeat(21)},
    ...['posicao','alvo'].flatMap((k)=>['0,0,0',null,{},[],[0,0],[0,0,0,0],[0,0,'0'],[0,0,null],[0,0,[0]],
      [0,0,10.001],[-10.001,0,0],[1e300,0,0]].map((v)=>({...vista,[k]:v}))),
    ...['pele',null,{},[1],[null],[['pele']],[''],['Pele'],['pele 2'],['pele-x'],['ação'],['a'.repeat(41)],
      Array(21).fill('pele')].map((v)=>({...vista,sistemas:v})),
    ...['0,1,0',null,{},[],[0,1],[0,1,0,0],[0,'1',0],[0,null,0],[0,[1],0],[0,1.001,0],[-1.001,0,0]]
      .map((up)=>({...vista,up})),
  ].map((v)=>JSON.stringify(v));
  // só o limite de bytes recusa: número válido com milhares de casas
  invalidas.push(JSON.stringify(vista).replace('0.25',`0.${'1'.repeat(2000)}`));
  const antes=await total();
  for(const json of invalidas){
    assert.equal(await valida(json),false,json.slice(0,200));
    // atlas/versão estragados caem antes, na consistência com a âncora; o resto, no CHECK
    const v=JSON.parse(json);
    const codigo=v?.atlas===vista.atlas && v?.atlas_versao===vista.atlas_versao?'23514':'22023';
    await assert.rejects(como(cardio,()=>db.query(`${REGISTRAR},$3::jsonb)`,
      [maria,JSON.stringify(ancora),json])),(e)=>e.code===codigo,json.slice(0,200));
  }
  assert.equal(await total(),antes);
});

test('registrar sem p_vista e importar por FHIR gravam vista nula',async()=>{
  const id=await como(cardio,async()=>(await db.query(`${REGISTRAR}) AS id`,[maria,null])).rows[0].id);
  const importacao=(await como(admin,()=>db.query("SELECT public.iniciar_importacao('vista.json',1,'teste') AS id"))).rows[0].id;
  await como(admin,()=>db.query(
    "SELECT public.importar_paciente_fhir($1,'Patient/vista','700000000000001','Maria','feminino','1994-01-01')",[importacao]));
  const fhir=(await como(admin,()=>db.query(
    "SELECT public.importar_condicao_fhir($1,$2,'Condition/vista','I10',NULL,'ativo',CURRENT_DATE) AS id",[importacao,maria]))).rows[0].id;
  for(const achado of [id,fhir])
    assert.equal((await db.query('SELECT vista FROM public.achados WHERE id=$1',[achado])).rows[0].vista,null);
});

test('anon é recusado e authenticated sem sessão ativa continua sem acesso',async()=>{
  const id=await registrar(vista);
  const antes=await total();
  const chamadas=[[`${REGISTRAR},$3::jsonb) AS id`,[maria,JSON.stringify(ancora),JSON.stringify(vista)]],
    ['SELECT * FROM public.listar_achados($1)',[maria]],['SELECT * FROM public.historico_achado($1)',[id]]];
  await db.exec('SET ROLE anon');
  for(const [sql,args] of chamadas) await assert.rejects(db.query(sql,args),(e)=>e.code==='42501');
  await db.exec('RESET ROLE');
  await db.exec('SET ROLE authenticated');
  await definirClaims(db,cardio);
  await assert.rejects(db.query(...chamadas[0]),(e)=>e.code==='42501');
  for(const chamada of chamadas.slice(1)) assert.deepEqual((await db.query(...chamada)).rows,[]);
  await db.exec('RESET ROLE');
  await limparClaims(db);
  assert.equal(await total(),antes);
});
