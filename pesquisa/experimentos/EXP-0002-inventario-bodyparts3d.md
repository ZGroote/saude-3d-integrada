# EXP-0002 — Inventário e classificação do BodyParts3D (2.234 malhas, 15 sistemas)

> **REGISTRO RETROSPECTIVO** — Reconstruído a partir de `bodyparts3d/RELATORIO.md`, `bodyparts3d/analisar.py`, `bodyparts3d/revisao_outros.csv`, `LICENCAS.md` e commits `1e1389e`, `2b7f443`. Campos ausentes nas evidências são marcados como `não documentado`.

## 1. Identificação
- **ID:** `EXP-0002`
- **Título:** Inventário e classificação do BodyParts3D (2.234 malhas, 15 sistemas)
- **Data:** `2026-11-25`
- **Responsável:** Joao-Guilherme-Groote (autor dos commits) — *fonte: mensagens de commit e registro do coordenador da sessão de 2026-11-25*
- **Agentes de IA:** Claude Code (Claude Opus, coordenador: planejamento, critérios, decisões e revisão; commits com `Co-Authored-By: Claude Opus 5.5`); Antigravity (Gemini — `revisao_outros.csv`, `traducoes_pt.json`); Codex 2 (GPT-6 Luna — 1ª tentativa de tradução, descartada por baixa qualidade) — *fonte: mensagens de commit e registro do coordenador da sessão de 2026-11-25*
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** `1e1389e`, `2b7f443`
- **Linha de pesquisa:** `LP01`
- **Situação:** `concluído`

## 2. Problema
Catalogar todas as malhas do BodyParts3D 4.0 e classificá-las em sistemas anatômicos padronizados em português para o atlas masculino `bp3d-m`.

## 3. Hipótese
A combinação de regras por nome em inglês com ancestrais da árvore FMA (`is_a` e `part_of`), complementada por revisão manual da categoria residual `outros`, classifica integralmente as 2.234 malhas em 15 sistemas.

## 4. Fundamentação teórica
Ontologia Foundational Model of Anatomy (FMA 3.0 — conforme o cabeçalho dos OBJ, `Build-up logic : FMA 3.0`, em `bodyparts3d/bruto/`, fora do git) e relações `is_a` / `part_of` distribuídas no BodyParts3D 4.0.

## 5. Materiais e ambiente
- **Datasets e versões:** BodyParts3D release 4.0 (2013-06-19), árvore `is_a`, malhas OBJ com 99% de redução.
- **Licenças:** CC BY 4.0 (página oficial atualizada em 2025-02-27; cabeçalhos OBJ citam CC BY-SA 2.1 JP).
- **Hashes:** não documentado para os OBJs brutos.
- **Hardware:** não documentado.
- **Sistema operacional:** não documentado.
- **Bibliotecas e versões:** Python (`csv`, `re`, `numpy`, `trimesh`); versões exatas não documentadas.
- **Seed:** não aplicável.

## 6. Metodologia
- **Procedimentos e algoritmos:** leitura dos cabeçalhos OBJ (`Concept ID`, `English name`, `Bounds(mm)`), contagem de vértices/triângulos, classificação por lista ordenada de regex no nome seguida de interseção com ancestrais FMA (`analisar.py`), e revisão manual das 149 entradas residuais `outros` (`revisao_outros.csv`, incluindo 17 OBJs sem nome resolvidos via `isa_element_parts.txt` e pares espelhados `FJxxxxM`).
- **Parâmetros:** 15 sistemas-alvo (`arterial`, `muscular`, `venoso`, `esqueletico`, `nervoso`, `digestorio`, `respiratorio`, `articular`, `sensorial`, `cardiaco`, `urogenital`, `endocrino`, `fascia`, `tegumentar`, `linfatico`).
- **Comandos para reproduzir:** `python -I bodyparts3d/analisar.py`

## 7. Critérios de sucesso (definidos antes da execução)
Não documentado retrospectivamente.

## 8. Resultados
- **2.234 malhas** catalogadas, **1.659 conceitos FMA distintos**, **6.681.030 triângulos** no total (média 2.990 por estrutura), altura do corpo 1.730 mm (unidades em mm, Z para cima).
- Distribuição final nos 15 sistemas documentada em `bodyparts3d/RELATORIO.md` (ex.: `arterial`: 633, `muscular`: 410, `venoso`: 385, `esqueletico`: 244, `nervoso`: 141, `digestorio`: 137, `respiratorio`: 104, `articular`: 69, `sensorial`: 45, `cardiaco`: 28, `urogenital`: 18, `endocrino`: 11, `fascia`: 4, `tegumentar`: 4, `linfatico`: 1).

## 9. Validação
Conferência da contagem total (2.234 malhas) e revisão manual das 149 entradas `outros` em `bodyparts3d/revisao_outros.csv`.

## 10. Limitações
Corpo único masculino adulto (2013), sem anatomia feminina; lacuna na artéria carótida (trecho entre comum e interna ausente, sem carótida externa); 17 malhas sem ID FMA no cabeçalho OBJ; nomes em português (`nomes_pt.csv`) pendentes de revisão médica.

## 11. Conclusão
- **Observado:** todas as 2.234 malhas foram catalogadas e distribuídas em 15 sistemas.
- **Interpretação:** o BodyParts3D 4.0 serve como base completa para o atlas masculino `bp3d-m`, respeitadas suas lacunas anatômicas conhecidas.
- **Veredito da hipótese:** `sustentada`

## 12. Próximos passos
Testar encaixe espacial com o caso `s1371` (`EXP-0003`) e comprimir os GLBs para web (`EXP-0004`).

## 13. Rastreabilidade
- **Commits:** `1e1389e`, `2b7f443`
- **Scripts:** `bodyparts3d/analisar.py`
- **Logs:** não documentado
- **Resultados / artefatos:** `bodyparts3d/catalogo_bp3d.csv`, `bodyparts3d/revisao_outros.csv`, `bodyparts3d/RELATORIO.md`

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** pendente para os nomes em português (`validacao = pendente`)
- **Validação científica:** não documentado
- **Validação clínica:** não realizada
