# Documentação Científica — Saúde 3D Integrada

Este diretório reúne a documentação científica paralela ao desenvolvimento da plataforma **Saúde 3D Integrada**, garantindo rastreabilidade, reprodutibilidade, preservação integral de resultados (inclusive negativos) e base documental para futura parceria acadêmica (UFSCar). A especificação de produto permanece em `../SPEC-MVP.md`; aqui registra-se **como** os resultados técnicos e anatômicos foram obtidos e com que evidência.

## Linhas de Pesquisa

- **LP01 — Modelagem anatômica computacional:** reconstrução tomográfica, segmentação, ICP (Iterative Closest Point), integração de malhas e validação geométrica.
- **LP02 — Computação gráfica aplicada à saúde:** compressão, desempenho em navegador, seleção anatômica, persistência e reprojeção de marcadores.
- **LP03 — Aplicabilidade clínica:** eficiência da anamnese, compreensão de históricos clínicos e comunicação multidisciplinar.
- **LP04 — Saúde materno-infantil:** histórico gestacional e acompanhamento longitudinal.
- **LP05 — Saúde digital e interoperabilidade:** prontuário eletrônico, segurança, governança, FHIR e integração ao SUS.

## Estrutura do diretório

| Pasta / Arquivo | Finalidade |
|---|---|
| `README.md` | Apresentação, objetivos científicos e linhas de pesquisa |
| `METODOLOGIA.md` | Fluxo científico padrão adotado em todo experimento |
| `DIARIO.md` | Histórico cronológico das atividades experimentais |
| `HIPOTESES.md` | Registro consolidado das hipóteses e sua situação atual |
| `REFERENCIAS.md` | Referências bibliográficas e fontes citadas no repositório |
| `experimentos/` | Fichas individuais `EXP-XXXX` |
| `resultados/` | Sínteses, tabelas comparativas e artefatos de saída |
| `protocolos/` | Protocolos operacionais reutilizáveis |
| `datasets/` | Fichas técnicas de origem, versão, licença e hashes das fontes |
| `limitacoes/` | Limitações técnicas, anatômicas e clínicas conhecidas |
| `publicacoes/` | Rascunhos de artigos, resumos e submissões acadêmicas |
| `templates/` | Modelos padronizados de registro (ex.: `EXPERIMENTO.md`) |
