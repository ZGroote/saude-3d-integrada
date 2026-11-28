# EXP-0029 — Relatório: NIH 3D e Open Anatomy contra as lacunas conhecidas

Execução: Claude Code, 2026-11-27. Navegação pública, sem login; NIH 3D lido com o Chrome do sistema via Playwright (a busca é montada no navegador e não tem API pública documentada). Nenhum modelo baixado; zips do Open Anatomy lidos por HTTP Range só no diretório central, `README.md`, `LICENSE.md`, cabeçalho NRRD e MRML (≈ 0,6 MB no total).

## Correção registrada antes da análise
O §2 do protocolo listou "joelho ausente no `hra-f`". **Está errado:** o `hra-f/1.10-1` tem patela, tíbia, fíbula, meniscos, côndilos femorais, cartilagem e ligamentos do joelho dos dois lados (44 malhas em `web/public/atlas/hra-f/1.10-1/indice.json`). O "sem correspondência" de `pesquisa/validacao-medica/bodysite_malhas.csv` vem só do mapeamento da importação FHIR (que procura UBERON, e o joelho do `hra-f` usa FMA). O joelho sai da lista de lacunas geométricas; continua como lacuna de mapeamento FHIR, já registrada no `SPEC-MVP.md`.

## Open Anatomy (openanatomy.org) — 7 atlas, todos conferidos

Licença de todos: **3D Slicer License, Parte B** (uso comercial e derivados permitidos com o texto da licença; cláusula 4: *"designed for research purposes only… clinical applications are neither recommended nor advised"*; cláusula 3: não cobre direitos de terceiros).

| Atlas | Origem | Sexo/idade | Lacuna coberta? | Resultado |
|---|---|---|---|---|
| SPL Knee (2016-09, 80,9 MB) | RM de um joelho (FOV 140 mm) | não informado | Nenhuma (o `hra-f` tem joelho) | K1, K3 ✗ |
| SPL Abdomen (2016-09, 34,9 MB) | TC (256×256×113, 0,94×0,94×1,5 mm, FOV 240 mm) | não informado | Pelve? Só **um rótulo "Pelvis"** (os dois ossos do quadril fundidos, sem lado, sem púbis/ísquio/acetábulo separados); FOV de 24 cm provavelmente corta a pelve | K3, K5 ✗ |
| SPL Head and Neck (2016-09) | TC "MANIX" da coleção de exemplos do OsiriX, reduzida a 256×256 | não informado | Crânio (o `hra-f` não tem crânio individualizado) | K3 ✗; dado de terceiro (OsiriX) com termos próprios não verificados |
| SPL Liver (2014) | TC | não informado | Nenhuma | K1 ✗ |
| SPL/NAC Brain (2017) | RM 3T | **homem**, 42 anos | Nenhuma feminina | K1 ✗ |
| SPL Inner Ear (2018) | TC de bancada | não informado | Nenhuma | K1 ✗ |
| Mauritania Thorax (2021) | TC | **homem**, 38 anos | Nenhuma feminina | K1 ✗ |

Não há metadado de doador em `README.md`, `LICENSE.md`, cabeçalhos NRRD ou MRML; as páginas de publicação do SPL citadas no `atlasStructure.json` (`/publications/item/view/1266`, `/1953`) respondem 404.

## NIH 3D (3d.nih.gov) — 24 termos, 504 modelos distintos, todas as páginas de resultado lidas

Termos: pelvis, hip bone, pubis, ischium, acetabulum, innominate, sacrum, knee, patella, tibia, femur, foot, ankle, female anatomy, female, full body, skeleton, skull, muscle, muscles, pediatric, child, infant, newborn. Lista bruta: `nih3d_busca.json`. Triagem por título → 20 fichas abertas (licença, descrição, janela "Source Data Details").

| ID | Modelo | Licença | Origem / sexo | Resultado |
|---|---|---|---|---|
| 3DPX-020984 | Pelvis, Female (HRA v1.2) | CC BY 4.0 | Visible Human Female — **mesma fonte do nosso `hra-f`** | Nada novo |
| 3DPX-020969/70 | Knee, Female L/R (HRA v1.1) | CC BY 4.0 | VHF — mesma fonte; joelho já está no `hra-f` | Nada novo |
| 3DPX-020992 | Body, Female (HRA United v1.5) | CC BY 4.0 | VHF — versão **mais antiga** que a nossa (1.10) | Nada novo |
| 3DPX-014841 / 015843 / 023525 | Pelve feminina inteira (os coxae, sacro, L4–L5, fêmur proximal), USUHS | **CC BY-NC-SA 4.0** | TC com contraste, feminina; refinada em zBrush/3ds Max | **K2 ✗** (não comercial) — a melhor candidata, mas reprovada |
| 3DPX-016666 | Female Thigh, Knee, Leg Bones (mesmo autor) | **CC BY-NC-SA 4.0** | TC, feminina | K2 ✗; K1 ✗ (joelho já existe) |
| 3DPX-017321 | Female Pelvis with Perineal Structures and Musculature | CC BY 4.0 | RM, U. Massachusetts, **modelada em CAD** (Fusion 360) para ensino | K3/K5 ✗ (estilizada, não segmentação) |
| 3DPX-016838 / 016829 | Human Skeleton / Pelvic (MySegmenter) | CC BY 4.0 | TC humana | **K3 ✗ (sexo não informado)** |
| 3DPX-000410 / 000828 | Pelvis (bgobbato) | CC BY 4.0 | sem detalhes de origem | K3 ✗ |
| 3DPX-001325 | Pubic Symphyses, Female 21 | CC BY 3.0 | TC de mulher de 21 anos (TCIA, QIN-HEADNECK-01-0140, segundo o autor) | K5 ✗ (só as faces da sínfise) |
| 3DPX-004896 | Pubic Bones, 34yo Female | CC BY-NC-ND | — | K2, K5 ✗ |
| 3DPX-003410 | Gluteal Muscle | CC BY-NC-ND | — | K2 ✗ |
| 3DPX-004645 / 004744 | Pelve e sacro (embodi3D / tomomahoney) | NC-ND / NC | — | K2 ✗ |
| 3DPX-009510 | Child Skull | CC0 | sem detalhes de origem | K3 ✗ (crânio isolado; pediatria segue sem base, EXP-0027) |
| 3DPX-003169 / 008145 | Baby cranium (13 meses) | CC BY-SA 4.0 | sem detalhes | K3 ✗; SA condicional |
| 3DPX-012260 / 012628 / 012629 / 020591 | Visible Human **Male** (crânio, músculos do braço) | — | homem | K1 ✗ (lacunas são femininas) |

Os demais títulos da varredura são proteínas, dispositivos, órteses, animais, casos de fratura sem metadado (bgobbato, SMART Neuro) ou órgãos do HRA já presentes no `hra-f`.

## Leitura
- **Nenhum modelo cumpre K1–K5.** A única pelve feminina inteira e real (USUHS) é não comercial; as pelves com licença livre não informam sexo ou são estilizadas.
- **Pelve feminina completa não é problema de fonte:** o TotalSegmentator V3 (CC BY 4.0) tem 823 exames femininos, e o `EXP-0024` já usou 31 mulheres com os ossos do quadril inteiros (`EXP-0023`, `EXP-0024`). O que falhou antes foi **encaixar** uma peça de outra pessoa no corpo do `hra-f` (`EXP-0014`–`EXP-0016`). Nenhuma das duas fontes muda isso.
- Caminho que ficaria aberto, só por ação humana: pedir ao autor da USUHS (3DPX-014841) licença para uso comercial. Mesmo assim, o problema do encaixe continuaria.
