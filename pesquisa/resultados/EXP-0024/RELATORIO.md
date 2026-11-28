# EXP-0024 — execução e resultados

## Síntese

O protocolo em `pesquisa/experimentos/EXP-0024-variabilidade-ossea-feminina.md` foi seguido sem alteração de critérios, seed ou divisões. Das 58 mulheres do pool primário, 31 passaram Q1/Q2; as 31 permaneceram únicas após Q4. A extensão não foi necessária (0 casos faltantes; `extension_needed.json` lista `[]`). Dos 20 controles masculinos sorteados, 12 passaram Q1/Q2. Resultado: **H24 inconclusiva pelo protocolo, pois V0 falha por haver menos de 20 controles masculinos**, embora V1, V2 e V3 tenham resultados mensuráveis.

As 390 máscaras locais (78 casos × 5) ocupam **43.212.790 bytes em disco**. O download foi feito pelo revisor Claude Code em 2026-11-27. O total de bytes transferidos não foi registrado e não é inferido do tamanho em disco. SHA-256 individual de cada arquivo, hashes do conjunto e proveniência estão em `download_manifest.json`. Nenhum CT foi baixado.

## Critérios pré-registrados V0–V3

| Critério | Resultado | Medição |
|---|---|---|
| V0 — amostra | **Falha** | 31 mulheres únicas após QC/Q4, 21 em validação, mas somente 12/20 homens passaram QC; o critério exige 20 homens. |
| V1 — discriminação | **Atendido** | AUC = **0,8373**, acima do limiar 0,80 (21 mulheres de validação; 12 homens QC). |
| V2 — `hra-f` | **Falha** | M1 médio = **6,6352 mm**, acima do p97,5 feminino (**4,7182 mm**). M3 largura/altura = 1,3078 (dentro de 1,2386–1,4634); largura/profundidade = 1,5723 (dentro de 1,4888–1,9430); distância entre cabeças/largura = 1,0769 (fora de 0,5862–0,9175). |
| V3 — `bp3d-m` | **Atendido** | M1 médio = **5,0055 mm**, acima do p97,5 feminino (4,7182 mm). |

Como V0 falha, a leitura do protocolo determina **inconclusiva**, sem concluir a hipótese geral H24. V2 é uma falha observada para `hra-f`, mas o protocolo não permite declarar H24 rejeitada quando V0 falha.

## Métodos, amostra e métricas

- Pools observados conforme os filtros pré-registrados: 200 mulheres elegíveis, 58 no pool primário, 142 remanescentes (67 elegíveis para extensão após exclusões), e 77 homens no controle. Foram selecionados 20 homens com seed 240024.
- QC Q1/Q2 aprovou 31/58 mulheres e 12/20 homens. Q3 usa extensão principal calculada exatamente sobre todos os voxels de cada máscara, com momentos acumulados por fatia para obter eixo principal e extensão, e teste exato da borda superior. Entre as mulheres aprovadas em pelve, 41 tinham fêmur esquerdo e 42 direito aprovados; na validação, 19/21 passaram Q3 bilateralmente e contribuíram ao M3 da distância entre cabeças.
- Q4 considerou 465 pares femininos e 66 masculinos. Para reduzir custo, o ICP foi executado apenas quando a diferença relativa do tamanho de centróide da pelve era <5%: executado em 280 pares femininos (185 pré-filtrados) e 46 masculinos (20 pré-filtrados). O critério registrado permanece distância média simétrica <1,0 mm; nenhuma alteração do limiar. Após Q4 permaneceram 31 mulheres e 12 homens.
- Divisão feminina congelada por `random.Random(240024)`: desenvolvimento (10): `s0139,s0440,s0760,s0764,s0836,s0873,s1128,s1136,s1228,s1358`; validação (21): `s0030,s0089,s0157,s0190,s0350,s0381,s0472,s0578,s0731,s0765,s0804,s0835,s0864,s0928,s1057,s1070,s1120,s1121,s1233,s1355,s1404`. Gabarito M3: `s0139`.
- Parâmetros congelados antes das métricas de validação, SHA-256 do `analisar_local.py`: `9b75b0239bb2c6d71a88485410520fa1591056a13953e2b2620c326d50654bcd`. 30.000 pontos de superfície para M1, ICP por similaridade uniforme; Q4 com 5.000 pontos de ajuste e 10.000 para distância; corte de 12%, máximo 200 iterações, tolerância 1e-7, `workers=1`. M3 usa ajuste rígido ao gabarito congelado.
- Faixas femininas de validação: M1 médio p2,5–p97,5 = **3,4221–4,7182 mm**; M1 p95 = **8,5777–13,7452 mm**; M2 tamanho de centróide = **15.369,7–17.607,0 mm**. Faixas M3 completas em `faixas_femininas.json`.
- Convergência: Q4 convergiu em 272/280 pares femininos e 45/46 masculinos. M1 convergiu em 165/210 comparações femininas, 231/252 masculinas e 39/42 comparações dos atlas; as demais atingiram o limite de 200 iterações. Resultados são aproximações de ICP e devem ser lidos com essa limitação.
- `hra-f`: M1 p95 médio 19,7690 mm; M3 consta acima. `bp3d-m`: M1 p95 médio 14,5789 mm; M3 largura/altura 1,3753, largura/profundidade 1,9056 e distância entre cabeças/largura 0,9037.

## DESVIOS e limitações

- **DESVIO ambiental histórico:** a execução inicial de download falhou no `HEAD` do Zenodo (WinError 10061); naquele momento nenhum dado foi transferido e os resultados estavam bloqueados. Em 2026-11-27, o revisor Claude Code forneceu localmente as máscaras. Depois, a tentativa de análise integrada esgotou threads em `cKDTree.query(workers=-1)`. A análise foi separada do download em `analisar_local.py`, sem conexão de rede e com `workers=1`. Esse bloqueio ambiental foi superado; o veredito final inconclusivo decorre exclusivamente de V0.
- O pré-filtro de 5% em Q4 economiza ICP entre tamanhos muito diferentes; é detalhe de implementação e pode deixar de testar duplicatas de escala divergente. O limiar original <1,0 mm foi mantido.
- 8 comparações Q4 femininas, 1 masculina e 69 comparações M1 não convergiram dentro do limite; ICP pode ter parado em mínimos locais.
- A amostra masculina QC ficou abaixo do tamanho exigido. Não se baixou extensão feminina porque 31 mulheres passaram (mínimo 30). 67 candidatas femininas de extensão permanecem disponíveis na ordem sorteada em `casos.csv`; seriam relevantes apenas se a amostra feminina primária caísse abaixo de 30.
- O rótulo `no_pathology` do conjunto não equivale a avaliação clínica de normalidade. Amostra de um centro/população, sem dados de paridade; máscaras são segmentações assistidas por modelo. Não é validação clínica.

## Arquivos e reprodução

`analisar_local.py` é somente leitura das máscaras locais e produz QC, Q4, M1–M3 e figuras; não contém acesso à rede. `preparar.py` registra seleção e divisão; `baixar_mascaras.py` é mantido para referência da aquisição, mas **não é necessário nem deve ser executado para reproduzir esta análise local**. Artefatos: `casos.csv`, `qc.json`, `q4.json`, `parametros_congelados.json`, `metricas.csv`, `faixas_femininas.json`, `auc.json`, `resultados.json`, `download_manifest.json`, `distribuicao_m1.png` e `pelve_tipica.png`.

Reprodução offline (Python do sistema e dependências já instaladas):

```powershell
C:/Python314/python.exe -I pesquisa/resultados/EXP-0024/analisar_local.py
C:/Python314/python.exe -I pesquisa/resultados/EXP-0024/consolidar_resultados.py
```

As figuras são gráficos gerados com os pontos e as métricas observados: distribuição M1 com atlas e grupos marcados, e sobreposição da pelve típica de validação `s0835` com `hra-f` e `bp3d-m`. Não são placeholders. O protocolo permanece inalterado; revisão humana e validação científica seguem pendentes.

