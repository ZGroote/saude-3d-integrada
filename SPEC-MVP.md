# Saúde 3D Integrada — Especificação técnica do MVP

> Conceito: https://claude.ai/artifact/1JB9C9ndfDyVUbd63bemM4 · Versão 0.2 · 2026-11-25
> 0.2: atlas BodyParts3D + HRA, IDs FMA, meshopt, âncora versionada, paciente em várias unidades, auditoria desde a base.

## 1. Objetivo

Provar, num piloto municipal, que um prontuário 3D codificado:

1. reduz o tempo de anamnese na consulta;
2. é usado de fato pelos médicos;
3. mostra ao médico da criança o histórico da gestação da mãe.

O MVP é **uma aplicação web** (desktop e tablet). App de celular, integração real com a RNDS e escala nacional ficam fora (§11).

**Limite rígido:** a anatomia não cresce no MVP. Já há 2.234 malhas masculinas e 956 femininas inventariadas; o trabalho agora é o prontuário de ponta a ponta.

## 2. Ponto de partida

| Fonte | O que reaproveita | Como |
| --- | --- | --- |
| `bodyparts3d/` (este repositório) | Atlas masculino: catálogo, GLBs por sistema, visualizador de referência | Base do motor anatômico (§5) |
| `hra/` (este repositório) | Inventário do atlas feminino (HRA) | Fonte do manequim feminino (§5) |
| `teste-anatomia/` | Primeiro teste a partir de tomografia (TotalSegmentator) | Só referência; não entra no produto |
| PHÝŌ | Campos da jornada de gestação, base jurídica LGPD com dados de menores (`docs/legal/`) | Referência de modelo e textos legais; sem código no MVP |

## 3. Stack

- **Front e servidor:** Next.js 16 (App Router), React 19, TypeScript, Tailwind + shadcn.
- **3D:** three, @react-three/fiber, drei, three-mesh-bvh. GLB com compressão **meshopt**, um arquivo por sistema, carregado sob demanda.
- **Banco e auth:** Supabase (Postgres, Auth, Storage, RLS). A secret key fica só no servidor.
- **Validação:** zod em toda entrada (formulários, API, importação FHIR).
- **Testes:** Playwright (fluxos) + testes unitários das funções puras (mapeamento FHIR, reprojeção de âncora) + testes de RLS no banco.
- **Deploy:** Vercel ou hospedagem exigida pelo município. Os dados ficam em região Brasil (`sa-east-1`).

## 4. Perfis

| Perfil | Pode |
| --- | --- |
| `profissional` | Ver e registrar achados dos pacientes vinculados à sua unidade; tem `especialidade` |
| `admin` | Cadastrar unidades, profissionais, importar FHIR; vê auditoria |

## 5. Atlas anatômico

### 5.1 Atlas disponíveis

Cada atlas é um corpo de referência **independente**. Atlas diferentes nunca são fundidos nem alinhados entre si: o teste com o caso s1371 deu 36 mm de erro médio entre corpos. O que os liga é o ID de ontologia da estrutura.

| Atlas (`atlas`) | Fonte | Uso no MVP |
| --- | --- | --- |
| `bp3d-m` | BodyParts3D 4.0, homem adulto | Corpo masculino completo: 15 sistemas, 2.234 malhas |
| `hra-f` | HRA, Visible Human Female | Corpo feminino: pele, mama, reprodutor, órgãos. Esqueleto, músculos e vasos parciais |

- No feminino entra tudo o que estiver alinhado, licenciado e funcionando; a tela diz claramente o que não existe naquele atlas.
- **Camada gestacional** (placenta, âmnio, cordão): camada própria do `hra-f`, ligada só no contexto de gestação. É representação de referência, não da gestação real da paciente.
- **Infantil:** não há atlas pediátrico. Prontuário de criança no MVP é estruturado e por linha do tempo, sem corpo 3D (nunca um corpo adulto no lugar).

### 5.2 Identificadores

- **Estrutura** = ID de ontologia permanente: `FMA24475` (BodyParts3D) ou `UBERON:0002097` (HRA). Nunca o nome da malha.
- **Malha** = nome do nó no GLB (`FJ1234`, `VH_F_skin`). Pode mudar entre versões do atlas; serve só para a geometria.
- Nomes em português vêm de `nomes_pt.csv` com `validacao` (`pendente` até revisão médica; a tela avisa).
- SNOMED fica fora do MVP; entra por mapeamento, sem migrar dados.

### 5.3 Pacote de atlas (contrato de dados)

Cada atlas publicado é uma pasta versionada:

```
atlas/<atlas>/<versao>/
  manifesto.json     { atlas, versao, fonte, licenca, atribuicao, unidade:"m", eixos:"x esq. paciente, y cima, z frente", sistemas:[{id, glb, estruturas}] }
  indice.json        [{ malha, estrutura, nome_en, nome_pt, validacao, sistema, lateralidade, glb }]
  <sistema>.glb      nós nomeados pela malha (o índice é a referência dos metadados)
```

Uma versão publicada nunca é alterada; mudança de geometria gera versão nova. O pacote é gerado por script (`bodyparts3d/publicar_atlas.py`) e não vai para o git; onde ele é hospedado (pasta `public/` ou Supabase Storage) se decide na Etapa 2.

### 5.4 Contrato do motor anatômico

O motor é um módulo independente (`packages/motor-anatomico`) que **não sabe o que é paciente**. Ele recebe um atlas e marcadores, desenha, e devolve só geometria.

```ts
type Ancora = {
  atlas: string; atlas_versao: string;            // ex.: 'bp3d-m', '4.0-1'
  estrutura: string | null;                        // ID de ontologia; null = superfície livre
  malha: string;                                   // nó clicado
  posicao_local: [number, number, number];         // no espaço da malha (fonte da verdade)
  normal_local: [number, number, number];
  triangulo: number; baricentricas: [number, number, number]; // válidos só nesta atlas_versao
};
type Marcador = { id: string; ancora: Ancora; cor: string; tamanho: number };

// entradas
<MotorAnatomico atlas="bp3d-m" versao="4.0-1" sistemasVisiveis={['esqueletico']}
  marcadores={Marcador[]} selecionado={id?}
// saídas
  onEscolherPonto={(a: Ancora) => …} onSelecionarMarcador={(id: string) => …} />
```

Ao abrir uma âncora gravada noutra `atlas_versao`, o motor reprojeta `posicao_local` na malha da versão atual (ponto mais próximo) e **nunca reescreve** a âncora original.

## 6. Modelo de dados

Nomes de tabelas e colunas em português.

```sql
-- unidades de saúde (UBS, maternidade)
unidades (id, nome, cnes text unique, municipio_ibge text)

-- perfis: um por usuário do Supabase Auth
perfis (id → auth.users, nome text, unidade_id → unidades, especialidade text,
        papel enum('profissional','admin'))

pacientes (id, nome text, cns text unique, cpf_hash text unique, sexo, data_nascimento date,
           municipio_ibge text)

-- o paciente não pertence a uma unidade: é atendido por várias (UBS, especialista, maternidade)
vinculos (id, paciente_id → pacientes, unidade_id → unidades, motivo text not null,
          origem enum('atendimento','encaminhamento','importacao') not null, criado_por → perfis not null,
          desde date not null, ate date, unique (paciente_id, unidade_id, desde))
-- só o admin da unidade cria ou encerra vínculo da própria unidade; profissional nunca se autovincula

-- achado = um ponto no corpo, codificado
achados (
  id uuid pk, paciente_id → pacientes, autor_id → perfis, unidade_id → unidades, especialidade text,
  sistema text,                                    -- sistema do atlas; null = sem local no corpo
  estrutura text,                                  -- ID de ontologia (ex.: 'FMA24475'); null = superfície ou sem local
  ancora jsonb,                                    -- tipo Ancora (§5.4); null = sem local no corpo
  cid10 text,                                      -- ex.: 'I50.0'
  categoria text, lado text, status text,          -- listas fixas no código
  inicio date, observacao text,
  origem enum('manual','fhir') default 'manual', fhir_id text,
  criado_em timestamptz default now()
)
-- achados não são editados nem apagados: correção = novo achado que substitui (substitui_id → achados)

-- gestação e nascimento: o elo mãe–filho
gestacoes (id, mae_id → pacientes, dum date, dpp date, inicio_pre_natal date,
           desfecho enum('nascido_vivo','obito_fetal','aborto','em_curso'))
condicoes_gestacao (id, gestacao_id → gestacoes, cid10 text not null, semana int)
nascimentos (id, gestacao_id → gestacoes, crianca_id → pacientes unique,
             data date, peso_g int, idade_gestacional_sem int, apgar_5 int)

-- rastreio de importações
importacoes_fhir (id, autor_id, arquivo text, recursos int, erros jsonb, criado_em)

-- auditoria: toda leitura e alteração de prontuário
auditoria (id, autor_id → perfis, paciente_id → pacientes, acao text, criado_em timestamptz)
```

**Tabela de referência:** `cid10 (codigo pk, descricao)` carregada da tabela pública do DATASUS.

### RLS

- `profissional` lê e escreve `achados`, `gestacoes` e `nascimentos` só de pacientes com **vínculo ativo** (`ate is null or ate >= hoje`) com a sua unidade.
- Qualquer profissional com vínculo ativo vê **todos** os achados do paciente (é o valor multidisciplinar), mas só cria achados em nome próprio e da sua unidade.
- Toda abertura de prontuário grava em `auditoria` (no servidor, não no cliente), inclusive tentativas negadas. Nasce na Etapa 1, junto com o banco.
- **Sigilo (Etapa 3):** `achados.nivel_sigilo enum('normal','restrito')`, restrito automático por faixa de CID (HIV/Lei 14.289/2022, violência, saúde mental, aborto — lista revisada por médico). Achado restrito só aparece para a unidade autora; para as outras não vira marcador nem mostra CID. Acesso de emergência (*break-glass*) com justificativa obrigatória, auditado e revisado depois.

### Contrato do banco para o app (Etapa 1)

O app só fala com o banco por estas portas; tudo o mais é RLS.

| Porta | Faz |
| --- | --- |
| `minha_unidade() returns uuid` | Unidade do `perfis` do `auth.uid()` |
| `eh_admin() returns boolean` | Papel do usuário logado |
| `select … from pacientes` | Só devolve pacientes com vínculo ativo com `minha_unidade()` |
| `abrir_prontuario(p_paciente uuid) returns pacientes` | Confere o vínculo e grava `auditoria(acao='abrir_prontuario')`; devolve o paciente. Sem vínculo grava `auditoria(acao='acesso_negado')` e devolve `null` (sem `raise`, para a tentativa não ser desfeita) |
| `select … from auditoria` | Só `admin`, só da própria unidade |

Leitura do prontuário pelo app passa **sempre** por `abrir_prontuario`; a página nunca lê o paciente direto.

**Endurecimento obrigatório:** funções `security definer` com `search_path = ''` e nomes qualificados, dono sem `BYPASSRLS`; `revoke execute … from public, anon` e `grant` só a `authenticated`; auditoria só aceita `insert` pelas funções (append-only); páginas de prontuário sem cache compartilhado (`dynamic`, `no-store`); `service_role` nunca no app.

### Organização do repositório

| Pasta | Conteúdo |
| --- | --- |
| `supabase/migrations/` | SQL versionado (compatível com Supabase) |
| `supabase/seed.sql` | Dados fictícios da demonstração (§14) |
| `supabase/testes/` | Testes de RLS em PGlite (Postgres em Node, sem Docker), com um shim de `auth.uid()` |
| `web/` | App Next.js |
| `packages/motor-anatomico/` | Motor 3D (§5.4) |

## 7. Telas e fluxos

| Rota | Função |
| --- | --- |
| `/login` | E-mail e senha (Supabase Auth) |
| `/pacientes` | Busca por nome, CNS ou CPF; lista dos pacientes vinculados à unidade |
| `/pacientes/[id]` | **Prontuário 3D**: visualizador com seletor de sistemas, filtros (especialidade, status, período), linha do tempo lateral, lista "sem local no corpo" |
| `/pacientes/[id]/achado/novo` | Clique no corpo → formulário com busca de CID-10, categoria, lado, status, início |
| `/pacientes/[id]/gestacao` | Gestações da paciente, condições (CID-10), desfecho |
| `/pacientes/[id]/nascimento` | Registrar nascimento e criar ou vincular a criança |
| `/pacientes/[id]/familia` | Mãe e filhos vinculados, com atalho para o prontuário de cada um |
| `/admin/importar` | Upload de Bundle FHIR R4 (JSON), prévia, confirmação, relatório de erros |

### Prontuário 3D (tela central)

1. Abre no atlas do sexo da paciente (`bp3d-m` ou `hra-f`), na pele, com todos os achados ativos.
2. Ligar um sistema o deixa visível e a pele fica translúcida.
3. Cada achado é um marcador colorido pela especialidade; o tamanho indica o status.
4. Clicar no marcador abre o cartão: CID, autor, especialidade, unidade, data, observação.
5. A linha do tempo filtra o corpo pelo período escolhido.
6. Meta de desempenho: abrir o prontuário em até 3 s num tablet intermediário com 200 achados.

## 8. Pesquisa populacional

**Fora do MVP — ideia em aberto.** Nada é construído para pesquisa agora.

O MVP só garante que a porta fique aberta, sem custo extra: achados e condições da gestação já são gravados com CID-10, e mãe e filho já ficam vinculados pelo uso clínico. Se a pesquisa entrar no futuro, ela é uma camada separada e anonimizada sobre esses mesmos dados, sem migração.

## 9. Importação FHIR

Entrada: Bundle FHIR R4 em JSON. No MVP é por upload; a conexão com a RNDS fica para depois.

| Recurso FHIR | Vira |
| --- | --- |
| `Patient` | `pacientes` (CNS em `identifier`) + `vinculos` com a unidade do admin que importou |
| `Condition` com `bodySite` | `achados` com `origem='fhir'`, posicionado no centro da estrutura mapeada |
| `Condition` sem `bodySite` | `achados` com `ancora=null`, listado em "sem local no corpo" |
| `Observation`, `Encounter` | Guardados para a linha do tempo; não viram ponto no corpo |

- **Validação:** zod sobre o subconjunto de campos usado.
- **Duplicatas:** recurso com `fhir_id` já importado é ignorado.
- **Dados de teste:** gerar Bundles sintéticos (ex.: Synthea) e ajustar para CNS e CID-10. Nenhum dado real fora do piloto.

## 10. Requisitos não funcionais

- **LGPD:** base legal de tutela da saúde para o atendimento. Termo e textos adaptados do PHÝŌ.
- **Segurança:** HTTPS, RLS em todas as tabelas, secret key só no servidor, sessão expira em 30 min de inatividade.
- **Auditoria:** quem leu ou alterou cada prontuário, consultável pelo admin.
- **Acessibilidade:** tudo o que está no 3D também aparece em lista (leitor de tela, teclado).
- **Responsivo:** 1440, 820 e 390 px.
- **Licenças:** cada atlas carrega sua atribuição na tela (ver `LICENCAS.md`).

## 11. Fora do MVP

- App de celular e Meu SUS Digital.
- Integração online com RNDS, e-SUS, SINASC, SIM.
- Atlas infantil, novas malhas, exames de imagem (DICOM) e laudos.
- Igualar a cobertura do atlas feminino à do masculino.
- Código SNOMED ativo (fica o mapeamento preparado).
- Pesquisa populacional e painéis anonimizados (§8).

## 12. Riscos técnicos e perguntas abertas

- [x] ~~CC BY-SA dos modelos anatômicos~~: o BodyParts3D é CC BY 4.0 desde 27/02/2025 (só exige atribuição). Z-Anatomy (CC BY-SA) não é usado.
- [x] ~~Licença do HRA~~: united female v1.10 é CC BY 4.0, com crédito à NLM (ver `LICENCAS.md`).
- [ ] **Homologação antes de dado real:** Supabase de homologação com dados sintéticos, testes adversariais (JWT, PostgREST, RPC, Storage), RIPD e aval do encarregado de dados do município. O teste em PGlite cobre só SQL/RLS.
- [ ] **Lista de CIDs sensíveis** para o sigilo automático, revisada por médico.
- [ ] **Validação médica** dos atlas e dos 1.659 nomes em português antes do piloto.
- [ ] **Hospedagem:** o município exige servidor próprio ou nuvem nacional?
- [ ] **Identificação:** CNS sozinho basta ou precisamos de CPF?

## 13. Plano de construção

Cada etapa termina com um teste que passa.

0. **Consolidar o atlas:** SPEC 0.2, `LICENCAS.md`, pacote de atlas (§5.3) para `bp3d-m`, PR #1 aprovado. Teste: `atlas/bp3d-m/<versao>/` abre no visualizador de referência.
1. **Fundação:** Next.js + Supabase, login, perfis, unidades, pacientes, vínculos, RLS e auditoria. Teste: profissional da unidade A não lê paciente sem vínculo com A; abrir prontuário grava auditoria.
2. **Motor anatômico:** `packages/motor-anatomico` em React Three Fiber com o contrato §5.4, atlas `bp3d-m` e `hra-f`. Teste: clicar no fêmur esquerdo devolve `estrutura='FMA24475'` e uma âncora com `posicao_local`.
3. **Primeiro prontuário:** criar, gravar, reabrir e ver achados com CID-10. Teste: achado criado reaparece no mesmo ponto após recarregar.
4. **Multidisciplinaridade:** especialidades, filtros, histórico, linha do tempo. Teste: demonstração da §14 e meta de 3 s com 200 achados.
5. **Gestação e nascimento:** gestação, condições, camada gestacional, nascimento, vínculo mãe–filho. Teste: registrar nascimento cria a criança ligada à mãe.
6. **Interoperabilidade:** importação FHIR. Teste: Bundle sintético com 50 pacientes importa sem erro e sem duplicar.
7. **Preparação para piloto:** validação médica, segurança, performance, acessibilidade e usabilidade nos três tamanhos de tela.

## 14. Demonstração de referência

Paciente fictícia de 32 anos, com vínculo em três unidades:

| Especialidade | Registro |
| --- | --- |
| Cardiologia | Hipertensão, CID-10 I10, sem local no corpo |
| Ortopedia | Dor lombar, marcada na região lombar |
| Obstetrícia | Gestação em acompanhamento, com histórico pré-natal |

Passa quando os três profissionais entram cada um na sua unidade, registram o próprio achado e veem o histórico unificado dos três.
