import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import test, { before, after } from 'node:test';
import { PGlite } from '@electric-sql/pglite';
import { criarSessaoAtiva, definirClaims, limparClaims } from './sessao_helper.mjs';

const pasta = dirname(fileURLToPath(import.meta.url));
const db = new PGlite();
const cardio = '20000000-0000-4000-8000-000000000002';
const obstetricia = '20000000-0000-4000-8000-000000000004';
const maria = '30000000-0000-4000-8000-000000000001';
const joao = '30000000-0000-4000-8000-000000000002';
const ausente = '90000000-0000-4000-8000-000000000099';

async function como(usuario, fn) {
  const sessao = await criarSessaoAtiva(db, usuario);
  await db.exec('SET ROLE authenticated');
  await definirClaims(db, usuario, sessao);
  try { return await fn(); }
  finally {
    await db.exec('RESET ROLE');
    await limparClaims(db);
  }
}

async function comoPapel(papel, sub, fn) {
  await db.exec(`SET ROLE ${papel}`);
  await definirClaims(db, sub || null);
  try { return await fn(); }
  finally {
    await db.exec('RESET ROLE');
    await limparClaims(db);
  }
}

async function registrar(usuario, paciente, cid, substitui = null, ancora = null, lado = 'nao_se_aplica') {
  return como(usuario, () => db.query(
    `SELECT public.registrar_achado($1,$2::jsonb,$3,'doenca',$4,'ativo',CURRENT_DATE,
      'registro de teste',$5) AS id`,
    [paciente, ancora === null ? null : JSON.stringify(ancora), cid, lado, substitui],
  ));
}

before(async () => {
  await db.exec(await readFile(resolve(pasta, 'shim_auth.sql'), 'utf8'));
  await db.exec(await readFile(resolve(pasta, '../migrations/0001_fundacao.sql'), 'utf8'));
  await db.exec(await readFile(resolve(pasta, '../seed.sql'), 'utf8'));
  await db.exec(await readFile(resolve(pasta, '../migrations/0002_cid10.sql'), 'utf8'));
  for (const file of ['0003_achados.sql','0004_gestacao.sql','0005_fhir.sql','0006_bodysite_leitura.sql','0007_endurecimento.sql','0008_endurecimento_piloto.sql','0009_sessao_inatividade.sql','0010_vista_achado.sql','0011_vista_up_consistencia.sql','0012_vista_up_unitario.sql'])
    await db.exec(await readFile(resolve(pasta, '../migrations', file), 'utf8'));
});
after(async () => db.close());

test('cardiologia registra I10 normal e F32 restrito; obstetrícia não recebe pista do restrito', async () => {
  const i10 = (await registrar(cardio, maria, 'I10')).rows[0].id;
  const f32 = (await registrar(cardio, maria, 'F32')).rows[0].id;
  const obst = await como(obstetricia, () => db.query('SELECT * FROM public.listar_achados($1)', [maria]));
  assert.deepEqual(obst.rows.map((r) => r.id), [i10]);
  assert.equal(JSON.stringify(obst.rows).includes(f32), false);
  assert.equal(JSON.stringify(obst.rows).includes('F32'), false);
  const cardioRows = await como(cardio, () => db.query('SELECT * FROM public.listar_achados($1)', [maria]));
  assert.equal(cardioRows.rows.length, 2);
  assert.equal(cardioRows.rows.find((r) => r.id === f32).nivel_sigilo, 'restrito');
  assert.deepEqual(Object.keys(cardioRows.rows[0]), [
    'id','ancora','estrutura','cid10','cid10_descricao','categoria','lado','status','nivel_sigilo',
    'inicio','observacao','especialidade','autor_nome','unidade_nome','unidade_id','substitui_id','criado_em','vista',
  ]);
  assert.equal(cardioRows.rows.find((r) => r.id === i10).cid10_descricao.length > 0, true);
  assert.equal(cardioRows.rows.find((r) => r.id === i10).autor_nome, 'Profissional Cardiologia');
  assert.equal(cardioRows.rows.find((r) => r.id === i10).unidade_nome, 'Ambulatório de Cardiologia');
  const hiddenHistory = await como(obstetricia, () => db.query('SELECT * FROM public.historico_achado($1)', [f32]));
  assert.equal(hiddenHistory.rows.length, 0);
});

test('correção mantém cadeia e lista apenas o vigente', async () => {
  const primeiro = (await registrar(cardio, maria, 'I10')).rows[0].id;
  const segundo = (await registrar(cardio, maria, 'I10', primeiro)).rows[0].id;
  const terceiro = (await registrar(cardio, maria, 'I10', segundo)).rows[0].id;
  const lista = await como(cardio, () => db.query('SELECT * FROM public.listar_achados($1)', [maria]));
  const idsLista = lista.rows.map((r) => r.id);
  assert.ok(idsLista.includes(terceiro));
  assert.equal(idsLista.includes(primeiro), false);
  assert.equal(idsLista.includes(segundo), false);
  const historico = await como(cardio, () => db.query('SELECT * FROM public.historico_achado($1)', [terceiro]));
  assert.deepEqual(historico.rows.map((r) => r.id), [primeiro, segundo, terceiro]);
  assert.deepEqual(Object.keys(historico.rows[0]), [
    'id','ancora','estrutura','cid10','cid10_descricao','categoria','lado','status','nivel_sigilo',
    'inicio','observacao','especialidade','autor_nome','unidade_nome','unidade_id','substitui_id','criado_em','vista',
  ]);
});

test('achados não permite DML direto nem forja autor ou unidade pela RPC', async () => {
  await como(cardio, async () => {
    await assert.rejects(db.query('SELECT * FROM public.achados'));
    await assert.rejects(db.query(`INSERT INTO public.achados(paciente_id,autor_id,unidade_id,cid10,categoria,lado,status)
      VALUES($1,$2,'10000000-0000-4000-8000-000000000001','I10','doenca','nao_se_aplica','ativo')`, [maria, obstetricia]));
    await assert.rejects(db.query("UPDATE public.achados SET observacao='forjado'"));
    await assert.rejects(db.query('DELETE FROM public.achados'));
  });
  await registrar(cardio, maria, 'I10');
  const row = (await db.query('SELECT autor_id,unidade_id,especialidade FROM public.achados ORDER BY criado_em DESC LIMIT 1')).rows[0];
  assert.equal(row.autor_id, cardio);
  assert.equal(row.unidade_id, '10000000-0000-4000-8000-000000000002');
  assert.equal(row.especialidade, 'cardiologia');
});

test('sem vínculo João não registra e não há vazamento de achado', async () => {
  const resultado = await registrar(cardio, joao, 'I10');
  assert.equal(resultado.rows[0].id, null);
  assert.equal((await registrar(cardio, ausente, 'I10')).rows[0].id, null);
  assert.equal((await db.query('SELECT * FROM public.achados WHERE paciente_id=$1', [joao])).rows.length, 0);
  assert.equal((await db.query(`SELECT * FROM public.auditoria WHERE paciente_id IS NULL AND unidade_id='10000000-0000-4000-8000-000000000002' AND acao='acesso_negado'`)).rows.length, 2);
  const lista = await como(cardio, () => db.query('SELECT * FROM public.listar_achados($1)', [joao]));
  assert.equal(lista.rows.length, 0);
  assert.equal((await db.query(`SELECT acao FROM public.auditoria WHERE paciente_id IS NULL
    AND unidade_id='10000000-0000-4000-8000-000000000002' AND acao='acesso_negado'`)).rows.length, 3);
});

test('abrir_prontuario com UUID inexistente devolve null e audita com paciente_id null', async () => {
  const antes = (await db.query(`SELECT count(*)::int AS n FROM public.auditoria
    WHERE paciente_id IS NULL AND acao='acesso_negado'
      AND unidade_id='10000000-0000-4000-8000-000000000002'`)).rows[0].n;
  const resultado = await como(cardio, () => db.query(
    'SELECT public.abrir_prontuario($1) AS paciente', [ausente],
  ));
  assert.equal(resultado.rows[0].paciente, null);
  const auditorias = await db.query(`SELECT paciente_id,acao,unidade_id FROM public.auditoria
    WHERE paciente_id IS NULL AND acao='acesso_negado'
      AND unidade_id='10000000-0000-4000-8000-000000000002'`);
  assert.equal(auditorias.rows.length, antes + 1);
  assert.equal(auditorias.rows[0].paciente_id, null);
});

test('UUID inexistente e paciente sem vínculo são indistinguíveis em lista e histórico', async () => {
  const listJoao = await como(cardio, () => db.query('SELECT * FROM public.listar_achados($1)', [joao]));
  const listAusente = await como(cardio, () => db.query('SELECT * FROM public.listar_achados($1)', [ausente]));
  assert.deepEqual(listAusente.rows, listJoao.rows);
  const idJoao = (await registrar('20000000-0000-4000-8000-000000000003', joao, 'I10')).rows[0].id;
  const histSemVinculo = await como(cardio, () => db.query('SELECT * FROM public.historico_achado($1)', [idJoao]));
  const histAusente = await como(cardio, () => db.query('SELECT * FROM public.historico_achado($1)', [ausente]));
  assert.deepEqual(histAusente.rows, histSemVinculo.rows);
  assert.deepEqual(histAusente.rows, []);
  const negadasNulas = await db.query(`SELECT paciente_id FROM public.auditoria
    WHERE unidade_id='10000000-0000-4000-8000-000000000002' AND acao='acesso_negado'
      AND paciente_id IS NULL`);
  assert.ok(negadasNulas.rows.length >= 6);
});

test('substituição só pode apontar achado da mesma unidade e paciente; erro é genérico', async () => {
  const restritoOutraUnidade = (await registrar(obstetricia, maria, 'F32')).rows[0].id;
  const normalOutraUnidade = (await registrar(obstetricia, maria, 'I10')).rows[0].id;
  const outroPaciente = (await registrar('20000000-0000-4000-8000-000000000003', joao, 'I10')).rows[0].id;
  const tentativas = [restritoOutraUnidade, normalOutraUnidade, ausente, outroPaciente];
  const erros = [];
  for (const alvo of tentativas) {
    try {
      await registrar(cardio, maria, 'I10', alvo);
      assert.fail('substituição deveria ser recusada');
    } catch (e) { erros.push(e); }
  }
  assert.ok(erros.every((e) => e.code === '42501'));
  assert.deepEqual(new Set(erros.map((e) => e.message)).size, 1);
});

test('CID inexistente e lateralidade incompatível retornam 22023', async () => {
  await assert.rejects(registrar(cardio, maria, 'ZZZ99.9'), (e) => e.code === '22023');
  const ancoraCatalogadaEsquerda = { atlas:'hra-f', atlas_versao:'1.10-1', sistema:'falso', estrutura:'FMA1', malha:'VH_F_fat_L', lateralidade:'right' };
  await assert.rejects(registrar(cardio, maria, 'I10', null, ancoraCatalogadaEsquerda, 'direito'), (e) => e.code === '22023');
  // sem contradição: malha esquerda aceita bilateral/não se aplica; malha sem lado aceita qualquer lado
  assert.ok((await registrar(cardio, maria, 'I10', null, ancoraCatalogadaEsquerda, 'nao_se_aplica')).rows[0].id);
  const semLado = (await como(cardio, () => db.query("SELECT malha FROM public.atlas_malhas WHERE atlas='hra-f' AND lateralidade IS NULL LIMIT 1"))).rows[0].malha;
  assert.ok((await registrar(cardio, maria, 'I10', null, { atlas:'hra-f', atlas_versao:'1.10-1', malha:semLado }, 'direito')).rows[0].id);
});

test('quatro RPCs bloqueiam anon e authenticated sem sub; cid10_sigilo não aceita acesso direto', async () => {
  const chamadas = [
    () => db.query("SELECT * FROM public.buscar_cid10('I10')"),
    () => db.query("SELECT public.registrar_achado($1,NULL,'I10','doenca','nao_se_aplica','ativo',CURRENT_DATE,NULL,NULL)", [maria]),
    () => db.query('SELECT * FROM public.listar_achados($1)', [maria]),
    () => db.query('SELECT * FROM public.historico_achado($1)', [ausente]),
  ];
  await comoPapel('anon', '', async () => {
    for (const chamada of chamadas) await assert.rejects(chamada());
  });
  await comoPapel('authenticated', '', async () => {
    assert.equal((await chamadas[0]()).rows.length, 0);
    await assert.rejects(chamadas[1](), (e) => e.code === '42501');
    assert.equal((await chamadas[2]()).rows.length, 0);
    assert.equal((await chamadas[3]()).rows.length, 0);
    await assert.rejects(db.query('SELECT * FROM public.cid10_sigilo'));
    await assert.rejects(db.query("INSERT INTO public.cid10_sigilo(prefixo,motivo) VALUES('Q','teste')"));
    await assert.rejects(db.query("UPDATE public.cid10_sigilo SET motivo='alterado' WHERE prefixo='F'"));
    await assert.rejects(db.query("DELETE FROM public.cid10_sigilo WHERE prefixo='F'"));
  });
});

test('âncora inexistente e atlas incompatível são recusados; metadados vêm do catálogo', async () => {
  await assert.rejects(registrar(cardio, maria, 'I10', null, { atlas: 'hra-f' }), (e) => e.code === '22023');
  const desconhecida = { atlas:'hra-f', atlas_versao:'1.10-1', sistema:'nervoso', estrutura:null, malha:'malha-inventada' };
  await assert.rejects(registrar(cardio, maria, 'I10', null, desconhecida), (e) => e.code === '22023');
  const masculina = { atlas:'bp3d-m', atlas_versao:'4.0-1', sistema:'digestorio', estrutura:'FMA59763', malha:'FJ1252' };
  await assert.rejects(registrar(cardio, maria, 'I10', null, masculina), (e) => e.code === '22023');
  const ancoraSemEstrutura = { atlas:'hra-f', atlas_versao:'1.10-1', sistema:'falso', estrutura:'falsa',
    malha:'Allen_frontal_agranular_insular_cortex_area_Fl_L', lateralidade:'right', posicao_local:[1,2,3], triangulo:17 };
  const id = (await registrar(cardio, maria, 'I10', null, ancoraSemEstrutura, 'esquerdo')).rows[0].id;
  const row = (await como(cardio, () => db.query('SELECT ancora,estrutura FROM public.listar_achados($1) WHERE id=$2', [maria,id]))).rows[0];
  assert.equal(row.ancora.sistema, 'nervoso');
  assert.equal(row.ancora.lateralidade, 'left');
  assert.equal(row.ancora.malha, ancoraSemEstrutura.malha);
  assert.deepEqual(row.ancora.posicao_local, [1,2,3]);
  assert.equal(row.ancora.triangulo, 17);
  assert.equal(row.ancora.estrutura, null);
  assert.equal(row.estrutura, null);
});

test('lateralidade enviada pelo cliente é substituída pela lateralidade catalogada', async () => {
  const enviada = { atlas:'hra-f', atlas_versao:'1.10-1', malha:'VH_F_fat_L', sistema:'falso',
    estrutura:'FMA:999999', lateralidade:'right', posicao_local:[0.1,0.2,0.3], normal_local:[0,1,0], triangulo:9, baricentricas:[0.2,0.3,0.5] };
  const id = (await registrar(cardio,maria,'I10',null,enviada,'esquerdo')).rows[0].id;
  const row = (await como(cardio,()=>db.query('SELECT ancora FROM public.listar_achados($1) WHERE id=$2',[maria,id]))).rows[0];
  assert.equal(row.ancora.sistema,'tegumentar');
  assert.equal(row.ancora.lateralidade,'left');
  assert.equal(row.ancora.estrutura,'FMA:73166');
  assert.deepEqual(row.ancora.posicao_local,[0.1,0.2,0.3]);
  assert.deepEqual(row.ancora.normal_local,[0,1,0]);
  assert.equal(row.ancora.triangulo,9);
  assert.deepEqual(row.ancora.baricentricas,[0.2,0.3,0.5]);
});

test('buscar CID encontra código e descrição sem acento', async () => {
  await como(cardio, async () => {
    assert.ok((await db.query('SELECT * FROM public.buscar_cid10($1)', ['I10'])).rows.some((r) => r.codigo === 'I10'));
    assert.ok((await db.query('SELECT * FROM public.buscar_cid10($1)', ['hipertens'])).rows.length > 0);
  });
});
