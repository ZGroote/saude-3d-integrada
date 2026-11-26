import { readFileSync, existsSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { ancoraEstrutural, ATLAS_DO_SEXO, type Mapeamento } from "./ancora";

const entrada = (malha: string, estrutura: string, lateralidade: string | null, triangulos = 10) =>
  ({ malha, estrutura, lateralidade, triangulos, sistema: "urogenital", nome_en: malha, nome_pt: "", validacao: "", glb: "x.glb" });
const rim = (lado: Mapeamento["lado"]): Mapeamento => ({ snomed: "1", estrutura_fma: null, estrutura_uberon: "UBERON:0002189", lado });
const feminino = ATLAS_DO_SEXO.feminino!;
// o lado direito tem menos triângulos: sem o filtro de lado, a "principal" seria a esquerda
const indice = [entrada("rim_L", "UBERON:0002189", "left", 99), entrada("rim_R", "UBERON:0002189", "right", 5)];

describe("ancoraEstrutural", () => {
  it("usa o lado do mapeamento quando o mesmo ID cobre os dois", () => {
    expect(ancoraEstrutural(rim("direito"), feminino, indice)?.malha).toBe("rim_R");
    expect(ancoraEstrutural(rim("esquerdo"), feminino, indice)?.malha).toBe("rim_L");
  });
  it("não adivinha: sem lado e com os dois lados, sem ID no atlas ou sem malha do lado", () => {
    expect(ancoraEstrutural(rim(null), feminino, indice)).toBeNull();
    expect(ancoraEstrutural({ ...rim(null), estrutura_uberon: null }, feminino, indice)).toBeNull();
    expect(ancoraEstrutural(rim("direito"), feminino, [indice[0]!])).toBeNull();
  });
  it("devolve âncora só estrutural, escolhendo a maior malha", () => {
    const varias = [entrada("a", "UBERON:0002189", "right", 3), entrada("b", "UBERON:0002189", "right", 30)];
    expect(ancoraEstrutural(rim("direito"), feminino, varias)).toMatchObject({ atlas: "hra-f", malha: "b", posicao_local: null, triangulo: null });
  });
  // pacote real (fora do git): os IDs da tabela existem nos índices
  const real = new URL("../../../../atlas/bp3d-m/4.0-1/indice.json", import.meta.url);
  it.skipIf(!existsSync(real))("resolve um mapeamento no atlas masculino publicado", () => {
    const m: Mapeamento = { snomed: "9846003", estrutura_fma: "FMA7204", estrutura_uberon: null, lado: "direito" };
    expect(ancoraEstrutural(m, ATLAS_DO_SEXO.masculino!, JSON.parse(readFileSync(real, "utf8")))?.malha).toBe("FJ3147");
  });
});
