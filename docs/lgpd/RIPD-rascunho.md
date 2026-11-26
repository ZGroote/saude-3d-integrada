# RIPD — piloto Saúde 3D Integrada

> **RASCUNHO técnico — não substitui avaliação jurídica nem do encarregado de dados; textos do PHÝŌ ainda não incorporados (fonte ausente)**
>
> Documento preparatório para homologação. Inventário produzido por inspeção do código e da `SPEC-MVP.md`; descreve implementação prevista/encontrada, não atesta conformidade jurídica, configuração de produção ou eficácia operacional. Escopo limitado ao piloto com dados sintéticos em homologação. Nenhum dado real foi usado nesta análise.

## 1. Identificação, escopo e situação

A SPEC exige, antes de dado real, Supabase de homologação com dados sintéticos, testes adversariais para JWT, PostgREST, RPC e Storage, RIPD e aprovação do encarregado municipal; ela esclarece que o teste PGlite cobre apenas SQL/RLS (`SPEC-MVP.md:327`). Este texto é um rascunho técnico para subsidiar essas etapas. Não encontrei no repositório documentos PHÝŌ, definição de controlador/operador, encarregado nomeado, ato municipal de instituição do piloto ou decisão de retenção.

## 2. Tratamento e dados pessoais

A aplicação prevê autenticação de profissionais e consulta/registro de prontuário por unidade; a lista abaixo é derivada das tabelas e colunas das migrações. Campos de identificação do profissional também são dados pessoais. Os dados de saúde e dados ligados à gestação/nascimento são dados pessoais sensíveis de saúde; a classificação jurídica final deve ser confirmada pelo encarregado/jurídico.

| Tabela | Colunas com dados pessoais ou clínicos | Origem |
| --- | --- | --- |
| `perfis` | `id` (referência a `auth.users`), `nome`, `unidade_id`, `especialidade`, `papel` | `supabase/migrations/0001_fundacao.sql:12-18` |
| `unidades` | `nome`, `cnes`, `municipio_ibge` (dados institucionais/localização) | `supabase/migrations/0001_fundacao.sql:5-10` |
| `pacientes` | `nome`, `cns`, `cpf_hash`, `sexo`, `data_nascimento`, `municipio_ibge` | `supabase/migrations/0001_fundacao.sql:20-28` |
| `vinculos` | `paciente_id`, `unidade_id`, `motivo`, `origem`, `criado_por`, `desde`, `ate` | `supabase/migrations/0001_fundacao.sql:30-40` |
| `achados` | `paciente_id`, `autor_id`, `unidade_id`, `especialidade`, `ancora`, `estrutura`, `cid10`, `categoria`, `lado`, `status`, `nivel_sigilo`, `inicio`, `observacao`, `substitui_id`, `origem`, `fhir_id`, `criado_em` | `supabase/migrations/0003_achados.sql:16-36` |
| `gestacoes` | `mae_id`, `dum`, `dpp`, `inicio_pre_natal`, `desfecho`, `autor_id`, `unidade_id`, `criado_em` | `supabase/migrations/0004_gestacao.sql:6-17` |
| `condicoes_gestacao` | `gestacao_id`, `cid10`, `semana`, `nivel_sigilo`, `autor_id`, `unidade_id`, `criado_em` | `supabase/migrations/0004_gestacao.sql:21-30` |
| `nascimentos` | `gestacao_id`, `crianca_id`, `data`, `peso_g`, `idade_gestacional_sem`, `apgar_5`, `autor_id`, `unidade_id`, `criado_em` | `supabase/migrations/0004_gestacao.sql:47-58` |
| `importacoes_fhir` | `autor_id`, `unidade_id`, `arquivo`, contagens, `erros`, `criado_em`, `concluido_em` | `supabase/migrations/0005_fhir.sql:3-14`; `erros` é restringido a id/motivo pela função em `supabase/migrations/0005_fhir.sql:298-307` |
| `eventos_clinicos` | `paciente_id`, `unidade_id`, `importacao_id`, `fhir_id`, `tipo`, `data`, `codigo`, `descricao`, `valor`, `criado_em` | `supabase/migrations/0005_fhir.sql:16-29` |
| `paciente_fhir` | `unidade_id`, `fhir_id`, `paciente_id`, `criado_em` | `supabase/migrations/0005_fhir.sql:33-40` |
| `auditoria` | `autor_id`, `unidade_id`, `paciente_id`, `acao`, `criado_em` | `supabase/migrations/0001_fundacao.sql:42-49`; `paciente_id` passa a aceitar nulo em `supabase/migrations/0003_achados.sql:42` |
| `cid10_sigilo` | prefixos CID e motivo/classificação para sigilo (pode revelar categorias sensíveis por associação) | `supabase/migrations/0003_achados.sql:7-14` |

`cid10`, `bodysite_estrutura` e índices anatômicos são tabelas de referência, não prontuário individual (`supabase/migrations/0002_cid10.sql:2-7`; `supabase/migrations/0005_fhir.sql:42-52`). A tabela `auth.users` pertence ao Supabase Auth; sua estrutura não é criada pelas migrações do projeto. Campos e metadados adicionais do provedor devem ser inventariados na homologação sem exportar credenciais.

### Titulares previstos

- Adultos atendidos e vinculados a uma ou mais unidades (`pacientes` e `vinculos`: `supabase/migrations/0001_fundacao.sql:20-40`).
- Gestantes ou pessoas registradas com sexo feminino, com DUM, início de pré-natal, DPP, condições e desfecho gestacional (`supabase/migrations/0004_gestacao.sql:6-30`). A implementação usa enum `sexo`; identidade de gênero não está modelada como campo.
- Crianças e recém-nascidos, vinculados à mãe por gestação/nascimento. O cadastro de nascimento cria paciente sem CNS, e há recorte gestacional pediátrico limitado (`SPEC-MVP.md:221-223`; `supabase/migrations/0004_gestacao.sql:47-58`).
- Profissionais e administradores que possuem conta, perfil, unidade e especialidade (`supabase/migrations/0001_fundacao.sql:12-18`).

## 3. Finalidade e base legal prevista

Finalidade funcional prevista: apoiar atendimento longitudinal e multidisciplinar na Atenção Primária/rede, representar achados clínicos por CID-10 e anatomia, acompanhar gestação/nascimento e importar subconjunto FHIR. A SPEC declara “base legal de tutela da saúde para o atendimento” e diz que termo e textos seriam adaptados do PHÝŌ (`SPEC-MVP.md:307`). A importação FHIR é por upload no MVP, sem conexão online à RNDS (`SPEC-MVP.md:273-284`).

A solicitação do projeto associa tutela da saúde ao art. 11, II, “f”, da LGPD e tratamento de dados de crianças/adolescentes ao art. 14. A SPEC consultada não cita esses artigos nem contém texto legal do PHÝŌ; portanto, essa associação fica **prevista para análise**, não concluída neste RIPD. A hipótese legal, melhor interesse, transparência/representação de menores, controlador, operadores e responsabilidades devem ser validados pela assessoria jurídica e pelo encarregado municipal antes de qualquer dado real.

## 4. Acesso, vínculos e sigilo

Há dois papéis de aplicação: `profissional` e `admin`. Profissional pode ver/registrar achados de pacientes vinculados à unidade; admin cadastra unidades/profissionais, importa FHIR e consulta auditoria (`SPEC-MVP.md:37-42`). O perfil guarda uma unidade (`supabase/migrations/0001_fundacao.sql:12-18`).

O acesso clínico exige vínculo ativo por unidade. A busca retorna nome, sexo, nascimento e apenas os quatro últimos dígitos do CNS; o prontuário é lido pela função `abrir_prontuario`, que confere vínculo e audita inclusive tentativas negadas (`supabase/migrations/0001_fundacao.sql:64-110`). Entretanto, a tela do prontuário renderiza `paciente.cns` sem mascaramento (`web/src/app/pacientes/[id]/page.tsx:33`). Isso é uma exposição implementada a revisar com política municipal de identificação, especialmente em tela compartilhada.

RLS está habilitada nas tabelas de negócio; acesso direto às tabelas clínicas é revogado e as operações passam por funções. Perfis têm leitura própria/da unidade e alteração por admin dentro da unidade; auditoria é consultável apenas por admin da unidade (`supabase/migrations/0001_fundacao.sql:192-215`; `supabase/migrations/0003_achados.sql:39-42`; `supabase/migrations/0004_gestacao.sql:60-62`; `supabase/migrations/0005_fhir.sql:68-75`). A lógica de consulta de achados só retorna registros normais ou restritos da própria unidade (`supabase/migrations/0003_achados.sql:152-177`).

A classificação automática de sigilo usa prefixos CID provisórios para HIV, violência, saúde mental e aborto (`supabase/migrations/0003_achados.sql:7-14`); condições gestacionais usam a mesma classificação (`supabase/migrations/0004_gestacao.sql:32-45`). A SPEC marca a lista como sujeita a revisão médica (`SPEC-MVP.md:182,328`). No recorte infantil, condições restritas de outra unidade não são exibidas; eventual alerta pediátrico de exposição vertical está pendente de decisão médica e jurídica (`SPEC-MVP.md:223-225`). Eventos FHIR não têm classificação de sigilo e permanecem visíveis apenas à própria unidade importadora conforme o contrato descrito (`SPEC-MVP.md:295-299`).

## 5. Fluxos de dados

1. **Login/sessão:** profissional envia e-mail e senha ao Supabase Auth por ação de servidor; após login é criado cookie de atividade assinado HMAC-SHA256. O código configura `httpOnly`, `sameSite=lax`, `secure` em produção e duração de 30 minutos (`web/src/app/login/actions.ts:9-35`; `web/src/lib/sessao.ts:3-38`). A senha não vai na URL (`web/src/app/login/actions.ts:15`).
2. **Busca:** profissional autenticado busca paciente por nome ou CNS; consulta restringe a pacientes com vínculo ativo e retorna CNS final com quatro dígitos (`supabase/migrations/0001_fundacao.sql:94-110`; `web/src/components/busca-pacientes.tsx:54-60`).
3. **Prontuário/achados:** abertura verifica vínculo e grava auditoria. Consultas seguintes leem achados, eventos e, conforme o caso, gestação ou recorte infantil; criação de achado usa CID-10, categoria, lateralidade, status, observação e âncora, com origem e nível de sigilo (`web/src/components/prontuario.tsx:36-44`; `web/src/app/pacientes/[id]/page.tsx:20-30`; `supabase/migrations/0003_achados.sql:92-145`).
4. **Gestação:** registro guarda DUM, DPP calculada como DUM + 280 dias, início do pré-natal, CID e semana de condições e desfecho (`supabase/migrations/0004_gestacao.sql:6-30,65-102`).
5. **Nascimento:** guarda data, peso, idade gestacional em semanas e Apgar 5; cria registro da criança sem CNS e vínculo com a unidade que registrou (`supabase/migrations/0004_gestacao.sql:47-58,129-160`; `SPEC-MVP.md:221`).
6. **Importação FHIR:** admin faz upload JSON até 10 MB, servidor valida/mapeia, mostra prévia e erros, depois grava Patient, Condition e eventos Observation/Encounter. Erros persistidos são id e motivo, e o contrato proíbe dado pessoal em logs; não há conexão direta RNDS no MVP (`SPEC-MVP.md:273-299`; `web/src/app/importar/actions.ts:9-32`; `web/src/lib/fhir/servidor.ts:1-2,46-60`).

## 6. Armazenamento e retenção

A arquitetura especifica Supabase (Postgres, Auth e Storage) e dados na região Brasil `sa-east-1`; prevê Supabase de homologação com dados sintéticos (`SPEC-MVP.md:32-35,327`). Scripts de homologação apontam para host Supabase `sa-east-1` (`supabase/seed_homologacao.py:1,15`; `supabase/limpar_testes_homologacao.py:8`). Isso é evidência de configuração/documentação do ambiente de homologação, não comprovação independente da região efetiva de todos os serviços, backups ou Storage. A escolha final de hospedagem depende do município (`SPEC-MVP.md:35,331`).

Não localizei regra de retenção, prazo de guarda, descarte de prontuário, auditoria, arquivos FHIR ou backups. As tabelas têm timestamps e funções de encerramento/estado, mas isso não define expurgo (`supabase/migrations/0001_fundacao.sql:42-49`; `supabase/migrations/0005_fhir.sql:3-14`). **Pergunta aberta:** qual tabela de temporalidade e base normativa municipal se aplicam a prontuários, importações, auditoria, logs e cópias de segurança? Como executar descarte e preservar obrigações legais sem apagar trilhas necessárias?

## 7. Medidas de segurança encontradas no código

- **RLS e menor privilégio:** RLS nas tabelas de aplicação e revogação de DML direto para tabelas clínicas; contratos SQL expõem funções específicas a autenticados (`supabase/migrations/0001_fundacao.sql:192-215`; migrações `0003_achados.sql:39-42`, `0004_gestacao.sql:60-62`, `0005_fhir.sql:68-75`).
- **RPC `SECURITY DEFINER`:** funções qualificam objetos, usam `search_path = ''`, conferem perfil/unidade/vínculo e registram ações; hardened grants/revokes também são descritos na SPEC (`supabase/migrations/0001_fundacao.sql:51-65`; `supabase/migrations/0003_achados.sql:92-117`; `supabase/migrations/0007_endurecimento.sql:27-36`; `SPEC-MVP.md:231`). A existência do padrão não substitui testes adversariais exigidos em `SPEC-MVP.md:327`.
- **Auditoria:** ações e acessos negados são registrados no servidor; leitura para admin da unidade. A SPEC prevê auditoria append-only e migração 0007 restringe a leitura por unidade, mas a homologação deve verificar privilégios efetivos e retenção (`supabase/migrations/0001_fundacao.sql:64-90,208-215`; `supabase/migrations/0007_endurecimento.sql:35-36`; `SPEC-MVP.md:231`).
- **Sessão:** validade por inatividade de 30 min, assinatura HMAC-SHA256, rejeição de timestamp futuro/assinatura inválida e falha fechada se segredo ausente (`web/src/lib/sessao.ts:3-38`; `web/src/proxy.ts:48-57,79-119`). Não registramos nem reproduzimos qualquer segredo neste documento.
- **Cabeçalhos e cache:** CSP, `nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy`, HSTS em produção e `Cache-Control: no-store, private` para rotas protegidas (`web/src/proxy.ts:18-45`).
- **CNS:** máscara parcial na lista de busca por meio de `cns_final` (últimos quatro dígitos), mas tela do prontuário exibe CNS integral (`supabase/migrations/0001_fundacao.sql:94-100`; `web/src/components/busca-pacientes.tsx:56-60`; `web/src/app/pacientes/[id]/page.tsx:33`). Não considerar o CNS globalmente mascarado.
- **Sigilo por CID:** `nivel_sigilo` calculado no servidor para achados e condições gestacionais; filtro não devolve registros restritos de outra unidade. A lista CID é provisória e depende de validação médica (`supabase/migrations/0003_achados.sql:7-14,130-145,152-177`; `supabase/migrations/0004_gestacao.sql:32-45`; `SPEC-MVP.md:328`).
- **FHIR/logs:** o módulo declara que não escreve Bundle em logs e usa mensagens de erro fixas; a função final persiste erros como id/motivo (`web/src/lib/fhir/servidor.ts:1-2`; `supabase/migrations/0005_fhir.sql:298-307`). Ainda é necessário verificar logging de infraestrutura e upload temporário na homologação.
- **Sem cache compartilhado:** a SPEC exige `dynamic`/`no-store` para páginas de prontuário (`SPEC-MVP.md:231`); proxy também põe resposta privada sem cache (`web/src/proxy.ts:44`).

## 8. Riscos, controles e ações pendentes

| Risco / impacto | Controle já encontrado | Ação antes de dado real |
| --- | --- | --- |
| Acesso indevido entre unidades ou por chamada direta | RLS, RPC com verificação de unidade/vínculo, grants limitados e auditoria | Concluir testes adversariais de JWT, PostgREST, RPC e Storage na homologação; inspecionar configuração real e revisar alertas (`SPEC-MVP.md:327,363`). |
| Exposição de CNS em ambiente compartilhado | Busca mascara parcialmente | Decidir com município se CNS completo é necessário; reduzir exposição na tela do prontuário se não for; avaliar CNS versus CPF, pergunta já aberta (`web/src/app/pacientes/[id]/page.tsx:33`; `SPEC-MVP.md:332`). |
| Erro/omissão na lista de CID sigiloso | Sigilo automático no servidor e ocultação entre unidades | Validação médica/jurídica da lista provisória; definir tratamento de exposição vertical (HIV/sífilis) com pediatria/jurídico (`SPEC-MVP.md:225,328`). |
| Reidentificação/compartilhamento indevido de eventos importados | Eventos ficam segregados por unidade no contrato; erros devem conter apenas id/motivo | Confirmar política para sigilo de Observation/Encounter e prevenir acesso/compartilhamento acidental (`SPEC-MVP.md:288,295-299`). |
| Tratamento inadequado de dados de crianças/recém-nascidos | Recorte pediátrico limitado, criança sem CNS no cadastro de nascimento | Obter avaliação jurídica do art. 14, melhor interesse, informação/representação legal e responsabilidades; textos PHÝŌ ausentes (`SPEC-MVP.md:26,221-225,307`). |
| Retenção excessiva ou descarte prematuro | Nenhuma regra de retenção encontrada | Aprovar temporalidade municipal para prontuário, auditoria, importações, logs, Storage e backups; implementar descarte e evidenciar sua execução. |
| Região ou suboperadores diferentes da expectativa | SPEC aponta `sa-east-1`; scripts indicam homologação nessa região | Verificar região efetiva de banco, Auth, Storage, backups e serviços, contratos/suboperadores e exigência municipal de hospedagem (`SPEC-MVP.md:35,331`). |
| Sessão roubada ou estação compartilhada | Cookie HttpOnly/HMAC, inatividade de 30 min, no-store | Validar renovação/encerramento, dispositivos compartilhados, logout e fluxo de incidente na homologação; revisar limite de tentativas via Auth (`SPEC-MVP.md:363`). |
| Dados pessoais em logs ou arquivo enviado | Erros sanitizados e declaração de não logging no módulo FHIR | Testar logs do Next/Supabase/proxy, upload temporário, backups e relatórios de erro com Bundle sintético; estabelecer resposta a incidente. |
| Dados incorretos por importação, com dano assistencial | Prévia, validação do subconjunto, associação por CNS e idempotência | Homologar casos adversariais/ambíguos, revisar processo de correção e atribuição de responsabilidade clínica (`SPEC-MVP.md:288-303,359-361`). |

## 9. Perguntas que dependem de decisão jurídica ou municipal

1. Quem é o controlador do piloto, quem são os operadores/suboperadores e quem foi formalmente designado encarregado? Quais instruções e contratos regem o tratamento?
2. Qual fundamento jurídico e documentação de transparência serão adotados para dados de saúde (incluindo a referência à tutela da saúde, LGPD art. 11, II, “f”) e para crianças/adolescentes (art. 14 e melhor interesse)? O PHÝŌ deve ser fornecido e revisado; não está incorporado neste repositório (`SPEC-MVP.md:26,307`).
3. Qual prazo e regra de retenção/descarte para prontuários, gestação/nascimento, importações FHIR, auditoria, logs e backups?
4. O piloto compartilhará dados com RNDS? A conexão online está fora do MVP; upload FHIR não equivale a integração com RNDS (`SPEC-MVP.md:15,273,317`). Se houver compartilhamento futuro, qual finalidade, base, contrato e minimização?
5. O município exige hospedagem própria/nuvem nacional? A região Brasil `sa-east-1` atende sua política e abrange todos os serviços/suboperadores usados (`SPEC-MVP.md:35,331`)?
6. CNS é identificador suficiente ou o município exige CPF? É necessário persistir `cpf_hash` no piloto, e o CNS completo deve aparecer no prontuário (`SPEC-MVP.md:129-132,332`; implementação: `web/src/app/pacientes/[id]/page.tsx:33`)?
7. Como classificar/compartilhar Observation e Encounter com conteúdo sensível e como tratar alerta pediátrico de exposição vertical sem revelar informação além do necessário (`SPEC-MVP.md:225,295-299`)?
8. Quem aprova a lista CID sigilosa e sua atualização, incluindo CID-10 BR, violência, saúde mental, aborto, HIV e sífilis? A SPEC registra revisão médica pendente (`SPEC-MVP.md:328`).
9. Qual processo municipal autoriza usuários, revoga acessos, responde a incidentes e revisa auditoria? Como registrar e atender direitos dos titulares/representantes?

## 10. Estado para homologação

**Não é autorização para tratar dados reais.** Conforme SPEC, permanecem pré-requisitos: ambiente de homologação com dados sintéticos, testes adversariais e aval do encarregado municipal (`SPEC-MVP.md:327`), além das revisões jurídicas/municipais acima. Este rascunho descreve apenas sinais verificáveis no repositório; não comprova configuração em nuvem, execução efetiva de controles, aprovação clínica ou conformidade legal.
