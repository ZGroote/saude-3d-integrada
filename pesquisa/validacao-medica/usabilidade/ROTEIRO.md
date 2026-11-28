# Roteiro — sessão de avaliação com médicos (EXP-0028)

Sessão individual e moderada, de 45 a 60 minutos, presencial ou por vídeo com tela compartilhada. **Só dados fictícios** (`PACIENTES.md`). Isto é teste de uso e de utilidade percebida, **não** validação clínica.

## Antes da sessão (moderador)
1. Rodar a carga da rodada: `node supabase/seed_avaliacao.mjs --rodada NN` (NN = número da sessão). Conferir o resumo impresso.
2. Abrir o link do app num navegador limpo (janela anônima). Ter à mão as senhas de `supabase/.env.demo` (nunca mostrar ao participante nem gravar na tela).
3. Preparar a ficha `FICHA.csv` (uma linha por tarefa) e o cronômetro.
4. Código do participante: `P01`, `P02`… Nunca anotar nome, CRM ou instituição na ficha; se for preciso contatar de novo, a lista código→contato fica fora do repositório.

## Abertura (5 min)
Ler em voz alta:

> "Obrigado por participar. Estamos testando um protótipo de prontuário com um corpo 3D. Quem está sendo avaliado é o sistema, não você: se algo for difícil, isso é informação útil para nós. Todos os pacientes são inventados. Peço que pense em voz alta enquanto usa: diga o que está procurando, o que espera que aconteça e o que te surpreende. Vou evitar ajudar para ver onde o sistema confunde; se você travar, eu ajudo. Você pode parar a qualquer momento. Posso gravar a tela e o áudio só para nossa análise?"

Registrar o consentimento verbal (e o escrito, se houver termo — ver EXP-0028 §5). Sem consentimento para gravar: só anotações.

## Perfil (3 min, sem identificar)
- Especialidade e tempo de prática (faixas: < 5, 5–15, > 15 anos).
- Onde atende (APS, ambulatório, hospital) e qual prontuário eletrônico usa hoje.
- Com que frequência precisa de informação de outra unidade sobre o mesmo paciente (nunca / às vezes / quase sempre).

## Tarefas (30–35 min)
Ler cada tarefa como está. Não dizer o nome de botões. Anotar: concluiu sem ajuda / concluiu com ajuda / não concluiu; tempo; erros; falas marcantes.

| # | Conta usada | Tarefa (lida ao participante) | Sucesso quando |
|---|---|---|---|
| T1 | Medicina de Família | "Encontre a paciente Ana Lima e diga quais problemas de saúde ela tem hoje." | Cita os achados **ativos** (HAS, FA, DM2, gonartrose) e não cita a pneumonia como atual |
| T2 | Medicina de Família | "Algum desses problemas foi registrado por outra unidade? Qual e por quem?" | Identifica HAS e FA como da Cardiologia |
| T3 | Ortopedia | "O paciente José Pereira voltou com dor no ombro esquerdo. Registre isso no prontuário, no lugar certo do corpo." | Achado salvo com local no ombro/estrutura do ombro **esquerdo**, lado esquerdo, CID compatível (ex.: M25.5/M75.x) |
| T4 | Medicina de Família | "Registre para a Ana Lima que ela tem dislipidemia." | Achado salvo **sem local** (E78.x) |
| T5 | Ortopedia | "No Pedro Alves, o diagnóstico do joelho mudou ao longo do tempo. Mostre como ele evoluiu." | Encontra a correção (M25.5 → M23.2) e o histórico de versões |
| T6 | Medicina de Família | "A Ana Lima caiu e fez fratura do ramo do púbis. Registre." | Lê o aviso de lacuna e registra **sem local** (ou com observação). **Falha crítica** se ancorar no ílio/sacro como se fosse o púbis |
| T7 | Ortopedia | "Mostre a lombalgia do José olhando o corpo por trás e deixe essa vista salva junto do achado que você registrar." | Usa vista posterior; ao reabrir o achado, a vista volta |
| T8 | Obstetrícia, depois Pediatria | "Quantas semanas de gestação tem a Carla Mendes e que condições ela tem nesta gestação?" Depois, na Pediatria: "O Davi Santos teve algo importante na gestação da mãe?" | 24 semanas e diabetes gestacional; depois, hipertensão gestacional da mãe visto a partir da criança |
| T9 | Obstetrícia, depois Medicina de Família | "Liste tudo o que a Lúcia Rocha tem." (nas duas contas) | Nota que a ansiedade (F41.1) aparece para uma e não para a outra; pedir que comente |
| T11 | Pediatria, depois Obstetrícia | "O Lucas Oliveira nasceu há 12 dias e veio para a primeira consulta. Há algo na gestação da mãe que mude a sua conduta?" Depois que responder, o moderador conta: "A mãe tem HIV registrado pela Maternidade; o sistema esconde isso de outras unidades." Na Obstetrícia, mostrar o mesmo histórico com O98.7. | Sem critério de acerto (observação). Anotar: se concluiu "nada relevante" a partir de "Nenhuma condição disponível", se desconfiou da mensagem, e a opinião sobre quem deveria ver. **Falha crítica** só se O98.7 aparecer na conta da Pediatria |
| T10 | qualquer | "Explore livremente por 3 minutos o que achar interessante no corpo 3D." | Sem critério; anotar o que usa e o que comenta |

Após T6 e T9, perguntar: "O que você entendeu dessa mensagem/desse comportamento? Faz sentido para a sua prática?"

T11 vem antes de T10 (a exploração livre fecha as tarefas). Após T11, perguntar: "A Pediatria deveria ver essa condição? Sempre, com consentimento da mãe, só como alerta sem o diagnóstico, ou nunca?" Anotar a resposta literal. Não defender a regra atual.

**Falha crítica** (registrar à parte, independentemente do sucesso): lado trocado, paciente errado, achado gravado em estrutura que não corresponde ao diagnóstico, ou informação sigilosa exposta indevidamente.

## Questionário (7 min)
1. **SUS (System Usability Scale)**, 10 itens, escala 1–5. Usar uma versão em português já validada; se não houver uma à mão, aplicar a tradução de trabalho abaixo e registrar isso como limitação.
   1. Eu acho que gostaria de usar este sistema com frequência.
   2. Achei o sistema desnecessariamente complexo.
   3. Achei o sistema fácil de usar.
   4. Acho que precisaria da ajuda de um técnico para conseguir usar este sistema.
   5. Achei que as funções do sistema estão bem integradas.
   6. Achei que o sistema tem muitas inconsistências.
   7. Imagino que a maioria das pessoas aprenderia a usar este sistema rapidamente.
   8. Achei o sistema muito complicado de usar.
   9. Eu me senti confiante ao usar o sistema.
   10. Precisei aprender muitas coisas antes de conseguir usar o sistema.
   Pontuação: itens ímpares (nota − 1), itens pares (5 − nota); soma × 2,5 → 0 a 100.
2. **Utilidade** (1 = discordo totalmente … 5 = concordo totalmente):
   - U1. "Ver os achados no corpo me ajudaria a entender o histórico do paciente mais rápido do que a lista que uso hoje."
   - U2. "Ver o que outras unidades registraram no mesmo paciente mudaria minha conduta em alguns casos."
   - U3. "Eu confiaria no local do corpo marcado por outro profissional."
   - U4. "Registrar um achado aqui leva um tempo aceitável numa consulta."

## Entrevista final (8 min)
- O que foi mais útil? E o que atrapalhou?
- Em que tipo de consulta você usaria isso? Em qual não usaria?
- O que falta para você usar com pacientes reais?
- Algo no corpo 3D pareceu errado anatomicamente ou com nome estranho? (anotar estrutura e nome)
- O tabagismo do José ficou restrito (regra "todo F é sigiloso"). Isso faz sentido?

## Depois da sessão
1. Conferir a ficha, calcular o SUS e transcrever falas relevantes **sem identificar** o participante.
2. Salvar em `pesquisa/resultados/EXP-0028/sessao-PNN.csv` (ficha) e `sessao-PNN.md` (notas). Gravações ficam fora do repositório.
3. Se o participante digitou qualquer dado real, apagar a rodada inteira daquele achado e registrar o incidente.
