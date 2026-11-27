# EXP-0026 — Viabilidade da reconstrução volumétrica da base KISTI de músculos do membro inferior

## 1. Identificação
- **ID:** `EXP-0026`
- **Título:** As fatias 2D do conjunto AI-ready (DataON 1472) podem ser empilhadas em volumes por caso, e os casos femininos podem ser identificados?
- **Data:** `2026-11-27`
- **Responsável:** usuário (autorização), Claude Code (protocolo e revisão)
- **Agentes de IA:** Claude Code (protocolo e revisão), Antigravity (execução)
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** a preencher
- **Linha de pesquisa:** `LP01`
- **Situação:** `planejado`

## 2. Problema
O EXP-0023 encontrou uma única base aberta (CC BY 4.0) com músculos do membro inferior segmentados individualmente: 20 pessoas (10 mulheres), 13 músculos e 31 ossos por membro, publicada como pares 2D de imagem e máscara. O artigo não liga o sexo aos IDs de caso (`hm_25_001_ct` a `hm_25_040_ct`). Se for possível remontar o volume de cada perna e saber quais são de mulheres, a base vira referência independente de validação muscular.

## 3. Hipótese
H26: as fatias axiais de cada caso estão completas, ordenadas e com espaçamento conhecido, permitindo remontar volumes 3D sem lacunas; e o sexo de cada caso pode ser determinado a partir de dados publicados.

## 4. Fundamentação teórica
O artigo informa que o plano axial manteve o espaçamento original de 0,7 mm (~1.291 fatias por membro) e que só foram excluídas fatias "só de fundo". Se as fatias forem numeradas pela posição original, o empilhamento reconstrói o volume; se a numeração for sequencial após a exclusão, pode haver buracos invisíveis.

## 5. Materiais e ambiente
- DataON `10.22711/idr/1472` (`class_info.csv`, `images.zip`, `labels.zip`) e `10.22711/idr/1473` (DICOM e STL da fonte, `data.tar`, relatórios `.hwp`).
- Artigo: `https://doi.org/10.1038/s41597-026-08630-0`.
- **Limite de download:** `≤ 5 GB` no total. Arquivos grandes só por HTTP Range (como em `pesquisa/resultados/EXP-0023/extrair_meta_s1.py`), se o servidor aceitar. Não contornar login, formulário ou bloqueio: se o download exigir conta, parar e registrar como ação humana.
- Dados em `hra/externo/kisti/` (fora do git).

## 6. Metodologia
1. **Acesso:** descobrir as URLs de download e os tamanhos dos arquivos dos dois registros; verificar se exigem login e se aceitam Range.
2. **Estrutura:** baixar `class_info.csv`; listar o conteúdo de `labels.zip` (diretório central por Range, ou download inteiro se `≤ 5 GB`).
3. **Um caso:** baixar só as máscaras axiais de um caso (`hm_25_001_ct`) e, se couber, as imagens axiais do mesmo caso.
4. **Ordem e lacunas:** verificar se o nome do arquivo traz índice de fatia; se os índices são contíguos; contar fatias.
5. **Continuidade:** Dice entre máscaras consecutivas por rótulo muscular; procurar saltos.
6. **Escala:** obter espaçamento no plano e entre fatias (metadados do arquivo, `class_info.csv` ou artigo).
7. **Reconstrução:** empilhar, gerar a superfície de um músculo (ex.: reto femoral) por marching cubes e medir comprimento e volume.
8. **Sexo por caso:** procurar em `class_info.csv`, nos nomes, nos relatórios do 1473, no cabeçalho DICOM (`PatientSex`) do 1473 se houver correspondência de casos, e no artigo. Se não houver, registrar e preparar um pedido de informação aos autores (o envio é decisão do usuário).

## 7. Critérios de sucesso (definidos antes da execução)
- **K1 — Ordem e completude:** índices de fatia recuperáveis e contíguos no caso testado (nenhuma lacuna interna ao membro).
- **K2 — Continuidade:** mediana do Dice entre fatias consecutivas `≥ 0,90` para os músculos presentes, sem saltos `< 0,5` no meio do músculo.
- **K3 — Escala:** espaçamento no plano e entre fatias determinado por fonte documentada.
- **K4 — Sexo:** sexo identificado para os 40 casos, ou pelo menos para 20 casos femininos (10 mulheres × 2 membros).
- **K5 — Acesso:** download sem login, ou com cadastro simples, dentro do limite.

Leitura: **H26 sustentada** se K1–K5; **viável sem sexo** se K1, K2, K3 e K5 sem K4 (depende de contato com os autores); **rejeitada** se K1 ou K2 falham.

## 8. Resultados
A preencher.

## 9. Validação
A preencher.

## 10. Limitações
- Teste em um caso; a conclusão para os outros 39 é extrapolação até verificação.
- A fonte é chinesa, adultos de 30–40 anos, sem anormalidades aparentes.
- Os músculos glúteos foram excluídos pelos autores.

## 11. Conclusão
A preencher.

## 12. Próximos passos
A preencher.

## 13. Rastreabilidade
- `pesquisa/resultados/EXP-0026/` (scripts, listagens, métricas de continuidade, figura do músculo reconstruído).

## 14. Revisão
- **Revisor:** Claude Code
- **Revisão humana:** pendente
- **Validação científica:** não se aplica
