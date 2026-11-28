# EXP-0020 — Interoperabilidade: importação FHIR R4 (`importacao_real.py`)

> **REGISTRO RETROSPECTIVO** — Não houve hipótese nem critério pré-registrado no formato de `pesquisa/` antes da execução; os critérios abaixo foram tirados de `SPEC-MVP.md` (§9) na data `2026-11-26`. Reconstruído a partir de `web/testes/importacao_real.py` e commits `1d6033a`, `2a7cf0e`, `3e6c960`.

## 1. Identificação
- **ID:** `EXP-0020`
- **Título:** Validação da importação FHIR R4 ponta a ponta (`importacao_real.py`)
- **Data:** `2026-11-26` (registro retrospectivo)
- **Responsável:** não documentado
- **Agentes de IA:** não documentado
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** `1d6033a`, `2a7cf0e`, `3e6c960`
- **Linha de pesquisa:** `LP05`
- **Situação:** `concluído`

## 2. Problema
Verificar se um Bundle FHIR R4 (pacientes, condições com `bodySite` SNOMED CT e eventos clínicos) é importado de forma idempotente, restrita a administradores, com mapeamento anatômico automático no atlas e sem vazamento de identificadores em logs/console.

## 3. Hipótese
Não houve hipótese pré-registrada antes da execução (registro retrospectivo).

## 4. Fundamentação teórica
Padrão HL7 FHIR R4 (`Bundle`, `Patient`, `Condition`, `Observation`), tabela de mapeamento `bodysite_estrutura` (`supabase/dados/bodysite_snomed.csv`) e processamento transacional por RPCs no servidor.

## 5. Materiais e ambiente
- **Datasets e versões:** `web/testes/dados/bundle-sintetico-50.json` (`50` pacientes sintéticos) + Bundle com `3` recursos inválidos, mapeamentos SNOMED CT verificados (`c21721b`).
- **Licenças:** dados sintéticos; ver `supabase/dados/LEIAME_BODYSITE.md` para termos de uso do SNOMED CT em produção no Brasil.
- **Hashes:** não documentado.
- **Hardware:** não documentado.
- **Sistema operacional:** Windows.
- **Bibliotecas e versões:** Playwright Python, Next.js, Supabase.
- **Seed:** não aplicável.

## 6. Metodologia
- **Procedimentos e algoritmos:** execução real via navegador + banco de homologação (`importacao_real.py`): (1) importação de Bundle de 50 pacientes; (2) reimportação do mesmo Bundle para idempotência; (3) Bundle com 3 recursos inválidos; (4) tentativa por profissional (acesso negado) e anônimo (login); (5) checagem de ancoragem automática (`52612000` em mulher no centro de `VH_F_lumbar_vertebra_1` e código não mapeado `73780009` em "sem local no corpo"); (6) verificação de ausência de nome/CNS no console e no log do servidor (`3020`).
- **Parâmetros:** `50` pacientes sintéticos, códigos mapeados `('52612000', '80891009', '9846003')`, código fora da tabela `'73780009'`.
- **Comandos para reproduzir:** `python web/testes/importacao_real.py`

## 7. Critérios de sucesso (tirados da SPEC na data `2026-11-26`)
Não houve critério pré-registrado no formato de `pesquisa/`; critérios tirados de `SPEC-MVP.md` (§9): idempotência na reimportação, isolamento de falhas por recurso, bloqueio para não-admin, ancoragem anatômica correta por sexo/estrutura e ausência de PII em logs.

## 8. Resultados
No commit `2a7cf0e` (reconfirmado em `3e6c960`):
1. Bundle sintético de 50 pacientes: relatório **`50/50/50`**, `0` erros, banco consistente.
2. Reimportação: mesmos IDs de pacientes, achados e eventos (sem duplicação).
3. Bundle com 3 recursos inválidos: recursos válidos gravados, inválidos rejeitados com motivo explícito.
4. Profissional bloqueado (`acesso negado`); anônimo redirecionado para login.
5. Condição lombar (`52612000`) em mulher ancorada no centro de `VH_F_lumbar_vertebra_1`; código fora da tabela em `"sem local no corpo"`; eventos exibidos na linha do tempo.
6. Nenhum nome nem CNS no console do navegador nem na saída do servidor (`3020`).

## 9. Validação
**45 testes** de banco (`1d6033a`) + teste ponta a ponta real em navegador (`2a7cf0e`, `3e6c960`).

## 10. Limitações
Uso de Bundle sintético (não testado ainda com exportações reais de e-SUS APS/RNDS); uso comercial/produção de SNOMED CT no Brasil exige *Affiliate License* via MLDS (`LEIAME_BODYSITE.md`).

## 11. Conclusão
- **Observado:** os 6 cenários de `importacao_real.py` passaram contra o banco de homologação.
- **Interpretação:** o fluxo de importação FHIR R4 atende ao contrato do MVP para dados sintéticos estruturados.
- **Veredito da hipótese:** `não aplicável` (registro retrospectivo sem hipótese prévia; critérios da SPEC atendidos)

## 12. Próximos passos
Testar interoperabilidade com amostras reais anonimizadas de e-SUS/RNDS em fase piloto.

## 13. Rastreabilidade
- **Commits:** `1d6033a`, `2a7cf0e`, `3e6c960`
- **Scripts:** `web/testes/importacao_real.py`
- **Logs:** não documentado em arquivo separado
- **Resultados / artefatos:** `web/testes/dados/bundle-sintetico-50.json`, `supabase/dados/bodysite_snomed.csv`

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** não documentado
- **Validação científica:** não documentado
- **Validação clínica:** não aplicável
