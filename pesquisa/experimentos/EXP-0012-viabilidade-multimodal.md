# EXP-0012 — Estudo de viabilidade: reconstrução multimodal (TC + RM + máscaras Denver) para o atlas feminino

## 1. Identificação
- **ID:** `EXP-0012`
- **Título:** Estudo de viabilidade multimodal (TC + RM + máscaras Denver) para completar o atlas feminino `hra-f`
- **Data:** `2026-11-25`
- **Responsável:** não documentado
- **Agentes de IA:** Antigravity (pesquisa documental e redação)
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** não aplicável (estudo pré-execução)
- **Linha de pesquisa:** `LP01`
- **Situação:** `planejado`

## 2. Problema
O atlas feminino `hra-f 1.10-1` (956 malhas) possui cobertura parcial de esqueleto, músculos e vasos (`EXP-0005`). O alinhamento Denver STL→TC NLM por ICP (`EXP-0011`, usando segmentação `--fast` de 3 mm) resultou em erro médio de ~3,3 mm nos fêmures, ~2,7 mm na pelve e `3,990 mm` no sacro (*holdout*), reprovando no critério `< 3 mm`. Resta avaliar se a incorporação de dados multimodais (máscaras `.mhd`/Slicer da Denver, ressonância magnética da NLM e `TotalSegmentator total_mr`) é viável e capaz de fechar as lacunas anatômicas restantes do atlas feminino.

## 3. Hipótese
A integração multimodal aumenta a cobertura anatômica sem comprometer a precisão geométrica.

## 4. Fundamentação teórica
Registro imagem-a-imagem intramodal (TC Denver × TC NLM) e multimodal (RM NLM × TC NLM por informação mútua), combinados com segmentação semântica aberta (`TotalSegmentator total` em TC e `total_mr` em RM, licença Apache-2.0).

## 5. Materiais e ambiente (previstos)
- **Datasets e versões:**
  - University of Denver Visible Human Female (<https://digitalcommons.du.edu/visiblehuman/1/>, DOI `10.56902/COB.vh.2022.1`, 2022): já baixados `Final 3D STL Models` (87,8 MB), `Aligned CT DICOM` (301,9 MB) e `Metadata` (55 KB). Pacote opcional não baixado: `Original Segmentation Masks and Aligned Scans (.mhd)` (1.318,1 MB).
  - NLM Visible Human Female MRI (`https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Female-Images/radiological/mri/` e `mriHeaders/`).
  - NLM Visible Human Female CT original (`hra/nlm/bruto/tc_nlm_1p5.nii.gz`).
  - HRA United Female `v1.10` (`atlas/hra-f/1.10-1/`).
- **Licenças:** Denver `CC BY 4.0`; NLM VHP sem licença desde 2019 (exige crédito `"Courtesy of the U.S. National Library of Medicine"` e não-endosso); TotalSegmentator `total` e `total_mr` sob `Apache-2.0`.
- **Hashes:** `não documentado` (pré-execução).
- **Hardware:** `NVIDIA GeForce GTX 1650, 4 GB` + CPU (`hra/totalseg/LEIAME.md`).
- **Sistema operacional:** Windows.
- **Bibliotecas e versões:** `TotalSegmentator 2.18.0`, `PyTorch 2.11.0+cu128`, `CUDA 12.8`.
- **Seed:** a definir no protocolo de execução.

---

## 6. Levantamento de viabilidade (evidências observadas vs. inferências)

### 6.1 Máscaras da University of Denver
- **Observado (`https://digitalcommons.du.edu/visiblehuman/1/`):**
  - A página disponibiliza `Aligned CT DICOM` (301,9 MB), `Aligned Cryosection DICOM` (462,7 MB), `Original Segmentation Masks and Aligned Scans (.mhd)` (1.318,1 MB), `Original Segmentation Masks and Aligned Scans (3D Slicer)` (2.616,3 MB), `Smoothed Segmentation Masks and Aligned Scans (3D Slicer)` (2.073,7 MB), `Final Segmentation Masks and Aligned Scans (3D Slicer)` (2.076,0 MB), além dos STLs (`87,8 MB` final) e `Metadata` (`55 KB`).
  - Descrição literal da página: os *Aligned and Rescaled CT Images* estão alinhados às imagens de criocortes com deslocamentos corrigidos e disponíveis em DICOM, TIFF e MHD; as máscaras estão em NRRD (3D Slicer) e mapas binários em MHD, TIFF e `.mat`.
- **Observado localmente (`hra/denver/bruto/MetaData/README.txt` e `hra/denver/bruto/Aligned CT-DICOM/README.txt`):** ambos contêm o mesmo texto institucional citando Andreassen et al. (2022, DOI `10.1038/s41597-022-01905-2` e `10.48550/arXiv.2209.06948`), dataset DOI `10.56902/COB.vh.2022.0` e licença **CC BY 4.0**. Não descrevem cabeçalhos `.mhd` nem offsets.
- **Inferência:**
  - **(a) Referencial exato dos STL:** como os `.mhd` acompanham os *Aligned Scans*, seus cabeçalhos devem declarar `ElementSpacing` e `Offset`, permitindo auditar o referencial dos STLs; entretanto, isso está **`não confirmado`** sem baixar o pacote mínimo de máscaras `.mhd` (`1.318,1 MB`).
  - **(b) Alinhamento imagem-a-imagem TC Denver × TC NLM:** a `Aligned CT DICOM` da Denver **já está baixada** (`hra/denver/bruto/tc_alinhada.nii.gz`) e é do mesmo sujeito da TC original da NLM (`tc_nlm_1p5.nii.gz`), permitindo testar registro imagem-a-imagem (por correlação normalizada / informação mútua) **sem nenhum download adicional**, embora a TC da Denver não tenha HU negativos (`EXP-0006`).

### 6.2 Ressonância Magnética do Visible Human Female (NLM)
- **Observado:** acesso direto via HTTP (`urllib` e `curl.exe -sI`) a `https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Female-Images/radiological/mri/` e `mriHeaders/` retornou **`HTTP 403 Forbidden`** (AmazonS3/CloudFront bloqueia listagem de diretório e acesso sem nome exato de objeto). Por esse motivo, contagem exata de cortes, resolução por bloco e leitura literal de 2–3 cabeçalhos `.txt` ficaram **`não confirmado`**.
- **Observado via busca documental (`datadiscovery.nlm.nih.gov` / `nih.gov`):** o acervo da Visible Human Female inclui aquisições de RM ponderadas em **T1, T2 e Densidade Protônica (PD)** em formato GE original com arquivos de texto em `mriHeaders/` (e equivalentes PNG), adquiridas **antes do congelamento** do cadáver.
- **Suficiência para segmentar músculos/tecidos moles (inferência):** **`não confirmado`** sem leitura direta dos `mriHeaders/*.txt`; aquisições clínicas em blocos com espessura típica de ~3 mm podem gerar descontinuidade axial e artefatos de movimento/posicionamento pré-congelamento.

### 6.3 TotalSegmentator `total_mr`
- **Observado literalmente (`https://raw.githubusercontent.com/wasserth/TotalSegmentator/master/README.md`):**
  - Licença: **`Openly available for any usage (Apache-2.0 license):`**
  - Tarefa **`total_mr`**: **`50` classes principais**: `spleen`, `kidney_right`, `kidney_left`, `gallbladder`, `liver`, `stomach`, `pancreas`, `adrenal_gland_right`, `adrenal_gland_left`, `lung_left`, `lung_right`, `esophagus`, `small_bowel`, `duodenum`, `colon`, `urinary_bladder`, `prostate`, `sacrum`, `vertebrae`, `intervertebral_discs`, `spinal_cord`, `heart`, `aorta`, `inferior_vena_cava`, `portal_vein_and_splenic_vein`, `iliac_artery_left`, `iliac_artery_right`, `iliac_vena_left`, `iliac_vena_right`, `humerus_left`, `humerus_right`, `scapula_left`, `scapula_right`, `clavicula_left`, `clavicula_right`, `femur_left`, `femur_right`, `hip_left`, `hip_right`, `gluteus_maximus_left`, `gluteus_maximus_right`, `gluteus_medius_left`, `gluteus_medius_right`, `gluteus_minimus_left`, `gluteus_minimus_right`, `autochthon_left`, `autochthon_right`, `iliopsoas_left`, `iliopsoas_right`, `brain`.
  - Tarefas como `appendicular_bones_mr` e `tissue_types_mr` exigem licença comercial específica.
- **Ganho real sobre a TC (`total`):** apenas **`intervertebral_discs`** e **`brain`** (não presentes de forma equivalente na tarefa `total` de TC). **Não acrescenta** ossos do antebraço/mão, músculos dos membros superiores nem vasos periféricos dos membros.

### 6.4 Matriz de cobertura das lacunas do atlas feminino (`hra-f`)

| Lacuna atual do `hra-f` | Fonte aberta identificada | Cobertura / observação |
|---|---|---|
| **Antebraço / mãos** (rádio, ulna, carpo, metacarpo, falanges) | **nenhuma fonte aberta identificada** | Denver cobre só pelve–pés; `total` e `total_mr` param no úmero; `appendicular_bones*` é comercial. |
| **Músculos do braço** (bíceps, tríceps, deltoide, antebraço) | **nenhuma fonte aberta identificada** | Denver cobre só membros inferiores; `total` e `total_mr` cobrem apenas glúteos, autóctones e iliopsoas. |
| **Vasos dos membros** (braquiais, radiais, ulnares, femorais, tibiais) | **nenhuma fonte aberta identificada** | `total` e `total_mr` param nas ilíacas; Denver não possui vasos. |
| **Nervos** (periféricos / plexos) | **nenhuma fonte aberta identificada** | `hra-f` já tem encéfalo, medula e ópticos; `total_mr` só acrescenta `brain` e `spinal_cord`. |
| **Cartilagens** (articulares e discos) | **Parcial:** Denver (`CC BY 4.0`, 16 STLs nos membros inferiores) e `total_mr` (`Apache-2.0`, `intervertebral_discs`) | Membros superiores e demais cartilagens: **nenhuma fonte aberta identificada**. |

### 6.5 Riscos e custo
- **Downloads:** pacote `.mhd` da Denver exige `1.318,1 MB`; RM da NLM tem tamanho total `não confirmado` (acesso por S3/Data Discovery).
- **Esforço:** alto para registro multimodal RM↔TC NLM (diferenças de postura pré- vs. pós-congelamento, blocos parciais e espessura ~3 mm); baixo/médio para registro imagem-a-imagem TC Denver × TC NLM (arquivos já locais).
- **Risco geométrico:** deformação de tecidos moles entre RM pré-congelamento e TC/criocortes pós-congelamento pode degradar a precisão (< 3 mm) exigida para ancoragem anatômica.
- **Licença:** todas as fontes abertas avaliadas (`CC BY 4.0`, `Apache-2.0`, NLM sem taxa com crédito) são compatíveis com o projeto; subtarefas comerciais do TotalSegmentator estão descartadas.

---

## 7. Metodologia proposta (caso o experimento seja executado)
- **Método A (só TC):** usar `tc_nlm_1p5.nii.gz` + TotalSegmentator `total` em resolução completa (ou blocos) + registro imagem-a-imagem TC Denver × TC NLM para alinhar os 128 STLs da Denver (ossos, 76 músculos inferiores, 16 cartilagens, 8 ligamentos).
- **Método B (só RM):** baixar e inspecionar `mriHeaders` e volumes RM da NLM, converter para NIfTI e rodar `TotalSegmentator total_mr` (`intervertebral_discs`, `brain`, vértebras/órgãos).
- **Método C (integração multimodal):** registrar RM→TC NLM (rígido/afim por informação mútua) e fundir `intervertebral_discs` + malhas da TC + STLs da Denver no referencial do `hra-f`.

## 8. Critérios de sucesso (definidos ANTES de qualquer execução)
1. **Ganho de cobertura:** aumento líquido de estruturas anatômicas únicas no `hra-f` sem duplicação de IDs de ontologia.
2. **Precisão geométrica:** erro médio simétrico de superfície em estruturas *holdout* independentes **`< 3,0 mm`** (P95 `< 8,0 mm`) no alinhamento Denver→TC NLM e TC NLM→HRA.
3. **Coerência multimodal (se Método C):** erro médio entre superfícies ósseas da RM (`vertebrae`, `femur`) e da TC após registro RM→TC **`< 3,0 mm`**.
4. **Conformidade legal e técnica:** 100% das fontes sob `CC BY 4.0`, `Apache-2.0` ou termos NLM, com SHA-256 validado e viável na GPU de 4 GB.

## 9. Resultados
Planejado — não executado.

## 10. Validação
Planejado — não executado.

## 11. Limitações
Listagem direta de `mri/` e `mriHeaders/` bloqueada por `HTTP 403` na sessão atual; pacotes `.mhd` (1,3 GB) não inspecionados para respeitar o limite de 50 MB do estudo.

## 12. Conclusão
- **Observado:** `total_mr` (Apache-2.0, 50 classes) quase não amplia a cobertura periférica além da TC (`total`), acrescentando essencialmente `intervertebral_discs` e `brain`; antebraço/mãos, músculos do braço, vasos distais e nervos periféricos seguem sem fonte aberta identificada.
- **Interpretação:** a reconstrução multimodal completa (TC+RM) traz alto custo de registro com baixo ganho de cobertura periférica para o MVP.
- **Veredito da hipótese:** `em aberto`

## 13. Recomendação
- **Fazer primeiro (no MVP):**
  1. Concluir o alinhamento **só com TC (`Método A`)**: testar o registro imagem-a-imagem entre `hra/denver/bruto/tc_alinhada.nii.gz` (já baixada) e `hra/nlm/bruto/tc_nlm_1p5.nii.gz` e/ou rodar `TotalSegmentator total` sem `--fast` nos ossos da pelve/sacro/fêmur para reduzir o erro do sacro (`3,990 mm` -> `< 3 mm`) e incorporar os **128 STLs da Denver** (ossos, músculos inferiores, cartilagens e ligamentos) ao `hra-f`.
  2. Documentar explicitamente na UI as lacunas estruturais restantes do `hra-f` (antebraço/mãos, músculos superiores, vasos periféricos), conforme `SPEC-MVP.md` §5.1.
- **Deixar para depois do MVP:**
  1. Download e inspeção dos cabeçalhos/volumes de RM da NLM (`Método B` / `C`) apenas se houver demanda clínica específica por `intervertebral_discs` no atlas feminino.
  2. Busca por fontes abertas futuras (ou modelagem anatômica específica em parceria acadêmica com a UFSCar) para membros superiores e vasos/nervos periféricos.

## 14. Rastreabilidade
- **Commits:** não aplicável (planejado)
- **Scripts:** não aplicável
- **Logs:** não aplicável
- **Resultados / artefatos:** `pesquisa/experimentos/EXP-0012-viabilidade-multimodal.md`

## 15. Revisão
- **Revisor:** não documentado
- **Revisão humana:** pendente
- **Validação científica:** pendente
- **Validação clínica:** não aplicável
