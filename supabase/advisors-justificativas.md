# Advisors do Supabase — Etapa 7

Rodado na homologação em 2026-11-26, antes e depois da `0007_endurecimento.sql` (saída em `advisors-etapa7.txt`).

| Antes da 0007 | Depois |
| --- | --- |
| 2 WARN `auth_rls_initplan` (políticas de `perfis`) | 0 WARN, 0 ERROR |

A 0007 trocou `auth.uid()`/`minha_unidade()`/`eh_admin()` por `(SELECT …)` nas políticas (mesma lógica, avaliada uma vez por consulta) e criou índices nas chaves estrangeiras.

## INFO mantidos, com justificativa

- **`rls_enabled_no_policy`** (achados, cid10_sigilo, condicoes_gestacao, eventos_clinicos, gestacoes, importacoes_fhir, nascimentos, paciente_fhir, pacientes, vinculos): intencional. Essas tabelas não têm acesso direto; tudo passa por funções `security definer` que conferem vínculo, papel e sigilo. Sem política = negado por padrão.
- **`unused_index`** (25): os índices da 0007 acabaram de ser criados e a homologação tem pouco volume; reavaliar com dados do piloto.
