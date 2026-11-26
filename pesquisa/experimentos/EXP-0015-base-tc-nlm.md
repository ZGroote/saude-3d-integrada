# EXP-0015 — Atlas feminino com base na TC da NLM (inversão de base)

> **PROTOCOLO PRÉ-REGISTRADO:** Registrado **ANTES** da execução (`2026-11-26 ~01:50`, registro em `2026-11-26T01:45:53-03:00`).

## 1. Identificação
- **ID:** `EXP-0015`
- **Título:** Atlas feminino com base na TC da NLM (inversão de base)
- **Data e hora de registro:** `2026-11-26T01:45:53-03:00` (previsto `2026-11-26 ~01:50`)
- **Responsável:** Coordenador do projeto
- **Agentes de IA:** Antigravity (documentação); consultoria externa (ChatGPT)
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** não aplicável (pré-execução)
- **Linha de pesquisa:** `LP01`
- **Situação:** `executado parcialmente; nao aceito nesta rodada`

## 2. Problema
No `EXP-0014` (rodada real, commit `5ec1c34`), a tentativa de usar o HRA como corpo base foi **NÃO ACEITA**: o HRA remodelado por ilustradores diverge na pelve, pernas e coluna lombar (joelho `23–25 mm`, cabeça do fêmur à pelve HRA `17–21 mm`, `32/164` fora da pele HRA aberta, `28/164` sobreposições), enquanto **Denver ↔ TC NLM** (mesma doadora e mesmo exame) encaixa em `~3–4 mm`. A consultoria externa (ChatGPT) aprovou a inversão de base, vetou deformação não rígida global e sugeriu um teto de **5 dias úteis**.

## 3. Hipótese
Usando a **TC da NLM como corpo base** (`TotalSegmentator 'total' + 'body'`) com as **pernas da Denver** e **somente os complementos do HRA por ajuste local**, o atlas feminino passa no protocolo do `EXP-0014` sem afrouxar critérios.

## 4. Fundamentação teórica
Registro intramodal/cadavérico de mesma doadora (Denver STLs ↔ TC NLM) como estrutura anatômica primária, complementado por ajuste regional local (similaridade local e, apenas se falhar, deformação não rígida estritamente local e preservadora de volume) para estruturas não segmentadas na TC.

## 5. Materiais e ambiente (previstos)
- **Datasets e versões:**
  - TC original da NLM (`hra/nlm/bruto/tc_nlm_1p5.nii.gz`) segmentada com `TotalSegmentator 'total'` (`hra/nlm/bruto/saida/`) e `'body'`.
  - Modelos STL da University of Denver (`CC BY 4.0`, membros inferiores).
  - Complementos selecionados do HRA `v1.10` (`atlas/hra-f/1.10-1/`).
- **Licenças:** Denver `CC BY 4.0`; TotalSegmentator `'total'` sob `Apache-2.0`; **licença da task `'body'` do TotalSegmentator a confirmar no README oficial antes de usar — se não for aberta, PARAR e reportar**; Termos NLM (crédito NLM).
- **Hashes:** SHA-256 dos insumos, scripts, manifesto, avaliação e todos os STL registrados em `atlas/hra-f/2.0-1/proveniencia_sha256.json`.
- **Hardware:** não documentado.
- **Sistema operacional:** Windows.
- **Bibliotecas e versões:** `TotalSegmentator 2.18.0`, Python (`numpy`, `trimesh`, `nibabel`, `scikit-image`).
- **Seed:** a definir na execução.

## 6. Metodologia
### Fontes por estrutura (regra de fonte única)
- **Pele / superfície:** `TotalSegmentator` task `'body'` (com verificação prévia obrigatória de licença aberta no README oficial).
- **Esqueleto, órgãos, grandes vasos:** `TotalSegmentator 'total'` em resolução normal (`hra/nlm/bruto/saida/`).
- **Membros inferiores (ossos, músculos, cartilagens, ligamentos):** University of Denver, usando a transformação da Etapa A (`Denver → TC NLM`).
- **Somente do HRA:** útero, ovários, tubas, mama (glândula, lóbulos, ductos) e cérebro detalhado (Allen) — por **ajuste LOCAL por região**:
  - **Pelve:** âncoras em quadris, sacro e bexiga.
  - **Tórax:** âncoras em esterno, costelas e pulmões.
  - **Crânio:** âncoras em crânio/cérebro do TotalSegmentator.
  - Deformação não rígida **apenas local e preservadora de volume**, somente se a similaridade local falhar (deformação não rígida global vetada).
- **Placenta / âmnio / cordão:** camada gestacional separada (não entra no corpo base).

### Governança e prazo
- **Teto de esforço:** **5 dias úteis**. Se não passar até lá: congelar o que passou, marcar o restante como lacuna e voltar ao MVP clínico.
- **Saída prevista:** `atlas/hra-f/2.0-1` (nome do atlas a decidir: como o corpo deixa de ser HRA, propor **`vhf-f`**).
- **Comandos para reproduzir:** a definir na execução.

## 7. Critérios de sucesso (os MESMOS do EXP-0014, sem alteração + checagem pélvica)
- **Critérios geométricos (distância de superfície simétrica):**
  - Pele / superfície: média `≤ 10 mm`
  - Ossos grandes (fêmur, pelve, sacro+cóccix), órgãos grandes, músculos grandes: média `≤ 5 mm` e `p95 ≤ 12 mm`
  - Vértebras e grandes vasos: média `≤ 3 mm`
  - Pequenos vasos e nervos: avaliação individual
- **Critérios funcionais:**
  - **F1 — Contenção:** `≥ 99%` dos vértices dentro da pele `'body'` (agora malha fechada).
  - **F2 — Articulações:** quadril pela cabeça do fêmur Denver ao acetábulo do quadril do TotalSegmentator `≤ 5 mm`; joelho `≤ 5 mm`; costelas–vértebras `≤ 5 mm`; crânio–`C1` `≤ 5 mm`.
  - **F3 — Sobreposição:** `< 2%` do volume próprio invadindo órgãos/ossos.
  - **F4 — Lateralidade:** correta (`esquerda`/`direita`) em todas as estruturas.
  - **F5 — Revisão humana:** capturas em 4 vistas aprovadas por uma pessoa.
- **Critério adicional específico para complementos pélvicos do HRA:**
  - Útero e ovários dentro da cavidade pélvica (**F1** em relação à pele e **F3** em relação aos ossos e à bexiga).

## 8. Resultados (execução em 2026-11-26)
- Conferência da licença: README oficial lista `body` sob “Openly available for any usage (Apache-2.0 license)”; trecho e URL registrados em `hra/vhf/LEIAME.md`.
- Implementados `hra/vhf/montar_base.py` e `hra/vhf/avaliar_base.py`; dependências sem instalação: execução com `C:\Python314\python.exe` (os pacotes geométricos não estão no venv `C:\Users\respawn\venvs\totalseg\Scripts\python.exe`).
- Geração final corrigida: 229 malhas no manifesto, em RAS mm, incluindo 122 Denver; sem decimação. 227/229 malhas são watertight (as exceções são esôfago e lobo superior esquerdo); a pele `body` é watertight. Deriva volumétrica máxima após correção uniforme: `2,46e-15` (erro numérico).
- **F1:** `2.396.767 / 2.451.108` vértices dentro da pele (`97,78%`; **FAIL** frente a `≥99%`). 196/228 estruturas individualmente atingem 99%; o critério global falha, com concentração dos escapes nas malhas Denver distais e em alguns músculos/cartilagens, além de úmeros TotalSegmentator. Avaliação por classificação em grade sólida de 3 mm.
- **F2 quadril:** cabeça femoral Denver ao vértice mais próximo da malha `hip` TotalSegmentator: esquerda `19,418 mm`, direita `17,911 mm` (**FAIL** como proxy; acetábulo não vem segmentado separadamente). Centro da cabeça aproximado pelo centroide da cartilagem femoral.
- **F2 joelho:** separação mínima fêmur–tíbia: esquerda `5,693 mm` (**FAIL**), direita `4,948 mm` (**PASS**); aproximação por distância entre vértices amostrados, não centro articular.
- **F2 costelas–vértebras:** `1/24` pares ≤5 mm; faixa observada `3,821–46,612 mm` (**FAIL**). Distâncias são estimativas superfície-vértices amostradas; a correspondência nível a nível requer revisão.
- **F2 crânio–C1:** `3,350 mm` (**PASS**, distância mínima amostrada).
- **F3:** não avaliado. A tentativa all-pairs de sobreposição volumétrica excedeu os recursos locais; nenhum resultado foi inferido.
- **F4:** `178/178` estruturas laterais concordam com o sinal de X em RAS (**PASS**); estruturas medianas excluídas.
- **F5:** pendente; nenhuma revisão humana/captura em 4 vistas.
- **Ambiente de montagem/avaliação:** Python 3.14.4; numpy 2.4.6; nibabel 5.5.0; trimesh 5.2.2; scikit-image 0.26.0; scipy 1.18.1. Sem instalação de pacotes; execução no Python local com dependências geométricas disponíveis.

- **Hashes SHA-256:** entradas (`total`, `body`, transformação Etapa A), manifesto e avaliação registrados em `atlas/hra-f/2.0-1/proveniencia_sha256.json`.

## 9. Validação
Parcial e **não aceita** pelos critérios funcionais: F1 falha; F2 quadril proxy e joelho esquerdo falham; costelas–vértebras falham; F3 não avaliado; F5 pendente. Joelho direito, crânio–C1 e F4 passaram nas métricas exploratórias. Nenhum resultado é validação clínica.

## 10. Limitações
Dependência de confirmação prévia da licença aberta da task `'body'`, da qualidade do fechamento da malha de pele gerada e do prazo máximo de 5 dias úteis.

## 11. Conclusão
- **Observado:** licença `Apache-2.0` da task `body` confirmada; corpo-base foi exportado com fonte única, incluindo sacro/S1 TotalSegmentator e membros inferiores Denver.
- **Interpretação:** os resultados atuais não sustentam aceitação; F1 abaixo do limite e falhas em articulações/alinhamento costovertebral. O protocolo e limites não foram afrouxados.
- **Veredito da hipótese:** `não aceita nesta rodada; F3/F5 e quadril seguem lacunas`

## 12. Próximos passos
1. Investigar F1 e as separações funcionais que falharam sem deformação global.
2. Executar F3 com avaliação de sobreposição volumétrica por pares anatomicamente relevantes; resolver disponibilidade do acetábulo para o F2.
3. Obter revisão humana F5 em quatro vistas.

## 13. Rastreabilidade
- **Commits:** não aplicável (pré-execução)
- **Scripts:** `hra/vhf/segmentar_body.py`, `hra/vhf/montar_base.py`, `hra/vhf/avaliar_base.py`; matriz etapa A: `hra/alinhar/transformacoes.json`
- **Logs:** não aplicável
- **Resultados / artefatos:** `pesquisa/experimentos/EXP-0015-base-tc-nlm.md`

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** pendente
- **Validação científica:** pendente
- **Validação clínica:** pendente
