# EXP-0025 — Adaptação muscular orientada por restrições anatômicas (prova de conceito no membro inferior)

## 1. Identificação
- **ID:** `EXP-0025`
- **Título:** Adaptar músculos do BodyParts3D (masculino) ao esqueleto feminino da Denver usando só ossos e inserções, com os músculos da Denver reservados para conferência
- **Data:** `2026-11-27`
- **Responsável:** usuário (autorização), Claude Code (protocolo e revisão)
- **Agentes de IA:** Claude Code (protocolo e revisão), Codex (execução); proposta discutida com o ChatGPT
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** a preencher
- **Linha de pesquisa:** `LP01`
- **Situação:** `em andamento — rodada 1 rejeitada; rodada 2 registrada`

## 2. Problema
O `hra-f` não tem ~95% da musculatura (EXP-0021), e não existe fonte aberta de músculos femininos de outras mulheres (EXP-0023). Deformar o corpo masculino pela silhueta não funciona (EXP-0022). A alternativa é deformar cada músculo masculino guiado pelos **ossos** femininos em que ele se prende. Antes de pensar em escala, é preciso saber se esse método chega perto de músculos femininos reais.

## 3. Hipótese
H25: deformar músculos do `bp3d-m` pelo campo de deformação entre ossos masculinos e femininos, com as inserções presas aos ossos femininos, aproxima os músculos femininos reais (Denver) melhor do que o alinhamento global por similaridade.

## 4. Fundamentação teórica
Origem, inserção e trajeto de um músculo são definidos pelos ossos. Se os ossos femininos forem conhecidos, um campo de deformação suave ancorado nos ossos leva o músculo para a posição e a extensão coerentes com eles. Isso não captura diferenças de volume muscular entre sexos, que precisam de regra própria; o experimento mede o quanto só a ancoragem óssea já explica.

## 5. Materiais e ambiente
- **Esqueleto feminino (alvo):** Denver, `hra/denver/bruto/Final 3D STL Models-stl/Left/` — somente arquivos `*_Bone_*` (pelve, sacro, fêmur, patela, tíbia, fíbula, pé). CC BY 4.0.
- **Molde masculino:** BodyParts3D 4.0, `bodyparts3d/bruto/` (OBJ, IDs FMA em `bodyparts3d/catalogo_bp3d.csv`): ossos do membro inferior esquerdo e os 10 músculos abaixo. CC BY 4.0 (DBCLS).
- **Referência reservada (só na avaliação):** `*_Muscle_*` da Denver, lado esquerdo.
- **Músculos (lado esquerdo; FMA do BP3D):** reto femoral (FMA38929), vasto lateral (FMA38931), vasto medial (FMA38933), sartório (FMA22355), grácil (FMA43884), adutor longo (FMA22457), bíceps femoral cabeça longa (FMA45889) + curta (FMA45892), gastrocnêmio medial (FMA45958), glúteo médio (FMA22331), tibial anterior (FMA22545).
- **Ambiente:** CPU local; trimesh, SciPy (RBF/thin-plate spline), scikit-image.

## 6. Metodologia
**Separação (obrigatória):** o script de adaptação não pode abrir nenhum arquivo `*_Muscle_*` da Denver (asserção no código que aborta se algum caminho com `_Muscle_` for lido). As malhas adaptadas são gravadas e seus SHA-256 registrados **antes** de o script de avaliação rodar.

**Etapas:**
1. **Referencial:** alinhar ossos BP3D (mm) aos ossos Denver por similaridade usando apenas pelve + fêmur + tíbia (ICP com escala). Esse alinhamento, aplicado aos músculos BP3D, é a **linha de base B0**.
2. **Correspondência óssea:** para cada osso, registro não rígido BP3D→Denver (ICP rígido + ajuste não rígido por pontos mais próximos com regularização, ou CPD implementado em NumPy). Resultado: pares de pontos osso masculino → osso feminino.
3. **Inserções (derivadas dos dados, não desenhadas):** vértices do músculo BP3D a `≤ 3 mm` da superfície de um osso BP3D. Cada região é rotulada com o osso e conferida contra a origem/inserção descrita na literatura (Gray's Anatomy, 42ª ed., ou Terminologia Anatomica), registrando a fonte na tabela de inserções.
4. **Deformação (método M):** thin-plate spline (ou RBF) ajustada nos pares ósseos dos ossos em que o músculo se prende e dos vizinhos imediatos, aplicada a todos os vértices do músculo. Depois, os vértices de inserção são projetados na superfície do osso feminino e o resto do músculo é relaxado por suavização laplaciana com as inserções fixas.
5. **Colisão:** volume do músculo que penetra osso, depois da deformação.

**Avaliação (só depois das malhas congeladas):** para cada músculo, contra o músculo Denver correspondente:
- distância de superfície simétrica média e p95 (mm);
- Dice volumétrico (voxelização a 1 mm);
- razão de volume (adaptado / Denver);
- distância das inserções adaptadas ao osso Denver.

Mesmas medidas para B0.

## 7. Critérios de sucesso (definidos antes da execução)
- **R1 — Melhora relativa (primário):** M reduz a distância média em `≥ 20%` em relação a B0 em pelo menos 8 dos 10 músculos.
- **R2 — Inserções:** mediana da distância das inserções ao osso Denver `≤ 2 mm`.
- **R3 — Colisão:** penetração muscular em osso `< 2%` do volume do músculo em todos os músculos.
- **R4 — Absoluto (exploratório, limiar escolhido antes sem referência na literatura):** Dice mediano `≥ 0,60`.

Leitura: **H25 sustentada** se R1, R2 e R3; **rejeitada** se R1 falha. R4 só descreve.

## 8. Resultados

### 8.1 Rodada 1 (método M como registrado)
Execução por Codex em 2026-11-27 (`pesquisa/resultados/EXP-0025/RELATORIO.md`, `metricas.csv`, `veredito_R1_R4.txt`). As 22 malhas adaptadas foram gravadas e tiveram o SHA-256 conferido antes de qualquer músculo da Denver ser aberto. O script de adaptação leu só 13 STLs ósseos.

| Critério | Resultado |
|---|---|
| R1 — M melhora `≥ 20%` sobre B0 em `≥ 8/10` | **reprovado (0/10)**: M **piorou** a distância média em 9 de 10 (de −5,7% no sartório a −42,0% no gastrocnêmio medial); tibial anterior +0,4% |
| R2 — inserções `≤ 2 mm` | atendido (0,000 mm), mas por construção: as inserções foram projetadas no osso |
| R3 — penetração em osso `< 2%` | reprovado (máximo 22,1%, tibial anterior) |
| R4 — Dice mediano `≥ 0,60` (exploratório) | 0,27 |

B0 (só alinhamento global com escala 0,895) já fica longe da Denver: distância média de 6,8 mm (tibial anterior) a 28,7 mm (grácil).

**Veredito da rodada 1: H25 rejeitada** (R1), pela regra pré-registrada.

### 8.2 Rodada 2 — mudança de método registrada antes da execução
Ver seção 9 para a causa. Mudanças (o resto da metodologia, B0, avaliação e critérios R1–R4 ficam iguais):
- **M2b (primário):** inserções = vértices `≤ 3 mm` de um osso **e** situados nos 10% terminais do comprimento do músculo ao longo do seu eixo principal (cada extremidade). Só esses vértices são projetados e fixados; o relaxamento laplaciano é o mesmo.
- **M2a (secundário):** só o campo thin-plate spline da rodada 1, sem projeção e sem relaxamento.
- Leitura: **H25 sustentada na rodada 2** se M2b cumprir R1, R2 e R3. M2a é reportado para separar o efeito do campo do efeito da projeção; não decide a hipótese.
- **Medida exploratória acrescentada (não decide):** distância unidirecional Denver→adaptado (média), para separar "músculo no lugar errado" de "músculo com tendão a mais".
- A rodada 1 fica preservada integralmente (malhas, hashes, métricas).

## 9. Validação
Revisão (Claude Code) da rodada 1:
- **Separação adaptação/avaliação:** conferida pelos hashes e pela lista de arquivos lidos (`metricas_meta.json`).
- **Causa da piora (falha de protocolo, do revisor):** a definição de inserção como "vértice `≤ 3 mm` de um osso" capturou de 11% a 49% da superfície de cada músculo (tibial anterior 49%, grácil 37%, glúteo médio 36%). Isso é **área de contato**, não origem/inserção. Projetar essas áreas no osso achatou os músculos: abriu 112–568 ciclos de borda por músculo e mudou o volume para 0,25–1,87× o da Denver.
- **Diferença de convenção de segmentação:** na figura, o reto femoral do BodyParts3D se estende ~200 mm abaixo do da Denver, sugerindo que o molde inclui tendão/ligamento patelar e a Denver só o ventre muscular. Isso pesa igual em B0 e M (não muda R1), mas infla as distâncias absolutas e o Dice.
- **R2:** passou por construção; não é evidência do método.

## 10. Limitações
- Uma única doadora (VHF): a prova é de viabilidade do método, não de generalização para outras mulheres.
- A Denver vem da mesma doadora do `hra-f`; a conferência é independente do método, não da doadora.
- O BP3D é masculino e de resolução moderada; erros do molde passam para o resultado.
- Diferenças de volume muscular entre sexos não são modeladas; R4 e a razão de volume mostram o tamanho desse efeito.
- Convenções diferentes de segmentação (tendão incluído ou não) entre BodyParts3D e Denver.

## 11. Conclusão
A preencher.

## 12. Próximos passos
A preencher.

## 13. Rastreabilidade
- `pesquisa/resultados/EXP-0025/` (scripts de adaptação e de avaliação separados, `insercoes.csv`, hashes das malhas adaptadas, métricas, figuras).

## 14. Revisão
- **Revisor:** Claude Code
- **Revisão humana:** pendente
- **Validação científica:** não realizada
