# Saúde 3D Integrada — Especificação técnica do MVP

> Conceito: https://claude.ai/artifact/1JB9C9ndfDyVUbd63bemM4 · Versão 0.2 · 2026-11-25
> **SPEC congelada na 0.2** — mudanças daqui em diante entram como critério de aceite da etapa, não como seção nova.
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
  - **Lacunas conhecidas** ficam em `web/src/lib/lacunas.ts` por `atlas/versao`. No `hra-f/1.10-1`: púbis, ísquio e acetábulo (pelve só com ílios e sacro, `EXP-0024`). A busca de estrutura avisa quando o termo é uma lacuna (registrar sem local, citar na observação, não marcar no osso vizinho) e o corpo mostra "Faltam neste corpo: …". Nome de exibição pode ser corrigido por malha no app (ex.: ílio do `hra-f`, que vem como tecido ósseo); a âncora e o ID de ontologia não mudam.
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

Uma versão publicada nunca é alterada; mudança de geometria gera versão nova.

**Versão leve (LOD):** cada sistema pode trazer `glb_leve` no manifesto (`sistemas:[{id, glb, glb_leve?, estruturas}]`), com as mesmas malhas simplificadas e os mesmos nomes de nó. O motor abre pelo leve e troca pelo completo quando o sistema é selecionado ou ampliado. A âncora continua no espaço do atlas e vale para as duas versões. Simplificação só onde não destrói anatomia: pele e grandes superfícies sim; vasos, nervos e estruturas finas não. O pacote é gerado por script (`bodyparts3d/publicar_atlas.py`) e não vai para o git; onde ele é hospedado (pasta `public/` ou Supabase Storage) se decide na Etapa 2.

### 5.4 Contrato do motor anatômico

O motor é um módulo independente (`packages/motor-anatomico`) que **não sabe o que é paciente**. Ele recebe um atlas e marcadores, desenha, e devolve só geometria.

```ts
type Ancora = {
  atlas: string; atlas_versao: string;            // ex.: 'bp3d-m', '4.0-1'
  sistema: string;                                 // do indice.json
  estrutura: string | null;                        // ID de ontologia; null = malha sem ID (17 no bp3d-m)
  malha: string;                                   // nó clicado
  // geometria: null numa âncora só estrutural (ex.: importação FHIR, sem clique)
  posicao_local: [number, number, number] | null;  // no espaço da malha (fonte da verdade)
  normal_local: [number, number, number] | null;
  triangulo: number | null; baricentricas: [number, number, number] | null; // válidos só nesta atlas_versao
};
type Marcador = { id: string; ancora: Ancora; cor: string; tamanho: number };

// entradas
<MotorAnatomico atlas="bp3d-m" versao="4.0-1" sistemasVisiveis={['esqueletico']}
  marcadores={Marcador[]} selecionado={id?}
// saídas
  onEscolherPonto={(a: Ancora) => …} onSelecionarMarcador={(id: string) => …} />
```

Ao abrir uma âncora gravada noutra `atlas_versao`, o motor reprojeta `posicao_local` na malha da versão atual (ponto mais próximo) e **nunca reescreve** a âncora original.

**Âncora só estrutural** (sem `posicao_local`): o motor desenha o marcador no centro da caixa da malha indicada. Quando uma estrutura tem várias malhas (559 no `bp3d-m`), quem monta a âncora escolhe a malha de mais triângulos e, no empate, o menor nome de malha — função `malhaPrincipal` do pacote `@saude3d/motor-anatomico/indice`, a mesma no servidor e no cliente (o `indice.json` traz `triangulos`).

**Carregamento:** `marcadoresPendentes` (opcional) diz ao motor que a lista de marcadores ainda vai chegar; ele desenha os marcadores antes de baixar o GLB do corpo, abre pelo `glb_leve` quando existir, baixa o completo em segundo plano depois que o corpo aparece e monta a estrutura de clique (BVH) após o primeiro desenho.

**Unidades:** `posicao_local` em metros nos eixos do atlas (nunca nas coordenadas quantizadas do GLB); `Marcador.tamanho` é raio em metros. O motor carrega, sem mostrar, os sistemas de que os marcadores precisam e avisa por `onMarcadoresSemPosicao(ids)` os que não conseguiu posicionar.

**Versão publicada** = enviada à hospedagem do app. Antes disso a versão é local e pode ser reconstruída.

**Lado:** `lateralidade` do índice (`left`/`right`/`null`) vira `achados.lado` (`esquerdo`/`direito`/`nao_se_aplica`).

**Câmera e visibilidade (Leva A):** `NomeVista`, `VistaCamera` e `ComandoCamera` permitem vistas anatômicas, enquadrar/focar/restaurar e reportar a câmera; `seq` evita executar o mesmo comando duas vezes. Props opcionais `ocultas`, `isoladas`, `transparencia`, `camadasRemovidas`/`onCamadas` controlam malhas sem alterar âncoras ou o carregamento necessário a marcadores. Selecionar um marcador centraliza a câmera respeitando movimento reduzido.

**Camadas musculares:** aproximação por profundidade do centro de cada malha muscular à pele, agrupada em até dez faixas por quantis; camadas superficiais podem ser removidas da visualização. Não representa planos anatômicos validados.

## 6. Modelo de dados

Nomes de tabelas e colunas em português.

```sql
-- unidades de saúde (UBS, maternidade)
unidades (id, nome, cnes text unique, municipio_ibge text)

-- perfis: um por usuário do Supabase Auth
perfis (id → auth.users, nome text, unidade_id → unidades, especialidade text,
        papel enum('profissional','admin'))

pacientes (id, nome text, cns text unique, cpf_hash text unique, sexo enum('feminino','masculino','indeterminado'),
           data_nascimento date, municipio_ibge text)
-- cpf_hash = HMAC-SHA256 com segredo do servidor (CPF tem poucos dígitos: hash puro é reversível)
-- atlas do prontuário: feminino → hra-f, masculino → bp3d-m, indeterminado → o profissional escolhe

-- o paciente não pertence a uma unidade: é atendido por várias (UBS, especialista, maternidade)
vinculos (id, paciente_id → pacientes, unidade_id → unidades, motivo text not null,
          origem enum('atendimento','encaminhamento','importacao') not null, criado_por → perfis not null,
          desde date not null, ate date, unique (paciente_id, unidade_id, desde))
-- só o admin da unidade cria ou encerra vínculo da própria unidade; profissional nunca se autovincula

-- achado = um ponto no corpo, codificado
achados (
  id uuid pk, paciente_id → pacientes, autor_id → perfis, unidade_id → unidades, especialidade text,
  ancora jsonb,                                    -- tipo Ancora (§5.4); null = sem local no corpo (fonte da verdade)
  estrutura text generated always as (ancora->>'estrutura') stored,  -- só para busca e índice
  cid10 text references cid10,                     -- ex.: 'I50.0'
  categoria enum('doenca','sintoma','lesao','cirurgia','dispositivo','alergia'),
  lado enum('esquerdo','direito','bilateral','nao_se_aplica'),
  status enum('ativo','resolvido','suspeito'),
  nivel_sigilo enum('normal','restrito') not null default 'normal',
  inicio date, observacao text,
  substitui_id uuid references achados,            -- correção = novo achado que aponta o anterior
  origem enum('manual','fhir') default 'manual', fhir_id text,
  criado_em timestamptz default now()
)
-- achados não são editados nem apagados

-- gestação e nascimento: o elo mãe–filho
gestacoes (id, mae_id → pacientes, dum date, dpp date, inicio_pre_natal date,
           desfecho enum('nascido_vivo','obito_fetal','aborto','em_curso'))
condicoes_gestacao (id, gestacao_id → gestacoes, cid10 text not null, semana int)
nascimentos (id, gestacao_id → gestacoes, crianca_id → pacientes unique,
             data date, peso_g int, idade_gestacional_sem int, apgar_5 int)

-- rastreio de importações
importacoes_fhir (id, autor_id, unidade_id → unidades, arquivo text, recursos int, erros jsonb, criado_em)
-- erros pode conter dados pessoais: RLS só para admin da unidade

-- auditoria: toda leitura e alteração de prontuário
auditoria (id, autor_id → perfis, unidade_id → unidades not null, paciente_id → pacientes, acao text,
           criado_em timestamptz)   -- unidade do autor no momento do evento; só insert por função
```

**Tabela de referência:** `cid10 (codigo pk, descricao)` carregada da tabela pública do DATASUS.

### RLS

- **Vínculo ativo** = `desde <= hoje and (ate is null or ate > hoje)`, em todo lugar. `ate` é exclusivo: encerrar grava `ate = hoje` e o acesso acaba na hora.
- Ninguém lê nem escreve `pacientes`, `vinculos`, `achados`, `gestacoes` ou `nascimentos` direto: só pelas funções do contrato abaixo, que conferem o vínculo e auditam. RLS fica ligada mesmo assim (defesa em profundidade).
- `perfis`: cada um lê o próprio e os da sua unidade; só o admin altera, e só na própria unidade; ninguém muda o próprio papel. `unidades`: leitura da própria; `cid10`: leitura para todo autenticado.
- Qualquer profissional com vínculo ativo vê **todos** os achados do paciente (é o valor multidisciplinar), mas só cria achados em nome próprio e da sua unidade.
- Toda abertura de prontuário grava em `auditoria` (no servidor, não no cliente), inclusive tentativas negadas. Nasce na Etapa 1, junto com o banco.
- **Sigilo (Etapa 3):** `achados.nivel_sigilo enum('normal','restrito')`, restrito automático por faixa de CID (HIV/Lei 14.289/2022, violência, saúde mental, aborto — lista revisada por médico). Achado restrito só aparece para a unidade autora; para as outras não vira marcador nem mostra CID. Acesso de emergência (*break-glass*) com justificativa obrigatória, auditado e revisado depois.

### Contrato do banco para o app (Etapa 1)

O app só fala com o banco por estas portas; tudo o mais é RLS.

| Porta | Faz |
| --- | --- |
| `minha_unidade() returns uuid` | Unidade do `perfis` do `auth.uid()` |
| `eh_admin() returns boolean` | Papel do usuário logado |
| `buscar_pacientes(p_texto text) returns table(id, nome, sexo, data_nascimento, cns_final)` | Resumo para lista e busca (nome ou CNS); só vínculos ativos; sem auditoria |
| `cadastrar_paciente(...)`, `vincular_paciente(...)`, `encerrar_vinculo(...)` | Só admin, só na própria unidade; CNS existente não duplica; tudo auditado |
| `abrir_prontuario(p_paciente uuid) returns pacientes` | Confere o vínculo e grava `auditoria(acao='abrir_prontuario')`; devolve o paciente. Sem vínculo grava `auditoria(acao='acesso_negado')` e devolve `null` (sem `raise`, para a tentativa não ser desfeita) |
| `select … from auditoria` | Só `admin`, só `unidade_id = minha_unidade()` |

Etapas seguintes acrescentam funções no mesmo padrão (`registrar_achado`, `historico_gestacional_crianca`…). A da criança devolve **só** o recorte gestacional relevante (condições da gestação, idade gestacional, peso, Apgar), nunca o prontuário da mãe.

### Contrato do banco — Etapa 3 (achados)

| Porta | Faz |
| --- | --- |
| `buscar_cid10(p_texto text, p_limite int default 20) returns table(codigo, descricao)` | Busca por código (prefixo) ou descrição (sem acento, `ilike`); sem auditoria |
| `registrar_achado(p_paciente uuid, p_ancora jsonb, p_cid10 text, p_categoria, p_lado, p_status, p_inicio date, p_observacao text, p_substitui uuid default null) returns uuid` | Exige vínculo ativo; autor, unidade e especialidade vêm do perfil (nunca do cliente); valida a âncora (atlas, atlas_versao, sistema, malha obrigatórios quando não for null); `nivel_sigilo` calculado no servidor por `cid10_sigilo`; `p_substitui` só aponta achado do mesmo paciente; audita `registrar_achado`. Sem vínculo ativo devolve `null` e grava `acesso_negado` (sem `raise`, mesmo padrão de `abrir_prontuario`); entrada inválida (âncora, CID, substituição) pode dar erro, pois não é tentativa de acesso |
| `listar_achados(p_paciente uuid) returns table(id, ancora, estrutura, cid10, cid10_descricao, categoria, lado, status, nivel_sigilo, inicio, observacao, especialidade, autor_nome, unidade_nome, substitui_id, criado_em)` | Exige vínculo ativo; devolve os achados **vigentes** (não substituídos) e audita `listar_achados`. Restrito de outra unidade **não aparece de forma alguma** (nem linha, nem contagem, nem marcador) |
| `historico_achado(p_achado uuid)` | Cadeia de correções (`substitui_id`) do achado, com as mesmas regras de visibilidade |

`cid10_sigilo (prefixo text pk, motivo text)` — lista **provisória**, pendente de revisão médica: HIV (B20–B24, Z21), violência (T74, Y05, Y07), saúde mental (F*), aborto (O04–O07). A tabela `achados` não recebe `select/insert/update/delete` direto de ninguém.

**Âncora de paciente feminina:** enquanto o app mostrar o corpo masculino provisório (sem pacote `hra-f`), o registro de achado com âncora fica bloqueado para ela (só "sem local no corpo"). É regra da tela; o banco não bloqueia por sexo. `ancora.estrutura` pode ser `null` (malha sem ID de ontologia).

`listar_achados` e `historico_achado` devolvem também `unidade_id` (o app decide "Corrigir" por id, não por nome).

### Contrato do banco — Etapa 5 (gestação e nascimento)

| Porta | Faz |
| --- | --- |
| `registrar_gestacao(p_mae uuid, p_dum date, p_inicio_pre_natal date) returns uuid` | Exige vínculo ativo com a mãe (sexo feminino); `dpp` = DUM + 280 dias, calculada no servidor; `desfecho='em_curso'`; no máximo uma gestação `em_curso` por mãe; audita |
| `registrar_condicao_gestacao(p_gestacao uuid, p_cid10 text, p_semana int) returns uuid` | Exige vínculo ativo com a mãe; semana 0–45; sigilo pela mesma `cid10_sigilo` (acrescida de O98.7 — HIV na gestação); autor/unidade do perfil; audita |
| `encerrar_gestacao(p_gestacao uuid, p_desfecho)` | `nascido_vivo` só via `registrar_nascimento`; `obito_fetal`/`aborto` encerram; audita |
| `registrar_nascimento(p_gestacao uuid, p_nome text, p_sexo, p_data date, p_peso_g int, p_idade_gestacional_sem int, p_apgar_5 int) returns uuid` | Exige vínculo ativo com a mãe; `p_data` entre a DUM e hoje; cria a criança em `pacientes` **sem CNS** (o CNS do recém-nascido é atribuído depois pelo fluxo do admin — evita usar o nascimento como oráculo de CNS existente), o `nascimentos` e marca a gestação como `nascido_vivo` (aceita novos nascimentos na mesma gestação para gêmeos); cria **vínculo da criança com a unidade que registrou** (`origem='atendimento'`, motivo "nascimento") — única exceção à regra "só admin cria vínculo", justificada pelo parto; tudo atômico e auditado; gemelaridade = várias chamadas para a mesma gestação |
| `listar_gestacoes(p_mae uuid)` | Exige vínculo com a mãe; gestações com condições (restritas de outra unidade ocultas) e nascimentos |
| `historico_gestacional_crianca(p_crianca uuid)` | Exige vínculo com a **criança**; devolve **só o recorte**: nome da mãe, condições da gestação não restritas (CID, descrição, semana), idade gestacional, peso, Apgar 5, data. Nunca achados, outras gestações ou o prontuário da mãe. Audita |

**Condição gestacional restrita e o pediatra (pergunta aberta para revisão médica):** exposição vertical (ex.: HIV, sífilis) é clinicamente relevante para a criança. No MVP, condições restritas **não** aparecem no recorte do pediatra de outra unidade; a decisão de exibir um alerta de exposição fica pendente de parecer médico e jurídico.

**Camada gestacional:** com gestação `em_curso`, o prontuário da mãe oferece ligar o sistema `gestacional` do atlas (placenta, âmnio, cordão) — representação de referência, não da gestação real.

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

Controles do visualizador: corpo inteiro/foco, seis vistas anatômicas, transparência e camadas musculares aproximadas; estruturas podem ser ocultadas ou isoladas. O card da estrutura mostra nome em português/inglês e, no prontuário, os achados ligados por estrutura (ou malha quando sem ID). A atribuição do atlas permanece visível.

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

### Contrato da Etapa 6 (importação)

**Fluxo:** só o `admin`, só no servidor (nunca o navegador falando com o banco para importar). Upload do Bundle (até 10 MB) → validação zod e mapeamento → **prévia** (pacientes novos/existentes, condições, eventos, erros por recurso) → confirmação → gravação → relatório. Nenhum dado pessoal em log; `importacoes_fhir.erros` guarda só o `id` do recurso e o motivo.

| Porta (banco) | Faz |
| --- | --- |
| `iniciar_importacao(p_arquivo text, p_recursos int) returns uuid` | Admin; cria `importacoes_fhir` da unidade |
| `importar_paciente_fhir(p_importacao uuid, p_fhir_id text, p_cns text, p_nome text, p_sexo, p_nascimento date) returns uuid` | Admin; mesmo comportamento de `cadastrar_paciente` (CNS existente não duplica; vínculo com a unidade, `origem='importacao'`); `fhir_id` registrado |
| `importar_condicao_fhir(p_importacao uuid, p_paciente uuid, p_fhir_id text, p_cid10 text, p_ancora jsonb, p_status, p_inicio date) returns uuid` | Admin com vínculo ativo; achado `origem='fhir'`, autor = admin, unidade = do admin, sigilo pela `cid10_sigilo`; **`fhir_id` já importado é ignorado** (devolve o id existente) |
| `importar_evento_fhir(p_importacao uuid, p_paciente uuid, p_fhir_id text, p_tipo text, p_data timestamptz, p_codigo text, p_descricao text, p_valor text)` | `Observation`/`Encounter` em `eventos_clinicos` (linha do tempo; não viram ponto no corpo); `fhir_id` idempotente |
| `concluir_importacao(p_importacao uuid, p_erros jsonb)` | Fecha o registro com contagens e erros |
| `listar_eventos(p_paciente uuid)` | Vínculo ativo; eventos **da própria unidade** para a linha do tempo. Decisão conservadora: eventos não têm classificação de sigilo (ex.: carga viral de HIV chega como código LOINC comum), então não circulam entre unidades até existir uma regra de sigilo para eles |

`eventos_clinicos (id, paciente_id, unidade_id, importacao_id, fhir_id, tipo, data, codigo, descricao, valor, criado_em)` — `fhir_id` único por unidade, enviado como `Tipo/id` (ids FHIR só são únicos por tipo); sem DML direto. `bodysite_estrutura` tem a coluna `lado` e é legível por `authenticated` (dado de referência, como `cid10`). Joelho só tem FMA: no atlas feminino fica sem local até haver mapeamento.

**CID-10 no `Condition.code`:** aceita os sistemas `http://hl7.org/fhir/sid/icd-10` e o CID-10 brasileiro; código inexistente na tabela `cid10` vira erro do recurso (não importa).

**`bodySite` → âncora:** tabela pequena `bodysite_estrutura (snomed text pk, descricao, estrutura_fma, estrutura_uberon)` mantida à mão (ex.: região lombar, coração, joelho E/D, fígado); a âncora estrutural é montada no servidor com `malhaPrincipal` do atlas do sexo do paciente. `bodySite` sem mapeamento → `ancora=null` ("sem local no corpo"). Nunca adivinhar.

### Endurecimento pré-piloto (migração 0008, revisão externa de 2026-11-26)

- **Âncora conferida no catálogo:** tabela `atlas_malhas (atlas, versao, malha, sistema, lateralidade, estrutura)`, PK `(atlas, versao, malha)`, populada com **3.190 malhas** dos pacotes **publicados** (`bp3d-m/4.0-1` e `hra-f/1.10-1`; rascunhos nunca entram); legível por `authenticated`, sem DML. `registrar_achado` e `importar_condicao_fhir` recusam (22023) âncora cuja `(atlas, atlas_versao, malha)` não exista, ou cujo atlas não seja o do sexo do paciente (feminino→`hra-f`, masculino→`bp3d-m`). `sistema`, `lateralidade` e `estrutura` são sobrescritos pelo catálogo, não pelo navegador; o lado clínico informado só é recusado se contradizer a lateralidade da malha no catálogo; só o ponto clicado vem do cliente.
- **Sistema de origem na importação:** `iniciar_importacao(p_arquivo, p_recursos, p_sistema_origem text)`; `sistema_origem` obrigatório (texto aparado, 1–200, comparado em minúsculas), informado pelo admin na tela. A unicidade de `fhir_id` passa a ser `(unidade_id, sistema_origem, fhir_id)` em `paciente_fhir`, `achados` (só `origem='fhir'`) e `eventos_clinicos`, porque dois sistemas de uma mesma unidade podem ter o mesmo `Patient/123`. Linhas antigas recebem `sistema_origem='legado'`.
- **`verificationStatus`:** `Condition` com `entered-in-error` ou `refuted` não importa; vira erro do recurso com o motivo. Os demais valores importam como hoje.
- **Verificação técnica aplicada à homologação (2026-11-26):** **49/49 testes PGlite** e **169 tentativas adversariais pela API pública com 0 falhas** (`supabase/testes_adversariais.mjs`). Permanecem pendentes de decisão/avaliação humana: validação médica, revisão jurídica do RIPD e aval do encarregado de dados, licença do SNOMED CT em produção, decisão de hospedagem (limite de login por IP do servidor).
- **Expiração por inatividade no banco (migração 0009, decisão do usuário em 2026-11-26):** o token do Supabase continua válido depois que o app expira a sessão, então a trava também fica no banco. `public.sessoes_atividade` guarda a última atividade por `session_id` do JWT; só o servidor do app grava (RPC `registrar_atividade_sessao`, apenas `service_role`, chave `SUPABASE_SECRET_KEY` só no servidor), no login e no ping `/api/sessao/atividade` (no máximo 1 por minuto). `minha_unidade()` e `eh_admin()` negam quando a sessão está sem atividade há mais de 32 min (30 do app + 1 do intervalo do ping + 1 de folga), e uma sessão expirada não revive. Aceite: acesso direto à API com token válido mas sem atividade registrada é negado (testes PGlite e adversariais).

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
- [ ] **Homologação antes de dado real:** Supabase de homologação com dados sintéticos, testes adversariais (JWT, PostgREST, RPC, Storage), RIPD e aval do encarregado de dados do município. O teste em PGlite cobre só SQL/RLS. Feito em 2026-11-26: `supabase/testes_adversariais.mjs` (169 tentativas via API pública — RPC anônima, CRUD direto, JWT forjado, outra unidade, Storage — 0 falhas) e rascunho técnico `docs/lgpd/RIPD-rascunho.md`; faltam a revisão jurídica do RIPD e o aval do encarregado.
- [ ] **Lista de CIDs sensíveis** para o sigilo automático, revisada por médico.
- [ ] **Validação médica** dos atlas e dos 1.659 nomes em português antes do piloto.
- [ ] **Licença do SNOMED CT em produção:** o Brasil aderiu em 2018 mas não consta hoje como membro ativo (snomed.org/members); uso institucional em produção pode exigir *Affiliate License* via MLDS. A importação FHIR só lê o código do `bodySite` e o mapeia por tabela própria (`bodysite_estrutura`, 12 códigos verificados em supabase/dados/bodysite_snomed.csv); confirmar o enquadramento antes do piloto.
- [ ] **Hospedagem:** o município exige servidor próprio ou nuvem nacional?
- [ ] **Limite de login por IP do servidor** (conferido no painel em 2026-11-26): o login é ação de servidor, então o Supabase Auth conta tudo pelo IP do app. O login por senha cai no balde do `/auth/v1/token` (150 req/5 min, rajada de 30), que também atende a renovação de sessão. Na prática, a rede inteira divide um balde só: quem errar senha em massa trava o login e a renovação de todos. A correção oficial é mandar o IP do usuário no cabeçalho `Sb-Forwarded-For`, o que exige: (1) chave `sb_secret_` só no servidor; (2) ativar "IP Address Forwarding" em Authentication > Rate Limits (`security_sb_forwarded_for_enabled`); (3) um proxy de confiança na frente do app que acrescente o IP real ao `X-Forwarded-For`, senão o atacante forja o IP e fura o limite. Depende da hospedagem; até lá, a tela avisa "muitas tentativas" no 429. Fonte: https://supabase.com/docs/guides/auth/rate-limits
- [ ] **Identificação:** CNS sozinho basta ou precisamos de CPF?

## 13. Plano de construção

Cada etapa termina com um teste que passa.

0. **Consolidar o atlas:** SPEC 0.2, `LICENCAS.md`, pacote de atlas (§5.3) para `bp3d-m`, PR #1 aprovado. Teste: `atlas/bp3d-m/<versao>/` abre no visualizador de referência.
1. **Fundação:** Next.js + Supabase, login, perfis, unidades, pacientes, vínculos, RLS e auditoria. Testes automatizados:
   - profissional da unidade A não acessa paciente sem vínculo com A (nem pela lista, nem por `abrir_prontuario`, nem por `select` direto);
   - ninguém lê ou altera `pacientes`/`vinculos` direto, nem o admin; ninguém apaga vínculo;
   - profissional não cria vínculo nem muda o próprio papel; admin não mexe em vínculo de outra unidade;
   - vínculo futuro, encerrado ou expirado não dá acesso;
   - acesso autorizado e acesso negado gravam auditoria persistente com `unidade_id`; auditoria não aceita update/delete;
   - páginas do prontuário sem cache compartilhado; sessão encerrada não acessa prontuário.
2. **Motor anatômico:** `packages/motor-anatomico` em React Three Fiber com o contrato §5.4, atlas `bp3d-m` e `hra-f`. Teste: clicar no fêmur esquerdo devolve `estrutura='FMA24475'` e uma âncora com `posicao_local`.
3. **Primeiro prontuário:** criar, gravar, reabrir e ver achados com CID-10. Teste: achado criado reaparece no mesmo ponto após recarregar; achado restrito não vaza por busca, marcador ou contagem para outra unidade.
4. **Multidisciplinaridade:** especialidades, filtros, histórico, linha do tempo. Teste: demonstração da §14 e meta de 3 s com 200 achados. Critérios:
   - **Demonstração §14** automatizada contra a homologação: cardiologia (I10, sem local), ortopedia (M54.5 marcado na região lombar) e obstetrícia (Z34, no útero), cada um na sua unidade; os três veem o histórico unificado dos três achados.
   - **Desempenho:** build de produção, navegador com CPU 4× mais lenta e rede "Fast 4G" (simulação de tablet intermediário), paciente de carga com 200 achados vigentes espalhados por vários sistemas; da navegação até lista e marcadores visíveis ≤ 3 s na **mediana de 5 aberturas** (registrar também o p95 e quanto vem do banco, da rede de GLB e da renderização).
   - **Filtros e linha do tempo:** especialidade, status e período filtram ao mesmo tempo o corpo e a lista; a linha do tempo ordena por início (ou criação) e permite escolher um intervalo; histórico de correções visível no cartão do achado.
5. **Gestação e nascimento:** gestação, condições, camada gestacional, nascimento, vínculo mãe–filho. Teste: registrar nascimento cria a criança ligada à mãe. Critérios:
   - Obstetrícia registra a gestação da Maria, uma condição (ex.: O24.4 diabetes gestacional) e o nascimento; a criança nasce com vínculo na Maternidade e aparece em `/pacientes/[id]/familia` da mãe e vice-versa.
   - Pediatra (unidade com vínculo só com a criança) vê o recorte gestacional e **nada** do prontuário da mãe (nem achados, nem outras gestações); condição restrita de outra unidade não aparece.
   - Criança abaixo de 12 anos não vê corpo 3D (§5.1); o prontuário dela é estruturado e por linha do tempo.
   - Gestação em curso: camada gestacional disponível no corpo da mãe.
6. **Interoperabilidade:** importação FHIR. Teste: Bundle sintético com 50 pacientes importa sem erro e sem duplicar. Critérios:
   - Bundle sintético (gerado por script do repositório, CNS e nomes fictícios) com 50 pacientes, condições com e sem `bodySite` mapeado e observações: importa sem erro; reimportar o mesmo Bundle não cria nada novo.
   - Prévia mostra contagens e erros antes de gravar; um Bundle com recursos inválidos importa os válidos e lista os inválidos com o motivo.
   - Só admin importa; profissional e anônimo são negados; nada de dado pessoal em log ou em `erros`.
   - Condição com `bodySite` mapeado aparece no ponto da estrutura; sem mapeamento, em "sem local no corpo"; condições sigilosas seguem `cid10_sigilo`.
7. **Preparação para piloto:** validação médica, segurança, performance, acessibilidade e usabilidade nos três tamanhos de tela. Critérios (registrados antes da execução, 2026-11-26):
   - **Segurança:** advisors do Supabase sem nenhum `ERROR` e cada `WARN` corrigido ou justificado por escrito; revisão independente do app inteiro (rotas, ações de servidor, proxy, RPCs) sem item grave em aberto; varredura do histórico do git sem segredo; sessão expira após 30 min de inatividade, com cookie HMAC-SHA256 assinado por `SESSAO_SEGREDO` e falha fechada se ausente, inválido ou futuro; limite de tentativas de login delegado ao Supabase Auth. A consulta a `/auth/v1/settings` não expôs o valor configurado, que não pôde ser verificado pela API.
   - **Performance:** critério da Etapa 4 mantido (mediana de 5 ≤ 3 s, CPU 4×, Fast 4G) depois de tudo da Etapa 7.
   - **Acessibilidade:** axe-core sem violação `serious` ou `critical` em login, lista de pacientes, prontuário (adulto e criança), gestação, nascimento, família e importar, nas três larguras; registrar um achado e abri-lo só pelo teclado; tudo o que está no 3D também está na lista.
   - **Usabilidade nos três tamanhos:** em 1440, 820 e 390 px, as mesmas telas sem rolagem horizontal, sem sobreposição e com alvos de toque ≥ 44 px em 390; a demonstração de referência (§14) passa em 390 px.
   - **Validação médica:** pacote para revisão humana com tudo o que hoje é "validação médica pendente" (nomes em português, lista de sigilo CID-10, mapa `bodySite` e malha representante, regra de idade do 3D, alerta de exposição vertical). A etapa só se dá por concluída na parte técnica; a validação médica fica **pendente de avaliação humana** e bloqueia o piloto, não o desenvolvimento.

## 14. Demonstração de referência

Paciente fictícia de 32 anos, com vínculo em três unidades:

| Especialidade | Registro |
| --- | --- |
| Cardiologia | Hipertensão, CID-10 I10, sem local no corpo |
| Ortopedia | Dor lombar, marcada na região lombar |
| Obstetrícia | Gestação em acompanhamento, com histórico pré-natal |

Passa quando os três profissionais entram cada um na sua unidade, registram o próprio achado e veem o histórico unificado dos três.
