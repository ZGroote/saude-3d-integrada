# EXP-0023 — Levantamento de Fontes S1 e S3

**Protocolo:** [EXP-0023-referencias-femininas-independentes.md](../../experimentos/EXP-0023-referencias-femininas-independentes.md) (Seções 5, 6 e 7)
**Data:** `2026-11-27`
**Escopo:** SOMENTE as fontes **S1** (`TotalSegmentator Dataset V3`) e **S3** (`SAROS`).
**Regra de registro:** Todo campo traz a URL comprobatória exata verificada nesta investigação. O que não pôde ser comprovado diretamente por URL ou metadado `<= 50 MB` está marcado como `não verificado`. Nenhum volume de imagem, máscara, malha ou zip grande (`> 50 MB`) foi baixado.

---

## Metadados pequenos baixados (`<= 50 MB`)

Para **S1 (`TotalSegmentator Dataset V3`)**, o registro `22688904` no Zenodo contém apenas um único arquivo monolítico (`Totalsegmentator_dataset_v300.zip`, `37.415.622.057` bytes ≈ `37,42 GB`), não havendo `meta.csv` avulso para download dentro do limite de `50 MB`.

Para **S3 (`SAROS`)**, os arquivos de metadados abaixo foram baixados de `https://www.cancerimagingarchive.net/analysis-result/saros/` para `pesquisa/resultados/EXP-0023/metadados/S3_saros/`:

| Arquivo | Tamanho (bytes) | SHA-256 |
|---|---:|---|
| `Segmentation-Info_09-29-2023.csv` | `180.787` | `66d932459fbb9c294fcd1322ae55b7609d302909d342658de4f641acfe96a92e` |
| `SAROS_SourceImages_TCIARestricted_9-12-2023-nbia-digest.xlsx` | `43.394` | `c0f39223e60919982e2b3494ea72c1cf4435caeb15b10e5e4257f49db889ba28` |
| `SAROS_SourceImages_CCby30_9-12-2023-nbia-digest.xlsx` | `145.857` | `cb580bc11dfcadaec1bb21f2f515ccc11dbb24706e4dc86a931ae43a059637e9` |
| `SAROS_SourceImages_CCbyNC30_9-12-2023-nbia-digest.xlsx` | `22.054` | `26c78b11fc45ab1fb061c6650f2061db02e1982d45bc4a4f2205981ab3c5c03e` |
| `SAROS_SourceImages_CCby40_9-12-2023-nbia-digest.xlsx` | `9.775` | `10c3d99e9b8b548924d8108979fda1f0ad333905c5a249ced358aa9455023ac3` |

Script Python utilizado para contagem em `S3`: [contar_s3_saros.py](./contar_s3_saros.py). Comando executado:
```bash
python pesquisa/resultados/EXP-0023/contar_s3_saros.py
```
Saída observada:
- Total de séries (linhas): `900` (`female: 450`, `male: 450`)
- Pacientes únicos (`tcia_case_id`): `882` (`female: 438`, `male: 444`)
- Regiões anatômicas nas séries femininas: `abdomen: 150`, `thorax: 150`, `wholebody: 150`
- Implante mamário (`has_breast_implant`): `FALSE: 882`, `TRUE: 18`

---

## S1. TotalSegmentator Dataset V3 (`https://zenodo.org/records/22688904`)

*(Nota sobre a URL: `https://zenodo.org/records/22688904` / API `https://zenodo.org/api/records/22688904` aponta efetivamente para a **versão 3.0.0** do dataset TotalSegmentator, publicada em `2026-09-10`, com **1.939** imagens de TC e **117** estruturas anatômicas.)*

| Campo | Registro verificado | URL comprobatória |
| :--- | :--- | :--- |
| **1. Número de mulheres independentes (e de homens); sexo nos metadados por caso** | **Na v3 (1.939 TCs): `não verificado`** (o `meta.csv` da v3 está dentro do arquivo único `Totalsegmentator_dataset_v300.zip` de `37,42 GB`, não baixado pela regra `<= 50 MB`). Sabe-se pelo padrão do dataset que `meta.csv` registra o sexo por caso, e o artigo da v1 (1.204 TCs) apresenta o sexo na Figura 3 em gráfico (sem contagem numérica de mulheres da v1 no texto extraível; para a coorte secundária de 4.004 TCs cita `1.461` mulheres e `2.543` homens). | https://zenodo.org/api/records/22688904 \| https://arxiv.org/pdf/2208.05868 |
| **2. Estruturas efetivamente segmentadas (pelve, fêmur, tíbia, fíbula, patela, pé e músculos do membro inferior)** | **117 estruturas** na tarefa `total` (`map_to_binary.py`). **Ossos da pelve/membro inferior:** `sacrum` (25), `femur_left` (75), `femur_right` (76), `hip_left` (77), `hip_right` (78); descrição da v3 cita melhoria nas segmentações ósseas (ex.: fêmur mais preciso). **Ausentes:** tíbia, fíbula, patela e ossos do pé. **Músculos individuais do membro inferior/quadril:** `gluteus_maximus_left/right` (80–81), `gluteus_medius_left/right` (82–83), `gluteus_minimus_left/right` (84–85), `iliopsoas_left/right` (88–89) (além de `autochthon_left/right` 86–87 no dorso). **Ausentes:** quadríceps, isquiotibiais, adutores e músculos da perna/panturrilha. | https://raw.githubusercontent.com/wasserth/TotalSegmentator/master/totalsegmentator/map_to_binary.py \| https://zenodo.org/api/records/22688904 |
| **3. Disponibilidade de exames, máscaras volumétricas e malhas; forma de acesso** | Exames de TC + máscaras volumétricas (NIfTI, sem malhas pré-geradas) disponíveis em **download direto público sem cadastro** no Zenodo (`Totalsegmentator_dataset_v300.zip`) e via link espelho no Dropbox listado na descrição. | https://zenodo.org/api/records/22688904 \| https://raw.githubusercontent.com/wasserth/TotalSegmentator/master/README.md |
| **4. Resolução espacial e cobertura corporal** | Todas as imagens reamostradas para **`1,5 mm` isotrópico** no protocolo do dataset (`arxiv.org/pdf/2208.05868`). Cobertura variável da rotina clínica (v1 excluiu séries restritas apenas a extremidades superiores/inferiores `n = 37`; v3 adicionou `291` TCs pediátricas aos `1.228` anteriores, totalizando `1.939` TCs). | https://arxiv.org/pdf/2208.05868 \| https://zenodo.org/api/records/22688904 |
| **5. Presença de patologias, implantes ou alterações anatômicas** | **Sim.** Amostragem aleatória da rotina clínica hospitalar com ampla variedade de patologias, scanners, fases de contraste e instituições (na v1: `404` pacientes sem patologia e `645` com patologias diversas; `40` casos com alta ambiguidade por distorção patológica). | https://zenodo.org/api/records/22688904 \| https://arxiv.org/pdf/2208.05868 |
| **6. Licença (pesquisa / transformação / redistribuição / uso comercial)** | **Creative Commons Attribution 4.0 International (`cc-by-4.0`)**: permite **pesquisa**, **transformação (obra derivada)**, **redistribuição** e **uso comercial** mediante atribuição. | https://api.datacite.org/dois/10.5281/zenodo.22688904 \| https://creativecommons.org/licenses/by/4.0/legalcode |
| **7. Uso possível como referência independente de validação** | **Parcial para ossos (H23a):** cobre quadril (`hip_left/right`), sacro (`sacrum`) e fêmur (`femur_left/right`) com `1,5 mm` isotrópico e CC BY 4.0, mas **não** cobre tíbia, fíbula, patela nem pé. **Não para músculos (H23b):** segmenta apenas 4 grupos musculares bilaterais do quadril/glúteos (`gluteus_maximus`, `gluteus_medius`, `gluteus_minimus`, `iliopsoas`), sem nenhum músculo individual da coxa ou da perna. | https://raw.githubusercontent.com/wasserth/TotalSegmentator/master/totalsegmentator/map_to_binary.py \| https://arxiv.org/pdf/2208.05868 |
| **8. Custo para experimento regional (download, subconjunto e CPU)** | **`37,42 GB`** (`37.415.622.057` bytes) em **arquivo `.zip` único** (`Totalsegmentator_dataset_v300.zip`). **Não permite** baixar só mulheres nem só uma região diretamente pelo Zenodo (existe apenas um subconjunto v2.0.1 de 102 sujeitos / `3,24 GB` em `zenodo.org/records/10047263`). Processamento na CPU local é viável para filtragem por `meta.csv` e extração de superfícies após download/descompactação. | https://zenodo.org/api/records/22688904 \| https://zenodo.org/api/records/10047263 |

**Avaliação D2 (sua leitura, não o veredito final):**
- **Ossos (H23a):** (a) `não verificado` (contagem exata de mulheres na v3 exige abrir `meta.csv` dentro do zip de 37,42 GB); (b) **atende ao mínimo H23a** (quadril e fêmur presentes, embora sem tíbia/fíbula/patela/pé); (c) **atende** (`1,5 mm` isotrópico); (d) **atende** (CC BY 4.0); (e) **atende no limite** (`37,42 GB <= 40 GB`, exigindo baixar o pacote inteiro).
- **Músculos (H23b):** (a) `não verificado`; (b) **não atende** (apenas 4 grupos musculares bilaterais do quadril/iliopsoas, abaixo dos `>= 5` músculos distintos do membro inferior e sem músculos de coxa/perna); (c) **atende**; (d) **atende**; (e) **atende no limite**.

---

## S3. SAROS (`https://www.nature.com/articles/s41597-024-03337-6`)

*(Nota: a URL da Nature aponta para o artigo publicado em *Scientific Data* 2024, disponível em texto integral no PMC `PMC11087485`; os dados estão hospedados no TCIA sob DOI `10.25737/SZ96-ZG60`, com scripts em `github.com/UMEssen/saros-dataset`.)*

| Campo | Registro verificado | URL comprobatória |
| :--- | :--- | :--- |
| **1. Número de mulheres independentes (e de homens); sexo nos metadados por caso** | **438 mulheres únicas** (`450` séries de TC femininas: `150 abdomen`, `150 thorax`, `150 wholebody`) e **444 homens únicos** (`450` séries masculinas), totalizando **882 pacientes / 900 séries de TC**. Sexo explícito por caso na coluna `gender` de `Segmentation-Info_09-29-2023.csv` (contado via `contar_s3_saros.py`). | https://www.cancerimagingarchive.net/wp-content/uploads/Segmentation-Info_09-29-2023.csv \| https://pmc.ncbi.nlm.nih.gov/articles/PMC11087485/ |
| **2. Estruturas efetivamente segmentadas (pelve, fêmur, tíbia, fíbula, patela, pé e músculos do membro inferior)** | **13 rótulos semânticos de região corporal** (`abdominal/thoracic cavity`, **`bones`**, `brain`, `breast implant`, `mediastinum`, **`muscle`**, `parotid/submandibular/thyroid glands`, `pericardium`, `spinal cord`, `subcutaneous tissue`) + **6 rótulos de parte do corpo** (`left/right arm/leg`, `head`, `torso`). **Todos os ossos estão fundidos em uma única classe `bones` e todos os músculos em uma única classe `muscle`** — **nenhum** osso ou músculo do membro inferior é segmentado individualmente. | https://pmc.ncbi.nlm.nih.gov/articles/PMC11087485/ |
| **3. Disponibilidade de exames, máscaras volumétricas e malhas; forma de acesso** | **Máscaras NIfTI** (`86,97 MB`) e **planilha de metadados** (`176,55 KB`) em download direto público no TCIA (sem malhas). **Exames de TC originais** baixados via `download.py` + API NBIA/TCIA em 4 grupos de acesso: 3 abertos (CC BY 4.0, CC BY 3.0, CC BY-NC 3.0) e **1 restrito (`TCIA Restricted`)** que exige conta TCIA e envio do formulário `TCIA Restricted License Agreement` por e-mail para 4–5 coleções (`ACRIN-HNSCC-FDG-PET-CT`, `Anti-PD-1_Melanoma`, `HNSCC`, `Head-Neck Cetuximab`, além de `QIN-HEADNECK` citada no README). | https://www.cancerimagingarchive.net/analysis-result/saros/ \| https://raw.githubusercontent.com/UMEssen/saros-dataset/main/README.md |
| **4. Resolução espacial e cobertura corporal** | Imagens e máscaras reamostradas para **espessura de corte de `5 mm`**, com **anotação esparsa apenas a cada 5ª fatia axial** (demais fatias recebem rótulo `255` *ignore*, resultando em espaçamento anotado efetivo de `~25 mm` entre fatias). Cobertura: `abdomen` (`300`), `thorax` (`300`), `wholebody` (`300`, sendo `150` séries femininas `wholebody`). | https://pmc.ncbi.nlm.nih.gov/articles/PMC11087485/ \| https://raw.githubusercontent.com/UMEssen/saros-dataset/main/download.py |
| **5. Presença de patologias, implantes ou alterações anatômicas** | **Sim.** Coorte oncológica/clínica reunida de **28 coleções do TCIA** (carcinomas de pulmão, cabeça e pescoço, mama, rim, pâncreas, útero/endométrio, melanoma, sarcoma de partes moles, COVID-19). Inclui explicitamente **`18` TCs com implante mamário** (`has_breast_implant = TRUE` no CSV). | https://www.cancerimagingarchive.net/analysis-result/saros/ \| https://pmc.ncbi.nlm.nih.gov/articles/PMC11087485/ |
| **6. Licença (pesquisa / transformação / redistribuição / uso comercial)** | **Máscaras SAROS e metadados:** **CC BY 4.0** (pesquisa, transformação, redistribuição e uso comercial com atribuição). **Código (`UMEssen/saros-dataset`):** **MIT**. **Imagens de TC fonte:** mistas por coleção — **CC BY 4.0** (`1,4 GB`), **CC BY 3.0** (`66,88 GB`), **CC BY-NC 3.0** (`4,63 GB`, sem uso comercial) e **TCIA Restricted** (`29,75 GB`, exige acordo institucional/formulário). | https://www.cancerimagingarchive.net/analysis-result/saros/ \| https://raw.githubusercontent.com/UMEssen/saros-dataset/main/LICENSE |
| **7. Uso possível como referência independente de validação** | **Não** (nem para ossos nem para músculos): agrupa todos os ossos em `bones` e todos os músculos em `muscle`, e possui resolução de `5 mm` de corte com anotação esparsa (1 em 5 fatias), não servindo para validar geometria individual de estruturas pélvicas ou do membro inferior. | https://pmc.ncbi.nlm.nih.gov/articles/PMC11087485/ |
| **8. Custo para experimento regional (download, subconjunto e CPU)** | Máscaras completas: **`86,97 MB`**. Imagens fonte totais: **`~102,66 GB`** (`1,4 + 4,63 + 66,88 + 29,75 GB`). **Permite baixar subconjunto** via `Segmentation-Info_09-29-2023.csv` + `download.py` (filtrando por `gender == female`, `anatomic_region == wholebody` e coleções abertas; das `150` séries `wholebody` femininas, `70` pertencem a coleções restritas listadas no README/artigo). Processável na CPU local. | https://www.cancerimagingarchive.net/analysis-result/saros/ \| https://raw.githubusercontent.com/UMEssen/saros-dataset/main/download.py |

**Avaliação D2 (sua leitura, não o veredito final):**
- **Ossos (H23a):** (a) **atende** (`438` mulheres únicas com sexo por caso); (b) **não atende** (classe única `bones`, sem pelve/fêmur individuais); (c) **não atende** (`5 mm` de corte e anotação esparsa 1/5); (d) **atende parcialmente** (máscaras CC BY 4.0, mas parte das TCs fonte é CC BY-NC ou TCIA Restricted); (e) **atende** para subconjunto aberto/máscaras (`86,97 MB` máscaras + `download.py` filtrável).
- **Músculos (H23b):** (a) **atende**; (b) **não atende** (classe única `muscle`, sem músculos individuais); (c) **não atende**; (d) **atende parcialmente**; (e) **atende** para subconjunto.
