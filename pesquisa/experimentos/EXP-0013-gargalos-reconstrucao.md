# EXP-0013 — Pesquisa de soluções para os gargalos de reconstrução, hardware, registro, validação geométrica e terminologia

## 1. Identificação
- **ID:** `EXP-0013`
- **Título:** Levantamento de soluções abertas para os gargalos atuais (G1–G5)
- **Data:** `2026-11-25`
- **Responsável:** não documentado
- **Agentes de IA:** Antigravity + 5 subagentes paralelos (pesquisa G1–G5)
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** não aplicável (levantamento pré-execução)
- **Linha de pesquisa:** `LP01` (e interface com `LP02`, `LP03`, `LP05`)
- **Situação:** `planejado`

## 2. Problema
Os experimentos `EXP-0009` a `EXP-0012` e `pesquisa/limitacoes/LIMITACOES_CONHECIDAS.md` evidenciaram cinco gargalos críticos para completar e validar o atlas feminino (`hra-f`) e a terminologia em português:
- **G1:** Lacunas anatômicas sem fonte aberta identificada (antebraço/mãos, músculos do braço/antebraço, vasos dos membros, nervos periféricos).
- **G2:** Restrição de hardware local (`NVIDIA GeForce GTX 1650`, 4 GB VRAM; 64 GB RAM) para segmentação `TotalSegmentator` em resolução padrão (1,5 mm).
- **G3:** Registro entre fontes heterogêneas (STLs cadavéricos Denver, TC original NLM e atlas HRA remodelado no Maya por ilustradores).
- **G4:** Qualidade geométrica, reparo de malhas, suavização preservadora de volume e protocolo formal de revisão por anatomista.
- **G5:** Validação automática e especializada dos `1.659` termos BodyParts3D + `721` termos HRA em português brasileiro (`validacao = 'pendente'`).

## 3. Hipótese
Existem fontes de dados, ferramentas e métodos abertos (com licenças compatíveis com uso comercial mediante atribuição) que reduzem cada um dos gargalos G1–G5.

## 4. Fundamentação teórica
Reuso de ativos 3D sob licenças permissivas/copyleft auditadas, segmentação por aprendizado profundo com particionamento espacial/nuvem pública, registro hierárquico (global afim + não-rígido por estrutura via CPD/BCPD ou mapas de distância), filtragem Taubin preservadora de volume, métricas de superfície (DSC, ASSD, HD95) e ancoragem terminológica em padrões FIPAT/TA2, Wikidata e DeCS.

## 5. Materiais e ambiente
- **Datasets e versões:** `hra-f 1.10-1`, `bp3d-m 4.0-1`, `TotalSegmentator 2.18.0`, coleções públicas pesquisadas (G1–G5).
- **Licenças:** auditadas individualmente nas tabelas da seção 8.
- **Hashes:** não aplicável (levantamento).
- **Hardware:** `NVIDIA GeForce GTX 1650, 4 GB VRAM`, `64 GB RAM`.
- **Sistema operacional:** Windows.
- **Bibliotecas e versões:** conforme especificações das ferramentas avaliadas.
- **Seed:** não aplicável.

## 6. Metodologia
Levantamento paralelo por gargalo (G1–G5) com conferência de URLs oficiais e cláusulas de licença. Itens cujo texto literal completo não pôde ser lido diretamente na sessão estão marcados explicitamente como `Parcial` ou `não verificado`.

## 7. Critérios de sucesso (definidos antes da execução)
Identificar, para cada gargalo G1–G5, até 5 opções ranqueadas com licença verificada, esforço estimado, riscos e distinção explícita entre o que resolve no MVP e o que deve ser postergado.

---

## 8. Resultados do levantamento (G1–G5)

### G1 — Lacunas do atlas feminino sem fonte aberta (antebraço/mãos, músculos do braço, vasos dos membros, nervos periféricos)

| opção | o que resolve | licença (trecho citado) | URL | esforço estimado | risco | verificado? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Z-Anatomy (`Models-of-human-anatomy`)** | Atlas completo em Blender com esqueleto (incl. antebraço/mão), músculos, vasos e nervos periféricos | **CC BY-SA 4.0** declarada em `Readme.md` (não há arquivo `LICENSE` separado): *"All the code and content shared by ‘Z-Anatomy’ is under Creative Commons Attribution-ShareAlike 4.0 International License"*. Atenção: `ATTRIBUTIONS` no mesmo `Readme.md` lista sub-modelos `CC-BY-NC-SA 4.0` (*Inner Ear*) e `CC-BY-NC 4.0` (*Kidney*) | <https://raw.githubusercontent.com/Z-Anatomy/Models-of-human-anatomy/master/Readme.md> | médio | Médio: copyleft **ShareAlike** (`LICENCAS.md` evita CC BY-SA sem decisão explícita) + risco de contaminação `NC` se incluir sub-modelos atribuídos sem filtro | Sim (`Readme.md` lido diretamente) |
| **2. MedShapeNet / MedShapeNetCore** | >100 mil formas 3D de TC/RM reais; inclui ossos apendiculares (`radius`, `ulna`), músculos, vasos e nervos | **MedShapeNetCore**: **CC BY 4.0** (uso comercial com atribuição). **MedShapeNet 2.0**: inclui subconjuntos **CC BY-NC-SA 4.0** (`não verificado` literalmente no registro Zenodo bruto) | <https://doi.org/10.5281/zenodo.10623506> | médio / alto | Médio-Alto: risco de contaminação `NC-SA` se não filtrar estritamente o subconjunto `Core`; exige montar e alinhar malhas isoladas | Parcial (não verificado literalmente no registro bruto) |
| **3. NIH 3D (`3DPX-017237`)** | Template anatômico 3D apenas de **mão adulta saudável** (RM T1 de 27 mãos). Não cobre antebraço, músculos, vasos ou nervos | **CC-BY** (permite uso comercial com atribuição; atenção: `3DPX-017249` é **GNU GPLv3** — não misturar) | <https://3d.nih.gov/entries/3DPX-017237> | médio | Baixo para `3DPX-017237`, mas cobertura restrita só à mão | Parcial (página HTML não lida literalmente) |
| **4. BodyParts3D / Anatomography (DBCLS)** | Malhas FMA de corpo inteiro (ossos, músculos, vasos, nervos) em adulto masculino | **CC BY 4.0** na página atual (`LICENCAS.md`), cabeçalhos antigos citam CC BY-SA 2.1 JP | <https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html> | médio | Médio: dimorfismo sexual (masculino→feminino) e decisão de arquitetura (`SPEC-MVP.md` §5.1 proíbe misturar corpos diferentes) | Sim (confirmado em `LICENCAS.md`) |
| **5. SPL / Open Anatomy Project** | Atlases regionais (Brain, Abdominal, Head & Neck, Knee, Thoracic); **não cobre** antebraço/mão feminino | **3D Slicer License (Part B)** — BSD-style permissiva (*"If you distribute Software... downloaded from Slicer, all of the paragraphs of Part B of this Agreement must be included..."*) | <https://www.openanatomy.org/> | alto | Alto na cobertura (lacuna dos membros superiores não resolvida) | Parcial (página completa não lida diretamente) |

- **Fontes descartadas para uso comercial / redistribuição em atlas público:**
  - **Visible Korean:** distribuído sob `CC BY-NC 4.0` (ex.: <https://zenodo.org/records/22759852>), uso comercial proibido.
  - **IT'IS Virtual Population — Ella V2.0 (legada) e ViP 3.x/4.x:**
    - *Verificação direta (`https://itis.swiss/virtual-population/virtual-population/vip2/ella/` + `LicenseAgreementv2-0_2024.pdf` + `VF2-0_tissue-list.txt`):* a **Ella V2.0** (DOI `10.13099/ViP-Ella-V2.0`, 26 anos, 1,63 m, 57,3 kg) possui **licença gratuita, não-exclusiva e sem restrição acadêmica** (cláusula `2.1`: *"grants the Licensee a non-exclusive, non-transferable, free license to use the Model Data and the Installer"*), com proibição apenas de uso militar (`2.3.5`) e obrigação de citação (Gosselin et al. 2014 + DOI, `2.3.8`). Download exige cadastro (`Affiliation`, nome, e-mail) em `ella-v2-0` (link único válido por 24 h).
    - **Por que NÃO resolve G1 para o nosso atlas:** (1) **Proibição de redistribuição** — cláusula `2.3.2` do contrato v2.0: *"The Model Data or works derived from the Model Data must not be distributed or redistributed in the original form or in any modified or updated form"*, inviabilizando servir malhas derivadas em repositório/app público; (2) **Granularidade anatômica insuficiente** — embora tenha alta resolução geométrica (`7.057.794` células em formato CAD), possui apenas **22 tecidos agregados** (`Bone`, `Muscle`, `Cartilage`, `Skull`, `Mandible`, `Eye`, `Tongue`, `Cerebrospinal Fluid`, `Cerebrum (Grey/White Matter)`, `Cerebrellum`, `Thalamus`, `Brain Stem`, `Spinal Cord`, `Respiratory System`, `Heart`, `Gastrointestinal System`, `Liver`, `Kidney`, `Bladder`, `Reproductive System`, `Other Tissues`): **não separa** ossos do braço/mão, músculos individuais, vasos nem nervos periféricos. (ViP 3.x/4.x exige licença comercial paga via `vip@itis.ethz.ch`.)
  - **TotalSegmentator `appendicular_bones`:** exige licença paga para uso comercial (`https://backend.totalsegmentator.com/license-academic/` é apenas não-comercial; comercial via `jakob.wasserthal@usb.ch` — `https://github.com/wasserth/TotalSegmentator`).

---

### G2 — Hardware (GTX 1650 4 GB VRAM; 64 GB RAM) para segmentação de corpo inteiro

| opção | o que resolve | licença (trecho citado) | URL | esforço estimado | risco | verificado? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Kaggle Notebooks (`GPU T4 x2`, 16 GB VRAM/GPU)** | Executa `TotalSegmentator` (`total` / `total_mr`) em resolução padrão **1,5 mm** sem OOM local (cota típica 30 h/sem, sessões até 12 h) | TotalSegmentator `total`/`total_mr`: **"Openly available for any usage (Apache-2.0 license):"**; Termos Kaggle: `não verificado` literalmente | <https://www.kaggle.com/docs/notebooks> | baixo | Médio: **LGPD** — usar **exclusivamente** com dados cadavéricos públicos (NLM VHP), nunca com dados de pacientes | Parcial (via `search_web`) |
| **2. Local CPU com 64 GB RAM (`--device cpu --nr_thr_saving 1`)** | Elimina OOM de 4 GB VRAM rodando 100% offline/LGPD-safe usando os 64 GB de RAM locais | **Apache-2.0** (`TotalSegmentator` `README.md`) | <https://github.com/wasserth/TotalSegmentator> | baixo | Baixo: mais lento (~40–50 min em 1,5 mm; acelerado com `--fast` 3 mm ou `--roi_subset`) | Parcial (via `search_web`) |
| **3. Local GPU 4 GB com redução (`--fast --body_seg --force_split --nr_thr_saving 1` + `--roi_subset`)** | Mantém aceleração CUDA na GTX 1650 dividindo o volume em 3 partes (`--force_split`) e recortando o corpo (`--body_seg`) | **Apache-2.0** (`TotalSegmentator` `README.md`) | <https://raw.githubusercontent.com/wasserth/TotalSegmentator/master/README.md> | baixo | Médio-Alto: `--fast` reduz para 3 mm; ainda pode dar OOM em volumes grandes sem `--fast` | Parcial (via `search_web`) |
| **4. Google Colab Free / Pay-As-You-Go (T4 ~16 GB VRAM)** | Alternativa em nuvem para rodar `1,5 mm` (sessões até 12 h) | Termos Colab: `não verificado` literalmente | <https://research.google.com/colaboratory/faq.html> | baixo | Médio: GPU não garantida no tier gratuito e desconexões dinâmicas; **proibido** para dados de pacientes (LGPD) | Parcial (via `search_web`) |
| **5. Pipeline Híbrido Local (`--fast` em GPU 4 GB + `--device cpu --roi_subset` em 1,5 mm)** | Triagem rápida na GPU 4 GB e refinamento `1,5 mm` na CPU (64 GB RAM) apenas nos ossos-alvo (pelve, sacro, fêmur) | **Apache-2.0** (`TotalSegmentator` `README.md`) | <https://github.com/wasserth/TotalSegmentator> | médio | Baixo: evita nuvem/LGPD e contorna OOM sem perder 1,5 mm nas regiões críticas do ICP | Parcial (via `search_web`) |

---

### G3 — Registro entre fontes (Denver STLs, NLM CT e HRA remodelado no Maya)

| opção | o que resolve | licença (trecho citado) | URL | esforço estimado | risco | verificado? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. CPD / BCPD via `probreg` + `pycpd` (Python)** | Registro rígido, afim e não-rígido de nuvens de pontos e malhas **por estrutura** (essencial para adaptar malhas artísticas do HRA ao referencial Denver/NLM) | **MIT License**: `"Permission is hereby granted, free of charge..."` (`probreg`, `pycpd`; `ohirose/bcpd`: `não verificado` literalmente) | <https://github.com/neka-nat/probreg/blob/master/LICENSE> <br> <https://github.com/siavashk/pycpd> | médio | Médio: sensível a subamostragem e oclusões se aplicado globalmente sem decomposição por órgão | Sim (`probreg`, `pycpd`) |
| **2. 3D Slicer (`SegmentRegistration` + `BRAINSFit` + `SlicerElastix`)** | Alinhamento interativo e por mapas de distância entre segmentações/superfícies com cálculo integrado de Dice, Hausdorff e TRE | **3D-Slicer-1.0** (`"3D Slicer Contribution and Software License Agreement"` Version 1.0) e **Apache-2.0** (`BRAINSFit`); `SegmentRegistration` LICENSE próprio: `não verificado` | <https://github.com/Slicer/Slicer/blob/main/License.txt> <br> <https://github.com/SlicerRt/SegmentRegistration> <br> <https://github.com/BRAINSia/BRAINSTools> | baixo | Médio: dependência de ambiente desktop/Slicer para automação headless | Sim (Slicer, BRAINSFit) |
| **3. ANTs / ANTsPy (`ants.registration` SyN + Mattes MI)** | Registro volumétrico multimodal/monomodal estado da arte (NLM CT ↔ TC Denver / máscaras rasterizadas) | **Apache License 2.0**: `"Apache License"` / `"Version 2.0, January 2004"` | <https://github.com/ANTsX/ANTsPy> <br> <https://github.com/ANTsX/ANTs> | médio | Médio-Alto: exige voxelização/SDF de malhas STL e maior custo computacional em 3D denso | Sim |
| **4. `itk-elastix` + `SimpleITK`** | Pipeline Python/C++ modular para registro rígido, afim e B-spline em volumes/mapas de distância (substitui o antigo `SimpleElastix`) | **Apache License 2.0**: `elastix`, `ITKElastix` e `SimpleITK` sob `"Apache License, Version 2.0"` | <https://github.com/InsightSoftwareConsortium/ITKElastix> <br> <https://github.com/SimpleITK/SimpleITK/blob/main/LICENSE> | médio | Médio: requer conversão de STLs para máscaras ou mapas de distância (SDF) | Sim |
| **5. Pipeline Híbrido (Global Afim + Regional por Estrutura `probreg` + Validação Slicer)** | Alinhamento global grosseiro seguido de registro não-rígido **órgão a órgão** para absorver distorções estilísticas do HRA (Maya) | Composição **MIT** + **Apache-2.0** + **3D-Slicer-1.0** | Ver URLs das opções 1–4 | alto | Baixo-Médio em qualidade; exige curadoria semântica de pares HRA ↔ Denver ↔ NLM | Sim (componentes) |

- **Estratégia para atlas remodelado por ilustradores (HRA):** evitar registro global rígido/deformável único; usar alinhamento global afim seguido de ajuste **regional/por estrutura** (órgão a órgão) avaliado por **DSC**, **HD95**, **ASSD/MSD**, **TRE** (fiduciais) e **Mattes Mutual Information** (imagem-imagem).

---

### G4 — Qualidade geométrica, reparo de malhas e protocolo de revisão

| opção | o que resolve | licença (trecho citado) | URL | esforço estimado | risco | verificado? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. `trimesh` + `Open3D`** | Checagem `is_watertight`, reparo básico (`fill_holes`, `fix_normals`), limpeza de vértices/triângulos duplicados e suavização Taubin preservadora de volume (`filter_taubin` / `filter_smooth_taubin`) | **MIT License**: `"Permission is hereby granted, free of charge..."` | <https://github.com/mikedh/trimesh> <br> <https://github.com/isl-org/Open3D> | baixo | Baixo: furos complexos ou *non-manifold* severo exigem fallback | Sim |
| **2. `surface-distance` + `MONAI` / `SimpleITK`** | Métricas padrão de fidelidade geométrica e segmentação: **Dice (DSC)**, **ASSD**, **HD95** e **Surface Dice (NSD)** | **Apache-2.0**: `"Licensed under the Apache License, Version 2.0..."` (`surface-distance`; `MONAI`/`SimpleITK` também Apache-2.0) | <https://github.com/google-deepmind/surface-distance> <br> <https://github.com/Project-MONAI/MONAI/blob/dev/LICENSE> | baixo | Baixo: exige rasterização consistente quando a entrada for apenas malha poligonal | Sim (`surface-distance`) |
| **3. Protocolo de Revisão Anatômica (HuBMAP HRA SME SOP + BodyParts3D/VHP)** | Governança de validação por anatomistas (SMEs): checagem ontológica (TA/FMA/Uberon), Posição Anatômica Padrão, marcos pós-decimação e controle de interpenetrações | HRA Zenodo SOP (`CC BY 4.0` reportado; trecho literal `não verificado`); BodyParts3D (`CC BY-SA 2.1 JP` / `CC BY 4.0` reportado) | <https://doi.org/10.5281/zenodo.11625379> <br> <https://doi.org/10.1093/nar/gkn613> | médio | Médio: depende de disponibilidade de anatomistas (SMEs / parceria UFSCar) | Parcial (DOIs verificados; trechos literais de licença não retornados) |
| **4. `PyMeshLab`** | Reparo topológico pesado (*non-manifold*, faces de área zero, `close_holes`) e `apply_coord_taubin_smoothing` | **GPLv3**: `"GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007..."` | <https://github.com/cnr-isti-vclab/PyMeshLab/blob/main/LICENSE> | médio | Médio: **copyleft forte (GPLv3)** — usar apenas como ferramenta batch offline isolada | Sim |
| **5. `FEMORS` (Andreassen et al., 2022/2024 — RBF/GRNN)** | Remoção automática de *overclosures* e ajuste de *gaps* entre malhas adjacentes | Reportado como **GPL-3.0** (`não verificado` literalmente no `LICENSE`) | <https://doi.org/10.48550/arXiv.2209.06948> <br> <https://github.com/thor-andreassen/femors> | alto | Alto custo de portabilidade (MATLAB) + possível GPL-3.0 | Parcial (DOIs verificados; licença não lida literalmente) |

---

### G5 — Validação dos nomes em português (1.659 BodyParts3D + 721 HRA)

| opção | o que resolve | licença (trecho citado) | URL | esforço estimado | risco | verificado? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Wikidata SPARQL (`P1323` TA98 + `P1402` FMA + labels `pt`/`pt-br`)** | Cruza automaticamente FMA/UBERON com IDs TA98 e rótulos `pt`/`pt-br` para pré-validação em lote | **CC0 1.0 Universal** (domínio público para dados estruturados; trecho literal da página: `não verificado`) | <https://www.wikidata.org/wiki/Wikidata:Licensing> | baixo | Médio: qualidade dos labels `pt-br` na Wikidata varia e exige auditoria humana | Parcial |
| **2. DeCS/MeSH — BIREME/OPAS/OMS (API v.2 + XML PT)** | Valida termos anatômicos em português com autoridade BVS/OMS | Licença gratuita mediante acordo formal OPAS/BIREME; proíbe redistribuição isolada (trecho literal do contrato: `não verificado`) | <https://decs.bvsalud.org/> | médio | Médio: trâmite de licença gratuita e escopo mais clínico/bibliográfico que TA estrita | Parcial |
| **3. FIPAT TA2 (`fipat.library.dal.ca/ta2/` + `ta2viewer.openanatomy.org`)** | Árvore canônica oficial TA2 (Latim + Inglês) e links cruzados para Wikidata/FMA/MeSH (não inclui PT-BR) | *"The publication of Terminologia Anatomica is under a Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0) license. The individual terms in this terminology are within the public domain."* (visto via `search_web` indexado em `fipat.library.dal.ca/ta2/`; URL não abriu diretamente na conferência do revisor por falha de DNS) | <https://fipat.library.dal.ca/ta2/> <br> <https://ta2viewer.openanatomy.org/> | médio | Baixo/Médio: termos individuais são domínio público, mas exige ponte para PT-BR | **não verificado diretamente** (visto apenas via `search_web`) |
| **4. SBA — *Terminologia Anatômica* (Livro Manole, 2001)** | Padrão-ouro oficial em PT-BR para revisão humana/especialista | Direitos autorais Editora Manole / SBA (`não verificado` texto literal; site da SBA não disponibiliza PDF/API digital) | <https://sbanatomia.org.br/> | alto | Alto se usado sem triagem automática prévia | Parcial |
| **5. SNOMED CT (MLDS / HL7 Brasil)** | Padrão clínico nacional (RNDS / Portaria MS 2.073/2011) | Exige Affiliate License via MLDS (`não verificado` literalmente) | <https://www.snomed.org/> | alto | Alto: burocracia de licença em produção e foco clínico diferente da TA descritiva | Parcial |

- **Cobertura do cruzamento automático em G5:** das `721` entradas em `hra/nomes_pt_hra.csv`, **`511` labels** possuem ID de ontologia FMA/UBERON (`210` não possuem ontologia — `sem_ontologia: true` — e ficam fora do cruzamento automático por ID, dependendo de revisão humana direta). No `bp3d-m`, os `1.659` conceitos FMA distintos permitem cruzamento direto por `P1402`.

---

## 9. Validação
Planejado — não executado.

## 10. Limitações
Em parte das consultas web (`G1` MedShapeNet/NIH 3D/SPL, `G2`, `G5` DeCS/SBA/SNOMED/Wikidata e `FIPAT TA2` cujo domínio `fipat.library.dal.ca` não resolveu diretamente na conferência), os dados vêm de trechos indexados via `search_web` sem leitura do arquivo bruto na íntegra; esses itens permanecem marcados como `Parcial` ou `não verificado diretamente`.

## 11. Conclusão
- **Observado:** foi verificada a existência e o regime de licenciamento de alternativas abertas para **G2** (Kaggle T4 gratuito e `TotalSegmentator` sob `Apache-2.0` com `--device cpu`/`--roi_subset`), **G3** (`probreg`/`pycpd` sob `MIT`, `ANTsPy`/`itk-elastix`/`SimpleITK` sob `Apache-2.0`, `3D Slicer` sob `3D-Slicer-1.0`), **G4** (`trimesh`/`Open3D` sob `MIT`, `surface-distance`/`MONAI` sob `Apache-2.0`) e **G5** (`Wikidata` reportada como `CC0`, `DeCS/BIREME` gratuito mediante acordo). Para **G1**, verificou-se que **Ella V2.0** proíbe redistribuição (`2.3.2`) e agrupa em 22 tecidos, **Visible Korean** é `CC BY-NC 4.0`, `appendicular_bones` é comercial e **Z-Anatomy** declara `CC BY-SA 4.0` em `Readme.md` (com sub-modelos `CC-BY-NC*` listados em `ATTRIBUTIONS`).
- **Interpretação:** as ferramentas identificadas em G2–G5 **podem** reduzir os respectivos gargalos (precisão em 1,5 mm, registro por estrutura, métricas de superfície e pré-triagem terminológica), mas sua eficácia e compatibilidade efetiva ainda dependem de execução experimental e auditoria das licenças marcadas como parciais/não verificadas. Em G1, nenhuma fonte aberta `CC BY 4.0` verificada cobre integralmente membros superiores, vasos e nervos periféricos.
- **Veredito da hipótese:** `em aberto`

## 12. Recomendação priorizada

### 3 ações de maior impacto para fazer JÁ (no MVP)
1. **Resolver G2 + `EXP-0011` sem OOM (1,5 mm real):** rodar `TotalSegmentator total` em resolução padrão `1,5 mm` nos ossos críticos (`--roi_subset femur_left femur_right hip_left hip_right sacrum` com `--device cpu` nos 64 GB RAM locais, ou no Kaggle `GPU T4 x2` usando apenas a TC pública da NLM) e reexecutar o ICP Etapa A e, **somente após aprovação da Etapa A (`< 3 mm`), executar a Etapa B (TC NLM → HRA)** + métricas **DSC, ASSD e HD95** (`trimesh`/`Open3D` + `surface-distance`), deixando explícito que os **128 STLs da Denver cobrem apenas membros inferiores** (pelve até os pés).
2. **Pré-validar os termos com ontologia (G5):** executar cruzamento automatizado via **Wikidata SPARQL (`P1402`/`P1323` + labels `pt`/`pt-br`)** sobre os `1.659` termos FMA do `bp3d-m` e os **`511` labels com ontologia** do `hra-f` (ficando os `210` sem ontologia para revisão humana direta), gerando uma fila priorizada para revisão contra a **SBA** (`validacao = 'revisado'`).
3. **Instituir checklist geométrico mínimo antes de publicar qualquer atlas (G4):** automatizar em pipeline permissivo (`trimesh`/`Open3D`, MIT) a checagem de estanqueidade, normais, ausência de vértices degenerados e preservação de volume após suavização Taubin, mantendo explicitamente documentadas na UI as lacunas de membros superiores do `hra-f`.

### O que fica para depois do MVP
- **Decisão jurídica/arquitetural sobre G1 (`Z-Anatomy CC BY-SA 4.0` vs. `MedShapeNetCore CC BY 4.0`):** avaliar se vale manter os assets 3D sob `CC BY-SA 4.0` (separados do código) ou compor membros superiores/vasos/nervos via subconjuntos `CC BY 4.0` auditados do `MedShapeNetCore` + `NIH 3D 3DPX-017237`.
- **Registro não-rígido por estrutura (`probreg` CPD/BCPD) entre HRA (Maya) e segmentações reais (NLM/Denver)** e **protocolo formal de revisão por anatomistas (parceria UFSCar)** inspirado no SOP do HuBMAP HRA.
- **Solicitação de licença gratuita DeCS/MeSH (BIREME/OPAS)** para enriquecimento terminológico clínico em escala.

## 13. Rastreabilidade
- **Commits:** não aplicável
- **Scripts:** não aplicável
- **Logs:** não aplicável
- **Resultados / artefatos:** `pesquisa/experimentos/EXP-0013-gargalos-reconstrucao.md`

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** pendente
- **Validação científica:** pendente
- **Validação clínica:** não aplicável
