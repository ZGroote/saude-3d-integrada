# EXP-0028 — Avaliação de uso e utilidade percebida com médicos (dados fictícios)

## 1. Identificação
- **ID:** `EXP-0028`
- **Título:** Teste de uso moderado do prontuário 3D com médicos, sobre pacientes fictícios
- **Data:** `2026-11-27` (pré-registro)
- **Responsável:** usuário (recrutamento e condução), Claude Code (protocolo e análise)
- **Agentes de IA:** Claude Code (protocolo, roteiro, catálogo de pacientes), Codex (carga de dados fictícios)
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** a preencher
- **Linha de pesquisa:** `LP03`
- **Situação:** `planejado — aguardando participantes`

## 2. Problema
O produto foi construído e testado só por agentes de IA e testes automáticos. Ninguém da prática clínica o usou. Antes de qualquer piloto, é preciso saber se médicos conseguem usar as funções centrais sem treino e se veem utilidade no corpo 3D para entender o histórico do paciente.

## 3. Hipótese
- **H28a (uso):** médicos sem treino concluem as tarefas centrais do prontuário 3D com pacientes fictícios.
- **H28b (utilidade):** médicos percebem o corpo 3D com achados de várias unidades como útil para entender o histórico do paciente.
- **H28c (segurança de registro):** diante de uma estrutura que falta no atlas (púbis no feminino), médicos não marcam o achado num osso vizinho.

## 4. Fundamentação teórica
Teste de uso formativo com poucos participantes (5 a 8) serve para achar problemas, não para estimar proporções na população. A SUS (System Usability Scale) é um questionário de 10 itens de uso comum; 68 é o valor usualmente adotado como média de referência (referência a confirmar e registrar em `pesquisa/REFERENCIAS.md` antes da análise).

## 5. Materiais e ambiente
- **Protocolo:** `pesquisa/validacao-medica/usabilidade/ROTEIRO.md` (roteiro, tarefas T1–T11, SUS, perguntas U1–U4, entrevista).
- **Dados:** `pesquisa/validacao-medica/usabilidade/PACIENTES.md` — 10 pacientes fictícios em 5 unidades/especialidades, carregados por `supabase/seed_avaliacao.mjs --rodada NN` na homologação. Quadros redigidos com apoio de IA, **sem revisão médica**.
- **Registro:** `FICHA.csv` (tarefas) e `QUESTIONARIO.csv` (SUS e utilidade), na mesma pasta.
- **Ambiente:** app de homologação no commit vigente (registrar o hash na sessão), navegador do participante ou do moderador.
- **Ética e privacidade:** nenhum dado real de paciente. Participante identificado só por código (`P01`…); nome, CRM e contato nunca entram no repositório. Gravação só com consentimento. **Se os resultados forem publicados como pesquisa, o protocolo precisa passar antes pelo sistema CEP/Conep**; como avaliação interna de produto, confirmar com a instituição se basta o consentimento registrado. Essa decisão é humana e está pendente.

## 6. Metodologia
- **Participantes:** 5 a 8 médicos; pelo menos 2 da APS (Medicina de Família ou clínica geral) e pelo menos 1 de cada: cardiologia, ortopedia, ginecologia/obstetrícia ou pediatria (o mesmo participante pode fazer tarefas de outras contas).
- **Procedimento:** sessão individual moderada de 45–60 min, pensar em voz alta, tarefas na ordem do roteiro, sem treino prévio. Moderador só ajuda quando o participante trava; ajuda conta como "concluiu com ajuda".
- **Rodada própria por sessão:** cada sessão começa com a carga de uma rodada nova; as anteriores têm vínculos encerrados.
- **Piloto:** a primeira sessão é piloto (`P00`), serve para ajustar roteiro e quadros clínicos e **não entra na análise**. Mudanças feitas depois do piloto são registradas aqui antes da sessão P01.
- **Análise:** taxa de sucesso por tarefa (sem ajuda), SUS por participante e média, distribuição de U1–U4, lista de problemas com gravidade (crítico / grave / menor) e falas.

## 7. Critérios de sucesso (definidos antes da execução)
Com n participantes analisados (excluído o piloto):
- **C1 — uso (H28a):** nas tarefas centrais T1, T2, T3, T4 e T5, pelo menos 80% das execuções concluídas **sem ajuda** (somando as cinco tarefas).
- **C2 — usabilidade (H28a):** SUS médio ≥ 68.
- **C3 — utilidade (H28b):** em U1, pelo menos 60% dos participantes respondem 4 ou 5.
- **C4 — segurança (H28c):** em T6, nenhum participante ancora a fratura do púbis no ílio ou no sacro como se fosse o púbis.
- **C5 — falhas críticas:** zero falhas críticas (lado trocado, paciente errado, estrutura incompatível com o diagnóstico, sigilo exposto) em todas as tarefas. Cada falha crítica vira problema obrigatório a corrigir antes do piloto clínico, independentemente dos outros critérios.

Veredito: H28a sustentada se C1 e C2; H28b se C3; H28c se C4. Com menos de 5 participantes analisados, o experimento fica **inconclusivo** e os dados viram só lista de problemas.

**Adendo 1 (2026-11-27, antes de qualquer sessão, inclusive o piloto):** acrescentados a família P09/P10 (HIV na gestação, O98.7 restrita) e a tarefa T11, por pedido do usuário. T11 é **só observacional**: não entra em C1–C4 e nenhum critério foi alterado. Vale para C5 apenas se O98.7 aparecer na conta da Pediatria. Se a Pediatria concluir "nada relevante" a partir de "Nenhuma condição disponível", isso entra na lista de problemas como problema de desenho do produto (gravidade decidida na análise), não como falha crítica.

**Regra de parada:** se as 2 primeiras sessões (após o piloto) tiverem a mesma falha crítica, interromper, corrigir o produto, registrar a mudança e recomeçar a contagem.

## 8. Resultados
A preencher.

## 9. Validação
A preencher.

## 10. Limitações
- Amostra pequena e por conveniência; resultados formativos.
- Pacientes e cenários fictícios; o comportamento numa consulta real pode diferir.
- Quadros clínicos redigidos com apoio de IA; revisão médica prevista só no piloto.
- Moderador ligado ao projeto (viés de cortesia do participante).
- SUS em tradução de trabalho, se não houver versão validada à mão.

## 11. Conclusão
- **Observado:** a preencher
- **Interpretação:** a preencher
- **Veredito da hipótese:** `em aberto`

## 12. Próximos passos
Recrutar participantes (humano), decidir a questão ética (humano), rodar o piloto P00.

## 13. Rastreabilidade
- **Commits:** a preencher
- **Scripts:** `supabase/seed_avaliacao.mjs`
- **Logs:** `pesquisa/resultados/EXP-0028/`
- **Resultados / artefatos:** `pesquisa/resultados/EXP-0028/sessao-PNN.{csv,md}`

## 14. Revisão
- **Revisor:** Claude Code
- **Revisão humana:** pendente
- **Validação científica:** não realizada
