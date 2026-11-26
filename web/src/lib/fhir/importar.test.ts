import { describe, expect, it } from "vitest";
import { planejarImportacaoFHIR, SYSTEM_CNS } from "./importar";

const patient = (id = "p1", gender = "female") => ({ resourceType: "Patient", id, gender, identifier: [{ system: SYSTEM_CNS, value: "999999999999999" }] });
const condition = (id = "c1", system = "http://hl7.org/fhir/sid/icd-10") => ({ resourceType: "Condition", id, subject: { reference: "Patient/p1" }, code: { coding: [{ system, code: "I10" }] }, bodySite: [{ coding: [{ system: "http://snomed.info/sct", code: "123456" }] }] });

describe("planejarImportacaoFHIR", () => {
  it("mapeia Bundle válido para pacientes, condições e eventos", () => {
    const plan = planejarImportacaoFHIR({ resourceType: "Bundle", type: "collection", entry: [
      { resource: patient() }, { resource: condition() },
      { resource: { resourceType: "Observation", id: "o1", subject: { reference: "Patient/p1" }, code: { coding: [{ code: "HR" }] }, valueQuantity: { value: 70, unit: "bpm" } } },
      { resource: { resourceType: "Encounter", id: "e1", subject: { reference: "Patient/p1" }, period: { start: "2026-01-01" } } },
    ] });
    expect(plan.pacientes).toHaveLength(1);
    expect(plan.pacientes[0].sexo).toBe("feminino");
    expect(plan.condicoes[0]).toMatchObject({ cid10: "I10", bodySite: ["123456"] });
    expect(plan.eventos.map((event) => event.tipo)).toEqual(["Observation", "Encounter"]);
    expect(plan.erros).toEqual([]);
  });

  it("continua diante de recursos inválidos misturados e não expõe dados pessoais", () => {
    const plan = planejarImportacaoFHIR({ resourceType: "Bundle", entry: [
      { resource: patient() },
      { resource: { resourceType: "Patient", id: "bad", name: [{ text: "NOME PESSOAL SINTÉTICO" }] } },
      { resource: condition() },
      { resource: { resourceType: "Condition", id: "bad-c", subject: { reference: "Patient/p1" }, code: {} } },
    ] });
    expect(plan.pacientes).toHaveLength(1);
    expect(plan.condicoes).toHaveLength(1);
    expect(plan.erros.map((error) => error.id)).toEqual(["bad", "bad-c"]);
    expect(JSON.stringify(plan.erros)).not.toContain("NOME PESSOAL");
  });

  it("marca referência Patient quebrada como erro do recurso", () => {
    const item = condition(); item.subject.reference = "Patient/missing";
    const plan = planejarImportacaoFHIR({ resourceType: "Bundle", entry: [{ resource: patient() }, { resource: item }] });
    expect(plan.condicoes).toHaveLength(0);
    expect(plan.erros).toEqual([{ id: "c1", motivo: "Referência Patient ausente, inválida ou não resolvida no Bundle." }]);
  });

  it("rejeita CID de sistema diferente", () => {
    const plan = planejarImportacaoFHIR({ resourceType: "Bundle", entry: [{ resource: patient() }, { resource: condition("c1", "urn:outro-sistema") }] });
    expect(plan.condicoes).toHaveLength(0);
    expect(plan.erros[0].id).toBe("c1");
  });

  it("mapeia sexo desconhecido para indeterminado", () => {
    const plan = planejarImportacaoFHIR({ resourceType: "Bundle", entry: [{ resource: patient("p1", "other") }] });
    expect(plan.pacientes[0].sexo).toBe("indeterminado");
  });
});
