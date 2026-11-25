// Copia atlas/<atlas>/<versao> (gerado, fora do git) para web/public/atlas/, que o Next serve em /atlas.
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
    return existsSync(join(pasta, "indice.json")) && sistemas.every((s) => existsSync(join(pasta, s.glb)));
  } catch {
    return false;
  }
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
    cpSync(de, para, { recursive: true });
    console.log(`copiado ${atlas}/${versao}`);
    copiados++;
  }
}
if (!copiados) {
  console.error("Nenhum atlas completo em atlas/. Gere com: python bodyparts3d/publicar_atlas.py");
  process.exit(1);
}
