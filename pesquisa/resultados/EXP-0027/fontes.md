# EXP-0027 — Levantamento de Fontes Anatômicas Pediátricas

**Protocolo:** [EXP-0027-levantamento-fontes-pediatricas.md](../../experimentos/EXP-0027-levantamento-fontes-pediatricas.md) (Seções 5–7)
**Data:** `2026-11-27`
**Regra de registro:** Todo campo traz a URL comprobatória exata verificada nesta investigação. O que não pôde ser comprovado diretamente está marcado como `não verificado`. Nenhum volume de imagem, máscara ou malha foi baixado.

---

## Metadados pequenos analisados (`<= 50 MB`)

| Fonte | Arquivo | Tamanho (bytes) | SHA-256 | Script de contagem |
|---|---|---:|---|---|
| **P1** (local de EXP-0023) | `pesquisa/resultados/EXP-0023/metadados/S1_totalsegmentator/meta.csv` | `163.753` | `b9ca9a5ce9407f9caad1d039c7574cba154efe93f3a5802bc1aed2e05a732922` | [contar_p1_pediatrico.py](./contar_p1_pediatrico.py) |
| **P5** (NBIA digest) | `pesquisa/resultados/EXP-0027/metadados/P5_pediatric_ct_seg/Pediatric-CT-SEG-Mar-22-2022-manifes-nbia-digest.xlsx` | `145.551` | `1fbf3d15796e6b51c7966a3156b993b7a99a3033363fe1cc1db1033c652e889f` | — |
| **P5** (TCIA NBIA API) | `pesquisa/resultados/EXP-0027/metadados/P5_pediatric_ct_seg/nbia_patient_study.json` | `112.252` | `f3b6ccb974ee1bafc09ee4ade57a46aa8fb1a7ba053cf1d32b9f6fa0d9cc1836` | [contar_p5_pediatrico.py](./contar_p5_pediatrico.py) |

Comandos executados:
```bash
python pesquisa/resultados/EXP-0027/contar_p1_pediatrico.py
python pesquisa/resultados/EXP-0027/contar_p5_pediatrico.py
```

---

## P1. TotalSegmentator V3 — subconjunto pediátrico (Zenodo `22688904`)

| Campo | Registro verificado | URL comprobatória |
| :--- | :--- | :--- |
| **1. Indivíduos por faixa etária (`0–1`, `2–5`, `6–11`, `12–17`) e sexo; referência ou coorte** | **Coorte clínica** de **`286` exames pediátricos (`< 18` anos)** em `meta.csv` (`1.939` exames no total; contagem via `contar_p1_pediatrico.py`): **`0–1` ano:** `21` (`f = 12`, `m = 9`); **`2–5` anos:** `100` (`f = 46`, `m = 54`); **`6–11` anos:** `144` (`f = 70`, `m = 74`); **`12–17` anos:** `21` (`f = 10`, `m = 11`). Sem sexo ausente entre os `286`. | https://zenodo.org/api/records/22688904 (e `meta.csv` local) |
| **2. Estruturas disponíveis (ossos, órgãos, músculos) e placas de crescimento/ossificação** | **117 classes** na tarefa `total`: órgãos toraco-abdomino-pélvicos, cérebro, medula, grandes vasos, costelas, vértebras `C1–S1`, sacro, `hip_left/right`, `femur_left/right`, `humerus`, `scapula`, `clavicula`, `skull`, e 4 grupos musculares bilaterais do quadril/dorso (`gluteus_maximus/medius/minimus`, `iliopsoas`, `autochthon`). **Sem** tíbia/fíbula/patela/pé, **sem** músculos da coxa/perna e **sem** rótulos específicos de placas de crescimento ou centros de ossificação. | https://raw.githubusercontent.com/wasserth/TotalSegmentator/master/totalsegmentator/map_to_binary.py \| https://zenodo.org/api/records/22688904 |
| **3. Formato (malha, voxel ou máscara) e resolução** | **TCs e máscaras volumétricas NIfTI** (sem malhas pré-geradas). No `meta.csv` local (`n = 279` pediátricos com `slice_thickness`): espessura original de **`0,4` a `6,0 mm`** (mediana **`2,5 mm`**). Protocolo de treinamento TotalSegmentator reamostra para `1,5 mm` isotrópico. | https://arxiv.org/pdf/2208.05868 (e `meta.csv` local) |
| **4. Forma de acesso** | **Download direto público sem cadastro** no Zenodo (`Totalsegmentator_dataset_v300.zip`, `37,42 GB`), com espelho no Dropbox listado na descrição. | https://zenodo.org/api/records/22688904 |
| **5. Licença (pesquisa / transformação / redistribuição / uso comercial)** | **Creative Commons Attribution 4.0 International (`cc-by-4.0`)**: permite **pesquisa**, **transformação**, **redistribuição** e **uso comercial** mediante atribuição. | https://api.datacite.org/dois/10.5281/zenodo.22688904 |
| **6. Uso possível** | **Referência de validação** para órgãos e ossos disponíveis (`hip`, `femur`, vértebras, órgãos internos) nas faixas `2–5`, `6–11` e `12–17` anos (e meninas `0–1`). Não serve como base de malhas prontas do produto (são máscaras clínicas heterogêneas, sem membros distais nem placas de crescimento). | https://zenodo.org/api/records/22688904 \| https://raw.githubusercontent.com/wasserth/TotalSegmentator/master/totalsegmentator/map_to_binary.py |
| **7. Cobertura corporal dos exames pediátricos (`P1`)** | **`study_type` vazio em `277/286` casos** no `meta.csv`. **Pendente para o revisor** (conferência por HTTP Range no diretório do `.zip` para identificar quais máscaras estão preenchidas sem baixar volumes). | `meta.csv` local (pendente leitura HTTP Range pelo revisor) |

**Avaliação P-D2/P-D3 (sua leitura):** **P-D2: ATENDE** (coorte com `>= 10` indivíduos por sexo em **3 faixas** — `2–5`, `6–11` e `12–17` anos; `0–1` tem `f=12`, `m=9`; máscaras volumétricas de ossos/órgãos e licença CC BY 4.0 sem contrato, ressalvando cobertura corporal pendente de verificação pelo revisor). **P-D3: NÃO ATENDE** (são máscaras volumétricas clínicas heterogêneas, não malhas anatômicas completas por idade).

---

## P2. Modelos computacionais pediátricos de referência da ICRP (Pub. 143 e Pub. 156 em malha)

| Campo | Registro verificado | URL comprobatória |
| :--- | :--- | :--- |
| **1. Indivíduos por faixa etária (`0–1`, `2–5`, `6–11`, `12–17`) e sexo; referência ou coorte** | **Modelos de referência (1 par masculino/feminino por idade):** **10 fantomas** representando **recém-nascido (`0–1`)**, **1 ano (`0–1`)**, **5 anos (`2–5`)**, **10 anos (`6–11`)** e **15 anos (`12–17`)**, ambos os sexos (ICRP Pub. 143 em voxel e ICRP Pub. 156 em malha). | https://www.icrp.org/publication.asp?id=ICRP%20Publication%20143 \| https://www.icrp.org/publication.asp?id=ICRP%20Publication%20156 |
| **2. Estruturas disponíveis (ossos, órgãos, músculos) e placas de crescimento/ossificação** | Mesma estrutura anatômica dos fantomas de referência ICRP (órgãos internos, esqueleto com osso cortical, espongiosa e cavidade medular para dosimetria, camadas finas de 8–300 µm na Pub. 156). Detalhe de separação individual de ossos/músculos do membro inferior e placas de crescimento: **`não verificado`** (sem baixar os arquivos eletrônicos). | https://www.icrp.org/publication.asp?id=ICRP%20Publication%20143 \| https://www.icrp.org/publication.asp?id=ICRP%20Publication%20156 |
| **3. Formato (malha, voxel ou máscara) e resolução** | **Pub. 143:** matrizes **voxel** 3D — RN `0,663×0,663×0,663 mm`; 1 ano `0,663×0,663×1,400 mm`; 5 anos `0,850×0,850×1,928 mm`; 10 anos `0,990×0,990×2,425 mm`; 15 anos M `1,250×1,250×2,832 mm` / F `1,200×1,200×2,828 mm`. **Pub. 156:** **malhas poligonais e tetraédricas (MRCPs)**. | https://www.icrp.org/publication.asp?id=ICRP%20Publication%20143 \| https://www.icrp.org/publication.asp?id=ICRP%20Publication%20156 |
| **4. Forma de acesso** | Arquivos suplementares publicados no site da ICRP (`docs/sj-zip-1-ani-49-1.zip`, `51,2 MB` para Pub. 143; `docs/P156 Electronic files.zip`, `11,79 GB` para Pub. 156, ambos retornando HTTP 200 no `HEAD`), vinculados às publicações nos *Annals of the ICRP* (SAGE). | https://www.icrp.org/publication.asp?id=ICRP%20Publication%20143 \| https://www.icrp.org/publication.asp?id=ICRP%20Publication%20156 |
| **5. Licença (pesquisa / transformação / redistribuição / uso comercial)** | **Copyright estrito da ICRP.** **Pesquisa / educação / proteção radiológica sem fins lucrativos:** permitido mediante citação. **Transformação/reempacotamento, redistribuição e uso comercial:** **proibidos sem permissão prévia por escrito** da ICRP (`permissions@icrp.org`). | https://www.icrp.org/publication.asp?id=ICRP%20Publication%20143 \| https://www.icrp.org/publication.asp?id=ICRP%20Publication%20156 |
| **6. Uso possível** | **Referência apenas para pesquisa interna não comercial** (dosimetria/comparação de massas e proporções de referência). **Inviável** como base do produto sem acordo comercial específico com a ICRP. | https://www.icrp.org/publication.asp?id=ICRP%20Publication%20156 |

**Avaliação P-D2/P-D3 (sua leitura):** **P-D2: NÃO ATENDE** (apenas 1 modelo de referência por idade/sexo, não é coorte com `>= 10` indivíduos). **P-D3: NÃO ATENDE** (apesar de a Pub. 156 ter malhas em todas as faixas, o copyright estrito da ICRP proíbe redistribuição e uso comercial sem licença escrita prévia).

---

## P3. Série de modelos pediátricos híbridos da UF/NCI (*University of Florida / National Cancer Institute*)

| Campo | Registro verificado | URL comprobatória |
| :--- | :--- | :--- |
| **1. Indivíduos por faixa etária (`0–1`, `2–5`, `6–11`, `12–17`) e sexo; referência ou coorte** | **Modelos de referência (e biblioteca por porte/IMC):** série base de **10 fantomas** (**recém-nascido, 1, 5, 10 e 15 anos**, masculino e feminino) + biblioteca expandida de **362 fantomas dependentes do porte corporal** (sem braços, pediátricos e adultos). Contagem exata de pediátricos por faixa na série de 362: `não verificado`. | https://ncidose.github.io/ \| https://ncidose.github.io/tools/phantom/ |
| **2. Estruturas disponíveis (ossos, órgãos, músculos) e placas de crescimento/ossificação** | Órgãos internos principais e contorno corporal/esquelético usados em dosimetria (NCICT/NCINM/NCIRF). Separação individual de músculos e placas de crescimento/ossificação: **`não verificado`** (os 362 fantomas liberados em `2026-10-13` são descritos como *armless* — sem braços). | https://ncidose.github.io/ \| https://dceg.cancer.gov/tools/radiation-dosimetry-tools |
| **3. Formato (malha, voxel ou máscara) e resolução** | Família híbrida construída originalmente em **NURBS + malha poligonal** (voxelizável para Monte Carlo). Pacotes liberados em `2026-10-13` em **DICOM CT e RT Structure Set** em alta e baixa resolução (valores exatos em mm: `não verificado`). | https://ncidose.github.io/ \| https://ncidose.github.io/tools/phantom/ |
| **4. Forma de acesso** | **Pesquisa não comercial:** gratuita mediante preenchimento e envio de **Software Transfer Agreement** ao NCI/DCEG. **Uso comercial:** requer coordenação com o **NCI Technology Transfer Center**. | https://dceg.cancer.gov/tools/radiation-dosimetry-tools \| https://ncidose.github.io/ |
| **5. Licença (pesquisa / transformação / redistribuição / uso comercial)** | **Pesquisa não comercial:** permitida sob *Software Transfer Agreement*. **Transformação / redistribuição / uso comercial:** **restritos** — exigem licença comercial separada via NCI Technology Transfer Center. | https://dceg.cancer.gov/tools/radiation-dosimetry-tools |
| **6. Uso possível** | **Referência apenas em pesquisa não comercial mediante acordo (STA)**. Não atende como base comercial aberta do produto sem licenciamento com o NCI. | https://dceg.cancer.gov/tools/radiation-dosimetry-tools |

**Avaliação P-D2/P-D3 (sua leitura):** **P-D2: NÃO ATENDE** (série base é modelo de referência, não coorte clínica de pacientes reais, e acesso exige *Software Transfer Agreement*). **P-D3: NÃO ATENDE** (exige acordo de transferência e não permite uso comercial nem redistribuição abertos).

---

## P4. XCAT pediátrico (Duke University)

| Campo | Registro verificado | URL comprobatória |
| :--- | :--- | :--- |
| **1. Indivíduos por faixa etária (`0–1`, `2–5`, `6–11`, `12–17`) e sexo; referência ou coorte** | **Modelos de referência (10 fantomas base):** **recém-nascido, 1, 5, 10 e 15 anos**, masculino e feminino (expandidos depois em biblioteca de 64 percentis e XCAT 3.0 com `> 2.500` fantomas personalizados adultos/diversos). | https://cvit.duke.edu/resources/ \| https://xcat-3.github.io/ |
| **2. Estruturas disponíveis (ossos, órgãos, músculos) e placas de crescimento/ossificação** | **Milhares de estruturas anatômicas** (órgãos, ossos, músculos e vasos) no padrão XCAT (braços/pernas da série pediátrica de 2014 completados por escalonamento do XCAT adulto/dados cadavéricos). Placas de crescimento: **`não verificado`** (provavelmente ausentes pelo escalonamento adulto nos membros). | https://cvit.duke.edu/resources/ \| https://xcat-3.github.io/ |
| **3. Formato (malha, voxel ou máscara) e resolução** | **Superfícies NURBS** (4D com movimento respiratório/cardíaco) e saída **voxelizada ou malha de superfície** (XCAT 3.0). | https://xcat-3.github.io/ |
| **4. Forma de acesso** | **Não há download público aberto.** Exige **solicitação formal e contrato de licença de software** junto ao Duke Center for Virtual Imaging Trials (`cvit.duke.edu/resources`). | https://cvit.duke.edu/resources/ \| https://xcat-3.github.io/ |
| **5. Licença (pesquisa / transformação / redistribuição / uso comercial)** | **Software e dados proprietários sob contrato específico (Duke CVIT)** para pesquisa acadêmica, clínica ou comercial. Termos públicos de transformação, redistribuição e uso comercial: **não livres / dependem de contrato**. | https://cvit.duke.edu/resources/ |
| **6. Uso possível** | **Nenhum sem contrato institucional/licença da Duke.** Inadequado como base aberta ou referência sem acordo. | https://cvit.duke.edu/resources/ |

**Avaliação P-D2/P-D3 (sua leitura):** **P-D2: NÃO ATENDE** (não é coorte aberta sem contrato; exige licença da Duke). **P-D3: NÃO ATENDE** (proprietário, exige solicitação formal e contrato; uso comercial/redistribuição restritos).

---

## P5. `Pediatric-CT-SEG` (TCIA — *Pediatric Chest/Abdomen/Pelvic CT Exams with Expert Organ Contours*)

| Campo | Registro verificado | URL comprobatória |
| :--- | :--- | :--- |
| **1. Indivíduos por faixa etária (`0–1`, `2–5`, `6–11`, `12–17`) e sexo; referência ou coorte** | **Coorte clínica** de **`359` pacientes/exames** (5 dias a 16 anos; **`179` F, `180` M**; contado via `contar_p5_pediatrico.py` sobre `nbia_patient_study.json`): **`0–1` ano:** `32` (`F = 16`, `M = 16`); **`2–5` anos:** `143` (`F = 70`, `M = 73`); **`6–11` anos:** `105` (`F = 54`, `M = 51`); **`12–17` anos:** `79` (`F = 39`, `M = 40`). | https://www.cancerimagingarchive.net/collection/pediatric-ct-seg/ \| https://services.cancerimagingarchive.net/nbia-api/services/v1/getPatientStudy?Collection=Pediatric-CT-SEG |
| **2. Estruturas disponíveis (ossos, órgãos, músculos) e placas de crescimento/ossificação** | Até **29 estruturas** contornadas por especialistas: órgãos toraco-abdomino-pélvicos (`Heart`, `Lung_L/R`, `Liver`, `Spleen`, `Kidney Left/Right`, `Stomach`, `Pancreas`, `Bladder`, `UteroCervix`, `Prostate`, `Thymus`, `Skin`, etc.) + **`Bones`** (agrupado), **`Femoral Head Lef`** e **`Femoral Head Rig`**. **Sem** músculos individuais, **sem** ossos separados além da cabeça femoral e **sem** membro inferior distal nem placas de crescimento. | https://www.cancerimagingarchive.net/collection/pediatric-ct-seg/ |
| **3. Formato (malha, voxel ou máscara) e resolução** | **TC em DICOM + contornos em DICOM RTSTRUCT** (`359` estudos, `65,69 GB` no manifesto v2). Espessura de corte adquirida: **`0,625 mm`** (scanners GE) e **`0,6 mm`** (scanners Siemens). | https://www.cancerimagingarchive.net/collection/pediatric-ct-seg/ |
| **4. Forma de acesso** | **Download público gratuito sem contrato** via **TCIA Data Retriever** ou API NBIA (sem restrição de acesso). | https://www.cancerimagingarchive.net/collection/pediatric-ct-seg/ |
| **5. Licença (pesquisa / transformação / redistribuição / uso comercial)** | **Creative Commons Attribution 4.0 International (`CC BY 4.0`)**: permite **pesquisa**, **transformação**, **redistribuição** e **uso comercial** mediante atribuição (`10.7937/TCIA.X0H0-1706`). | https://www.cancerimagingarchive.net/collection/pediatric-ct-seg/ |
| **6. Uso possível** | **Referência de validação excelente** para **órgãos internos do tronco/pelve** e posição da cabeça femoral em **todas as 4 faixas etárias** (`0–1`, `2–5`, `6–11`, `12–17`). Não serve para membro inferior completo, músculos individuais nem como malha pronta do produto. | https://www.cancerimagingarchive.net/collection/pediatric-ct-seg/ |

**Avaliação P-D2/P-D3 (sua leitura):** **P-D2: ATENDE** (coorte com `>= 16` indivíduos por sexo em **todas as 4 faixas etárias**, contornos de órgãos + `Bones` + `Femoral Head`, alta resolução `0,6–0,625 mm`, e licença **CC BY 4.0** sem contrato). **P-D3: NÃO ATENDE** (são TCs + contornos DICOM RTSTRUCT, não malhas anatômicas 3D prontas de esqueleto/órgãos por idade).

---

## Outras fontes pediátricas encontradas (seção à parte)

- **Stanford Pediatric Whole-Body CT Segmentation Dataset (Stanford AIMI / Redivis):** `358` TCs de corpo inteiro (`0–16` anos) com **`117` estruturas anatômicas** (refinamento manual do TotalSegmentator + classes pediátricas como timo). Acesso típico via **Stanford AIMI / Redivis** (`https://aimidatasetindex.stanford.edu/`), geralmente gratuito para **pesquisa não comercial** mediante acordo click-through (DUA), com uso comercial sujeito a licenciamento institucional separado. Link direto ao registro específico no Redivis: `não verificado`.
