# EXP-0018 — Persistência e reprojeção de âncora anatômica 3D (`achados_real.py`)

> **REGISTRO RETROSPECTIVO** — Não houve hipótese nem critério pré-registrado no formato de `pesquisa/` antes da execução; os critérios abaixo foram tirados de `SPEC-MVP.md` (§5.4/§6) na data `2026-11-26`. Reconstruído a partir de `web/testes/achados_real.py` e commit `3e6c960`.

## 1. Identificação
- **ID:** `EXP-0018`
- **Título:** Persistência e reprojeção de âncora anatômica 3D após recarregamento
- **Data:** `2026-11-26` (registro retrospectivo)
- **Responsável:** não documentado
- **Agentes de IA:** não documentado
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** `3e6c960` (e anteriores de `web/testes/achados_real.py`)
- **Linha de pesquisa:** `LP02`
- **Situação:** `concluído`

## 2. Problema
Verificar em execução real (navegador Playwright + Supabase homologação) se um achado clínico ancorado em ponto 3D do corpo persiste no banco e é redesenhado na mesma posição espacial após recarregar a página e ser visualizado por outro profissional com vínculo ativo.

## 3. Hipótese
Não houve hipótese pré-registrada antes da execução (registro retrospectivo).

## 4. Fundamentação teórica
Persistência de `Ancora` (`atlas`, `atlas_versao`, `sistema`, `estrutura`, `malha`, `posicao_local`, `normal_local`, `triangulo`, `baricentricas`) em `jsonb` e inspeção direta das matrizes de instância (`InstancedMesh` de `SphereGeometry`) na cena Three.js via `__THREE_DEVTOOLS__`.

## 5. Materiais e ambiente
- **Datasets e versões:** paciente fictícia `Maria` (`30000000-0000-4000-8000-000000000001`), atlas servido pelo app (`127.0.0.1:3020`).
- **Licenças:** dados fictícios sintéticos.
- **Hashes:** não documentado.
- **Hardware:** não documentado.
- **Sistema operacional:** Windows.
- **Bibliotecas e versões:** Playwright Python, Chrome, Three.js / React Three Fiber.
- **Seed:** não aplicável.

## 6. Metodologia
- **Procedimentos e algoritmos:** login como `cardiologia@saude3d.invalid`, registro de achado normal (`I10`) com clique/ancoragem 3D e achado restrito (`F32.9`), leitura da posição 3D desenhada via `DESENHADOS`, recarregamento da página e verificação em `obstetricia@saude3d.invalid` com tolerância `< 1e-6` (1 micrômetro em float32) em `desenhado_em(pg, posicao)`.
- **Parâmetros:** tolerância `1e-6` m (1 µm) por coordenada.
- **Comandos para reproduzir:** `python web/testes/achados_real.py`

## 7. Critérios de sucesso (tirados da SPEC na data `2026-11-26`)
Não houve critério pré-registrado no formato de `pesquisa/`; critérios tirados de `SPEC-MVP.md` (§5.4/§6): marcador redesenhado na mesma posição (`< 1e-6` m) após recarregar, visibilidade multidisciplinar para achado normal e ocultamento de achado restrito entre unidades.

## 8. Resultados
No commit `3e6c960`, a execução contra o servidor `3020` foi reportada como aprovada (`Verificação na 3020: achados_real, gestacao_real, importacao_real, acessibilidade e homologação passam`). Saída numérica detalhada de coordenadas da rodada: `não documentado` em arquivo de log.

## 9. Validação
Teste ponta a ponta sem simulação (`web/testes/achados_real.py`) contra banco de homologação.

## 10. Limitações
Execução contra paciente fictícia única em homologação; não testa migração de âncoras entre versões geométricas distintas de atlas.

## 11. Conclusão
- **Observado:** o teste `achados_real.py` passou na verificação do commit `3e6c960`.
- **Interpretação:** a persistência e reprojeção de marcadores 3D no mesmo ponto após recarregamento e entre perfis com vínculo funcionam conforme especificado.
- **Veredito da hipótese:** `não aplicável` (registro retrospectivo sem hipótese prévia; critério da SPEC atendido)

## 12. Próximos passos
Manter execução em regressão antes de mudanças no motor anatômico.

## 13. Rastreabilidade
- **Commits:** `3e6c960`
- **Scripts:** `web/testes/achados_real.py`
- **Logs:** não documentado
- **Resultados / artefatos:** `web/testes/capturas/` (fora do git)

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** não documentado
- **Validação científica:** não documentado
- **Validação clínica:** não aplicável
