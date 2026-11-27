import { describe, expect, it } from "vitest";
import { lacunasDaBusca, nomearIndiceLacunas } from "./lacunas";

describe("lacunas do atlas feminino", () => {
  it("reconhece prefixos de lacunas e não palavras maiores que apenas começam igual", () => {
    expect(lacunasDaBusca("hra-f", "1.10-1", "isq").map((l) => l.nome)).toContain("Ísquio");
    expect(lacunasDaBusca("hra-f", "1.10-1", "isquiotibiais")).toEqual([]);
    expect(lacunasDaBusca("hra-f", "1.10-1", "pub").map((l) => l.nome)).toContain("Púbis");
    expect(lacunasDaBusca("hra-f", "1.10-1", "acetabulo").map((l) => l.nome)).toContain("Acetábulo");
    expect(lacunasDaBusca("bp3d-m", "4.0-1", "isq")).toEqual([]);
  });

  it("ajusta só os nomes das malhas do ílio e preserva a identificação estrutural", () => {
    const entrada = {
      malha: "VH_F_ilium_compact_bone_R", estrutura: "UBERON:0001274", lateralidade: "right",
      nome_pt: "Tecido ósseo compacto", nome_en: "Compact bone", triangulos: 12, sistema: "esqueletico",
      validacao: "", glb: "esqueletico.glb",
    };
    const [renomeada] = nomearIndiceLacunas("hra-f", "1.10-1", [entrada]);
    expect(renomeada).toMatchObject({ nome_pt: "Ílio (osso compacto)", nome_en: "Ilium (compact bone)" });
    expect(renomeada?.estrutura).toBe(entrada.estrutura);
  });
});
