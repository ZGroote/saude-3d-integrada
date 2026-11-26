"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { formatarData } from "@/lib/achados";
import type { Sexo } from "@/lib/banco";
import { CAMPO, hoje, ROTULO } from "@/lib/formulario";
import { useHidratado } from "@/lib/hidratacao";
import { createClient } from "@/lib/supabase/client";

export function FormularioNascimento({ gestacaoId, dum }: { gestacaoId: string; dum: string | null }) {
  const router = useRouter();
  const hidratado = useHidratado();
  const [erro, setErro] = useState("");
  const [salvando, setSalvando] = useState(false);
  // o banco recusa (22023) data fora deste intervalo
  const dataFora = `A data do nascimento tem que estar entre ${dum ? `a DUM (${formatarData(dum)})` : "a DUM"} e hoje.`;

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const campos = new FormData(evento.currentTarget);
    const texto = (nome: string) => String(campos.get(nome) ?? "").trim();
    if (!texto("nome")) return setErro("Informe o nome da criança.");
    setErro("");
    setSalvando(true);
    const { data, error } = await createClient().rpc("registrar_nascimento", {
      p_gestacao: gestacaoId,
      p_nome: texto("nome"),
      p_sexo: texto("sexo") as Sexo,
      p_data: texto("data"),
      p_peso_g: Number(texto("peso")),
      p_idade_gestacional_sem: Number(texto("idade_gestacional")),
      p_apgar_5: Number(texto("apgar")),
    });
    if (error || !data) {
      setSalvando(false);
      return setErro(error?.code === "22023"
        ? `O nascimento não foi registrado. ${dataFora} Confira também os demais dados.`
        : "O nascimento não foi registrado. Confira os dados e o vínculo com a mãe.");
    }
    // o botão fica desabilitado até a troca de página: um segundo envio criaria outra criança
    router.push(`/pacientes/${data}`);
  }

  return (
    <Card className="mt-4 max-w-2xl px-5 py-4">
      <form onSubmit={salvar}>
        <fieldset disabled={!hidratado || salvando} className="grid gap-3 sm:grid-cols-2">
          <label className={`${ROTULO} sm:col-span-2`}>Nome da criança<Input name="nome" required maxLength={200} autoComplete="off" /></label>
          <label className={ROTULO}>Sexo
            <select name="sexo" required className={CAMPO} defaultValue="">
              <option value="" disabled>Escolha…</option>
              <option value="feminino">Feminino</option><option value="masculino">Masculino</option><option value="indeterminado">Indeterminado</option>
            </select>
          </label>
          <label className={ROTULO}>Data do nascimento<Input type="date" name="data" required min={dum ?? undefined} max={hoje()} onChange={() => setErro("")}
            onInvalid={(e) => { if (e.currentTarget.value) setErro(dataFora); }} /></label>
          <label className={ROTULO}>Peso ao nascer (g)<Input type="number" name="peso" required min={200} max={7000} step={1} inputMode="numeric" /></label>
          <label className={ROTULO}>Idade gestacional (semanas)<Input type="number" name="idade_gestacional" required min={20} max={45} step={1} inputMode="numeric" /></label>
          <label className={ROTULO}>Apgar no 5º minuto<Input type="number" name="apgar" required min={0} max={10} step={1} inputMode="numeric" /></label>
          {erro && <p role="alert" className="text-sm text-red-800 sm:col-span-2">{erro}</p>}
          <Button type="submit" className="sm:col-span-2">{salvando ? "Salvando…" : "Registrar nascimento"}</Button>
        </fieldset>
      </form>
    </Card>
  );
}
