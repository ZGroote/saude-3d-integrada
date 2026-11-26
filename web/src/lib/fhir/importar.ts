import { z } from "zod";

const SYSTEM_CNS = "http://rnDS.saude.gov.br/fhir/r4/StructureDefinition/BRIndividuo-1.0";
const ICD10_SYSTEMS = new Set([
  "http://hl7.org/fhir/sid/icd-10",
  "http://www.saude.gov.br/fhir/r4/CodeSystem/BRCID10",
  "http://www.saude.gov.br/fhir/CodeSystem/BRCID10",
]);

const codingSchema = z.object({
  system: z.string().optional(),
  code: z.string().optional(),
  display: z.string().optional(),
}).passthrough();
const codeableConceptSchema = z.object({ coding: z.array(codingSchema).optional() }).passthrough();
const referenceSchema = z.object({ reference: z.string().optional() }).passthrough();
const resourceBase = z.object({ resourceType: z.string(), id: z.string().min(1) }).passthrough();
const patientSchema = resourceBase.extend({
  resourceType: z.literal("Patient"),
  identifier: z.array(z.object({ system: z.string().optional(), value: z.string().optional() }).passthrough()).optional(),
  gender: z.string().optional(),
  birthDate: z.string().optional(),
  name: z.array(z.unknown()).optional(),
});
const conditionSchema = resourceBase.extend({
  resourceType: z.literal("Condition"),
  subject: referenceSchema,
  code: codeableConceptSchema,
  bodySite: z.array(codeableConceptSchema).optional(),
  clinicalStatus: codeableConceptSchema.optional(),
  onsetDateTime: z.string().optional(),
  recordedDate: z.string().optional(),
});
const observationSchema = resourceBase.extend({
  resourceType: z.literal("Observation"),
  subject: referenceSchema,
  code: codeableConceptSchema,
  effectiveDateTime: z.string().optional(),
  effectiveInstant: z.string().optional(),
  valueString: z.string().optional(),
  valueQuantity: z.object({ value: z.number().optional(), unit: z.string().optional() }).passthrough().optional(),
  status: z.string().optional(),
});
const encounterSchema = resourceBase.extend({
  resourceType: z.literal("Encounter"),
  subject: referenceSchema,
  type: z.array(codeableConceptSchema).optional(),
  period: z.object({ start: z.string().optional(), end: z.string().optional() }).passthrough().optional(),
  status: z.string().optional(),
});
const entrySchema = z.object({ fullUrl: z.string().optional(), resource: z.unknown() }).passthrough();
const bundleSchema = z.object({ resourceType: z.literal("Bundle"), type: z.string().optional(), entry: z.array(entrySchema) }).passthrough();

export type ErroImportacao = { id: string; motivo: string };
export type PacienteImportacao = {
  fhir_id: string;
  cns: string;
  sexo: "feminino" | "masculino" | "indeterminado";
  nascimento: string | null;
};
export type CondicaoImportacao = {
  fhir_id: string;
  paciente_fhir_id: string;
  cid10: string;
  bodySite: string[];
  status: string | null;
  inicio: string | null;
};
export type EventoImportacao = {
  fhir_id: string;
  paciente_fhir_id: string;
  tipo: "Observation" | "Encounter";
  data: string | null;
  codigo: string | null;
  descricao: string | null;
  valor: string | null;
};
export type PlanoImportacao = {
  pacientes: PacienteImportacao[];
  condicoes: CondicaoImportacao[];
  eventos: EventoImportacao[];
  erros: ErroImportacao[];
};

function reason(resource: unknown): string {
  if (!resource || typeof resource !== "object") return "Recurso FHIR inválido.";
  const type = (resource as { resourceType?: unknown }).resourceType;
  if (type === "Patient") return "Patient inválido ou sem CNS no sistema esperado.";
  if (type === "Condition") return "Condition inválido, sem referência interna ou sem CID-10 aceito.";
  if (type === "Observation" || type === "Encounter") return `${type} inválido ou sem referência interna.`;
  return "Tipo de recurso não suportado.";
}

function referenceId(reference: string | undefined): string | null {
  if (!reference) return null;
  const match = /^Patient\/([^/]+)$/.exec(reference);
  return match?.[1] ?? null;
}

function sex(gender: string | undefined): PacienteImportacao["sexo"] {
  if (gender === "female") return "feminino";
  if (gender === "male") return "masculino";
  return "indeterminado";
}

function firstCid(codings: Array<z.infer<typeof codingSchema>> | undefined): string | null {
  return codings?.find((item) => item.system && ICD10_SYSTEMS.has(item.system) && item.code)?.code ?? null;
}

function snomedCodes(sites: Array<z.infer<typeof codeableConceptSchema>> | undefined): string[] {
  return [...new Set((sites ?? []).flatMap((site) => (site.coding ?? [])
    .filter((coding) => coding.system === "http://snomed.info/sct" && coding.code)
    .map((coding) => coding.code!)))];
}

function display(concept: z.infer<typeof codeableConceptSchema> | undefined): string | null {
  return concept?.coding?.find((item) => item.display)?.display ?? null;
}

/** Parses a FHIR R4 subset into a persistence-independent import preview plan. */
export function planejarImportacaoFHIR(input: unknown): PlanoImportacao {
  const output: PlanoImportacao = { pacientes: [], condicoes: [], eventos: [], erros: [] };
  const bundle = bundleSchema.safeParse(input);
  if (!bundle.success) {
    output.erros.push({ id: "Bundle", motivo: "Bundle FHIR inválido." });
    return output;
  }

  const entries = bundle.data.entry;
  const patientIds = new Set<string>();
  for (const entry of entries) {
    const candidate = entry.resource;
    if (!candidate || typeof candidate !== "object" || !["Patient", "Condition", "Observation", "Encounter"].includes(String((candidate as { resourceType?: unknown }).resourceType))) continue;
    const type = (candidate as { resourceType: string }).resourceType;
    const parsed = type === "Patient" ? patientSchema.safeParse(candidate) : null;
    if (type !== "Patient") continue;
    const id = parsed.success ? parsed.data.id : ((candidate as { id?: unknown }).id && typeof (candidate as { id?: unknown }).id === "string" ? (candidate as { id: string }).id : "Patient");
    if (!parsed.success) { output.erros.push({ id, motivo: reason(candidate) }); continue; }
    const cns = parsed.data.identifier?.find((item) => item.system === SYSTEM_CNS)?.value;
    if (!cns) { output.erros.push({ id: parsed.data.id, motivo: reason(candidate) }); continue; }
    if (patientIds.has(parsed.data.id)) { output.erros.push({ id: parsed.data.id, motivo: "ID de recurso duplicado no Bundle." }); continue; }
    patientIds.add(parsed.data.id);
    output.pacientes.push({ fhir_id: parsed.data.id, cns, sexo: sex(parsed.data.gender), nascimento: parsed.data.birthDate ?? null });
  }

  const patientIdSet = new Set(output.pacientes.map((item) => item.fhir_id));
  for (const entry of entries) {
    const candidate = entry.resource;
    if (!candidate || typeof candidate !== "object") continue;
    const type = (candidate as { resourceType?: unknown }).resourceType;
    if (type !== "Condition" && type !== "Observation" && type !== "Encounter") continue;
    const schema = type === "Condition" ? conditionSchema : type === "Observation" ? observationSchema : encounterSchema;
    const parsed = schema.safeParse(candidate);
    const id = parsed.success ? parsed.data.id : (typeof (candidate as { id?: unknown }).id === "string" ? (candidate as { id: string }).id : String(type));
    if (!parsed.success) { output.erros.push({ id, motivo: reason(candidate) }); continue; }
    const patientId = referenceId(parsed.data.subject.reference);
    if (!patientId || !patientIdSet.has(patientId)) {
      output.erros.push({ id, motivo: "Referência Patient ausente, inválida ou não resolvida no Bundle." });
      continue;
    }
    if (type === "Condition") {
      const cid10 = firstCid(parsed.data.code.coding);
      if (!cid10) { output.erros.push({ id, motivo: reason(candidate) }); continue; }
      output.condicoes.push({
        fhir_id: id, paciente_fhir_id: patientId, cid10,
        bodySite: snomedCodes(parsed.data.bodySite),
        status: display(parsed.data.clinicalStatus),
        inicio: parsed.data.onsetDateTime ?? parsed.data.recordedDate ?? null,
      });
      continue;
    }
    if (type === "Observation") {
      const value = parsed.data.valueString ?? (parsed.data.valueQuantity?.value === undefined ? null : `${parsed.data.valueQuantity.value}${parsed.data.valueQuantity.unit ? ` ${parsed.data.valueQuantity.unit}` : ""}`);
      output.eventos.push({ fhir_id: id, paciente_fhir_id: patientId, tipo: "Observation", data: parsed.data.effectiveDateTime ?? parsed.data.effectiveInstant ?? null, codigo: parsed.data.code.coding?.find((item) => item.code)?.code ?? null, descricao: display(parsed.data.code), valor: value });
    } else {
      const code = parsed.data.type?.flatMap((item) => item.coding ?? []).find((item) => item.code);
      output.eventos.push({ fhir_id: id, paciente_fhir_id: patientId, tipo: "Encounter", data: parsed.data.period?.start ?? null, codigo: code?.code ?? null, descricao: code?.display ?? null, valor: parsed.data.status ?? null });
    }
  }
  return output;
}

export { SYSTEM_CNS, ICD10_SYSTEMS };
