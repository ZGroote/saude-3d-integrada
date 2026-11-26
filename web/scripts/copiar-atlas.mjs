// Copia atlas/<atlas>/<versao> (gerado, fora do git) para web/public/atlas/, que o Next serve em /atlas.
// Pacote rascunho (não publicado ou não aceito) fica de fora, a não ser com `npm run atlas -- --rascunho`, para
// revisar em desenvolvimento. `--limpar-rascunhos` só os apaga de public/ (roda antes de todo build).
import { cpSync, existsSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const origem = fileURLToPath(new URL("../../atlas/", import.meta.url));
const destino = fileURLToPath(new URL("../public/atlas/", import.meta.url));

// pastas com ponto são temporárias do script de publicação
const subpastas = (pasta) =>
  existsSync(pasta)
    ? readdirSync(pasta, { withFileTypes: true }).filter((e) => e.isDirectory() && !e.name.startsWith(".")).map((e) => e.name)
    : [];

function completo(pasta) {
  try {
    const { sistemas } = JSON.parse(readFileSync(join(pasta, "manifesto.json"), "utf8"));
    return existsSync(join(pasta, "indice.json")) && sistemas.every((s) => [s.glb, s.glb_leve].every((glb) => !glb || existsSync(join(pasta, glb))));
  } catch {
    return false;
  }
}

function rascunho(pasta) {
  try {
    const { publicado, aceito, status } = JSON.parse(readFileSync(join(pasta, "manifesto.json"), "utf8"));
    return publicado === false || aceito === false || /rascunho/i.test(status ?? "");
  } catch {
    return false;
  }
}

const comRascunho = process.argv.includes("--rascunho");

if (process.argv.includes("--limpar-rascunhos")) {
  for (const atlas of subpastas(destino)) {
    for (const versao of subpastas(join(destino, atlas))) {
      if (!rascunho(join(destino, atlas, versao))) continue;
      rmSync(join(destino, atlas, versao), { recursive: true, force: true });
      console.log(`removido de public/ o rascunho ${atlas}/${versao}`);
    }
  }
  process.exit(0);
}

let copiados = 0;
for (const atlas of subpastas(origem)) {
  for (const versao of subpastas(join(origem, atlas))) {
    const de = join(origem, atlas, versao);
    if (!completo(de)) {
      console.warn(`ignorado ${atlas}/${versao}: pacote incompleto`);
      continue;
    }
    const para = join(destino, atlas, versao);
    rmSync(para, { recursive: true, force: true });
    if (rascunho(de)) {
      if (!comRascunho) {
        console.warn(`ignorado ${atlas}/${versao}: rascunho (use --rascunho para revisar em desenvolvimento)`);
        continue;
      }
      console.warn(`ATENÇÃO: ${atlas}/${versao} é rascunho, só para desenvolvimento`);
    }
    cpSync(de, para, { recursive: true });
    console.log(`copiado ${atlas}/${versao}`);
    copiados++;
  }
}
if (!copiados) {
  console.error("Nenhum atlas completo em atlas/. Gere com: python bodyparts3d/publicar_atlas.py");
  process.exit(1);
}
