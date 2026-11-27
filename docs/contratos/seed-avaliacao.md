# Contrato — carga de pacientes fictícios para avaliação com médicos (EXP-0028)

Fonte do conteúdo: `pesquisa/validacao-medica/usabilidade/PACIENTES.md` (unidades, contas, rodadas, CNS, 8 pacientes, achados, gestações, regras). Seguir à risca; não inventar achados nem trocar estruturas.

## Entregas
1. **Conta nova** em `supabase/seed.sql`: usuário `20000000-0000-4000-8000-00000000000a`, `mfc@saude3d.invalid`, perfil "Profissional Medicina de Família", UBS Centro (`10000000-…-0001`), especialidade `medicina_familia`, papel `profissional`. O revisor roda `python supabase/seed_homologacao_complemento.py` depois (você não tem rede); não rode.
2. **Módulo de âncoras** `supabase/ancoras_seed.mjs`: extrair de `seed_etapa4.mjs` `carregarGlb`, `dadosMalha`, `ancora`, `lado`, generalizados por `atlas`/`versao` (o `bp3d-m/4.0-1` também). `seed_etapa4.mjs` passa a importar dele sem mudar comportamento.
3. **`supabase/seed_avaliacao.mjs --rodada NN`** (NN = 00–99, obrigatório):
   - usa `login`/`rpc` de `etapa4_comum.mjs` (acrescente as contas que faltarem em `emails`: mfc, pediatria, admins de cada unidade presentes em `seed.sql`);
   - **antes de criar**: para cada paciente cujo CNS começa com `79` e cuja rodada ≠ NN, encerrar todos os vínculos ativos com `encerrar_vinculo` (pelo admin da unidade do vínculo). Nada é apagado;
   - cria os 8 pacientes da rodada (CNS conforme `PACIENTES.md`), vínculos, achados (observação `AVAL-NN-<paciente>-<CID>`), gestações, condição, nascimento e a correção do P04 (`p_substitui`);
   - idempotente dentro da mesma rodada: rodar de novo não duplica (conferir por CNS e por observação);
   - local: escolher a malha pelo nome no `indice.json` do atlas do paciente (lista de candidatas na ordem do `PACIENTES.md`; casar por `nome_pt`/`nome_en`/`malha`, sem acento e sem caixa). Sem candidata → sem local, e anotar;
   - imprime no fim um resumo: por paciente, achados criados, com local (malha escolhida) e sem local por falta de malha.
4. **`--seco`**: só resolve as malhas e imprime o que faria, **sem login e sem rede** (lê só os `indice.json` e GLBs locais). Use-o para verificar tudo o que der offline.
5. Teste: `node supabase/seed_avaliacao.mjs --rodada 01 --seco` roda sem erro e imprime as 8 fichas. Não rode sem `--seco` (o revisor roda na homologação).

## Fora do escopo
Não alterar `web/`, `packages/`, migrações, `pesquisa/`. Não commitar.

## Relatório
Responder com: arquivos alterados, saída resumida do `--seco` (malha escolhida por achado e o que ficou sem local), e qualquer função do banco cuja assinatura não bateu com o `PACIENTES.md`.
