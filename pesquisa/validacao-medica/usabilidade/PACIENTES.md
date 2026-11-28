# Pacientes fictícios da avaliação com médicos (EXP-0028)

Todos os dados são **fictícios**, escritos para teste de uso. Os quadros clínicos são plausíveis, mas foram redigidos com apoio de IA e **não foram revisados por médico**: revisar com o primeiro participante-piloto antes das sessões. Nenhum nome, CNS ou data corresponde a pessoa real; todo nome termina em "Fictício/Fictícia".

## Unidades e contas (já existem em `supabase/seed.sql`)

| Unidade | Profissional | Especialidade |
|---|---|---|
| UBS Centro | Profissional Medicina de Família (**nova**: `mfc@saude3d.invalid`) | `medicina_familia` |
| UBS Centro | Profissional Ortopedia | `ortopedia` |
| Ambulatório de Cardiologia | Profissional Cardiologia | `cardiologia` |
| Maternidade Municipal | Profissional Obstetrícia | `obstetricia` |
| Ambulatório de Pediatria | Profissional Pediatria | `pediatria` |

Senhas ficam só em `supabase/.env.demo` (fora do git). O moderador faz o login pelo participante.

## Rodadas

Cada sessão usa uma **rodada** própria: `node supabase/seed_avaliacao.mjs --rodada 01`. A rodada nova encerra (`encerrar_vinculo`) os vínculos das rodadas anteriores e cria os mesmos pacientes de novo, com CNS próprio. Nada é apagado; o que o participante registrou fica preso à rodada dele e some da busca na sessão seguinte. A carga lê os vínculos a encerrar com a chave de serviço (só leitura) e os encerra pela função `encerrar_vinculo`, logada como admin da unidade de cada vínculo; o mesmo vale para a criança P07 das rodadas anteriores (achada pelo nascimento ligado à gestação da P06).

CNS: `7` + `9` + rodada (2 dígitos) + `0000000000` + paciente (2 dígitos) → 15 dígitos. Ex.: rodada 01, paciente 03 → `790100000000003`. Observação de todo achado semeado começa com `AVAL-<rodada>-`.

## Pacientes

Datas de referência: hoje = data da execução; "há N anos" é calculado a partir dela. Datas absolutas abaixo são de `inicio`.

### P01 — Ana Lima Fictícia
Feminino, 58 anos. Vínculos: UBS Centro, Cardiologia.

| Autor | CID-10 | Categoria | Local (atlas `hra-f`) | Lado | Status | Início | Observação |
|---|---|---|---|---|---|---|---|
| Cardiologia | I10 | doença | sem local | não se aplica | ativo | 2012-03-01 | Hipertensão em uso de losartana |
| Cardiologia | I48 | doença | `VH_F_left_cardiac_atrium` (átrio esquerdo) | não se aplica | ativo | 2024-09-15 | Fibrilação atrial paroxística; anticoagulada |
| Medicina de Família | E11.9 | doença | sem local | não se aplica | ativo | 2015-06-01 | Diabetes tipo 2; metformina |
| Medicina de Família | J18.9 | doença | `VH_F_right_posterior_basal_bronchopulmonary_segment` (segmento basal posterior direito = lobo inferior) | direito | **resolvido** | 2023-07-10 | Pneumonia comunitária tratada |
| Medicina de Família | M17.0 | doença | `VH_F_patella_R` (patela direita) | bilateral | ativo | 2020-02-01 | Gonartrose bilateral |

Uso no roteiro: T1, T2 (histórico entre unidades), **T6** (o participante registra fratura do ramo púbico — lacuna do atlas).

### P02 — José Pereira Fictício
Masculino, 65 anos. Vínculos: UBS Centro, Cardiologia.

| Autor | CID-10 | Categoria | Local (`bp3d-m`) | Lado | Status | Início | Observação |
|---|---|---|---|---|---|---|---|
| Cardiologia | I25.2 | doença | `FJ2428` (parede do ventrículo; o `bp3d-m` não separa o ventrículo esquerdo) | não se aplica | ativo | 2019-04-20 | IAM antigo de parede anterior; angioplastia |
| Cardiologia | Z95.5 | dispositivo | `FJ2631` (tronco do ramo interventricular anterior da coronária esquerda = DA) | não se aplica | ativo | 2019-04-21 | Stent coronário |
| Cardiologia | I10 | doença | sem local | não se aplica | ativo | 2010-01-01 | Hipertensão |
| Medicina de Família | J44.9 | doença | `FJ2539` (brônquio principal direito; o `bp3d-m` **não tem tecido pulmonar**, só a árvore brônquica) | bilateral | ativo | 2018-05-01 | DPOC; ex-tabagista desde 2019 |
| Medicina de Família | F17.2 | doença | sem local | não se aplica | resolvido | 1980-01-01 | Tabagismo 40 maços-ano (fica **restrito** pela regra F*) |
| Medicina de Família | N40 | doença | `FJ3139` (próstata) | não se aplica | ativo | 2022-08-01 | HPB; tansulosina |
| Ortopedia | M54.5 | sintoma | `FJ3165` (4ª vértebra lombar) | não se aplica | ativo | 2025-10-05 | Lombalgia mecânica |

Uso: T3 (registrar achado com local no corpo masculino), T7 (vista posterior), ponto de observação: tabagismo restrito.

### P03 — Carla Mendes Fictícia
Feminino, 29 anos. Vínculos: UBS Centro, Maternidade. **Gestante**: DUM = hoje − 168 dias (24 semanas), início do pré-natal = DUM + 28 dias.

| Autor | CID-10 | Categoria | Local (`hra-f`) | Lado | Status | Início | Observação |
|---|---|---|---|---|---|---|---|
| Medicina de Família | J45.9 | doença | sem local | não se aplica | ativo | 2010-03-01 | Asma leve intermitente |
| Obstetrícia | O23.4 | doença | `VH_F_fundus_of_urinary_bladder_dome` (fundo da bexiga) | não se aplica | resolvido | DUM + 70 d | ITU na gestação tratada |

Condição da gestação (`registrar_condicao_gestacao`), pela Obstetrícia: O24.4 (diabetes gestacional), início DUM + 170 d (se a data ficar no futuro, use hoje).

Uso: T8 (gestação).

### P04 — Pedro Alves Fictício
Masculino, 41 anos. Vínculo: UBS Centro.

| Autor | CID-10 | Categoria | Local (`bp3d-m`) | Lado | Status | Início | Observação |
|---|---|---|---|---|---|---|---|
| Ortopedia | M75.1 | doença | `FJ1506` (supraespinal direito) | direito | ativo | hoje − 90 d | Síndrome do manguito rotador |
| Ortopedia | M25.5 | sintoma | `FJ3275` (patela esquerda; o `bp3d-m` não tem menisco) | esquerdo | suspeito | hoje − 200 d | Dor no joelho esquerdo |
| Ortopedia | M23.2 | doença | mesma âncora do anterior | esquerdo | ativo | hoje − 180 d | **Correção** do anterior (`p_substitui`): lesão de menisco medial na RM |
| Medicina de Família | K21.9 | doença | `FJ2563` (esôfago) | não se aplica | ativo | 2024-02-01 | DRGE |

Uso: T5 (correção e histórico de versões), lateralidade.

### P05 — Lúcia Rocha Fictícia
Feminino, 47 anos. Vínculos: UBS Centro, Maternidade.

| Autor | CID-10 | Categoria | Local (`hra-f`) | Lado | Status | Início | Observação |
|---|---|---|---|---|---|---|---|
| Obstetrícia | N63 | sintoma | `VH_F_mammary_lobes_L` (lobo mamário esquerdo) | esquerdo | suspeito | hoje − 20 d | Nódulo palpável QSE; USG solicitada |
| Obstetrícia | D25.9 | doença | `VH_F_body_of_uterus` (corpo do útero) | não se aplica | ativo | 2021-05-01 | Mioma uterino |
| Medicina de Família | G43.9 | doença | sem local | não se aplica | ativo | 2005-01-01 | Enxaqueca |
| Medicina de Família | F41.1 | doença | sem local | não se aplica | ativo | 2023-03-01 | Ansiedade generalizada (**restrito**) |

Uso: T9 (sigilo: o que a Obstetrícia vê e o que a Medicina de Família vê).

### P06 — Juliana Santos Fictícia e P07 — Davi Santos Fictício
P06: feminino, 32 anos. Vínculos: UBS Centro, Maternidade. Gestação **encerrada**: DUM = hoje − 485 d; pré-natal DUM + 35 d; condição O13 (hipertensão gestacional) pela Obstetrícia; nascimento (`registrar_nascimento`, pela Obstetrícia) em DUM + 273 d criando a criança P07: peso 3150 g, idade gestacional 39 semanas, Apgar 5 min = 9.

P07: Davi Santos Fictício, masculino, nascido na data acima (≈ 7 meses). **Sem CNS** (`registrar_nascimento` não recebe CNS); é identificado pelo nascimento ligado à gestação da P06 da mesma rodada. Vínculo: Pediatria (além do que `registrar_nascimento` criar).

| Autor | CID-10 | Categoria | Local | Lado | Status | Início | Observação |
|---|---|---|---|---|---|---|---|
| Pediatria | J21.9 | doença | sem local (criança: sem corpo 3D) | não se aplica | resolvido | nascimento + 90 d | Bronquiolite; sem internação |

Uso: T8 (família mãe–filho, histórico gestacional visto pela Pediatria).

### P09 — Marina Oliveira Fictícia e P10 — Lucas Oliveira Fictício
P09: feminino, 26 anos. Vínculos: UBS Centro, Maternidade. Gestação **encerrada**: DUM = hoje − 285 d; pré-natal DUM + 56 d; condição **O98.7** (HIV complicando a gravidez) pela Obstetrícia na semana 8 — fica **restrita** pela regra de sigilo (só a Maternidade vê). Nascimento (`registrar_nascimento`, Obstetrícia) em DUM + 273 d (≈ 12 dias antes da sessão) criando P10: peso 2890 g, 39 semanas, Apgar 5 min = 9. Sem achados.

P10: Lucas Oliveira Fictício, masculino, sem CNS, identificado pelo nascimento ligado à gestação da P09. Vínculos: Maternidade (do nascimento) e Pediatria. Sem achados (primeira consulta).

O que cada unidade vê no histórico gestacional do P10: Pediatria vê a mãe, peso, idade gestacional e Apgar, e **"Nenhuma condição disponível"**; Maternidade vê também O98.7. A carga confere isso no banco e aborta se não bater.

Uso: T11 (conflito entre sigilo da mãe e cuidado do recém-nascido exposto ao HIV).

### P08 — Sam Costa Fictício
Sexo **indeterminado**, 36 anos. Vínculo: UBS Centro.

| Autor | CID-10 | Categoria | Local | Lado | Status | Início | Observação |
|---|---|---|---|---|---|---|---|
| Medicina de Família | J45.9 | doença | sem local | não se aplica | ativo | 2001-01-01 | Asma |
| Medicina de Família | E66.9 | doença | sem local | não se aplica | ativo | 2022-01-01 | Obesidade, IMC 32 |

Uso: escolha de atlas para sexo indeterminado (pergunta aberta).

## Malhas
As malhas acima foram escolhidas pelo revisor (Claude Code) a partir dos `indice.json` publicados, sem revisão médica. O `bp3d-m/4.0-1` não tem tecido pulmonar nem meniscos.

## Regras para a carga
- Escrever **só pelas funções** (`cadastrar_paciente`, `vincular_paciente`, `registrar_achado`, `registrar_gestacao`, `registrar_condicao_gestacao`, `encerrar_gestacao`/`registrar_nascimento`), logado como o profissional/admin de cada unidade, como em `seed_etapa4.mjs`.
- Local: achar a malha pelo nome no `indice.json` do atlas certo; se nenhuma candidata existir, gravar **sem local** e listar no relatório final (não inventar outra estrutura).
- Lado do achado nunca contradiz a lateralidade da malha.
