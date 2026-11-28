# EXP-0019 — Segurança de banco e API pública (RLS/PGlite e testes adversariais)

> **REGISTRO RETROSPECTIVO** — Não houve hipótese nem critério pré-registrado no formato de `pesquisa/` antes da execução; os critérios abaixo foram tirados de `SPEC-MVP.md` (§6/§12) na data `2026-11-26`. Reconstruído a partir de `supabase/testes_adversariais.mjs` e commits `ae87ef7`, `60e5eba`, `1d6033a`, `2185cc0`, `ef3aa53`.

## 1. Identificação
- **ID:** `EXP-0019`
- **Título:** Segurança de banco (RLS/PGlite) e testes adversariais pela API pública
- **Data:** `2026-11-26` (registro retrospectivo)
- **Responsável:** não documentado
- **Agentes de IA:** não documentado
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** `ae87ef7`, `60e5eba`, `1d6033a`, `2185cc0`, `ef3aa53`
- **Linha de pesquisa:** `LP05`
- **Situação:** `concluído`

## 2. Problema
Comprovar que o isolamento por unidade (RLS), sigilo de achados sensíveis, controle de acesso por vínculo ativo, bloqueio de autovinculação/escalação de papel, auditoria *append-only* e ausência de exposição via API pública PostgREST/Auth/Storage resistem a tentativas adversariais.

## 3. Hipótese
Não houve hipótese pré-registrada antes da execução (registro retrospectivo).

## 4. Fundamentação teórica
Row Level Security (RLS) no PostgreSQL/Supabase, funções `SECURITY DEFINER` com `search_path = ''`, *least privilege* (`anon` / `authenticated`) e testes adversariais de caixa-preta na API pública.

## 5. Materiais e ambiente
- **Datasets e versões:** migrações `0001_fundacao.sql` a `0007`+, dados sintéticos de homologação.
- **Licenças:** código próprio.
- **Hashes:** não documentado.
- **Hardware:** não documentado.
- **Sistema operacional:** Windows.
- **Bibliotecas e versões:** PGlite, `@supabase/supabase-js`, Node.js.
- **Seed:** dados sintéticos em `supabase/seed_homologacao.py`.

## 6. Metodologia
- **Procedimentos e algoritmos:**
  1. Suíte local em PGlite simulando papéis `authenticated` e `anon` (isolamento entre unidades, vínculo futuro/encerrado, sessão sem usuário, autovínculo, sigilo, auditoria append-only).
  2. Suíte adversarial contra a API pública de homologação (`supabase/testes_adversariais.mjs`) cobrindo `15` tabelas e `24` RPCs sob perfis anônimo e autenticados sem vínculo/permissão.
- **Parâmetros:** `169` tentativas adversariais em `testes_adversariais.mjs`; `46` testes PGlite e e2e (`2185cc0`).
- **Comandos para reproduzir:** `node supabase/testes_adversariais.mjs`

## 7. Critérios de sucesso (tirados da SPEC na data `2026-11-26`)
Não houve critério pré-registrado no formato de `pesquisa/`; critérios tirados de `SPEC-MVP.md` (§6/§12): toda tentativa adversarial deve ser negada ou devolver vazio/`null`/`false` sem vazar dados nem gravar registros; `0` *warnings* nos *advisors* do Supabase.

## 8. Resultados
- **PGlite + e2e (`2185cc0`):** **`46` testes** passaram; *advisors* da homologação passaram de `2 WARN` (`auth_rls_initplan`) para **`0 WARN` e `0 ERROR`**. Varredura `git log -p --all` (`65` commits): nenhum segredo literal.
- **Testes adversariais na API pública (`ef3aa53`):** **`169` tentativas, `0` falhas** (`cid10` e `bodysite_estrutura` são referência aberta por desenho).

## 9. Validação
Execução direta contra PGlite e contra o projeto Supabase de homologação (`ef3aa53`).

## 10. Limitações
Valor exato do limite de tentativas de login (rate limit 429) do Supabase Auth não lido via API (`3e6c960`); *pentest* externo independente em ambiente de produção não realizado.

## 11. Conclusão
- **Observado:** `46` testes PGlite/e2e passaram, *advisors* zerados e `169` tentativas adversariais na API pública resultaram em `0` falhas.
- **Interpretação:** as políticas RLS e RPCs de contrato impedem acesso indevido nos cenários testados.
- **Veredito da hipótese:** `não aplicável` (registro retrospectivo sem hipótese prévia; critérios da SPEC atendidos)

## 12. Próximos passos
Concluir revisão jurídica/encarregado de dados (RIPD) e verificar rate limit de autenticação antes do piloto.

## 13. Rastreabilidade
- **Commits:** `ae87ef7`, `60e5eba`, `1d6033a`, `2185cc0`, `ef3aa53`
- **Scripts:** `supabase/testes_adversariais.mjs`
- **Logs:** não documentado em arquivo separado
- **Resultados / artefatos:** `supabase/migrations/`

## 14. Revisão
- **Revisor:** revisão dupla (Antigravity Revisor) e consultoria externa registradas no commit `ae87ef7`
- **Revisão humana:** parcial (RIPD pendente de jurídico/encarregado em `a454727`)
- **Validação científica:** não aplicável
- **Validação clínica:** não aplicável
