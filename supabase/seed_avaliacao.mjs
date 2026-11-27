import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { criarAncorasSeed } from './ancoras_seed.mjs';

const args = process.argv.slice(2);
const rodadaArg = args.find((arg) => arg.startsWith('--rodada='))?.split('=')[1]
  ?? (args.includes('--rodada') ? args[args.indexOf('--rodada') + 1] : null);
const seco = args.includes('--seco');
if (!rodadaArg || !/^\d{2}$/.test(rodadaArg)) {
  console.error('Uso: node supabase/seed_avaliacao.mjs --rodada NN [--seco], com NN entre 00 e 99.');
  process.exit(2);
}
if (args.some((arg) => !['--seco', '--rodada', rodadaArg].includes(arg) && !arg.startsWith('--rodada='))) {
  console.error('Argumento não reconhecido.');
  process.exit(2);
}
const rodada = rodadaArg;

const unidades = {
  ubs: '10000000-0000-4000-8000-000000000001',
  cardio: '10000000-0000-4000-8000-000000000002',
  maternidade: '10000000-0000-4000-8000-000000000003',
  pediatria: '10000000-0000-4000-8000-000000000004',
};

const pacientes = [
  { id: 'P01', nome: 'Ana Lima Fictícia', sexo: 'feminino', idade: 58, atlas: 'hra-f', versao: '1.10-1', unidades: ['ubs', 'cardio'] },
  { id: 'P02', nome: 'José Pereira Fictício', sexo: 'masculino', idade: 65, atlas: 'bp3d-m', versao: '4.0-1', unidades: ['ubs', 'cardio'] },
  { id: 'P03', nome: 'Carla Mendes Fictícia', sexo: 'feminino', idade: 29, atlas: 'hra-f', versao: '1.10-1', unidades: ['ubs', 'maternidade'] },
  { id: 'P04', nome: 'Pedro Alves Fictício', sexo: 'masculino', idade: 41, atlas: 'bp3d-m', versao: '4.0-1', unidades: ['ubs'] },
  { id: 'P05', nome: 'Lúcia Rocha Fictícia', sexo: 'feminino', idade: 47, atlas: 'hra-f', versao: '1.10-1', unidades: ['ubs', 'maternidade'] },
  { id: 'P06', nome: 'Juliana Santos Fictícia', sexo: 'feminino', idade: 32, atlas: 'hra-f', versao: '1.10-1', unidades: ['ubs', 'maternidade'], gestacao: 'encerrada' },
  { id: 'P07', nome: 'Davi Santos Fictício', sexo: 'masculino', idade: null, atlas: null, versao: null, unidades: ['maternidade', 'pediatria'], nascimento: true },
  { id: 'P08', nome: 'Sam Costa Fictício', sexo: 'indeterminado', idade: 36, atlas: 'hra-f', versao: '1.10-1', unidades: ['ubs'] },
];

// Malhas fixadas na revisão de PACIENTES.md. A ausência de qualquer ID no índice aborta.
const achados = [
  ['P01', 'cardiologia', 'I10', 'doenca', 'nao_se_aplica', 'ativo', '2012-03-01', null, 'Hipertensão em uso de losartana'],
  ['P01', 'cardiologia', 'I48', 'doenca', 'nao_se_aplica', 'ativo', '2024-09-15', 'VH_F_left_cardiac_atrium', 'Fibrilação atrial paroxística; anticoagulada'],
  ['P01', 'mfc', 'E11.9', 'doenca', 'nao_se_aplica', 'ativo', '2015-06-01', null, 'Diabetes tipo 2; metformina'],
  ['P01', 'mfc', 'J18.9', 'doenca', 'direito', 'resolvido', '2023-07-10', 'VH_F_right_posterior_basal_bronchopulmonary_segment', 'Pneumonia comunitária tratada'],
  ['P01', 'mfc', 'M17.0', 'doenca', 'bilateral', 'ativo', '2020-02-01', 'VH_F_patella_R', 'Gonartrose bilateral'],
  ['P02', 'cardiologia', 'I25.2', 'doenca', 'nao_se_aplica', 'ativo', '2019-04-20', 'FJ2428', 'IAM antigo de parede anterior; angioplastia'],
  ['P02', 'cardiologia', 'Z95.5', 'dispositivo', 'nao_se_aplica', 'ativo', '2019-04-21', 'FJ2631', 'Stent coronário'],
  ['P02', 'cardiologia', 'I10', 'doenca', 'nao_se_aplica', 'ativo', '2010-01-01', null, 'Hipertensão'],
  ['P02', 'mfc', 'J44.9', 'doenca', 'bilateral', 'ativo', '2018-05-01', 'FJ2539', 'DPOC; ex-tabagista desde 2019'],
  ['P02', 'mfc', 'F17.2', 'doenca', 'nao_se_aplica', 'resolvido', '1980-01-01', null, 'Tabagismo 40 maços-ano'],
  ['P02', 'mfc', 'N40', 'doenca', 'nao_se_aplica', 'ativo', '2022-08-01', 'FJ3139', 'HPB; tansulosina'],
  ['P02', 'ortopedia', 'M54.5', 'sintoma', 'nao_se_aplica', 'ativo', '2025-10-05', 'FJ3165', 'Lombalgia mecânica'],
  ['P03', 'mfc', 'J45.9', 'doenca', 'nao_se_aplica', 'ativo', '2010-03-01', null, 'Asma leve intermitente'],
  ['P03', 'obstetricia', 'O23.4', 'doenca', 'nao_se_aplica', 'resolvido', null, 'VH_F_fundus_of_urinary_bladder_dome', 'ITU na gestação tratada'],
  ['P04', 'ortopedia', 'M75.1', 'doenca', 'direito', 'ativo', null, 'FJ1506', 'Síndrome do manguito rotador'],
  ['P04', 'ortopedia', 'M25.5', 'sintoma', 'esquerdo', 'suspeito', null, 'FJ3275', 'Dor no joelho esquerdo'],
  ['P04', 'ortopedia', 'M23.2', 'doenca', 'esquerdo', 'ativo', null, 'FJ3275', 'Lesão de menisco medial na RM'],
  ['P04', 'mfc', 'K21.9', 'doenca', 'nao_se_aplica', 'ativo', '2024-02-01', 'FJ2563', 'DRGE'],
  ['P05', 'obstetricia', 'N63', 'sintoma', 'esquerdo', 'suspeito', null, 'VH_F_mammary_lobes_L', 'Nódulo palpável QSE; USG solicitada'],
  ['P05', 'obstetricia', 'D25.9', 'doenca', 'nao_se_aplica', 'ativo', '2021-05-01', 'VH_F_body_of_uterus', 'Mioma uterino'],
  ['P05', 'mfc', 'G43.9', 'doenca', 'nao_se_aplica', 'ativo', '2005-01-01', null, 'Enxaqueca'],
  ['P05', 'mfc', 'F41.1', 'doenca', 'nao_se_aplica', 'ativo', '2023-03-01', null, 'Ansiedade generalizada'],
  ['P07', 'pediatria', 'J21.9', 'doenca', 'nao_se_aplica', 'resolvido', null, null, 'Bronquiolite; sem internação'],
  ['P08', 'mfc', 'J45.9', 'doenca', 'nao_se_aplica', 'ativo', '2001-01-01', null, 'Asma'],
  ['P08', 'mfc', 'E66.9', 'doenca', 'nao_se_aplica', 'ativo', '2022-01-01', null, 'Obesidade, IMC 32'],
].map(([paciente, autor, cid10, categoria, lado, status, inicio, malha, texto], ordem) => ({
  paciente, autor, cid10, categoria, lado, status, inicio, malha, texto, ordem,
}));

function cnsPara(id) {
  // PACIENTES.md fornece exemplo com 15 dígitos; portanto são nove zeros no campo central.
  const numero = Number(id.slice(1));
  const cns = `79${rodada}000000000${String(numero).padStart(2, '0')}`;
  assert.equal(cns.length, 15, `CNS gerado inválido para ${id}`);
  return cns;
}

function hojeISO() {
  const partes = Object.fromEntries(new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date()).map((parte) => [parte.type, parte.value]));
  return `${partes.year}-${partes.month}-${partes.day}`;
}
function somarDias(dataISO, dias) {
  const data = new Date(`${dataISO}T00:00:00.000Z`);
  data.setUTCDate(data.getUTCDate() + dias);
  return data.toISOString().slice(0, 10);
}
function anosAtras(anos) {
  const hoje = new Date(`${hojeISO()}T00:00:00.000Z`);
  const dia = hoje.getUTCDate();
  hoje.setUTCFullYear(hoje.getUTCFullYear() - anos);
  if (hoje.getUTCDate() !== dia) hoje.setUTCDate(0);
  return hoje.toISOString().slice(0, 10);
}
function dataNascimento(paciente) {
  if (paciente.id === 'P07') return somarDias(somarDias(hojeISO(), -485), 273);
  return anosAtras(paciente.idade);
}

function dataInicio(finding) {
  if (finding.inicio) return finding.inicio;
  const hoje = hojeISO();
  if (finding.paciente === 'P03' && finding.cid10 === 'O23.4') return somarDias(somarDias(hoje, -168), 70);
  if (finding.paciente === 'P04' && finding.cid10 === 'M75.1') return somarDias(hoje, -90);
  if (finding.paciente === 'P04' && finding.cid10 === 'M25.5') return somarDias(hoje, -200);
  if (finding.paciente === 'P04' && finding.cid10 === 'M23.2') return somarDias(hoje, -180);
  if (finding.paciente === 'P05' && finding.cid10 === 'N63') return somarDias(hoje, -20);
  if (finding.paciente === 'P07' && finding.cid10 === 'J21.9') return somarDias(somarDias(hoje, -485 + 273), 90);
  return hoje;
}

function resolverEntrada(indice, finding) {
  if (!finding.malha) return null;
  const entrada = indice.find((item) => item.malha === finding.malha);
  if (!entrada) throw new Error(`Malha fixa ausente no índice (${finding.paciente}/${finding.cid10}): ${finding.malha}`);
  if ((entrada.lateralidade === 'left' && finding.lado === 'direito')
    || (entrada.lateralidade === 'right' && finding.lado === 'esquerdo')) {
    throw new Error(`Lateralidade incompatível (${finding.paciente}/${finding.cid10}): ${finding.malha}`);
  }
  return entrada;
}

async function resolverAncoras() {
  const atlasCache = new Map();
  const contexts = new Map();
  const resolucoes = new Map();
  const ancorasCache = new Map();
  for (const paciente of pacientes.filter((p) => p.atlas)) {
    const key = `${paciente.atlas}/${paciente.versao}`;
    if (!atlasCache.has(key)) {
      const contexto = criarAncorasSeed(paciente.atlas, paciente.versao);
      atlasCache.set(key, contexto.indice);
      contexts.set(key, contexto);
    }
  }
  for (const finding of achados) {
    const paciente = pacientes.find((p) => p.id === finding.paciente);
    if (!paciente?.atlas || !finding.malha) {
      resolucoes.set(finding, { entrada: null, ancora: null, motivo: 'sem local especificado no roteiro' });
      continue;
    }
    const key = `${paciente.atlas}/${paciente.versao}`;
    const entrada = resolverEntrada(atlasCache.get(key), finding);
    const contexto = contexts.get(key);
    await contexto.carregarGlb(entrada.glb);
    const chaveAncora = `${paciente.id}/${paciente.atlas}/${paciente.versao}/${entrada.malha}`;
    if (!ancorasCache.has(chaveAncora)) ancorasCache.set(chaveAncora, contexto.ancora(entrada, 'dispersa', finding.ordem));
    const ancora = ancorasCache.get(chaveAncora);
    resolucoes.set(finding, { entrada, ancora, motivo: null });
  }
  return resolucoes;
}

async function mainSeco() {
  const resolucoes = await resolverAncoras();

  console.log(`SECO — rodada ${rodada}; sem login e sem chamadas de rede.`);
  console.log('Plano: 8 pacientes, 25 achados; idempotência prevista por CNS e observação AVAL-<rodada>-<paciente>-<CID>.');
  for (const paciente of pacientes) {
    const registros = achados.filter((item) => item.paciente === paciente.id);
    const comLocal = registros.filter((item) => resolucoes.get(item)?.ancora);
    const semLocal = registros.filter((item) => !resolucoes.get(item)?.ancora);
    const identificador = paciente.id === 'P07' ? 'sem CNS (identificado pelo nascimento)' : `CNS=${cnsPara(paciente.id)}`;
    console.log(`${paciente.id} ${paciente.nome}: sexo=${paciente.sexo}; nascimento=${dataNascimento(paciente)}; ${identificador}; unidades=${paciente.unidades.join(',')}; ${registros.length} achados; ${comLocal.length} com malha e GLB válidos; ${semLocal.length} sem local.`);
    for (const finding of registros) {
      const resolucao = resolucoes.get(finding);
      console.log(`  ${finding.cid10} (${finding.autor}) início ${dataInicio(finding)} → ${resolucao.entrada?.malha ?? 'sem local'}${resolucao.motivo ? `; ${resolucao.motivo}` : ''}`);
    }
  }
  console.log('Fluxos previstos: links por unidade; achados com observação AVAL-' + rodada + '-<paciente>-<CID>; gestações de P03/P06; condição gestacional; nascimento P07; correção P04 via p_substitui.');
  console.log(`Datas da rodada: hoje=${hojeISO()}; P03 DUM=${somarDias(hojeISO(), -168)}, pré-natal=${somarDias(hojeISO(), -140)}; P06 DUM=${somarDias(hojeISO(), -485)}, nascimento=${somarDias(hojeISO(), -212)}.`);
}

// Leituras de controle (rodadas, vínculos, CNS) pelo dono do banco, só SELECT: a chave de serviço não lê pacientes (0008).
// Toda escrita continua pelas funções do banco, logado como profissional/admin.
function lerSQL(sql) {
  const env = Object.fromEntries(readFileSync(new URL('./.env', import.meta.url), 'utf8').split(/\r?\n/)
    .filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1)]));
  assert.match(sql.trim(), /^select\b/i, 'lerSQL só aceita SELECT');
  const url = `postgresql://postgres.zmrxskzokpbedmvikrvc:${env.SUPABASE_DB_PASSWORD}@aws-0-sa-east-1.pooler.supabase.com:5432/postgres`;
  const pasta = mkdtempSync(join(tmpdir(), 'aval-'));
  const arquivo = join(pasta, 'q.sql');
  writeFileSync(arquivo, sql, 'utf8');
  // sem shell: o SQL e a senha não passam pelo cmd do Windows
  const npx = join(dirname(process.execPath), 'node_modules', 'npm', 'bin', 'npx-cli.js');
  const r = spawnSync(process.execPath, [npx, '-y', 'supabase@latest', 'db', 'query', `--remote=${url}`, '--yes', '-f', arquivo],
    { encoding: 'utf8', maxBuffer: 1 << 26 });
  rmSync(pasta, { recursive: true, force: true });
  if (r.status !== 0) throw new Error(`Leitura SQL falhou: ${(r.stderr || '').replaceAll(env.SUPABASE_DB_PASSWORD, '***').slice(-500)}`);
  const ini = r.stdout.indexOf('{'), fim = r.stdout.lastIndexOf('}');
  return JSON.parse(r.stdout.slice(ini, fim + 1)).rows ?? [];
}
const uuid = (v) => { assert.match(v, /^[0-9a-f-]{36}$/); return `'${v}'`; };

async function mainReal() {
  const resolucoes = await resolverAncoras();
  const { emails, login, rpc } = await import('./etapa4_comum.mjs');
  const emailAdmin = {
    ubs: emails.adminUbs,
    cardio: emails.adminCardio,
    maternidade: emails.adminMaternidade,
    pediatria: emails.adminPediatria,
  };
  const adminPorUnidadeId = Object.fromEntries(Object.entries(unidades).map(([nome, id]) => [id, nome]));
  const clientes = new Map();
  async function cliente(email) {
    if (!clientes.has(email)) clientes.set(email, await login(email));
    return clientes.get(email);
  }
  async function ler(query, descricao) {
    const { data, error } = await query;
    if (error) throw new Error(`Leitura de ${descricao} falhou (${error.code ?? 'sem código'}).`);
    return data ?? [];
  }
  async function lerUm(query, descricao) {
    const { data, error } = await query;
    if (error) throw new Error(`Leitura de ${descricao} falhou (${error.code ?? 'sem código'}).`);
    return data;
  }
  async function vinculosAtivos(ids) {
    if (!ids.length) return [];
    return lerSQL(`select id, paciente_id, unidade_id from public.vinculos where paciente_id in (${ids.map(uuid).join(',')}) and (ate is null or ate > current_date)`);
  }
  async function encerrarRodadasAnteriores() {
    const antigos = lerSQL(`select id, cns from public.pacientes where cns like '79%' and substr(cns, 3, 2) <> '${rodada}'`);
    const idsMaes = antigos.map((p) => p.id);
    const nascimentos = idsMaes.length
      ? lerSQL(`select n.crianca_id from public.nascimentos n join public.gestacoes g on g.id = n.gestacao_id where g.mae_id in (${idsMaes.map(uuid).join(',')})`)
      : [];
    const ids = [...new Set([...idsMaes, ...nascimentos.map((n) => n.crianca_id)])];
    const vinculos = await vinculosAtivos(ids);
    for (const vinculo of vinculos) {
      const unidade = adminPorUnidadeId[vinculo.unidade_id];
      if (!unidade || !emailAdmin[unidade]) throw new Error('Há vínculo ativo em unidade sem administrador configurado no seed.');
    }
    for (const vinculo of vinculos) {
      await rpc(await cliente(emailAdmin[adminPorUnidadeId[vinculo.unidade_id]]), 'encerrar_vinculo', { p_vinculo: vinculo.id });
    }
    return vinculos.length;
  }
  async function temVinculoAtivo(pacienteId, unidadeId) {
    return lerSQL(`select id from public.vinculos where paciente_id = ${uuid(pacienteId)} and unidade_id = ${uuid(unidadeId)} and (ate is null or ate > current_date) limit 1`).length > 0;
  }
  async function garantirVinculo(pacienteId, unidade) {
    if (await temVinculoAtivo(pacienteId, unidades[unidade])) return false;
    await rpc(await cliente(emailAdmin[unidade]), 'vincular_paciente', {
      p_paciente: pacienteId, p_motivo: `Avaliação fictícia EXP-0028, rodada ${rodada}`, p_origem: 'atendimento',
    });
    return true;
  }
  async function pacientePorCns(cns) {
    assert.match(cns, /^\d{15}$/);
    return lerSQL(`select id, cns from public.pacientes where cns = '${cns}'`)[0] ?? null;
  }

  const linksEncerrados = await encerrarRodadasAnteriores();
  const idsPacientes = new Map();
  for (const paciente of pacientes.filter((p) => p.id !== 'P07')) {
    const cns = cnsPara(paciente.id);
    let existente = await pacientePorCns(cns);
    if (!existente) {
      const id = await rpc(await cliente(emailAdmin.ubs), 'cadastrar_paciente', {
        p_nome: paciente.nome, p_cns: cns, p_sexo: paciente.sexo,
        p_data_nascimento: dataNascimento(paciente),
        p_motivo: `Avaliação fictícia EXP-0028, rodada ${rodada}`, p_origem: 'atendimento',
      });
      if (!id) throw new Error(`cadastrar_paciente não retornou ID para ${paciente.id}.`);
      existente = { id, cns };
    }
    idsPacientes.set(paciente.id, existente.id);
    for (const unidade of paciente.unidades) await garantirVinculo(existente.id, unidade);
  }

  async function obterGestacao(motherId, dum, unidadeCliente) {
    const rows = await rpc(unidadeCliente, 'listar_gestacoes', { p_mae: motherId }) ?? [];
    return rows.find((row) => String(row.dum).slice(0, 10) === dum) ?? null;
  }
  async function garantirCondicao(gestacaoId, gestacao, cid10, semana, obstetra) {
    const condicoes = Array.isArray(gestacao?.condicoes) ? gestacao.condicoes : [];
    if (condicoes.some((condicao) => condicao.cid10 === cid10)) return false;
    await rpc(obstetra, 'registrar_condicao_gestacao', {
      p_gestacao: gestacaoId, p_cid10: cid10, p_semana: semana,
    });
    return true;
  }

  const obstetra = await cliente(emails.obstetricia);
  const hoje = hojeISO();
  const dadosGestacoes = new Map();
  for (const config of [
    { paciente: 'P03', offset: 168, prenatal: 28, condicao: 'O24.4' },
    { paciente: 'P06', offset: 485, prenatal: 35, condicao: 'O13' },
  ]) {
    const motherId = idsPacientes.get(config.paciente);
    const dum = somarDias(hoje, -config.offset);
    const prenatal = somarDias(dum, config.prenatal);
    let gestacao = await obterGestacao(motherId, dum, obstetra);
    if (!gestacao) {
      const id = await rpc(obstetra, 'registrar_gestacao', {
        p_mae: motherId, p_dum: dum, p_inicio_pre_natal: prenatal,
      });
      if (!id) throw new Error(`registrar_gestacao não retornou ID para ${config.paciente}.`);
      gestacao = { gestacao_id: id, dum, condicoes: [], nascimentos: [], desfecho: 'em_curso' };
    }
    const inicioCondicaoP03 = somarDias(dum, 170) > hoje ? hoje : somarDias(dum, 170);
    const semana = config.paciente === 'P03'
      ? Math.floor((new Date(`${inicioCondicaoP03}T00:00:00Z`) - new Date(`${dum}T00:00:00Z`)) / 604800000)
      : Math.floor((new Date(`${somarDias(dum, 273)}T00:00:00Z`) - new Date(`${dum}T00:00:00Z`)) / 604800000);
    await garantirCondicao(gestacao.gestacao_id, gestacao, config.condicao, semana, obstetra);
    dadosGestacoes.set(config.paciente, { gestacao, dum, id: gestacao.gestacao_id });
  }

  const gestacaoP06 = dadosGestacoes.get('P06');
  const dataNascimentoP07 = somarDias(gestacaoP06.dum, 273);
  const nascimentoExistente = (gestacaoP06.gestacao.nascimentos ?? [])
    .find((nascimento) => String(nascimento.data).slice(0, 10) === dataNascimentoP07);
  let idP07 = nascimentoExistente?.crianca_id;
  if (!idP07) {
    idP07 = await rpc(obstetra, 'registrar_nascimento', {
      p_gestacao: gestacaoP06.id, p_nome: pacientes.find((p) => p.id === 'P07').nome,
      p_sexo: 'masculino', p_data: dataNascimentoP07, p_peso_g: 3150,
      p_idade_gestacional_sem: 39, p_apgar_5: 9,
    });
    if (!idP07) throw new Error('registrar_nascimento não retornou o ID da P07.');
  }
  idsPacientes.set('P07', idP07);
  await garantirVinculo(idP07, 'pediatria');

  const resumo = new Map(pacientes.map((p) => [p.id, { criados: 0, existentes: 0, comLocal: [], semLocal: [] }]));
  const idsPorObservacao = new Map();
  for (const finding of achados) {
    const pacienteId = idsPacientes.get(finding.paciente);
    const profissional = await cliente(emails[finding.autor]);
    const obs = `AVAL-${rodada}-${finding.paciente}-${finding.cid10}`;
    const atuais = await rpc(profissional, 'listar_achados', { p_paciente: pacienteId }) ?? [];
    const existentes = [...atuais];
    for (const atual of atuais.filter((row) => row.substitui_id)) {
      const historico = await rpc(profissional, 'historico_achado', { p_achado: atual.id }) ?? [];
      for (const row of historico) if (!existentes.some((item) => item.id === row.id)) existentes.push(row);
    }
    for (const row of existentes) {
      const etiqueta = row.observacao?.match(/\[(AVAL-[^\]]+)\]$/)?.[1];
      if (etiqueta) idsPorObservacao.set(`${finding.paciente}/${etiqueta}`, row.id);
    }
    const linhaResumo = resumo.get(finding.paciente);
    const resolucao = resolucoes.get(finding);
    if (resolucao?.ancora) linhaResumo.comLocal.push(`${finding.cid10}:${resolucao.entrada.malha}`);
    else linhaResumo.semLocal.push(finding.cid10);
    if (existentes.some((row) => row.observacao?.endsWith(`[${obs}]`))) {
      linhaResumo.existentes++;
      continue;
    }

    const substituiObs = finding.paciente === 'P04' && finding.cid10 === 'M23.2'
      ? `AVAL-${rodada}-P04-M25.5` : null;
    const substitui = substituiObs ? idsPorObservacao.get(`P04/${substituiObs}`) : null;
    if (substituiObs && !substitui) throw new Error('Não encontrei o achado original P04 M25.5 para p_substitui.');
    const id = await rpc(profissional, 'registrar_achado', {
      p_paciente: pacienteId, p_ancora: resolucao?.ancora ?? null, p_cid10: finding.cid10,
      p_categoria: finding.categoria, p_lado: finding.lado, p_status: finding.status,
      p_inicio: dataInicio(finding), p_observacao: `${finding.texto} [${obs}]`, p_substitui: substitui ?? null, p_vista: null,
    });
    if (!id) throw new Error(`registrar_achado não retornou ID (${finding.paciente}/${finding.cid10}).`);
    idsPorObservacao.set(`${finding.paciente}/${obs}`, id);
    linhaResumo.criados++;
  }

  console.log(`Rodada ${rodada}: encerrados ${linksEncerrados} vínculos ativos de rodadas anteriores.`);
  for (const paciente of pacientes) {
    const linha = resumo.get(paciente.id);
    console.log(`${paciente.id}: criados=${linha.criados}; já_existiam=${linha.existentes}; com_local=[${linha.comLocal.join(', ')}]; sem_local=[${linha.semLocal.join(', ')}].`);
  }
}

if (seco) await mainSeco();
else await mainReal();

