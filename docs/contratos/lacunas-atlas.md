# Contrato — lacunas do atlas na tela + pontos residuais do visualizador

Origem: EXP-0024 (pelve do `hra-f/1.10-1` só tem ílios e sacro; cobertura 52%) e revisão externa do commit `4a3060e`.
Regra do produto (SPEC-MVP §5): "a tela diz claramente o que não existe naquele atlas".

## A. Lacunas conhecidas (web) — Codex

1. Novo `web/src/lib/lacunas.ts`, dados fixos por `atlas/versao` (sem config, sem banco):
   ```ts
   export type Lacuna = { nome: string; termos: string[]; parcial?: string };
   export const LACUNAS: Record<string, Lacuna[]> = {
     "hra-f/1.10-1": [
       { nome: "Púbis", termos: ["pubis", "pube", "pubic"] },
       { nome: "Ísquio", termos: ["isquio", "ischium", "ischial"] },
       { nome: "Acetábulo", termos: ["acetabulo", "acetabulum"] },
       { nome: "Osso do quadril", termos: ["quadril", "coxal", "hip"], parcial: "só o ílio está no corpo" },
     ],
   };
   export function lacunasDaBusca(atlas: string, versao: string, texto: string): Lacuna[]
   ```
   Casamento: normalizar com `normalizar` de `lib/estruturas.ts`; uma lacuna casa quando alguma palavra do texto com ≥ 3 letras é **prefixo** de algum termo (`"isq"` casa Ísquio; `"isquiotibiais"` NÃO casa). Teste vitest cobrindo esses dois casos, `"pub"`, `"acetabulo"`, atlas sem lacunas (`bp3d-m`) → `[]`.

2. `BuscaEstrutura` recebe `lacunas?: (texto) => Lacuna[]` (ou atlas/versão) e, quando há lacuna casada, mostra abaixo do status, **mesmo que haja outros resultados**, um parágrafo `role="note"`:
   - lacuna total: "**{nome}** não existe neste corpo (lacuna conhecida do atlas feminino). Registre o achado sem local e escreva a estrutura na observação; não marque no osso vizinho."
   - lacuna parcial: "**{nome}**: {parcial}. Púbis, ísquio e acetábulo não existem neste corpo." (texto livre a partir de `parcial`; não precisa ser genérico além disso)

3. Aviso fixo no corpo: em `visualizador-atlas.tsx`, quando o atlas aberto tiver lacunas totais, uma linha discreta abaixo da barra de ferramentas: "Faltam neste corpo: Púbis, Ísquio, Acetábulo." (lista gerada de `LACUNAS`, só as sem `parcial`).

4. Nome do ílio: no `hra-f/1.10-1` as malhas `VH_F_ilium_compact_bone_R/L` e `VH_F_ilium_spongy_bone_R/L` vêm com nome de tecido ("Tecido ósseo compacto/trabecular"). O pacote publicado não muda (hash no manifesto). No **ponto único em que o web recebe o índice do atlas**, sobrescrever `nome_pt` por malha: compacto → "Ílio (osso compacto)", esponjoso → "Ílio (osso trabecular)"; `nome_en` → "Ilium (compact bone)" / "Ilium (trabecular bone)". Mapa por `atlas/versao` + `malha` em `lacunas.ts`. Assim busca "ilio" acha, o cartão e o formulário mostram "Ílio". Âncora/estrutura (UBERON) não mudam.

5. Teste de navegador em `web/testes/motor.py` (bloco do `hra-f` real): digitar "isq" na busca de estrutura → aparece a nota de lacuna; digitar "ilio" → aparece "Ílio (osso compacto)" com lado; o aviso "Faltam neste corpo" está visível. Se a busca só existir no formulário de achado, use `achados_real.py` ou o fluxo mais curto que já abra o formulário no `hra-f`.

## B. Pontos residuais da revisão (motor) — Codex

6. Fixar `three` em `0.182.0` exato (sem `^`) em `web/package.json` e nos devDependencies de `packages/motor-anatomico/package.json`; atualizar o lockfile com `npm install` (sem rede? avise e pare neste item).
7. Teste de regressão vitest no motor: `new OrbitControls(camera)` tem `_quat` e `_quatInverse` instâncias de `Quaternion`, e `atualizarEixoOrbitacao` com up `[0,0,1]` faz `_quat` levar (0,0,1) em (0,1,0). Exporte a função só se precisar para o teste.
8. Memória de GPU: expor no wrapper do motor `data-gpu="{geometrias}/{texturas}"` lido de `gl.info.memory` após cada mudança de visuais (mesmo efeito do `data-visuais`). Em `motor.py`: ligar/desligar o sistema muscular 8 vezes; registrar `data-gpu` e `data-visuais` após cada ciclo; afirmar que, depois do 2º ciclo, geometrias e visuais não crescem. Imprimir os números.

## C. `up` degenerado (banco) — Claude Visualizador

9. Migração `supabase/migrations/0012_vista_up_unitario.sql`: `CREATE OR REPLACE FUNCTION public.vista_valida` igual à 0011, mas `up`, quando presente, além de 3 números com |v| ≤ 1, precisa ter norma entre 0,99 e 1,01 (rejeita `[0,0,0]` e não unitários). Mesmos grants da 0011.
10. Testes em `supabase/testes/vista.test.mjs`: `[0,0,0]` e `[0.5,0,0]` recusados (22023 sem gravar); `[0,0,1]` e `[0,1,0]` aceitos. Rodar a suíte local inteira. **Não aplicar na homologação** (o revisor aplica).

## Fora do escopo
Não alterar `web/public/atlas/**`, `hra/**`, `pesquisa/**`. Não commitar.
