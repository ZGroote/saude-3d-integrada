# EXP-0029 — NIH 3D e Open Anatomy: conferência de modelos que cubram lacunas conhecidas

## 1. Identificação
- **ID:** `EXP-0029`
- **Título:** Conferência completa do NIH 3D e do Open Anatomy (SPL) contra as lacunas conhecidas dos atlas
- **Data:** `2026-11-27`
- **Responsável:** usuário (pedido de exploração), Claude Code (protocolo e execução)
- **Agentes de IA:** Claude Code
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** a preencher
- **Linha de pesquisa:** `LP01`
- **Situação:** `concluído — H29 rejeitada (nenhum modelo atende; melhor pelve feminina é não comercial)`

## 2. Problema
O `EXP-0013` citou o NIH 3D e o Open Anatomy só por trechos de busca (fichas "parcial") e com foco no membro superior. Desde então surgiram lacunas novas e confirmadas: pelve feminina incompleta (púbis, ísquio, acetábulo — `EXP-0024`), joelho ausente no `hra-f` (`pesquisa/validacao-medica/bodysite_malhas.csv`), músculos femininos (`EXP-0023`, `EXP-0025`), pés femininos e pediatria (`EXP-0027`). É preciso conferir as duas fontes por inteiro antes de descartá-las.

## 3. Hipótese
- **H29:** pelo menos um modelo do NIH 3D ou do Open Anatomy atende todos os critérios de §7 para alguma lacuna listada.

## 4. Fundamentação teórica
Ver `EXP-0013` (levantamento de fontes) e `EXP-0023`/`EXP-0027` (critérios de licença e procedência usados antes).

## 5. Materiais e ambiente
- Fontes: <https://3d.nih.gov/> (catálogo e API pública, se houver) e <https://www.openanatomy.org/> (atlas e repositórios ligados).
- Sem login, sem contornar proteção, sem download de arquivo grande (> 50 MB) nesta etapa; só páginas, metadados e, quando necessário para ler licença ou cabeçalho, arquivos pequenos.

## 6. Metodologia
1. NIH 3D: buscar no catálogo os termos de cada lacuna (pelvis, hip bone, pubis, ischium, acetabulum, knee, femur, tibia, patella, foot, muscle, female, pediatric/child/infant, full body/anatomy) e registrar cada entrada anatômica humana encontrada: ID, título, origem (imagem real? paciente/voluntário? sexo/idade), formato, licença.
2. Open Anatomy: listar todos os atlas publicados; para cada um: região, estruturas, origem (sujeito, sexo, idade, modalidade), formato, licença e onde baixar.
3. Classificar cada candidato pelos critérios de §7.

## 7. Critérios de sucesso (definidos antes da execução)
Um modelo **serve** (candidato a experimento de integração) só se cumprir todos:
- **K1 lacuna:** cobre ao menos uma lacuna de §2 (no sexo certo quando a lacuna é feminina).
- **K2 licença:** permite uso comercial e obras derivadas (CC0, CC BY, BSD/MIT/Slicer-like). NC, ND ou licença ausente reprovam; GPL fica "condicional" (exige decisão jurídica).
- **K3 procedência:** vem de imagem de pessoa real (TC/RM/criossecção), com sexo informado.
- **K4 formato:** malha ou rótulo volumétrico baixável (STL/OBJ/GLB/VTK/NRRD/NIfTI…), não só imagem ou impressão.
- **K5 completude:** a estrutura vem inteira (não um fragmento ou peça impressa simplificada).

H29 sustentada se ao menos um modelo cumprir K1–K5. Cumprir isso **não** significa que o modelo será usado: só que vale um experimento de integração próprio, pré-registrado.

## 8. Resultados
Detalhes e tabelas em `pesquisa/resultados/EXP-0029/RELATORIO.md`.
- **Correção do protocolo:** o joelho **não** é lacuna do `hra-f` (44 malhas de joelho no índice); o "sem correspondência" era só do mapeamento FHIR (UBERON × FMA). Registrado antes da classificação.
- **Open Anatomy:** 7 atlas; licença 3D Slicer Parte B (permissiva, mas "clinical applications are neither recommended nor advised"). Sexo informado só nos atlas masculinos (cérebro 42 a, tórax 38 a). O abdome tem a pelve como **um único rótulo** e FOV de 24 cm. Nenhum cobre lacuna feminina.
- **NIH 3D:** 24 termos, 504 modelos distintos, 20 fichas abertas. Entradas do HRA são a mesma fonte do `hra-f` (pelve v1.2, joelho v1.1, corpo v1.5 — mais antigo que o nosso 1.10). A única pelve feminina inteira e real (USUHS, 3DPX-014841/015843) é **CC BY-NC-SA**. As pelves CC BY não informam sexo (MySegmenter, bgobbato) ou são estilizadas em CAD (3DPX-017321). Pediatria: crânios isolados sem origem.
- **Nenhum modelo cumpre K1–K5.**

## 9. Validação
Conferência feita pelo próprio executor; sem segundo revisor. Licenças lidas nos links de cada ficha e no texto da licença do 3D Slicer (GitHub, Parte B).

## 10. Limitações
- Triagem por título: um modelo útil com título enganoso pode ter escapado; os termos cobrem cada lacuna em inglês.
- "Source Data Details" é preenchido pelo autor; sexo ausente não prova que o dado não exista na origem.
- Termos de terceiros (dados do OsiriX no atlas de cabeça e pescoço, TCIA nas sínfises) não verificados.
- Ao importar o leitor por Range do `EXP-0023`, o código de nível de módulo dele rodou de novo e baixou outra vez o `meta.csv` do TotalSegmentator (35,9 MB); o arquivo regravado é idêntico (sem diferença no git).

## 11. Conclusão
- **Observado:** nenhum dos 7 atlas do Open Anatomy nem dos 504 modelos do NIH 3D varridos cumpre os critérios; a melhor pelve feminina é não comercial.
- **Interpretação:** as duas fontes não resolvem nenhuma lacuna do produto. Para a pelve, fonte livre já existe (TotalSegmentator); o gargalo é o encaixe no `hra-f` (`EXP-0014`–`EXP-0016`).
- **Veredito da hipótese:** H29 `rejeitada`.

## 12. Próximos passos
- Opcional (humano): pedir ao autor da USUHS licença comercial para 3DPX-014841. Não abre experimento sem decisão de retomar o encaixe ósseo.
- Nenhuma ação no produto.

## 13. Rastreabilidade
- **Scripts:** `pesquisa/resultados/EXP-0029/nih_varre.py`, `nih_fichas.py`, `nih_fonte.py`
- **Logs:** `pesquisa/resultados/EXP-0029/nih3d_busca.json`, `openanatomy_*_atlasStructure.json`
- **Resultados / artefatos:** `pesquisa/resultados/EXP-0029/RELATORIO.md`

## 14. Revisão
- **Revisor:** Claude Code
- **Revisão humana:** pendente
- **Validação científica:** não realizada
