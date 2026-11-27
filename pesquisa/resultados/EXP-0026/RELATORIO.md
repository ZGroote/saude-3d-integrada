# EXP-0026 — Relatório de Viabilidade da Base KISTI (DataON 1472 / 1473)

**Protocolo:** [EXP-0026-viabilidade-kisti-volumetrica.md](../../experimentos/EXP-0026-viabilidade-kisti-volumetrica.md)
**Data:** `2026-11-27`
**Ambiente:** Python `3.14.4` (stdlib `json`, `re`, `subprocess`, `pathlib`) + `curl.exe`

---

## 1. Resumo executivo e situação dos critérios (K1–K5)

A execução foi **interrompida na etapa de download** porque o portal **KISTI DataON** exige autenticação (`/user/userLogin.do`) para baixar qualquer arquivo — inclusive `class_info.csv` (`4,5 KB`). As páginas públicas de `10.22711/idr/1472` e `10.22711/idr/1473` abriram normalmente e permitiram extrair a lista completa de arquivos, tamanhos, hashes SHA-256 e licença (`CC-BY-4`).

| Critério | Situação | Resultado observado |
|---|---|---|
| **K1 — Ordem e completude** | `não verificado (bloqueado por login)` | Exige download ou listagem de `labels.zip` (`323,56 MB`), bloqueado por login no DataON. |
| **K2 — Continuidade** | `não verificado (bloqueado por login)` | Exige máscaras axiais de `hm_25_001_ct` em `labels.zip`, bloqueado por login. |
| **K3 — Escala** | `parcialmente verificado (artigo)` | Artigo (`10.1038/s41597-026-08630-0`) informa espaçamento axial de `0,7 mm` e planos coronal/sagital com `512` fatias (`~0,4–0,53 mm`). Confirmação por caso em `class_info.csv` / DICOM (`1473`) bloqueada por login. |
| **K4 — Sexo** | `não verificado (bloqueado por login)` | Artigo confirma `10` mulheres e `10` homens (`40` casos de membros), sem mapeamento público por ID nas fontes acessíveis sem login; `class_info.csv`, relatórios `.hwp` e `data.tar` (`1473`) exigem login. |
| **K5 — Acesso** | **Bloqueado — ação humana necessária** | Páginas públicas exibem tamanhos (`1472` = `1,22 GB` / `1.282.706.381 B`, dentro do limite de `5 GB`; `1473` `data.tar` = `25,31 GB`), mas o download real exige conta/login no DataON. |

**Leitura segundo o protocolo:** resultado **inconclusivo / bloqueado por login (`K5`)**, exigindo **ação humana** (login no DataON para baixar `1472` ou ao menos `class_info.csv` e `labels.zip`, e eventualmente os relatórios `.hwp` de `1473`).

---

## 2. Desvios do protocolo

- **DESVIO (Etapas 2–8 da metodologia):** O protocolo previa baixar `class_info.csv`, listar/baixar `labels.zip` (caso `hm_25_001_ct`), empilhar fatias, calcular Dice consecutivo e reconstruir por *marching cubes*. Ao testar o endpoint de download do DataON (`/search/fileDownload_C.do`), o servidor respondeu `{"result":"false","msg":"Please log in to access this page."}` e a função JS `fn_fileDownload` redireciona para `/user/userLogin.do`. Seguindo a regra explícita do protocolo (*"se o download exigir conta, parar e registrar como ação humana"*), **nenhum download autenticado foi tentado** e a execução foi encerrada após extrair todos os metadados públicos e consultar o artigo científico.

---

## 3. Evidências observadas (DataON 1472 e 1473)

### 3.1 Bloqueio de download e licença
- **Páginas consultadas:** `https://dataon.kisti.re.kr/dr/doi/?key=10.22711/idr/1472` e `https://dataon.kisti.re.kr/dr/doi/?key=10.22711/idr/1473`.
- **Licença exibida nas páginas públicas:** `CC-BY-4` (Creative Commons Attribution 4.0) em ambos os registros.
- **Mecanismo de bloqueio observado no HTML/JS e POST:**
  - JS `fn_fileDownload(fileNm, fileUrl, fileId)` executa `location.href="/user/userLogin.do"; return false;`.
  - Chamada POST direta a `https://dataon.kisti.re.kr/search/fileDownload_C.do` para `classinfo.a0e1f7.csv` (`file_id=55046679`) retornou `{"result":"false","msg":"Please log in to access this page."}`.

### 3.2 Arquivos e hashes listados no HTML público

#### DataON `10.22711/idr/1472` (`svc_id: 491509761651c02d9fc8d05cb3996681`)
| Arquivo | Nome interno | Tamanho | Bytes | SHA-256 |
|---|---|---:|---:|---|
| `class_info.csv` | `classinfo.a0e1f7.csv` | `4,5 KB` | `4.613` | `555438bc359e1007c16b5c6df51654c0d07d80a60cb6febd1a20af80003839f0` |
| `labels.zip` | `labels.c2cffa.zip` | `323,56 MB` | `339.273.873` | `f88950f8ccb8f2fa9b8c7d380d5a7953a634e99973f8dcf3b40480335a3215fe` |
| `images.zip` | `images.48408d.zip` | `899,72 MB` | `943.427.895` | `82d67f63c58876f0f668bb57279e1dafd51a2d3fb1d4d1ec37b0375ab70ce509` |

*(Total `1472`: `1.282.706.381` bytes ≈ `1,19 GiB` / `1,28 GB`, bem abaixo do limite de `5 GB`.)*

#### DataON `10.22711/idr/1473` (`svc_id: 317a908c965555983cfd6b904d8b5941`)
| Arquivo | Nome interno | Tamanho | Bytes | SHA-256 |
|---|---|---:|---:|---|
| `[첨부#1] IRB_승인내역.png` | `첨부1IRB승인내역.4f0280.png` | `275,77 KB` | `282.392` | `bc9066e600636f3812bac59509e8a9be9e75a0863d85f77423bac9c808cdd98d` |
| `[첨부#2] 11년_최종보고서.hwp` | `첨부211년최종보고서.1e3be3.hwp` | `1,98 MB` | `2.079.232` | `6bd6ca7aacea41847d819b7bb359c8db3bd9c39bcee2f25a7382f908d292f0f5` |
| `[첨부#3] 12년_최종보고서.hwp` | `첨부312년최종보고서.ab9d3b.hwp` | `1,98 MB` | `2.078.720` | `e10ed95ae3e6d8378b7213f14b0affae10fe99725a94be8310d21cb80a2afcb8` |
| `[첨부#4] data.tar` | `첨부4data.799f3a.tar` | `25,31 GB` | `27.181.592.064` | `dcf1c9fa123f9ec6f4de7c3f201675da540fb8754837ba3a46d5526ff05466b9` |

---

## 4. Limitações

- Nenhum arquivo de `1472` ou `1473` pôde ser inspecionado internamente devido à exigência de login no DataON.
- Os parâmetros de resolução do artigo (`0,7 mm` axial, `~0,4–0,53 mm` nos planos coronal/sagital) vêm de metadados/resumos indexados do artigo `10.1038/s41597-026-08630-0`, ainda sem verificação direta nos cabeçalhos dos arquivos baixados.

---

## 5. Como reproduzir e próximo passo (ação humana)

1. Reproduzir a coleta de metadados públicos:
```bash
python pesquisa/resultados/EXP-0026/inspecionar_dataon.py
```
Saída gerada fora do git em `hra/externo/kisti/metadados_dataon_1472_1473.json`.

2. **Ação humana necessária para destravar o EXP-0026:**
   - Criar/acessar conta no **KISTI DataON** (`https://dataon.kisti.re.kr/user/userLogin.do`).
   - Baixar de `10.22711/idr/1472` ao menos `class_info.csv` (`4,5 KB`) e `labels.zip` (`323,56 MB`) — ou o pacote completo (`1,19 GiB`, `<= 5 GB`) — para `hra/externo/kisti/`.
   - Baixar de `10.22711/idr/1473` os relatórios `.hwp` (`~4 MB`) caso seja necessário verificar correspondência de sexo por caso (além de eventual solicitação aos autores se `class_info.csv` não trouxer o sexo).
