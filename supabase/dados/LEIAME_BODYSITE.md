# Mapeamento `bodySite` SNOMED CT → Atlas (`bp3d-m` e `hra-f`)

## Verificação dos códigos SNOMED CT

Todos os 12 conceitos em `bodysite_snomed.csv` foram consultados e confirmados como ativos (`"active": true`) em `2026-11-26` diretamente na API oficial do SNOMED International Browser operada pelo HL7 Brasil (`https://snomed.hl7.org.br/snowstorm/snomed-ct/browser/MAIN/concepts/<codigo>`) e em consulta cruzada no servidor FHIR oficial da CSIRO (`https://r4.ontoserver.csiro.au/fhir/CodeSystem/$lookup?system=http://snomed.info/sct&code=<codigo>`).

Trechos literais retornados pela API oficial (`pt.term` / `fsn.term`):
- `80891009`: `Heart structure` / `Heart structure (body structure)`
- `10200004`: `Liver structure` / `Liver structure (body structure)`
- `3341006`: `Right lung structure` / `Right lung structure (body structure)`
- `44029006`: `Left lung structure` / `Left lung structure (body structure)`
- `9846003`: `Right kidney structure` / `Right kidney structure (body structure)`
- `18639004`: `Left kidney structure` / `Left kidney structure (body structure)`
- `52612000`: `Structure of lumbar region of back` / `Structure of lumbar region of back (body structure)`
- `6757004`: `Structure of right knee region` / `Structure of right knee region (body structure)`
- `82169009`: `Structure of left knee region` / `Structure of left knee region (body structure)`
- `35039007`: `Uterine structure` / `Uterine structure (body structure)`
- `73056007`: `Right breast structure` / `Right breast structure (body structure)`
- `80248007`: `Left breast structure` / `Left breast structure (body structure)`

*(Nota: como ambos os atlas armazenam malhas folha por sub-estrutura, órgãos compostos como pulmão, fígado, coração, região lombar e joelho apontam para uma malha representativa do catálogo `bodyparts3d/catalogo_bp3d.csv` e `hra/catalogo_hra.csv`; no `bp3d-m`, útero e mamas estão ausentes por ser um atlas masculino.)*

## Licença de uso do SNOMED CT no Brasil

Embora o Brasil tenha aderido à SNOMED International como seu 33º país-membro em abril de 2018 (via Ministério da Saúde) e a Portaria MS nº 2.073/2011 adote padrões internacionais de terminologia para interoperabilidade no SUS, o Brasil **não consta atualmente como país-membro ativo** na lista de membros da SNOMED International (`https://www.snomed.org/members`, que lista 54 membros ativos, sem o Brasil). Em consequência, o acesso institucional local para pesquisa, ensino e demonstração ocorre por iniciativas específicas como o navegador mantido pelo HL7 Brasil (`https://snomed.hl7.org.br/`, sob licença própria para projetos ligados ao HL7 Brasil) ou via *SNOMED Global Patient Set (GPS)* (`https://www.snomed.org/`, gratuito para subconjunto restrito de interoperabilidade). Para uso em **produção comercial ou institucional** em país não-membro, a SNOMED International exige solicitação de **Affiliate License** diretamente pelo *Member Licensing and Distribution Service (MLDS)*, sujeita a taxas anuais conforme a faixa econômica do Banco Mundial (`https://www.snomed.org/`).
