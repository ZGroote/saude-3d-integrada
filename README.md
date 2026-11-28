# Saúde 3D Integrada

Prontuário 3D multidisciplinar e longitudinal, da gestação à vida adulta, para a Atenção Primária e a rede do SUS.

- `Saude-3D-Integrada-Conceito.pdf`: documento de conceito.
- `SPEC-MVP.md`: especificação técnica do MVP (etapas, critérios de aceite, pendências de piloto em §12).
- `supabase/`: banco (migrações `0001`–`0008`, RLS, testes PGlite em `supabase/testes/`, testes de homologação e adversariais).
- `web/`: aplicação Next.js (prontuário, achados no corpo 3D, gestação, importação FHIR); testes ponta a ponta em `web/testes/`.
- `packages/motor-anatomico/`: motor 3D (React Three Fiber).
- `bodyparts3d/` e `hra/`: preparo dos atlas — masculino `bp3d-m/4.0-1` (BodyParts3D) e feminino `hra-f/1.10-1` (HRA). Os pacotes em `atlas/` são gerados localmente e não são versionados.
- `pesquisa/`: documentação científica — índice em `pesquisa/INDICE_EXPERIMENTOS.md`, diário, hipóteses, limitações; conferência automática com `python pesquisa/verificar_documentacao.py`.
- `docs/lgpd/RIPD-rascunho.md`: rascunho técnico de RIPD.
- `teste-anatomia/`: teste inicial de geração de camadas anatômicas a partir de tomografia (veja o `LEIAME.md` de lá).

## Situação (2026-11-26)

- Etapas 0–7 do MVP implementadas e testadas tecnicamente em homologação com dados fictícios.
- **Nada aqui foi validado clinicamente nem juridicamente.** Antes de qualquer dado real faltam: validação médica (pacote em `pesquisa/validacao-medica/`), revisão jurídica do RIPD e aval do encarregado de dados, licença SNOMED CT, decisão de hospedagem e a regra de expiração por inatividade no acesso direto ao Supabase.

Os modelos em `teste-anatomia/modelos` derivam do TotalSegmentator Dataset (CC BY 4.0); crédito completo em `teste-anatomia/LEIAME.md`. Licenças dos atlas em `LICENCAS.md`.
