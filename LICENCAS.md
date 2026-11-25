# Licenças das fontes de terceiros

Toda fonte anatômica usada no repositório, com a versão exata e a atribuição exigida. Atualizar ao trocar qualquer versão.

| Atlas / uso | Fonte e versão | Licença | Situação |
| --- | --- | --- | --- |
| `bp3d-m` (`bodyparts3d/`) | BodyParts3D release 4.0 (dados de 2013-06-19), árvore is_a, malhas 99% reduzidas | CC BY 4.0 | Confirmada em 2026-11-25 na página oficial (licença atualizada em 2025-02-27) |
| `hra-f` (`hra/`) | Human Reference Atlas, 3D Reference Organ Set United Female **v1.10** (publicado em 2026-06-15, DOI 10.48539/HBM637.DWBM.744), baixado do CDN `latest` em 2026-11-25 | CC BY 4.0 | Confirmada em 2026-11-25 no README oficial (detalhes em `hra/LICENCA_HRA.md`) |
| `teste-anatomia/` | TotalSegmentator, "Small subset" v2.0.1, caso s1371 | CC BY 4.0 | Só teste interno; fora do produto |
| Nomes em português (`bodyparts3d/nomes_pt.csv`) | Tradução própria dos nomes FMA | Do projeto | Revisão médica pendente |

## Atribuições exigidas

**BodyParts3D** — mostrar na tela onde o atlas aparece:

> BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International

Fonte: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html. Os cabeçalhos dos OBJ ainda citam CC BY-SA 2.1 JP (texto antigo); vale a licença da página.

**TotalSegmentator** (só `teste-anatomia/`):

> Wasserthal J. et al., "TotalSegmentator: Robust Segmentation of 104 Anatomic Structures in CT Images", Radiology: Artificial Intelligence, 2023. Dataset v2.0.1, University Hospital Basel — https://zenodo.org/records/10047263

**HRA** (`hra-f`):

> Browne, Kristen, and Heidi Schlehlein. 2026. 3D Reference Organ Set for Female, v1.10. https://doi.org/10.48539/HBM637.DWBM.744 — CC BY 4.0. Data from the Visible Human Dataset, courtesy of the U.S. National Library of Medicine.

A NLM pede o crédito "Courtesy of the U.S. National Library of Medicine" e proíbe sugerir endosso; a frase acima cumpre os dois.

## Regras

- Uma versão de atlas publicada nunca muda; versão nova = nova linha nesta tabela.
- Fonte sem licença confirmada não entra em build público.
- CC BY-SA (ex.: Z-Anatomy) não é usado sem decisão explícita: obrigaria a compartilhar os derivados.
