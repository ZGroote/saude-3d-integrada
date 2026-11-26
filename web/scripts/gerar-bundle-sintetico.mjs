import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const output = resolve(root, "web/testes/dados/bundle-sintetico-50.json");
const CNS_SYSTEM = "http://rnDS.saude.gov.br/fhir/r4/StructureDefinition/BRIndividuo-1.0";
const ICD_SYSTEM = "http://hl7.org/fhir/sid/icd-10";
const ICD_BR_SYSTEM = "http://www.saude.gov.br/fhir/r4/CodeSystem/BRCID10";

// Deterministic PRNG (Mulberry32); seed is fixed and contains no personal data.
let state = 0x6f1234ab;
function random() {
  state += 0x6d2b79f5;
  let t = state;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}
function cnsFor(index) {
  const base = `999${String(index).padStart(11, "0")}`;
  const sum = [...base].reduce((total, digit, pos) => total + Number(digit) * (15 - pos), 0);
  const remainder = sum % 11;
  return `${base}${remainder < 2 ? 0 : 11 - remainder}`;
}
const patients = Array.from({ length: 50 }, (_, offset) => {
  const n = offset + 1;
  return {
    resourceType: "Patient", id: `sintetico-${String(n).padStart(3, "0")}`,
    identifier: [{ system: CNS_SYSTEM, value: cnsFor(n) }],
    name: [{ text: `PACIENTE FICTICIO ${String(n).padStart(3, "0")}` }],
    gender: ["female", "male", "unknown"][Math.floor(random() * 3)],
    birthDate: `198${Math.floor(random() * 10)}-${String(1 + Math.floor(random() * 12)).padStart(2, "0")}-15`,
  };
});
const entries = patients.map((resource) => ({ fullUrl: `urn:uuid:${resource.id}`, resource }));
for (let i = 1; i <= 50; i++) {
  const patientId = `sintetico-${String(i).padStart(3, "0")}`;
  const withSite = i % 2 === 0;
  entries.push({ resource: {
    resourceType: "Condition", id: `condicao-${String(i).padStart(3, "0")}`,
    subject: { reference: `Patient/${patientId}` },
    code: { coding: [{ system: i % 2 === 0 ? ICD_SYSTEM : ICD_BR_SYSTEM, code: i % 3 === 0 ? "M54.5" : "I10" }] },
    // 3 códigos de supabase/dados/bodysite_snomed.csv (lombar, coração, rim D) + 1 fora da tabela ("sem local")
    ...(withSite ? { bodySite: [{ coding: [{ system: "http://snomed.info/sct", code: ["52612000", "80891009", "9846003", "73780009"][(i / 2) % 4] }] }] } : {}),
    clinicalStatus: { coding: [{ code: "active", display: "active" }] },
    onsetDateTime: `2025-${String(1 + (i % 12)).padStart(2, "0")}-10`,
  } });
  entries.push({ resource: {
    resourceType: "Observation", id: `observacao-${String(i).padStart(3, "0")}`,
    subject: { reference: `Patient/${patientId}` },
    code: { coding: [{ system: "http://loinc.org", code: "8867-4", display: "Heart rate" }] },
    effectiveDateTime: `2026-${String(1 + (i % 12)).padStart(2, "0")}-10T10:00:00Z`,
    valueQuantity: { value: 60 + Math.floor(random() * 41), unit: "bpm" },
  } });
}
const bundle = { resourceType: "Bundle", type: "collection", entry: entries };
await mkdir(dirname(output), { recursive: true });
await writeFile(output, `${JSON.stringify(bundle, null, 2)}\n`, "utf8");
console.log(`Bundle FHIR sintético determinístico gerado: ${output}`);
console.log(`Pacientes: ${patients.length}; condições: 50 (25 com bodySite, 25 sem); observações: 50; entradas: ${entries.length}`);
console.log(`Seed: 0x6f1234ab; CNS fictícios com dígito verificador; nomes explicitamente fictícios.`);
