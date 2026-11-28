import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const aqui = dirname(fileURLToPath(import.meta.url));
const origem = resolve(aqui, 'dados/cid10.csv');
const destino = resolve(aqui, 'migrations/0002_cid10.sql');

function parseCsv(texto) {
  const linhas = [];
  let linha = [];
  let campo = '';
  let aspas = false;
  for (let i = 0; i < texto.length; i += 1) {
    const c = texto[i];
    if (aspas) {
      if (c === '"' && texto[i + 1] === '"') { campo += '"'; i += 1; }
      else if (c === '"') aspas = false;
      else campo += c;
    } else if (c === '"') aspas = true;
    else if (c === ',') { linha.push(campo); campo = ''; }
    else if (c === '\n') {
      linha.push(campo.replace(/\r$/, ''));
      linhas.push(linha);
      linha = [];
      campo = '';
    } else campo += c;
  }
  if (campo.length || linha.length) { linha.push(campo); linhas.push(linha); }
  return linhas;
}

const registros = parseCsv(await readFile(origem, 'utf8'));
const cabecalho = registros.shift();
if (cabecalho?.[0] !== 'codigo' || cabecalho?.[1] !== 'descricao') {
  throw new Error('Cabeçalho esperado: codigo,descricao');
}
const dados = registros.filter((r) => r.length >= 2 && r[0]);
const quote = (valor) => `'${valor.replaceAll("'", "''")}'`;
const sql = [
  '-- Gerado por node supabase/gerar_cid10_sql.mjs a partir de dados/cid10.csv.',
  'CREATE TABLE public.cid10 (',
  '  codigo text PRIMARY KEY,',
  '  descricao text NOT NULL',
  ');',
  'ALTER TABLE public.cid10 ENABLE ROW LEVEL SECURITY;',
  'CREATE POLICY cid10_leitura_authenticated ON public.cid10',
  '  FOR SELECT TO authenticated USING (true);',
  'REVOKE ALL ON TABLE public.cid10 FROM PUBLIC, anon, authenticated;',
  'GRANT SELECT ON TABLE public.cid10 TO authenticated;',
];
for (let i = 0; i < dados.length; i += 500) {
  sql.push('INSERT INTO public.cid10 (codigo, descricao) VALUES');
  sql.push(dados.slice(i, i + 500).map(([codigo, descricao]) =>
    `  (${quote(codigo)}, ${quote(descricao)})`).join(',\n') + ';');
}
sql.push(`-- Total de códigos carregados: ${dados.length}.`);
await writeFile(destino, `${sql.join('\n')}\n`, 'utf8');
console.log(`Gerada ${destino}: ${dados.length} registros CID-10.`);
