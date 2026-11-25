# Licença dos Modelos 3D do Human Reference Atlas (HRA)

Pesquisa sobre a licença, versão, atribuição e eventuais restrições herdadas do modelo `united-female` (`3d-vh-f-united.glb`) e dos órgãos femininos de referência (`VH_F_*`) do Human Reference Atlas (HuBMAP).

---

## 1. Licença dos modelos 3D de órgãos de referência e do `united-female` (`latest`)

Todos os modelos verificados são distribuídos sob a licença **Creative Commons Attribution 4.0 International (CC BY 4.0)** (`https://creativecommons.org/licenses/by/4.0/`).

### Evidências literais

- **README da versão `latest` de `united-female`** (`https://cdn.humanatlas.io/digital-objects/ref-organ/united-female/latest/README.md`):
  > `**License:**`
  >
  > `Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/))`

- **Metadados do grafo `graph.json` de `united-female` (`latest`)** (`https://cdn.humanatlas.io/digital-objects/ref-organ/united-female/latest/graph.json`):
  > `"license": "https://creativecommons.org/licenses/by/4.0/",`

- **Registro LOD de `united-female` (`latest`)** (`https://lod.humanatlas.io/ref-organ/united-female/latest`, nó `https://lod.humanatlas.io/ref-organ/united-female/v1.10#raw-data`):
  > `"dct:license": "Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/))",`

- **Órgãos femininos individuais (`VH_F_*`, exemplos verificados):**
  - `kidney-female-left` (`https://cdn.humanatlas.io/digital-objects/ref-organ/kidney-female-left/latest/README.md`):
    > `**License:**`
    >
    > `Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/))`
  - `heart-female` (`https://cdn.humanatlas.io/digital-objects/ref-organ/heart-female/latest/README.md`):
    > `**License:**`
    >
    > `Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/))`

- **Processador oficial (`hra-do-processor`)** (`https://raw.githubusercontent.com/hubmapconsortium/hra-do-processor/main/LICENSE`):
  - O código do processador está sob **MIT License** (`Copyright (c) 2023 HuBMAP Consortium`), distinta da licença **CC BY 4.0** aplicada aos ativos 3D gerados.

---

## 2. Número de versão do `united-female` (`latest`)

- **Versão atual em `latest`:** **`v1.10`**
  - **Data de processamento (`creation_date`):** `2026-06-09`
  - **Data de publicação (`Date published`):** `2026-06-15`
  - **DOI:** `https://doi.org/10.48539/HBM637.DWBM.744`
  - **HuBMAP ID:** `HBM637.DWBM.744`
- **Fontes:**
  - `https://cdn.humanatlas.io/digital-objects/ref-organ/united-female/latest/README.md`: `# 3D Reference Organ Set for United, Female, v1.10`
  - `https://cdn.humanatlas.io/digital-objects/ref-organ/united-female/latest/graph.json`: `"version": "v1.10"`, `"see_also": "https://lod.humanatlas.io/ref-organ/united-female/v1.10"`

---

## 3. Texto de atribuição exigido

Nos metadados oficiais do LOD (`https://lod.humanatlas.io/ref-organ/united-female/latest`, nó `https://lod.humanatlas.io/ref-organ/united-female/v1.10#raw-data`), constam literalmente dois formatos de citação para atribuição (em conjunto com os requisitos da licença CC BY 4.0 — crédito aos autores, link para a licença e indicação de alterações, se houver):

- **Citação específica do modelo (`schema1:citation`):**
  > `Browne, Kristen, and Heidi Schlehlein. 2026. *3D Reference Organ Set for Female, v1.10*. https://doi.org/10.48539/HBM637.DWBM.744. Accessed on June 15, 2026.`

- **Citação geral da biblioteca (`ccf:citation_overall`):**
  > `Browne, Kristen, Heidi Schlehlein, Bruce W. Herr II, Ellen Quardokus, Andreas Bueckle, and Katy Börner. 2026. HuBMAP CCF 3D Reference Object Library. https://humanatlas.io/3d-reference-library. Accessed on June 15, 2026.`

- **Referência à fonte anatômica original (citada no `README.md`):**
  > `This reference organ, Female-united set (https://humanatlas.io/3d-reference-library) was created using data from the Visible Human Dataset, provided by the National Library of Medicine (Spitzer and Whitlock 2002).`

---

## 4. Restrições herdadas do Visible Human Project (NLM)

Não há mais exigência de contrato de licença prévio, registro ou cobrança de royalties para uso dos dados do Visible Human Project (VHP):

- **`https://www.nlm.nih.gov/research/visible/visible_human.html`:**
  > `As of 2019, a license is no longer required to access the VHP datasets.`

- **`https://www.nlm.nih.gov/research/visible/getting_data.html`:**
  > `As of July 2019, the NLM Data License has been replaced by Terms and Conditions. No registration is required to access data available from NLM's FTP servers. Users will not be required to renew a license agreement at the end of the year.`

Os **Termos e Condições da NLM** (`https://www.nlm.nih.gov/databases/download/terms_and_conditions.html`) estabelecem apenas condições de atribuição, não-endosso e transparência de versão para quem usa ou redistribui os dados da NLM:

- > `No charges, usage fees or royalties are paid to NLM for this data.`
- > `Users of the data agree to: acknowledge NLM as the source of the data by including the phrase "Courtesy of the U.S. National Library of Medicine" in a clear and conspicuous manner, not indicate or imply that NLM has endorsed its products/services/applications.`
- > `Users who republish or redistribute the data (services, products or raw data) agree to: maintain the most current version of all distributed data, or make known in a clear and conspicuous manner that the products/services/applications do not reflect the most current/accurate data available from NLM.`

*(Observação: a documentação do HRA não afirma explicitamente se essas cláusulas da NLM se estendem às malhas 3D derivadas já publicadas sob CC BY 4.0 — **não confirmado** nesse ponto —, mas incluir `"Courtesy of the U.S. National Library of Medicine"` e evitar qualquer sugestão de endosso pela NLM cumpre integralmente os termos sem conflito com a CC BY 4.0.)*

---

## Fontes consultadas

1. `https://cdn.humanatlas.io/digital-objects/ref-organ/united-female/latest/README.md`
2. `https://cdn.humanatlas.io/digital-objects/ref-organ/united-female/latest/graph.json`
3. `https://lod.humanatlas.io/ref-organ/united-female/latest`
4. `https://cdn.humanatlas.io/digital-objects/ref-organ/kidney-female-left/latest/README.md`
5. `https://cdn.humanatlas.io/digital-objects/ref-organ/heart-female/latest/README.md`
6. `https://raw.githubusercontent.com/hubmapconsortium/ccf-releases/main/README.md`
7. `https://raw.githubusercontent.com/hubmapconsortium/hra-do-processor/main/LICENSE`
8. `https://www.nlm.nih.gov/research/visible/visible_human.html`
9. `https://www.nlm.nih.gov/research/visible/getting_data.html`
10. `https://www.nlm.nih.gov/databases/download/terms_and_conditions.html`
