import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const pasta = dirname(fileURLToPath(import.meta.url));
const raiz = resolve(pasta, '..');
const entradas = [
  { arquivo: 'atlas/bp3d-m/4.0-1/indice.json', atlas: 'bp3d-m', versao: '4.0-1' },
  { arquivo: 'atlas/hra-f/1.10-1/indice.json', atlas: 'hra-f', versao: '1.10-1' },
];
const quote = (valor) => valor == null ? 'NULL' : `'${String(valor).replaceAll("'", "''")}'`;

async function gerar() {
  const linhas = [];
  for (const entrada of entradas) {
    const rows = JSON.parse(await readFile(resolve(raiz, entrada.arquivo), 'utf8'));
    if (!Array.isArray(rows) || rows.length === 0) throw new Error(`Índice vazio/inválido: ${entrada.arquivo}`);
    const chaves = new Set();
    for (const row of rows) {
      if (typeof row.malha !== 'string' || !row.malha || typeof row.sistema !== 'string' || !row.sistema ||
          (row.lateralidade != null && !['left', 'right'].includes(row.lateralidade))) {
        throw new Error(`Entrada inválida em ${entrada.arquivo}`);
      }
      if (chaves.has(row.malha)) throw new Error(`Malha duplicada em ${entrada.arquivo}`);
      chaves.add(row.malha);
      linhas.push(`  (${[entrada.atlas, entrada.versao, row.malha, row.sistema, row.lateralidade, row.estrutura]
        .map(quote).join(', ')})`);
    }
  }
  return `INSERT INTO public.atlas_malhas(atlas,versao,malha,sistema,lateralidade,estrutura) VALUES\n${linhas.join(',\n')};`;
}

const sql = await gerar();
if (process.argv.includes('--atualizar-migracao')) {
  const migracao = resolve(pasta, 'migrations/0008_endurecimento_piloto.sql');
  const original = await readFile(migracao, 'utf8');
  const inicio = '-- INÍCIO: seed atlas_malhas gerado por gerar_atlas_malhas.mjs';
  const fim = '-- FIM: seed atlas_malhas gerado';
  const padrao = new RegExp(`${inicio}[\\s\\S]*?${fim}`);
  if (!padrao.test(original)) throw new Error('Marcadores do seed não encontrados em 0008_endurecimento_piloto.sql');
  const atualizado = original.replace(padrao, `${inicio}\n${sql}\n${fim}`);
  await writeFile(migracao, atualizado, 'utf8');
  console.log(`Seed atlas_malhas atualizado (${sql.split('\n').length - 1} registros).`);
} else {
  process.stdout.write(`${sql}\n`);
}
