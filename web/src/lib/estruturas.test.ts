import { describe, expect, it } from "vitest";
import { ancoraEstrutural, ancoraNaEntrada, ATLAS_DO_SEXO } from "./fhir/ancora";
import { listarEstruturas, procurarEstruturas } from "./estruturas";

const entrada = (malha: string, nome_pt: string, lateralidade: string | null, triangulos: number, estrutura: string | null = "UBERON:1") =>
  ({ malha, estrutura, lateralidade, triangulos, sistema: "urogenital", nome_en: `en ${malha}`, nome_pt, validacao: "", glb: "x.glb" });
const indice = [
  entrada("rim_L", "Córtex do rim", "left", 10), entrada("rim_R_menor", "Córtex do rim", "right", 1), entrada("rim_R", "Córtex do rim", "right", 9),
  entrada("sem_id", "Malha sem identificador", null, 3, null),
];

describe("estruturas por nome", () => {
  const todas = listarEstruturas(indice);
  it("separa os lados e usa a malha principal de cada um", () => {
    expect(todas.map((e) => e.entrada.malha)).toEqual(["rim_L", "rim_R", "sem_id"].sort((a, b) => a.localeCompare(b)));
  });
  it("acha sem acento, em qualquer ordem, pelo lado e pelo nome em inglês", () => {
    expect(procurarEstruturas(todas, "direito cortex").map((e) => e.entrada.malha)).toEqual(["rim_R"]);
    expect(procurarEstruturas(todas, "en rim_L").map((e) => e.entrada.malha)).toEqual(["rim_L"]);
    expect(procurarEstruturas(todas, "c")).toEqual([]);
  });
  it("gera a mesma âncora da importação FHIR", () => {
    const direito = procurarEstruturas(todas, "rim direito")[0]!;
    const daImportacao = ancoraEstrutural({ snomed: "1", estrutura_fma: null, estrutura_uberon: "UBERON:1", lado: "direito" }, ATLAS_DO_SEXO.feminino!, indice);
    expect(ancoraNaEntrada(direito.entrada, ATLAS_DO_SEXO.feminino!)).toEqual(daImportacao);
  });
});
