# EXP-0021 — Frente B: Levantamento de Fontes Anatômicas Femininas

**Protocolo:** [EXP-0021-inventario-atlas-feminino-v3.md](../../experimentos/EXP-0021-inventario-atlas-feminino-v3.md) (Seção 6, Frente B; Critério B1)
**Data:** 2026-11-27
**Regra de registro:** Todo campo traz a URL comprobatória exata verificada nesta investigação. O que não pôde ser comprovado diretamente por URL está marcado como `não verificado` (ou `não verificado (site bloqueou)` quando houve bloqueio HTTP). Nenhum conjunto de dados grande foi baixado.

---

## 1. Female Atlas (`HiMahendraBeniwal/female-atlas`)

| Campo | Registro verificado | URL comprobatória |
| :--- | :--- | :--- |
| **1. Disponibilidade real para download** | **Sim, aberto e público no GitHub.** Os arquivos de modelo estão versionados diretamente em `public/models/` (`atlas.json`, `female-0.bin`..`female-21.bin` e `.bin.gz`). | https://github.com/HiMahendraBeniwal/female-atlas \| https://api.github.com/repos/HiMahendraBeniwal/female-atlas/contents/public/models |
| **2. Formato** | **JSON + buffers binários comprimidos (`atlas.json` + `.bin` / `.bin.gz`)** consumidos via Three.js (`meshoptimizer`), não `.glb` nativo. | https://api.github.com/repos/HiMahendraBeniwal/female-atlas/contents/public/models \| https://raw.githubusercontent.com/HiMahendraBeniwal/female-atlas/main/public/models/atlas.json |
| **3. Nº de estruturas** | **3.004** peças selecionáveis, **2.557** estruturas anatômicas nomeadas, em **16 sistemas** (`Skeletal: 343`, `Muscular: 416`, `Arterial: 666`, `Venous: 413`, `Reproductive: 54`, `Pregnancy: 8`, `Cardiac: 58`, `Digestive: 158`, `Respiratory: 189`, `Urinary: 93`, `Nervous: 434`, `Sensory: 98`, `Endocrine: 7`, `Lymphatic: 17`, `Integumentary: 5`, `Connective: 46`). | https://raw.githubusercontent.com/HiMahendraBeniwal/female-atlas/main/README.md \| https://raw.githubusercontent.com/HiMahendraBeniwal/female-atlas/main/public/ATTRIBUTION.md |
| **4. Origem dos dados** | Compósito: **HRA** *3D Reference Organ Set for Female v1.5* (2023, DOI `10.48539/HBM352.BTSQ.586`) para vísceras/reprodutor/mamas/gestacional + **BodyParts3D** (DBCLS) para esqueleto, 416 músculos e vasculatura periférica, com adaptações morfológicas femininas feitas por Mahendra Beniwal. *(Atenção: mistura BodyParts3D masculino deformado com HRA v1.5.)* | https://raw.githubusercontent.com/HiMahendraBeniwal/female-atlas/main/public/ATTRIBUTION.md |
| **5. Licença (uso / modificação / redistribuição / uso comercial)** | Código sob **MIT License** (`LICENSE`); dados anatômicos sob **CC BY 4.0** (`ATTRIBUTION.md`). Uso, modificação, redistribuição e uso comercial são permitidos mediante atribuição a HRA/HuBMAP, DBCLS BodyParts3D e ao autor. | https://raw.githubusercontent.com/HiMahendraBeniwal/female-atlas/main/LICENSE \| https://raw.githubusercontent.com/HiMahendraBeniwal/female-atlas/main/public/ATTRIBUTION.md |
| **6. Resolução** | Simplificação de malha com limite de erro relativo de **0,2%** por estrutura via `meshoptimizer`; normais quantizadas em **16-bit**. Contagem total de triângulos não declarada no README (`não verificado` sem baixar todos os `.bin`). | https://raw.githubusercontent.com/HiMahendraBeniwal/female-atlas/main/public/ATTRIBUTION.md |
| **7. Referencial** | Coordenadas Three.js em metros (`bounds` em `atlas.json`, ex.: `y` entre `1.14` e `1.32` na mama) com proporções morfológicas femininas aplicadas pelo autor, sem validação anatômica/médica declarada. | https://raw.githubusercontent.com/HiMahendraBeniwal/female-atlas/main/public/models/atlas.json \| https://raw.githubusercontent.com/HiMahendraBeniwal/female-atlas/main/README.md |
| **8. Método de reconstrução** | Soldagem de vértices coincidentes (*welding*), cálculo de normais médias, decimação via `meshoptimizer` (`0,2%` erro relativo) e deformação morfológica manual/computacional sobre malhas HRA + BodyParts3D. | https://raw.githubusercontent.com/HiMahendraBeniwal/female-atlas/main/public/ATTRIBUTION.md |

---

## 2. Visible Korean Female (KISTI / Ajou University)

| Campo | Registro verificado | URL comprobatória |
| :--- | :--- | :--- |
| **1. Disponibilidade real para download** | **Não há download público aberto dos conjuntos completos.** Exige envio de formulário oficial de solicitação de uso para pesquisa (`정보이용신청서(연구용)`) à KISTI (`sblee@kisti.re.kr`) e cópia/entrega após aprovação (com ressarcimento de custos). PDFs demonstrativos gratuitos (ex.: `PDF_Female pelvis.pdf`, 20 MB) estão disponíveis para download direto. | https://vkh3.kisti.re.kr/?q=node/4 \| https://vkh3.kisti.re.kr/?q=node/12 |
| **2. Formato** | **Visible Female (corpo inteiro):** TC em `.bmp` / `.dcm`; criossecções em `.tiff`; segmentação em `.bmp`; 3D listado como em andamento (`진행 중 부위별 제공가능`). **Visible Pelvis (pelve feminina):** RM T1/T2 e TC em `.bmp` / `.dcm`; criossecções em `.tiff`; segmentação em `.bmp`; modelos 3D em **`.mb` (Maya)**. | https://vkh3.kisti.re.kr/?q=node/4 |
| **3. Nº de estruturas** | **Visible Pelvis (VP):** **154** estruturas segmentadas (`VP-4`) e **143** modelos 3D (`VP-5`). **Visible Female (VF, corpo inteiro):** `não verificado` (a tabela da KISTI lista `VF-3` sem contagem de estruturas e `VF-4` 3D como em andamento; Chung et al., 2021 informam conclusão da segmentação do corpo inteiro feminino, sem contagem numérica no resumo). | https://vkh3.kisti.re.kr/?q=node/4 \| https://pubmed.ncbi.nlm.nih.gov/32803722/ |
| **4. Origem dos dados** | Cadáveres coreanos doados ao projeto na Ajou University School of Medicine: **Visible Female (corpo inteiro):** mulher, 26 anos, 160 cm, 53 kg (início 2008, sem RM); **Visible Pelvis (pelve feminina):** mulher, 43 anos, 152 cm, 54 kg (2007, com RM 3 T e TC). | https://vkh3.kisti.re.kr/?q=node/4 \| https://vkh3.kisti.re.kr/?q=node/24 |
| **5. Licença (uso / modificação / redistribuição / uso comercial)** | **Contrato restritivo da KISTI (não é licença aberta):** uso restrito ao laboratório solicitante sob responsabilidade do pesquisador; relatório anual obrigatório à KISTI; proibida redistribuição a outros laboratórios/instituições sem notificar a KISTI; **uso comercial ou pesquisa com empresas exige notificação e contrato comercial adicional separado com a KISTI**; exige agradecimento à KISTI e Depto. de Anatomia da Ajou Univ.; exige destruição dos dados e certificado ao fim do prazo. | https://vkh3.kisti.re.kr/?q=node/4 |
| **6. Resolução** | **Visible Female:** TC `1,0 mm`, `512×512` (`.dcm`, 1.764 fatias); criossecções `0,2 mm` / `1,0 mm`, **`5616×3744` px** (`.tiff`, 4.937 fatias, 356 GB); segmentação `1,0 mm`, `5616×3744` (`.bmp`, 42,4 GB). **Visible Pelvis:** RM T1/T2 `1,0 mm` (`512×512`, 230 fatias cada); TC `1,0 mm` (`512×512`, 256 fatias); criossecções **`0,1 mm`**, `4368×2912` px (2.500 fatias, 47,8 GB); segmentação `1,0 mm`. | https://vkh3.kisti.re.kr/?q=node/4 |
| **7. Referencial** | Alinhamento serial em bloco congelado (`-70 °C`) na caixa de inclusão paralela ao eixo longitudinal da mesa de RM/TC guiado por laser. Sistema de coordenadas 3D exato dos modelos `.mb`: `não verificado`. | https://vkh3.kisti.re.kr/?q=node/24 |
| **8. Método de reconstrução** | Congelamento (`-70 °C`), criosseccionamento serial em criomácrotono (`0,1 mm` / `0,2 mm`, erro `0,001 mm`), fotografia digital de alta resolução, segmentação manual/semi-automática em fatias e reconstrução de superfície em Maya. | https://vkh3.kisti.re.kr/?q=node/24 \| https://pubmed.ncbi.nlm.nih.gov/32803722/ |

---

## 3. Chinese Visible Human (CVH — Female: CVH-2 / CVH-4 / CVH-5)

| Campo | Registro verificado | URL comprobatória |
| :--- | :--- | :--- |
| **1. Disponibilidade real para download** | **Não é aberto para download público direto.** Não há espelho aberto verificado para os conjuntos completos; os dados são obtidos somente via solicitação institucional e assinatura de acordo formal de licença (*licence agreement*) com a Third Military Medical University (atual Army Medical University, Chongqing, China). | https://pmc.ncbi.nlm.nih.gov/articles/PMC1571260/ \| https://pubmed.ncbi.nlm.nih.gov/15032906/ |
| **2. Formato** | Fatias criosseccionadas em **TIFF** (*true-color*, ~36 MB/fatia no CVH-2; ~62,9 MB/fatia no CVH-4/5); TC e RM prévias em matriz `512×512`. Malhas 3D públicas (`.glb`/`.obj`/`.stl`): não distribuídas em repositório aberto oficial. | https://pmc.ncbi.nlm.nih.gov/articles/PMC1571260/ \| https://pmc.ncbi.nlm.nih.gov/articles/PMC3584111/ |
| **3. Nº de estruturas** | O dataset bruto é composto por pilhas de imagens transversais sem malhas pré-segmentadas de fábrica. Em segmentação derivada reportada na literatura (Wu et al., 2012), citam-se **90** estruturas no CVH feminino, porém o texto primário desse artigo não foi verificado diretamente nesta pesquisa (**contagem derivada: `não verificado` em fonte primária**). | https://pmc.ncbi.nlm.nih.gov/articles/PMC1571260/ |
| **4. Origem dos dados** | Cadáveres humanos adultos chineses sem lesões orgânicas, processados na TMMU (Chongqing): **CVH-2 (Female):** 22 anos, 162 cm, 54,0 kg (fev/2003); **CVH-4 (Female):** 25 anos, 162 cm, 57,5–57,7 kg; **CVH-5 (Female):** 25 anos, 170 cm, 59,0 kg. | https://pmc.ncbi.nlm.nih.gov/articles/PMC1571260/ \| https://pmc.ncbi.nlm.nih.gov/articles/PMC3584111/ |
| **5. Licença (uso / modificação / redistribuição / uso comercial)** | Sob **acordo formal de licença institucional (*licence agreement*)** com a TMMU. Termos específicos para uso, modificação, redistribuição e uso comercial não estão publicados em URL aberta: **`não verificado`**. | https://pmc.ncbi.nlm.nih.gov/articles/PMC1571260/ |
| **6. Resolução** | **CVH-2:** 3.640 fatias axiais em `3072×2048` px (~170 µm/px), corte `0,25 mm` (cabeça) e `0,5 mm` (corpo), ~131,04 GB; TC/RM `512×512`. **CVH-4:** `4064×2704` px, `0,25 mm` (cabeça). **CVH-5:** `4064×2704` px, `0,2 mm` uniforme (8.510 imagens, ~535 GB). | https://pmc.ncbi.nlm.nih.gov/articles/PMC1571260/ \| https://pmc.ncbi.nlm.nih.gov/articles/PMC3584111/ |
| **7. Referencial** | Alinhamento primário por **4 hastes plásticas fiduciais longitudinais** na gelatina de inclusão. No atlas encefálico derivado (CVH-1, 2, 4, 5), coordenadas estereotáxicas **AC-PC**. | https://pmc.ncbi.nlm.nih.gov/articles/PMC1571260/ \| https://pmc.ncbi.nlm.nih.gov/articles/PMC3584111/ |
| **8. Método de reconstrução** | TC e RM prévias, perfusão vascular com gelatina colorida, inclusão em bloco com 4 hastes fiduciais, criomilling/criosseccionamento a `-25 °C`, fotografia digital e alinhamento fiducial; reconstrução 3D em estudos derivados via *volume rendering* e segmentação manual/semi-automática. | https://pmc.ncbi.nlm.nih.gov/articles/PMC1571260/ \| https://pmc.ncbi.nlm.nih.gov/articles/PMC3584111/ |

---

## 4. HRA-VCCF (*Human Reference Atlas — Vasculature Common Coordinate Framework*)

| Campo | Registro verificado | URL comprobatória |
| :--- | :--- | :--- |
| **1. Disponibilidade real para download** | **Sim, aberto e público** no GitHub (`hubmapconsortium/hra-vccf`), Zenodo (`10.5281/zenodo.7542316`) e portal HRA (`humanatlas.io/vccf`). *(Nota: `lod.humanatlas.io/ds-graph/vccf` e `cdn.humanatlas.io/digital-objects/ds-graph/vccf/latest/README.md` retornaram HTTP 404.)* | https://github.com/hubmapconsortium/hra-vccf \| https://pmc.ncbi.nlm.nih.gov/articles/PMC10356915/ \| https://humanatlas.io/vccf |
| **2. Formato** | **Tabelas `.csv`** (`Vessel.csv`, `Geometry.csv`, `CellTypeBiomarker.csv`, `VesselCTB.csv`, `VesselOrganCrosswalk.csv`), **`.sql`** e `schema.yaml`. **Não contém malhas 3D próprias** no repositório `hra-vccf`: apenas colunas de ponteiro (`SpatialReferenceObjectFemale`, `SpatialReferenceObjectMale`) para objetos 3D do HRA (ex.: `VH_F_*`). | https://api.github.com/repos/hubmapconsortium/hra-vccf/contents/ \| https://raw.githubusercontent.com/hubmapconsortium/hra-vccf/main/Vessel.csv |
| **3. Nº de estruturas** | **993 vasos sanguíneos** e conexões de ramificação, **10 tipos celulares** e **10 biomarcadores** na publicação de 2023 (*Scientific Data*); no repositório `main` atual, `Vessel.csv` possui **244 linhas** (cabeçalho + 243 linhas), `Geometry.csv` **194 linhas** e `VesselOrganCrosswalk.csv` **577 linhas**. | https://pmc.ncbi.nlm.nih.gov/articles/PMC10356915/ \| https://raw.githubusercontent.com/hubmapconsortium/hra-vccf/main/Vessel.csv |
| **4. Origem dos dados** | Base curada a partir da literatura científica e revisão por especialistas (ASCT+B / HRA), vinculando propriedades geométricas de estudos clínicos (CT, ultrassom, etc.) e ponteiros aos órgãos de referência 3D do HRA (derivados do *Visible Human Project*). | https://pmc.ncbi.nlm.nih.gov/articles/PMC10356915/ \| https://raw.githubusercontent.com/hubmapconsortium/hra-vccf/main/Geometry.csv |
| **5. Licença (uso / modificação / redistribuição / uso comercial)** | Dados (`.csv`): **Creative Commons Attribution 4.0 International (CC BY 4.0)** — permite uso, modificação, redistribuição e uso comercial com atribuição. Código (`.sql`): **MIT License**. | https://raw.githubusercontent.com/hubmapconsortium/hra-vccf/main/README.md \| https://raw.githubusercontent.com/hubmapconsortium/hra-vccf/main/LICENSE |
| **6. Resolução** | **Não aplicável como malha/imagem** (base tabular/ontológica). `Geometry.csv` registra medidas lineares em `cm` (comprimento e diâmetro luminal por sexo/estudo). Resolução dos objetos 3D apontados (`VH_F_*`): `não verificado` neste repositório. | https://raw.githubusercontent.com/hubmapconsortium/hra-vccf/main/Geometry.csv |
| **7. Referencial** | Ontológico e topológico (árvore vascular a partir do coração: `BranchesFrom`, `PathFromHeart`, **UBERON** e **FMA** no formato `FMA:NNNNN`), com ponteiros nominais `VH_F_*` e `VH_M_*` para o HRA CCF e coordenadas 2D esquemáticas (`CoordX`, `CoordY`). | https://raw.githubusercontent.com/hubmapconsortium/hra-vccf/main/Vessel.csv \| https://raw.githubusercontent.com/hubmapconsortium/hra-vccf/main/README.md |
| **8. Método de reconstrução** | **Curadoria manual da literatura e modelagem relacional/ontológica** (sem reconstrução 3D de imagem neste dataset; apenas vinculação a objetos 3D externos do HRA). | https://pmc.ncbi.nlm.nih.gov/articles/PMC10356915/ |

---

## 5. University of Denver (*Visible Human Female* — máscaras e exames)

| Campo | Registro verificado | URL comprobatória |
| :--- | :--- | :--- |
| **1. Disponibilidade real para download** | **Sim, aberto e público** no Digital Commons @ DU (DOI `10.56902/COB.vh.2022.1`): `Aligned CT DICOM` (301,9 MB), `Aligned Cryosection DICOM` (462,7 MB), `Original Segmentation Masks and Aligned Scans (.mhd)` (1.318,1 MB), pacotes 3D Slicer (2.073–2.616 MB), `Final 3D STL Models` (87,8 MB) e `Metadata` (55 KB). *(O pacote `Final 3D STL Models` e o `Metadata` já foram inspecionados localmente em `hra/denver/`.)* | https://digitalcommons.du.edu/visiblehuman/1/ |
| **2. Formato** | **`.stl`**, **`.dcm` (DICOM)**, **`.mhd` (MetaImage)**, **`.nrrd` (3D Slicer)**, `.tiff` e `.mat`. | https://digitalcommons.du.edu/visiblehuman/1/ |
| **3. Nº de estruturas** | **128 modelos STL** no pacote final (28 ossos, 76 músculos, 16 cartilagens, 8 ligamentos; **2.335.390 triângulos**; região da pelve até os pés); TC alinhada com **1.727 cortes**. | https://digitalcommons.du.edu/visiblehuman/1/ (e relatório local `hra/denver/RELATORIO.md`) |
| **4. Origem dos dados** | Criossecções e TC do cadáver feminino do *Visible Human Project* (NLM), processados pelo Center for Orthopaedic Biomechanics (University of Denver, Andreassen et al., 2022). | https://digitalcommons.du.edu/visiblehuman/1/ \| https://doi.org/10.1038/s41597-022-01905-2 |
| **5. Licença (uso / modificação / redistribuição / uso comercial)** | **Creative Commons Attribution 4.0 International (CC BY 4.0)** — permite uso, modificação, redistribuição e uso comercial mediante atribuição/citação (Andreassen et al., 2022). | https://digitalcommons.du.edu/visiblehuman/1/ (e `hra/denver/bruto/MetaData/README.txt`) |
| **6. Resolução** | STL bruto ScanIP `~0,33 mm`; *smoothed* (músculo `1,5 mm`, osso `1,0 mm`, cartilagem/ligamento `0,75 mm`); TC DICOM `0,722656 × 0,722656 × 1,0 mm` (`673×670×1727`). | https://digitalcommons.du.edu/visiblehuman/1/ (e `hra/denver/RELATORIO.md`) |
| **7. Referencial** | LPS → RAS, porém com tags DICOM `ImagePositionPatient (IPP)` e `ImageOrientationPatient (IOP)` ausentes na TC alinhada (registrado em `hra/denver/RELATORIO.md`). | https://digitalcommons.du.edu/visiblehuman/1/ (e `hra/denver/RELATORIO.md`) |
| **8. Método de reconstrução** | Alinhamento das criossecções e TC, segmentação manual no **ScanIP**, suavização no **MeshMixer** e remoção de *overclosure* (`gap 0,05 mm`) por interpolação RBF / FEMORS em MATLAB. | https://digitalcommons.du.edu/visiblehuman/1/ \| https://doi.org/10.1038/s41597-022-01905-2 |

---

## 6. Visible Human Female da NLM (RM e criossecções)

| Campo | Registro verificado | URL comprobatória |
| :--- | :--- | :--- |
| **1. Disponibilidade real para download** | **Acesso público sem cadastro/licença desde julho de 2019** via NLM Data Discovery (`ux2j-9i9a`). *(Nota: a listagem direta do diretório S3/CloudFront em `data.lhncbc.nlm.nih.gov/public/Visible-Human/Female-Images/...` retornou `HTTP 403 Forbidden`.)* | https://www.nlm.nih.gov/research/visible/getting_data.html \| https://datadiscovery.nlm.nih.gov/Images/Visible-Human-Project/ux2j-9i9a/about_data |
| **2. Formato** | Criossecções em **`.raw` (`.Z`)** e **`.png`** (24-bit cor); RM em formato **GE original (`.Z`)**, cabeçalhos **`.txt`** (`mriHeaders/`) e **`.png`** (12-bit cinza). Sem malhas 3D nativas. | https://www.nlm.nih.gov/research/visible/getting_data.html \| https://datadiscovery.nlm.nih.gov/Images/Visible-Human-Project/ux2j-9i9a/about_data |
| **3. Nº de estruturas** | **0 estruturas segmentadas** (imagens brutas não segmentadas; **> 5.000** cortes criosseccionais, ~40 GB no conjunto feminino). Contagem exata de cortes de RM: `não verificado (site bloqueou)` por `403` na listagem S3. | https://www.nlm.nih.gov/research/visible/visible_human.html \| https://www.nlm.nih.gov/research/visible/getting_data.html |
| **4. Origem dos dados** | 1 cadáver feminino doado à ciência (University of Colorado Health Sciences Center / NCAR sob contrato da National Library of Medicine, EUA, 1995). | https://www.nlm.nih.gov/research/visible/visible_human.html |
| **5. Licença (uso / modificação / redistribuição / uso comercial)** | Desde julho de 2019 **não exige acordo de licença nem taxas**. Regido pelos Termos e Condições da NLM: uso, modificação, redistribuição e uso comercial são livres, exigindo atribuição (`"Courtesy of the U.S. National Library of Medicine"`) e proibindo implicar endosso da NLM. | https://www.nlm.nih.gov/research/visible/getting_data.html \| https://www.nlm.nih.gov/databases/download/terms_and_conditions.html |
| **6. Resolução** | Criossecções: **`2048×1216` px**, espaçamento **`0,33 × 0,33 × 0,33 mm`** (voxels cúbicos). RM: **`256×256` px**, intervalos de **`4 mm`** (axial cabeça/pescoço + longitudinal corpo). | https://www.nlm.nih.gov/research/visible/visible_human.html \| https://datadiscovery.nlm.nih.gov/Images/Visible-Human-Project/ux2j-9i9a/about_data |
| **7. Referencial** | Cabeçalhos GE originais (RM) e fatias axiais sequenciais em bloco congelado (criossecções), sem sistema de coordenadas de malha 3D pronto. | https://www.nlm.nih.gov/research/visible/getting_data.html |
| **8. Método de reconstrução** | **Não há reconstrução 3D pronta** na fonte NLM (aquisição primária por RM pré-congelamento + criomilling/fotografia digital de cortes anatômicos). | https://www.nlm.nih.gov/research/visible/visible_human.html |

---

## Classificação final (Critério B1)

1. **Podem entrar sem pedir permissão:**
   - **University of Denver (*Visible Human Female*)** — CC BY 4.0 (malhas STL + TC/criossecções alinhadas, restrito de pelve a pés).
   - **Visible Human Female da NLM** — sem exigência de licença nem taxas (termos NLM exigem apenas atribuição e não implicar endosso; fornece imagens brutas, sem segmentação/malhas).
   - **HRA-VCCF** — CC BY 4.0 (`.csv`) / MIT (`.sql`), porém contém apenas dados tabulares/ontológicos vasculares e ponteiros `VH_F_*`, sem malhas 3D próprias.
   - **Female Atlas (`HiMahendraBeniwal/female-atlas`)** — CC BY 4.0 (dados) / MIT (código); ressalva científica crítica: combina BodyParts3D masculino deformado com HRA v1.5 sem validação anatômica declarada.
2. **Exigem acordo ou permissão:**
   - **Visible Korean Female** — exige solicitação formal à KISTI, relatório anual, proibição de repasse sem notificação e contrato comercial separado para uso comercial.
   - **Chinese Visible Human (CVH)** — exige contato institucional e assinatura de *licence agreement* com a TMMU/Army Medical University (termos completos não públicos).
3. **Indisponíveis para download público direto (ou sem malha 3D feminina aberta pronta):**
   - **Chinese Visible Human (CVH):** sem repositório público aberto verificado para os datasets completos ou malhas 3D.
   - **Visible Korean Female (`VF-4` 3D corpo inteiro):** sem download público aberto do pacote completo e com modelos 3D de corpo inteiro listados como em andamento/por região na página da KISTI (apenas PDFs demonstrativos e pelve/imagens via solicitação).
   - *(Observação técnica na NLM: o espelho direto `data.lhncbc.nlm.nih.gov/public/Visible-Human/...` retornou `HTTP 403`, devendo-se usar o portal NLM Data Discovery `ux2j-9i9a`.)*
