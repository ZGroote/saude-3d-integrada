# EXP-0004 — Compressão meshopt sem simplificação (BodyParts3D)

> **REGISTRO RETROSPECTIVO** — Reconstruído a partir de `bodyparts3d/comprimir_web.py`, `bodyparts3d/publicar_atlas.py`, `atlas/bp3d-m/4.0-1/manifesto.json` e commits `2b7f443`, `c5157e4`, `3e701c7`. Campos ausentes nas evidências são marcados como `não documentado`.

## 1. Identificação
- **ID:** `EXP-0004`
- **Título:** Compressão `meshopt` sem simplificação (132 → 29 MB, triângulos preservados)
- **Data:** `2026-11-25`
- **Responsável:** não documentado
- **Agentes de IA:** não documentado
- **Branch:** `etapa-1-fundacao`
- **Commit(s):** `2b7f443`, `c5157e4`, `3e701c7`
- **Linha de pesquisa:** `LP02`
- **Situação:** `concluído`

## 2. Problema
Os 15 arquivos GLB originais do BodyParts3D (~132 MB no total) são pesados para carregamento em navegador; é necessário comprimi-los para web sem alterar nomes de nós, metadados extras nem contagem de triângulos.

## 3. Hipótese
A quantização de posições em 16 bits por malha combinada com compressão `EXT_meshopt_compression` (`level=high`) reduz drasticamente o tamanho dos GLBs preservando integralmente nós, `extras` e triângulos.

## 4. Fundamentação teórica
Extensão glTF `EXT_meshopt_compression` implementada via `@gltf-transform/cli`.

## 5. Materiais e ambiente
- **Datasets e versões:** 15 GLBs gerados de BodyParts3D 4.0 (`bodyparts3d/modelos/*.glb`).
- **Licenças:** CC BY 4.0.
- **Hashes:** SHA-256 finais registrados em `atlas/bp3d-m/4.0-1/manifesto.json`.
- **Hardware:** não documentado.
- **Sistema operacional:** Windows (evidência de `npx.cmd` em `comprimir_web.py`).
- **Bibliotecas e versões:** `@gltf-transform/cli@4.5.1` via `npx`; Python (`json`, `struct`, `subprocess`).
- **Seed:** não aplicável.

## 6. Metodologia
- **Procedimentos e algoritmos:** execução de `gltf-transform meshopt <entrada> <saida> --level high --quantize-position 16 --quantization-volume mesh`, seguida de verificação estrutural (`assinatura` comparando nomes de nós, `extras` de nós/malhas/cenas e contagem de triângulos), presença de `EXT_meshopt_compression` em `extensionsRequired` e decodificação via `gltf-transform inspect`.
- **Parâmetros:** `--level high --quantize-position 16 --quantization-volume mesh`.
- **Comandos para reproduzir:** `python bodyparts3d/comprimir_web.py`

## 7. Critérios de sucesso (definidos antes da execução)
Preservação exata da assinatura (`assinatura(comprimido) == original`), presença de `EXT_meshopt_compression` e aprovação no `inspect`.

## 8. Resultados
Redução aproximada de ~132 MB para ~29 MB nos 15 GLBs (`bodyparts3d/modelos_web/*.glb`), preservando todos os 2.234 nós e 6.681.030 triângulos (`atlas/bp3d-m/4.0-1/manifesto.json`). Log completo por arquivo da execução original: `não documentado`.

## 9. Validação
Verificação automatizada em `comprimir_web.py` (`assert assinatura(comprimido) == original`, `EXT_meshopt_compression`, `inspect`) e revalidação na publicação em `bodyparts3d/publicar_atlas.py`.

## 10. Limitações
Exige suporte ao decodificador `MeshoptDecoder` no cliente (`GLTFLoader.setMeshoptDecoder`). Quantização de posição a 16 bits por malha introduz discretização espacial não quantificada em mm neste relatório.

## 11. Conclusão
- **Observado:** todos os 15 GLBs passaram na verificação de integridade estrutural e `inspect` após compressão `meshopt`.
- **Interpretação:** a compressão `meshopt` sem simplificação topológica é adequada para distribuição web do atlas `bp3d-m`.
- **Veredito da hipótese:** `sustentada`

## 12. Próximos passos
Aplicar o mesmo pipeline de compressão ao atlas feminino `hra-f` (`EXP-0005`).

## 13. Rastreabilidade
- **Commits:** `2b7f443`, `c5157e4`, `3e701c7`
- **Scripts:** `bodyparts3d/comprimir_web.py`, `bodyparts3d/publicar_atlas.py`
- **Logs:** não documentado
- **Resultados / artefatos:** `bodyparts3d/modelos_web/*.glb`, `atlas/bp3d-m/4.0-1/`

## 14. Revisão
- **Revisor:** não documentado
- **Revisão humana:** não documentado
- **Validação científica:** não documentado
- **Validação clínica:** não aplicável
