import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import test, { before, after } from 'node:test';
import { PGlite } from '@electric-sql/pglite';

const pasta = dirname(fileURLToPath(import.meta.url));
const db = new PGlite();
const adminUbs = '20000000-0000-4000-8000-000000000001';
const cardiologia = '20000000-0000-4000-8000-000000000002';
const ortopedia = '20000000-0000-4000-8000-000000000003';
const obstetricia = '20000000-0000-4000-8000-000000000004';
const adminCardio = '20000000-0000-4000-8000-000000000005';
const adminMaternidade = '20000000-0000-4000-8000-000000000006';
const adminUbs2 = '20000000-0000-4000-8000-000000000007';
let joao;
let maria;
const ubs = '10000000-0000-4000-8000-000000000001';
const cardio = '10000000-0000-4000-8000-000000000002';

async function como(usuario, fn) {
  await db.exec('SET ROLE authenticated');
  await db.query("SELECT set_config('request.jwt.claim.sub', $1, false)", [usuario]);
  try { return await fn(); }
  finally {
    await db.exec('RESET ROLE');
    await db.query("SELECT set_config('request.jwt.claim.sub', '', false)");
  }
}

async function comoPapel(papel, sub, fn) {
  await db.exec(`SET ROLE ${papel}`);
  await db.query("SELECT set_config('request.jwt.claim.sub', $1, false)", [sub]);
  try { return await fn(); }
  finally {
    await db.exec('RESET ROLE');
    await db.query("SELECT set_config('request.jwt.claim.sub', '', false)");
  }
}

async function auditorias(autor, paciente) {
  return db.query(
    'SELECT acao, unidade_id FROM public.auditoria WHERE autor_id = $1 AND paciente_id = $2 ORDER BY criado_em',
    [autor, paciente],
  );
}

before(async () => {
  await db.exec(await readFile(resolve(pasta, 'shim_auth.sql'), 'utf8'));
  await db.exec(await readFile(resolve(pasta, '../migrations/0001_fundacao.sql'), 'utf8'));
  await db.exec(await readFile(resolve(pasta, '../seed.sql'), 'utf8'));
  await db.exec(await readFile(resolve(pasta, '../migrations/0002_cid10.sql'), 'utf8'));
  maria = (await db.query("SELECT id FROM public.pacientes WHERE cns='700000000000001'")).rows[0].id;
  joao = (await db.query("SELECT id FROM public.pacientes WHERE cns='700000000000002'")).rows[0].id;
});
after(async () => db.close());

test('profissional da Cardiologia não vê João sem vínculo', async () => {
  await como(cardiologia, async () => {
    const result = await db.query('SELECT id FROM public.buscar_pacientes() WHERE id = $1', [joao]);
    assert.equal(result.rows.length, 0);
  });
});

test('abrir prontuário sem vínculo devolve null e grava acesso_negado', async () => {
  await como(cardiologia, async () => {
    const result = await db.query('SELECT public.abrir_prontuario($1) AS paciente', [joao]);
    assert.equal(result.rows[0].paciente, null);
  });
  assert.equal((await auditorias(cardiologia, joao)).rows.at(-1).acao, 'acesso_negado');
});

test('abrir prontuário vinculado grava auditoria com unidade_id', async () => {
  await como(cardiologia, async () => {
    const result = await db.query('SELECT (public.abrir_prontuario($1)).id AS id', [maria]);
    assert.equal(result.rows[0].id, maria);
  });
  const rows = (await auditorias(cardiologia, maria)).rows;
  assert.equal(rows.at(-1).acao, 'abrir_prontuario');
  assert.equal(rows.at(-1).unidade_id, cardio);
});

test('profissional não lê nem insere auditoria; admin lê somente a própria unidade', async () => {
  await como(cardiologia, async () => {
    await db.query('SELECT public.abrir_prontuario($1)', [maria]);
    assert.equal((await db.query('SELECT * FROM public.auditoria')).rows.length, 0);
    await assert.rejects(db.query(
      "INSERT INTO public.auditoria (autor_id, unidade_id, paciente_id, acao) VALUES ($1,$2,$3,'manual')",
      [cardiologia, cardio, maria],
    ));
  });
  await como(adminUbs, async () => {
    const rows = (await db.query('SELECT unidade_id FROM public.auditoria')).rows;
    assert.ok(rows.length);
    assert.ok(rows.every((row) => row.unidade_id === ubs));
  });
});

test('auditoria é append-only', async () => {
  await como(adminUbs, async () => {
    await assert.rejects(db.query("UPDATE public.auditoria SET acao = 'alterada'"));
    await assert.rejects(db.query('DELETE FROM public.auditoria'));
  });
});

test('profissional não cria vínculo nem altera o próprio papel', async () => {
  await como(cardiologia, async () => {
    const erro = (promise) => assert.rejects(promise, (e) => e.code === '42501');
    await erro(db.query("SELECT public.vincular_paciente($1, 'tentativa', 'atendimento')", [joao]));
    await erro(db.query("SELECT public.cadastrar_paciente('Inválido', NULL, 'indeterminado', NULL, 'tentativa', 'atendimento')"));
    await erro(db.query("SELECT public.encerrar_vinculo(gen_random_uuid())"));
    const update = await db.query("UPDATE public.perfis SET papel = 'admin' WHERE id = $1 RETURNING id", [cardiologia]);
    assert.equal(update.rows.length, 0);
    await assert.rejects(db.query('SELECT * FROM public.vinculos'));
  });
  const persistido = await db.query('SELECT papel, unidade_id FROM public.perfis WHERE id=$1', [cardiologia]);
  assert.equal(persistido.rows[0].papel, 'profissional');
  assert.equal(persistido.rows[0].unidade_id, cardio);
});

test('admin não altera o próprio perfil nem move perfis para outra unidade', async () => {
  await como(adminCardio, async () => {
    const self = await db.query("UPDATE public.perfis SET papel='profissional' WHERE id=$1 RETURNING id", [adminCardio]);
    assert.equal(self.rows.length, 0);
    await assert.rejects(db.query(
      'UPDATE public.perfis SET unidade_id=$1 WHERE id=$2 RETURNING id', [ubs, cardiologia],
    ));
  });
  const perfil = await db.query('SELECT papel, unidade_id FROM public.perfis WHERE id=$1', [adminCardio]);
  assert.equal(perfil.rows[0].papel, 'admin');
  assert.equal(perfil.rows[0].unidade_id, cardio);
});

test('sessões sem usuário não acessam funções nem tabelas', async () => {
  await comoPapel('authenticated', '', async () => {
    assert.equal((await db.query('SELECT public.minha_unidade() AS unidade')).rows[0].unidade, null);
    assert.equal((await db.query('SELECT public.eh_admin() AS admin')).rows[0].admin, false);
    assert.equal((await db.query('SELECT * FROM public.buscar_pacientes()')).rows.length, 0);
    assert.equal((await db.query('SELECT public.abrir_prontuario($1) AS paciente', [maria])).rows[0].paciente, null);
    for (const tabela of ['unidades', 'perfis', 'auditoria']) {
      assert.equal((await db.query(`SELECT * FROM public.${tabela}`)).rows.length, 0);
    }
    await assert.rejects(db.query('SELECT * FROM public.pacientes'));
    await assert.rejects(db.query('SELECT * FROM public.vinculos'));
    await assert.rejects(db.query("SELECT public.cadastrar_paciente('Sem perfil',NULL,'indeterminado',NULL,'x','atendimento')"), (e) => e.code === '42501');
    await assert.rejects(db.query("SELECT public.vincular_paciente($1,'x','atendimento')", [maria]), (e) => e.code === '42501');
    await assert.rejects(db.query('SELECT public.encerrar_vinculo(gen_random_uuid())'), (e) => e.code === '42501');
  });
  await comoPapel('anon', '', async () => {
    for (const funcao of [
      'public.minha_unidade()', 'public.eh_admin()', 'public.buscar_pacientes()',
      `public.abrir_prontuario('${maria}')`,
    ]) await assert.rejects(db.query(`SELECT ${funcao}`));
    for (const tabela of ['unidades', 'perfis', 'pacientes', 'vinculos', 'auditoria', 'cid10']) {
      await assert.rejects(db.query(`SELECT * FROM public.${tabela}`));
    }
  });
});

test('fluxo completo de cadastro, vínculo, encerramento e reabertura usa só funções', async () => {
  await como(adminUbs, async () => {
    const criado = await db.query(
      `SELECT public.cadastrar_paciente('Paciente Fluxo', '  788877766655544  ', 'indeterminado', NULL,
        'Primeiro motivo', 'atendimento') AS id`,
    );
    const id = criado.rows[0].id;
    assert.equal((await db.query('SELECT * FROM public.buscar_pacientes($1)', ['Paciente Fluxo'])).rows.length, 1);
    const vinculo = await db.query(
      "SELECT public.vincular_paciente($1, 'Motivo atualizado', 'encaminhamento') AS id", [id],
    );
    await db.query('SELECT public.encerrar_vinculo($1)', [vinculo.rows[0].id]);
    assert.equal((await db.query('SELECT * FROM public.buscar_pacientes($1)', ['Paciente Fluxo'])).rows.length, 0);
    assert.equal((await db.query('SELECT public.abrir_prontuario($1) AS paciente', [id])).rows[0].paciente, null);
    const reaberto = await db.query(
      `SELECT public.cadastrar_paciente('Nome ignorado', '788877766655544', 'indeterminado', NULL,
        'Reaberto', 'atendimento') AS id`,
    );
    assert.equal(reaberto.rows[0].id, id);
    assert.equal((await db.query('SELECT * FROM public.buscar_pacientes($1)', ['Paciente Fluxo'])).rows.length, 1);
  });
});

test('reabertura no mesmo dia atualiza criado_por e preserva autoria na auditoria', async () => {
  const id = await como(adminUbs, async () => {
    const r = await db.query(
      `SELECT public.cadastrar_paciente('Troca de responsável', '766655544433322', 'indeterminado', NULL,
        'Criado pelo admin 1', 'atendimento') AS id`,
    );
    return r.rows[0].id;
  });
  const vínculo = (await db.query(
    'SELECT id FROM public.vinculos WHERE paciente_id=$1 AND unidade_id=$2', [id, ubs],
  )).rows[0].id;
  await como(adminUbs, () => db.query('SELECT public.encerrar_vinculo($1)', [vínculo]));
  await como(adminUbs2, () => db.query(
    "SELECT public.vincular_paciente($1, 'Reaberto pelo admin 2', 'encaminhamento')", [id],
  ));
  const registro = await db.query('SELECT motivo, origem, criado_por, ate FROM public.vinculos WHERE id=$1', [vínculo]);
  assert.equal(registro.rows[0].motivo, 'Reaberto pelo admin 2');
  assert.equal(registro.rows[0].origem, 'encaminhamento');
  assert.equal(registro.rows[0].criado_por, adminUbs2);
  assert.equal(registro.rows[0].ate, null);
  const historico = await db.query(
    'SELECT autor_id, acao FROM public.auditoria WHERE paciente_id=$1 AND unidade_id=$2 ORDER BY criado_em', [id, ubs],
  );
  assert.ok(historico.rows.some((r) => r.autor_id === adminUbs && r.acao === 'cadastrar_paciente'));
  assert.ok(historico.rows.some((r) => r.autor_id === adminUbs && r.acao === 'encerrar_vinculo'));
  assert.ok(historico.rows.some((r) => r.autor_id === adminUbs2 && r.acao === 'criar_vinculo'));
});

test('vínculo encerrado no passado remove paciente da leitura', async () => {
  const vinculo = (await db.query(
    'SELECT id FROM public.vinculos WHERE paciente_id = $1 AND unidade_id = $2', [maria, cardio],
  )).rows[0].id;
  await como(adminCardio, () => db.query('SELECT public.encerrar_vinculo($1)', [vinculo]));
  await como(cardiologia, async () => {
    assert.equal((await db.query('SELECT * FROM public.buscar_pacientes() WHERE id = $1', [maria])).rows.length, 0);
    const opened = await db.query('SELECT public.abrir_prontuario($1) AS paciente', [maria]);
    assert.equal(opened.rows[0].paciente, null);
  });
  assert.equal((await auditorias(cardiologia, maria)).rows.at(-1).acao, 'acesso_negado');
});

test('admin não lê nem altera paciente sem vínculo na sua unidade', async () => {
  await como(adminCardio, async () => {
    assert.equal((await db.query('SELECT * FROM public.buscar_pacientes() WHERE id = $1', [joao])).rows.length, 0);
    await assert.rejects(db.query("UPDATE public.pacientes SET nome = 'alterado' WHERE id = $1", [joao]));
  });
});

test('DML direto em pacientes é negado até para admin', async () => {
  await como(adminUbs, async () => {
    await assert.rejects(db.query('SELECT * FROM public.pacientes'));
    await assert.rejects(db.query("INSERT INTO public.pacientes (nome) VALUES ('Direto')"));
    await assert.rejects(db.query("UPDATE public.pacientes SET nome = 'alterado'"));
    await assert.rejects(db.query('DELETE FROM public.pacientes'));
  });
});

test('profissional não pode ler pacientes ou vínculos diretamente; unidades sem UPDATE', async () => {
  await como(cardiologia, async () => {
    await assert.rejects(db.query('SELECT * FROM public.pacientes'));
    await assert.rejects(db.query('SELECT * FROM public.vinculos'));
  });
  await como(adminUbs, async () => {
    await assert.rejects(db.query("UPDATE public.unidades SET nome='alterada' WHERE id=$1", [ubs]));
  });
});

test('vínculo com início futuro não concede acesso', async () => {
  await db.exec(`INSERT INTO public.pacientes (id, nome, cns, sexo)
    VALUES ('30000000-0000-4000-8000-000000000099', 'Futuro', '799999999999999', 'indeterminado')`);
  await db.exec(`INSERT INTO public.vinculos (paciente_id, unidade_id, motivo, origem, criado_por, desde)
    VALUES ('30000000-0000-4000-8000-000000000099', '${cardio}', 'Agendado', 'atendimento', '${adminCardio}', CURRENT_DATE + 1)`);
  await como(cardiologia, async () => {
    assert.equal((await db.query('SELECT * FROM public.buscar_pacientes() WHERE id = $1', ['30000000-0000-4000-8000-000000000099'])).rows.length, 0);
    assert.equal((await db.query('SELECT public.abrir_prontuario($1) AS paciente', ['30000000-0000-4000-8000-000000000099'])).rows[0].paciente, null);
  });
  assert.equal((await auditorias(cardiologia, '30000000-0000-4000-8000-000000000099')).rows.at(-1).acao, 'acesso_negado');
});

test('admin não encerra vínculo de outra unidade e ninguém apaga vínculo', async () => {
  const vinculoUbs = (await db.query('SELECT id FROM public.vinculos WHERE paciente_id=$1 AND unidade_id=$2', [joao, ubs])).rows[0].id;
  await como(adminCardio, async () => {
    await assert.rejects(db.query('SELECT public.encerrar_vinculo($1)', [vinculoUbs]));
    await assert.rejects(db.query('SELECT * FROM public.vinculos'));
    await assert.rejects(db.query('DELETE FROM public.vinculos WHERE id = $1', [vinculoUbs]));
  });
});

test('cadastrar com CNS existente não duplica e cria vínculo auditado', async () => {
  const antes = await db.query('SELECT count(*)::int AS n FROM public.pacientes WHERE cns = $1', ['700000000000001']);
  await como(adminCardio, async () => {
    const result = await db.query(
      `SELECT public.cadastrar_paciente('Nome ignorado', $1, 'feminino', NULL, 'Novo vínculo', 'encaminhamento') AS id`,
      ['700000000000001'],
    );
    assert.equal(result.rows[0].id, maria);
  });
  const depois = await db.query('SELECT count(*)::int AS n FROM public.pacientes WHERE cns = $1', ['700000000000001']);
  assert.equal(depois.rows[0].n, antes.rows[0].n);
  assert.ok((await db.query('SELECT id FROM public.vinculos WHERE paciente_id=$1 AND unidade_id=$2', [maria, cardio])).rows.length);
  assert.ok((await auditorias(adminCardio, maria)).rows.some((r) => r.acao === 'criar_vinculo' && r.unidade_id === cardio));
});

test('cada função de escrita registra unidade do autor na auditoria', async () => {
  await como(adminUbs, () => db.query(
    `SELECT public.cadastrar_paciente('Nova', '788888888888888', 'indeterminado', NULL,
      'Cadastro', 'atendimento')`,
  ));
  const novo = await db.query('SELECT id FROM public.pacientes WHERE cns=$1', ['788888888888888']);
  assert.equal((await auditorias(adminUbs, novo.rows[0].id)).rows[0].unidade_id, ubs);
  const vinculo = await como(adminUbs, async () => {
    const r = await db.query("SELECT public.vincular_paciente($1, 'Encaminhado', 'encaminhamento') AS id", [maria]);
    return r.rows[0].id;
  });
  assert.ok((await auditorias(adminUbs, maria)).rows.some((r) => r.acao === 'criar_vinculo' && r.unidade_id === ubs));
  await como(adminUbs, () => db.query('SELECT public.encerrar_vinculo($1)', [vinculo]));
  assert.ok((await auditorias(adminUbs, maria)).rows.some((r) => r.acao === 'encerrar_vinculo' && r.unidade_id === ubs));
});

test('buscar_pacientes filtra apenas vínculos ativos e retorna últimos 4 dígitos', async () => {
  await como(obstetricia, async () => {
    const result = await db.query("SELECT * FROM public.buscar_pacientes('Maria')");
    assert.equal(result.rows.length, 1);
    assert.equal(result.rows[0].id, maria);
    assert.equal(result.rows[0].cns_final, '0001');
    assert.equal((await db.query("SELECT * FROM public.buscar_pacientes('700000000000999')")).rows.length, 0);
  });
});

test('CID-10 é legível e não gravável por authenticated', async () => {
  await como(cardiologia, async () => {
    const result = await db.query("SELECT descricao FROM public.cid10 WHERE codigo = 'A00'");
    assert.equal(result.rows.length, 1);
    await assert.rejects(db.query("INSERT INTO public.cid10 VALUES ('Z99.9', 'Teste')"));
    await assert.rejects(db.query("UPDATE public.cid10 SET descricao = 'Teste' WHERE codigo = 'A00'"));
  });
});
