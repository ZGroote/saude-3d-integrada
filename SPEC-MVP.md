# Saúde 3D Integrada — Especificação técnica do MVP

> Conceito: https://claude.ai/artifact/1JB9C9ndfDyVUbd63bemM4 · Versão 0.1 · 2026-11-24

## 1. Objetivo

Provar, num piloto municipal, que um prontuário 3D codificado:

1. reduz o tempo de anamnese na consulta;
2. é usado de fato pelos médicos;
3. mostra ao médico da criança o histórico da gestação da mãe.

O MVP é **uma aplicação web** (desktop e tablet). App de celular, integração real com a RNDS e escala nacional ficam fora (§11).

## 2. Ponto de partida

| Fonte | O que reaproveita | Como |
| --- | --- | --- |
| `teste-anatomia/` (este repositório) | Geração das camadas internas a partir de tomografia | Base do pipeline de modelos |
| PHÝŌ | Campos da jornada de gestação, base jurídica LGPD com dados de menores (`docs/legal/`) | Referência de modelo e textos legais; sem código no MVP |

## 3. Stack

- **Front e servidor:** Next.js 16 (App Router), React 19, TypeScript, Tailwind + shadcn.
- **3D:** three, @react-three/fiber, drei, three-mesh-bvh. Modelos em GLB com compressão Draco, carregados por camada sob demanda.
- **Banco e auth:** Supabase (Postgres, Auth, Storage, RLS). A secret key fica só no servidor.
- **Validação:** zod em toda entrada (formulários, API, importação FHIR).
- **Testes:** Playwright (fluxos) + testes unitários das funções puras (mapeamento FHIR).
- **Deploy:** Vercel ou hospedagem exigida pelo município. Os dados ficam em região Brasil (`sa-east-1`).

## 4. Perfis

| Perfil | Pode |
| --- | --- |
| `profissional` | Ver e registrar achados dos pacientes da sua unidade; tem `especialidade` |
| `admin` | Cadastrar unidades, profissionais, importar FHIR; vê auditoria |

## 5. Camadas anatômicas

Cada camada é um GLB separado, alinhado ao mesmo esqueleto e escala do manequim base (masculino e feminino).

| Camada (`camada`) | Conteúdo do GLB | Prioridade no MVP |
| --- | --- | --- |
| `pele` | Manequim base | MVP |
| `musculos` | Músculos principais | MVP |
| `ossos` | Esqueleto e articulações | MVP |
| `coracao` | Coração com câmaras e valvas | MVP |
| `vasos` | Artérias e veias principais | MVP |
| `orgaos` | Órgãos torácicos e abdominais | Depois do MVP |

**Nomeação das malhas = chave do dado.** Cada malha interna se chama por um código interno estável (`ventriculo_esquerdo`, `femur_d`). Um arquivo `public/modelos/estruturas.json` mapeia:

```json
{ "ventriculo_esquerdo": { "camada": "coracao", "rotulo": "Ventrículo esquerdo", "snomed": null, "lado": "esquerdo" } }
```

O campo `snomed` fica `null` no MVP. O dado nasce com o código interno, e o SNOMED só entra se um dia houver integração que o exija, por mapeamento e sem migrar dados.

**Fonte dos modelos:** Z-Anatomy ou BodyParts3D, reprocessados no pipeline Blender para casar com o manequim. Os dois são CC BY-SA (ver §12).

## 6. Modelo de dados

Nomes de tabelas e colunas em português.

```sql
-- unidades de saúde (UBS, maternidade)
unidades (id, nome, cnes text unique, municipio_ibge text)

-- perfis: um por usuário do Supabase Auth
perfis (id → auth.users, nome text, unidade_id → unidades, especialidade text,
        papel enum('profissional','admin'))

pacientes (id, nome text, cns text unique, cpf_hash text unique, sexo, data_nascimento date,
           unidade_id → unidades, municipio_ibge text)

-- achado = um ponto no corpo, codificado
achados (
  id uuid pk, paciente_id → pacientes, autor_id → perfis, especialidade text,
  camada text not null, estrutura text,            -- chave do estruturas.json; null = pele livre
  ancora jsonb not null,                           -- { personagem, camada, malha, triangulo, baricentricas, posicao, normal }
  cid10 text,                                      -- ex.: 'I50.0'
  categoria text, lado text, status text,          -- listas fixas no código
  inicio date, observacao text,
  origem enum('manual','fhir') default 'manual', fhir_id text,
  criado_em timestamptz default now()
)

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

- `profissional` lê e escreve `achados`, `gestacoes` e `nascimentos` só de pacientes com `unidade_id` igual à sua.
- Toda abertura de prontuário grava em `auditoria` (no servidor, não no cliente).

## 7. Telas e fluxos

| Rota | Função |
| --- | --- |
| `/login` | E-mail e senha (Supabase Auth) |
| `/pacientes` | Busca por nome, CNS ou CPF; lista da unidade |
| `/pacientes/[id]` | **Prontuário 3D**: visualizador com seletor de camadas, filtros (especialidade, status, período), linha do tempo lateral, lista "sem local no corpo" |
| `/pacientes/[id]/achado/novo` | Clique no corpo → formulário com busca de CID-10, categoria, lado, status, início |
| `/pacientes/[id]/gestacao` | Gestações da paciente, condições (CID-10), desfecho |
| `/pacientes/[id]/nascimento` | Registrar nascimento e criar ou vincular a criança |
| `/pacientes/[id]/familia` | Mãe e filhos vinculados, com atalho para o prontuário de cada um |
| `/admin/importar` | Upload de Bundle FHIR R4 (JSON), prévia, confirmação, relatório de erros |

### Prontuário 3D (tela central)

1. Abre na camada `pele` com todos os achados ativos.
2. Ligar uma camada a deixa visível e a pele fica translúcida.
3. Cada achado é um marcador colorido pela especialidade; o tamanho indica o status.
4. Clicar no marcador abre o cartão: CID, autor, especialidade, data, observação.
5. A linha do tempo filtra o corpo pelo período escolhido.
6. Meta de desempenho: abrir o prontuário em até 3 s num tablet intermediário com 200 achados.

## 8. Pesquisa populacional

**Fora do MVP — ideia em aberto.** Nada é construído para pesquisa agora.

O MVP só garante que a porta fique aberta, sem custo extra: achados e condições da gestação já são gravados com CID-10, e mãe e filho já ficam vinculados pelo uso clínico. Se a pesquisa entrar no futuro, ela é uma camada separada e anonimizada sobre esses mesmos dados, sem migração.

## 9. Importação FHIR

Entrada: Bundle FHIR R4 em JSON. No MVP é por upload; a conexão com a RNDS fica para depois.

| Recurso FHIR | Vira |
| --- | --- |
| `Patient` | `pacientes` (CNS em `identifier`) |
| `Condition` com `bodySite` | `achados` com `origem='fhir'`, posicionado no centro da estrutura mapeada |
| `Condition` sem `bodySite` | `achados` com `camada='pele'`, `estrutura=null`, listado em "sem local no corpo" |
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

## 11. Fora do MVP

- App de celular e Meu SUS Digital.
- Integração online com RNDS, e-SUS, SINASC, SIM.
- Camada `orgaos`, exames de imagem (DICOM) e laudos.
- Código SNOMED ativo (fica o mapeamento preparado).
- Pesquisa populacional e painéis anonimizados (§8).

## 12. Riscos técnicos e perguntas abertas

- [ ] **CC BY-SA dos modelos anatômicos:** os derivados precisam manter a licença. Confirmar se isso afeta a venda ou o código do produto.
- [ ] **Validação médica** de cada camada antes do piloto.
- [ ] **Hospedagem:** o município exige servidor próprio ou nuvem nacional?
- [ ] **Identificação:** CNS sozinho basta ou precisamos de CPF?

## 13. Plano de construção

Cada etapa termina com um teste que passa.

1. **Base:** projeto Next.js + Supabase, login, perfis e unidades. Teste: login por perfil e RLS por unidade.
2. **Achados codificados:** tabela `achados`, CID-10 carregado, formulário com busca. Teste: criar achado na pele com CID e vê-lo após recarregar.
3. **Camadas:** gerar no Blender e carregar `musculos`, `ossos`, `coracao`, `vasos`; `estruturas.json`. Teste: clicar no ventrículo esquerdo grava `estrutura='ventriculo_esquerdo'`.
4. **Prontuário 3D completo:** filtros, linha do tempo, lista "sem local". Teste: meta de 3 s com 200 achados.
5. **Mãe–filho:** gestação, condições, nascimento, vínculo. Teste: registrar nascimento cria a criança ligada à mãe.
6. **Importação FHIR:** upload, prévia, mapeamento. Teste: Bundle sintético com 50 pacientes importa sem erro e sem duplicar.
7. **Endurecimento:** auditoria de leitura, sessão, acessibilidade, testes nos três tamanhos de tela.
