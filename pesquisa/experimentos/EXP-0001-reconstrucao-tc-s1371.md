# EXP-0001 — Reconstrução anatômica a partir de TC com TotalSegmentator (caso s1371)

> **REGISTRO RETROSPECTIVO** — Reconstruído a partir de `teste-anatomia/LEIAME.md`, `teste-anatomia/scripts/*.py`, `LICENCAS.md` e commit `1fec829`. Campos ausentes nas evidências são marcados como `não documentado`.

## 1. Identificação
- **ID:** `EXP-0001`
- **Título:** Reconstrução anatômica a partir de TC com TotalSegmentator (caso `s1371`)
- **Data:** `2026-11-25`
- **Responsável:** não documentado
- **Agentes de IA:** não documentado
- **Branch:** `etapa-1-fundacao` (origem em `1fec829`)
- **Commit(s):** `1fec829`
- **Linha de pesquisa:** `LP01`
- **Situação:** `concluído`

## 2. Problema
Avaliar se segmentações tomográficas públicas do TotalSegmentator podem ser convertidas em malhas 3D leves, organizadas por camadas anatômicas, para visualização direta no navegador.

## 3. Hipótese
É possível extrair malhas 3D por camada anatômica (`ossos`, `musculos`, `coracao`, `vasos`, `orgaos`) a partir das máscaras NIfTI do caso `s1371`, mantendo alinhamento espacial entre camadas após centralização comum.

## 4. Fundamentação teórica
Superfícies isovalor via *marching cubes* sobre máscaras binárias em espaço canônico NIfTI, seguidas de simplificação quádrica e suavização de Taubin (`teste-anatomia/scripts/gerar_malhas.py`).

## 5. Materiais e ambiente
- **Datasets e versões:** TotalSegmentator `"Small subset"` v2.0.1, caso `s1371` (`https://zenodo.org/records/10047263`).
- **Licenças:** CC BY 4.0 (`LICENCAS.md`).
- **Hashes:** não documentado.
- **Hardware:** não documentado.
- **Sistema operacional:** não documentado.
- **Bibliotecas e versões:** Python com `nibabel`, `numpy`, `trimesh`, `scikit-image` (`skimage.measure`); versões exatas não documentadas; Three.js no visualizador HTML.
- **Seed:** não aplicável (determinístico).

## 6. Metodologia
- **Procedimentos e algoritmos:** download seletivo via HTTP Range (`baixar_caso.py`); conversão NIfTI→malha com `nib.as_closest_canonical`, padding de 1 voxel, `marching_cubes(step_size=1)`, transformação `RAS_PARA_THREE` (`mm → m`), simplificação por `simplify_quadric_decimation` (alvo `4000` triângulos/estrutura), `filter_taubin(iterations=10)`, centralização pelo centro médio das caixas e exportação em GLB por camada (`gerar_malhas.py`).
- **Parâmetros:** `ALVO_TRIANGULOS = 4000`, `mascara.sum() >= 50`, `iterations=10`.
- **Comandos para reproduzir:** `python baixar_caso.py` → `python gerar_malhas.py <pasta_segmentations> <pasta_saida>` → `python gerar_visualizador.py`.

## 7. Critérios de sucesso (definidos antes da execução)
Não documentado retrospectivamente.

## 8. Resultados
Gerados 5 arquivos GLB (`ossos.glb`, `musculos.glb`, `coracao.glb`, `vasos.glb`, `orgaos.glb`), `estruturas.json` e `visualizador.html` funcional (`teste-anatomia/captura.png`). Contagens exatas de triângulos não documentadas em relatório separado (presentes em `estruturas.json`).

## 9. Validação
Inspeção visual via `visualizador.html` (`teste-anatomia/captura.png`).

## 10. Limitações
Uso exclusivo para teste interno (fora do produto); alvo fixo de 4.000 triângulos por estrutura sem adaptação por tamanho; dependência de internet no visualizador para carregar Three.js.

## 11. Conclusão
- **Observado:** o pipeline gerou malhas GLB alinhadas entre camadas a partir do caso `s1371`.
- **Interpretação:** a abordagem é viável para prototipagem rápida, mas não substitui um atlas anatômico completo de referência.
- **Veredito da hipótese:** `sustentada`

## 12. Próximos passos
Avaliar atlas anatômicos completos (BodyParts3D) e testar compatibilidade espacial com `s1371` (`EXP-0002`, `EXP-0003`).

## 13. Rastreabilidade
- **Commits:** `1fec829`
- **Scripts:** `teste-anatomia/scripts/baixar_caso.py`, `teste-anatomia/scripts/gerar_malhas.py`, `teste-anatomia/scripts/gerar_visualizador.py`
- **Logs:** não documentado
- **Resultados / artefatos:** `teste-anatomia/LEIAME.md`, `teste-anatomia/modelos/*.glb`, `teste-anatomia/modelos/estruturas.json`, `teste-anatomia/captura.png`

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** não documentado
- **Validação científica:** não documentado
- **Validação clínica:** não aplicável (teste interno de prototipagem)
