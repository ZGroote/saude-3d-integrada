# Documentação Científica — Saúde 3D Integrada

Este diretório reúne a documentação científica paralela ao desenvolvimento da plataforma **Saúde 3D Integrada**, garantindo rastreabilidade, reprodutibilidade, preservação integral de resultados (inclusive negativos) e base documental para futura parceria acadêmica (UFSCar). A especificação de produto permanece em `../SPEC-MVP.md`; aqui registra-se **como** os resultados técnicos e anatômicos foram obtidos e com que evidência.

> **Distinção obrigatória:** validação técnica/experimental (testes automatizados, métricas geométricas, PGlite/adversarial) **não equivale** a validação clínica nem jurídica. Nenhuma funcionalidade está validada clinicamente nem juridicamente até avaliação pelos respectivos responsáveis.

## Estado atual (2026-11-26)
- **Atlas do MVP:** masculino `bp3d-m/4.0-1` (2.234 malhas) e feminino `hra-f/1.10-1` (956 malhas). As linhas experimentais de reconstrução/integração feminina (`EXP-0015` `vhf-f/0.1-0` e `EXP-0016` `hib-f/0.1-0`) foram encerradas/congeladas sem aceitação (`c1ad34a`), permanecendo apenas como rascunhos locais não versionados.
- **Experimentos registrados:** `EXP-0001` a `EXP-0020` (ver [INDICE_EXPERIMENTOS.md](./INDICE_EXPERIMENTOS.md)), sendo `EXP-0001`–`0011` e `EXP-0017`–`0020` registros retrospectivos.
- **Pendências humanas:** validação médica (nomes PT-BR, lista de sigilo CID-10, mapa `bodySite`, regras clínicas), revisão jurídica do RIPD e aval do encarregado de dados, licença SNOMED CT em produção, decisão de hospedagem e expiração por inatividade com acesso direto ao Supabase.

## Linhas de Pesquisa

- **LP01 — Modelagem anatômica computacional:** reconstrução tomográfica, segmentação, ICP (Iterative Closest Point), integração de malhas e validação geométrica.
- **LP02 — Computação gráfica aplicada à saúde:** compressão, desempenho em navegador, seleção anatômica, persistência e reprojeção de marcadores.
- **LP03 — Aplicabilidade clínica:** eficiência da anamnese, compreensão de históricos clínicos e comunicação multidisciplinar.
- **LP04 — Saúde materno-infantil:** histórico gestacional e acompanhamento longitudinal.
- **LP05 — Saúde digital e interoperabilidade:** prontuário eletrônico, segurança, governança, FHIR e integração ao SUS.

## Estrutura do diretório

| Pasta / Arquivo | Finalidade |
|---|---|
| `README.md` | Apresentação, estado atual, objetivos científicos e linhas de pesquisa |
| `INDICE_EXPERIMENTOS.md` | Índice mestre de todos os `EXP-XXXX`, situação, evidências e rastreabilidade |
| `verificar_documentacao.py` | Verificador automático de consistência, links, encoding e seções |
| `METODOLOGIA.md` | Fluxo científico padrão adotado em todo experimento |
| `DIARIO.md` | Histórico cronológico das atividades experimentais |
| `HIPOTESES.md` | Registro consolidado das hipóteses e sua situação atual |
| `REFERENCIAS.md` | Referências bibliográficas e fontes citadas no repositório |
| `experimentos/` | Fichas individuais `EXP-XXXX` |
| `resultados/` | Sínteses, tabelas comparativas e inventário de artefatos não versionados |
| `protocolos/` | Protocolos operacionais reutilizáveis |
| `datasets/` | Fichas técnicas de origem, versão, licença e hashes das fontes |
| `limitacoes/` | Limitações técnicas, anatômicas e clínicas conhecidas |
| `publicacoes/` | Rascunhos de artigos, resumos e submissões acadêmicas |
| `templates/` | Modelos padronizados de registro (ex.: `EXPERIMENTO.md`) |
