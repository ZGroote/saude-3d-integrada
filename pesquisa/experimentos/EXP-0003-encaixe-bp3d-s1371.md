# EXP-0003 — Encaixe BodyParts3D × s1371 por similaridade

> **REGISTRO RETROSPECTIVO** — Reconstruído a partir de `bodyparts3d/analisar.py`, `bodyparts3d/RELATORIO.md`, `SPEC-MVP.md` §5.1 e commit `1e1389e`. Campos ausentes nas evidências são marcados como `não documentado`.

## 1. Identificação
- **ID:** `EXP-0003`
- **Título:** Encaixe BodyParts3D × `s1371` por similaridade (erro médio 36,5 mm)
- **Data:** `2026-11-25`
- **Responsável:** não documentado
- **Agentes de IA:** não documentado
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** `1e1389e`
- **Linha de pesquisa:** `LP01`
- **Situação:** `concluído`

## 2. Problema
Verificar se um atlas anatômico de referência (BodyParts3D) pode ser alinhado geometricamente a um caso tomográfico independente (`s1371` do TotalSegmentator) por transformação global de similaridade.

## 3. Hipótese
Um ajuste global de similaridade (escala uniforme, rotação e translação) sobre os centros de estruturas comuns alinha o BodyParts3D ao caso `s1371` com erro residual baixo o suficiente para combinar ou sobrepor fontes diferentes.

## 4. Fundamentação teórica
Algoritmo de Umeyama (mínimos quadrados por SVD para estimativa de escala `s`, rotação `R` e translação `t` entre nuvens de centroides correspondentes).

## 5. Materiais e ambiente
- **Datasets e versões:** BodyParts3D 4.0 e TotalSegmentator `"Small subset"` v2.0.1 caso `s1371`.
- **Licenças:** CC BY 4.0 (`LICENCAS.md`).
- **Hashes:** não documentado.
- **Hardware:** não documentado.
- **Sistema operacional:** não documentado.
- **Bibliotecas e versões:** Python (`numpy`, `trimesh`); versões exatas não documentadas.
- **Seed:** não aplicável.

## 6. Metodologia
- **Procedimentos e algoritmos:** pareamento manual de 28 estruturas comuns entre `s1371` e BodyParts3D (`PARES` em `bodyparts3d/analisar.py`), cálculo dos centros das caixas delimitadoras e ajuste por `umeyama(A, B)`.
- **Parâmetros:** 28 pares anatômicos completos no CT de `s1371`.
- **Comandos para reproduzir:** `python -I bodyparts3d/analisar.py`

## 7. Critérios de sucesso (definidos antes da execução)
Não documentado retrospectivamente.

## 8. Resultados
- **Escala BP3D → `s1371`:** `0.950`
- **Erro médio após o ajuste:** **`36.5 mm`** (máximo **`86.2 mm`** em `lung_upper_lobe_right`; `55 mm` em `sacrum` e `trachea`; `54 mm` em `spleen`; menor erro `10 mm` em `vertebrae_L5`).

## 9. Validação
Autoteste sintético da função `umeyama` em `analisar.py` recuperando transformação conhecida (`escala 1.3`, rotação `0.7 rad` em `[1,2,3]`, translação `+5`) com tolerância `< 1e-9` (`assert abs(_s - 1.3) < 1e-9 and np.allclose(_Rr, _R)`).

## 10. Limitações
Alinhamento avaliado apenas por centroides de caixas delimitadoras (não por superfícies completas) em um único par de indivíduos.

## 11. Conclusão
- **Observado:** mesmo após ajuste ótimo de similaridade, as diferenças individuais de proporção e postura entre sujeitos produzem erro médio de 36,5 mm (até 86,2 mm).
- **Interpretação:** fontes anatômicas de indivíduos distintos **não devem ser misturadas ou alinhadas diretamente** entre si; cada atlas deve ser um corpo de referência independente, ligado apenas por IDs de ontologia (`SPEC-MVP.md` §5.1).
- **Veredito da hipótese:** `rejeitada`

## 12. Próximos passos
Adotar arquitetura multi-atlas independente (`bp3d-m`, `hra-f`) em `SPEC-MVP.md` §5.1.

## 13. Rastreabilidade
- **Commits:** `1e1389e`
- **Scripts:** `bodyparts3d/analisar.py`
- **Logs:** não documentado
- **Resultados / artefatos:** `bodyparts3d/RELATORIO.md`, `SPEC-MVP.md` §5.1

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** não documentado
- **Validação científica:** não documentado
- **Validação clínica:** não aplicável
