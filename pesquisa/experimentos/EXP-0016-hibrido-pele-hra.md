# EXP-0016 — Atlas feminino híbrido: pele e órgãos do HRA + esqueleto TC NLM/Denver

> **PROTOCOLO PRÉ-REGISTRADO:** registrado **antes** da execução (2026-11-26). Escolha do usuário na revisão F5 do `EXP-0015`: opção "híbrido".

## 1. Identificação
- **ID:** `EXP-0016`
- **Título:** Atlas feminino híbrido (pele/órgãos HRA + esqueleto `vhf-f`)
- **Responsável:** Coordenador do projeto (decisão do usuário; protocolo pelo Claude coordenador)
- **Agentes de IA:** Claude (protocolo), Codex (execução)
- **Branch:** `etapa-1-fundacao`
- **Linha de pesquisa:** `LP01`
- **Situação:** `planejado`

## 2. Problema
Na comparação F5 (`web/testes/capturas/f5/comparacao.html`), o corpo `vhf-f` (`EXP-0015`) tem esqueleto completo da doadora, mas pele com rosto real, braços cortados pelo campo da TC e degraus. O `hra-f` tem pele idealizada e completa e órgãos ricos (956 malhas), mas esqueleto remodelado que falhou no `EXP-0014`. A proposta é juntar a pele e os órgãos do HRA ao esqueleto da TC/Denver.

## 3. Hipótese
O esqueleto `vhf-f` (ossos e articular, TotalSegmentator + Denver), levado ao referencial do HRA pela similaridade global já calculada (Etapa B do `EXP-0014`), fica contido na pele do HRA e não invade os órgãos do HRA, nos limites do `EXP-0014`.

**Risco conhecido antes de rodar:** o `EXP-0014` mediu a mesma interface (TC/Denver → HRA) e reprovou (F1 `32/164`, F3 `28/164`, fêmur `10–20 mm`, `L1–L5` `5,6–19,2 mm`). O que muda aqui é a regra de fonte: o esqueleto inteiro passa a vir de uma única doadora/exame, então as articulações internas não dependem do HRA.

## 4. Materiais
- `atlas/hra-f/1.10-1/` (HRA v1.10, CC BY 4.0): **pele** (sistema tegumentar, inclusive mama) e **todos os sistemas não esqueléticos**.
- `atlas/vhf-f/0.1-0/` (rascunho `EXP-0015`): somente sistemas **esqueletico** e **articular**.
- Transformação: `hra/alinhar/transformacoes.json`, `stage_b.similarity` (TC RAS mm → HRA RAS mm), e `stage_b.regional_registration` para a variante B.
- Conversão app ↔ RAS: `x_RAS = -x·1000`, `y_RAS = z·1000`, `z_RAS = y·1000`.

## 5. Metodologia
### Regra de fonte única
- Esquelético e articular: só `vhf-f`. Os 117 + 16 itens esquelético/articular do HRA saem.
- Todo o resto (pele, órgãos, vasos, nervos, músculos, gestacional, sensorial): só HRA, sem mudança.

### Variantes (só estas duas, nesta ordem)
- **A — global:** uma similaridade (`stage_b.similarity`) para todo o esqueleto.
- **B — regional:** só se A reprovar em F1 ou F3. As três matrizes de `stage_b.regional_registration.matrices_4x4` (`head_neck`, `thorax`, `abdomen_pelvis`), aplicadas por osso conforme a região. Os membros superiores seguem o tórax e os inferiores seguem abdome/pelve, porque não há matriz própria para eles; nenhuma matriz nova é ajustada. Continuidade nas emendas medida por F2.

Nenhuma deformação não rígida.

### Medidas
- **F1 — contenção:** % de vértices do esqueleto importado dentro da pele HRA. A pele HRA é aberta (`EXP-0014`), então é fechada por voxelização em grade de 3 mm + preenchimento de buracos (`scipy.ndimage.binary_fill_holes`) por fatia axial. Reportar o volume preenchido como checagem de sanidade.
- **F2 — articulações:** quadril, joelhos, costelas–vértebras e crânio–C1 herdados do `EXP-0015` na variante A (a similaridade global não muda distâncias relativas além da escala, que será reportada). Na variante B, medir de novo as emendas entre regiões.
- **F3 — sobreposição entre fontes:** pares osso `vhf-f` × órgão/estrutura HRA; invasão = fração ≥ 2% do volume próprio e profundidade > 3 mm (regra F3 v2, mesmas exclusões anatômicas do `EXP-0015`). Os pares de mesma fonte já reprovados no `EXP-0015` (133 Denver–Denver, 90 TotalSegmentator–TotalSegmentator) são herdados e não medidos de novo.
- **F4 — lateralidade:** como no `EXP-0015`.
- **F5 — revisão humana:** capturas nas 4 vistas × 3 modos, ao lado do `hra-f` atual, no formato de `web/testes/capturas/f5/`.

## 6. Critérios de sucesso (os do `EXP-0014`, sem alteração)
- F1 `≥ 99%`; F2 cada articulação `≤ 5 mm`; F3 `< 2%` (regra acima); F4 todas corretas; F5 aprovação humana.
- **Herança conhecida:** F2 costelas–vértebras e o F3 de mesma fonte já reprovaram no `EXP-0015`. Logo, **a aceitação formal completa é improvável antes da execução**. O que este experimento decide é se a interface nova (esqueleto × pele/órgãos HRA) passa. O registro do resultado deve separar "interface nova" de "herdado".

## 7. Governança
- Dentro do teto de 5 dias úteis aberto pelo `EXP-0015` (2026-11-26 a 2026-12-02).
- Parada: se A e B reprovarem F1 ou F3 de interface, o híbrido é **não aceito**; preserva-se o registro e o usuário escolhe entre o corpo novo (`vhf-f` com rosto suavizado) ou manter o HRA.
- Saída: pacote `atlas/hib-f/0.1-0`, status `rascunho, nao publicado, nao aceito` até F5, no mesmo formato do `vhf-f/0.1-0` (SPEC §5.3, um GLB por sistema, `glb_leve` da pele reaproveitado do HRA). Sem publicação, sem uso em produção.
- Sem validação clínica em nenhum caso.

## 8. Resultados

### Execução interrompida — instrumentação não validada (2026-11-26)

**Veredito EXP-0016: inconclusivo; sem aceitação.** Não foi possível completar a verificação geométrica com confiabilidade; a regra de parada A/B não pode ser avaliada. Nenhum pacote `atlas/hib-f/0.1-0` ou captura F5 foi produzido; revisão humana pendente.

#### Interface nova (tentativas diagnósticas, INVALIDADAS)

- Cópias diagnósticas A e B: 932 entradas, 16 sistemas e cerca de 90,1 MB cada. Não são saídas EXP-0016: não foi possível validar que a quantização glTF do VHF permaneceu no referencial exigido. Cópias removidas após o diagnóstico.
- F1 preliminar A indicou 0,71345% de vértices contidos; volume fechado voxelizado 2.110,428 cm³ e volume acrescentado pelo `binary_fill_holes` 8,424 cm³. **INVALIDADO:** o decodificador disponível remove meshopt, mas não reverte `KHR_mesh_quantization`; coordenadas não comprovadamente compatíveis com RAS mm. F1 correto não medido.
- F3 preliminar A relatou 89 invasões, mas incluiu a própria pele como par e usou geometria com quantização não validada. **INVALIDADO; F3 de interface não medido.**
- F4 preliminar A: 413/709 pelo sinal da média x (HRA 333/629; VHF 80/80). **INVALIDADO** pela incerteza de reconstrução dos GLBs; F4 correto não medido.
- Variante B foi montada apenas como cópia diagnóstica. F1/F3/F4 e emendas F2 não foram calculados validamente; sem veredito de aprovação/reprovação de B.

#### Herdado do EXP-0015 (sem remedição, conforme protocolo)

- F2 quadril: folga cartilagem Denver 0,014 mm (E) e 0,037 mm (D), passou; joelho esquerdo e costovertebral reprovaram; joelho direito e crânio–C1 passaram, conforme seção 8.3 do EXP-0015.
- F3 v2 mesma fonte: 133 invasões Denver–Denver e 90 TotalSegmentator–TotalSegmentator (EXP-0015, seção 8.4); herdado, sem nova medição.

#### Limitação e rastreabilidade

O pacote VHF usa quantização glTF (`KHR_mesh_quantization`) e meshopt. O decoder `hra/alinhar/decoder_glb.mjs` decodifica meshopt, mas a transformação inversa para recuperar as coordenadas de entrada não está disponível no fluxo usado. O empacotador original usa `npx --no-install @gltf-transform/cli@4.5.1`; a dependência não está instalada e não foi instalada, conforme instrução. Sem geometria fonte/decodificador compatível, não se pode garantir a aplicação das matrizes `stage_b` nem medir F1/F3/F4/F2 de emendas. Critérios e variantes permanecem intactos; não se afirma resultado clínico.

Scripts de cálculo: `hra/hibrido/construir.py`, `hra/hibrido/avaliar.py`. Relatórios preliminares não preservados como resultados, por serem geometricamente inválidos. Nenhum pacote final, HTML comparativo ou captura F5 foi criado.

### Rodada 2 (2026-11-26) - sanidades, metricas e pacote provisorio

**Variante avaliada:** A (apenas para checagens prévias). Critérios, variantes e regra de parada mantidos. O esqueleto foi lido exclusivamente das STLs originais de `atlas/hra-f/2.0-1/`, filtradas pelos 109 itens `esqueletico`/`articular` do índice `vhf-f/0.1-0` e casadas pelo nome de malha/arquivo. A leitura HRA foi encaminhada por import de `hra/alinhar/alinhar.py` (`load_hra_catalog_mesh` → `extract_gltf_meshes`) e conversão app→RAS documentada; nenhum GLB VHF quantizado foi usado nesta rodada.

#### Sanidade antes das métricas

- **Altura pele body VHF:** 1.730,43 mm em `z_RAS` antes de stage B e 1.769,41 mm após `stage_b.similarity`; passa a faixa aproximada de 1.500–1.800 mm.
- **Altura pele HRA (`VH_F_skin`):** 1.657,78 mm em `z_RAS`; passa a faixa aproximada.
- **Distância simétrica body transformado ↔ pele HRA:** média amostrada 35,96 mm (50.000 vértices por direção, seed 16001; body→HRA 28,43 mm; HRA→body 43,49 mm). Diagnóstico somente, sem limite de aceitação neste protocolo.
- **Centro do crânio VHF após A:** `(3,86; −63,76; 747,49) mm RAS`. **Checagem “dentro do crânio HRA” não mensurável:** o índice e os GLBs de `hra-f/1.10-1` não contêm estrutura craniana/crânio; busca no nome de malha e `nome_en` não achou candidato. Não substituo por cérebro, pois cavidade cerebral não é crânio.

**Decisao preliminar da primeira passagem (superada pela correcao abaixo):** a checagem originalmente solicitada nao podia ser confirmada porque a base HRA nao contem cranio. Naquela passagem, a rodada foi suspensa antes das metricas; a substituicao autorizada pelo coordenador permitiu retomar esta mesma Rodada 2 sem alterar criterios, variantes ou regra de parada.

Fontes e métodos: STL `body__skin.stl` e `total__skull.stl` em `atlas/hra-f/2.0-1/`; lista de estruturas em `web/public/atlas/vhf-f/0.1-0/indice.json`; pele HRA via `web/public/atlas/hra-f/1.10-1/tegumentar.glb`, nó `VH_F_skin`; matriz `stage_b.similarity` em `hra/alinhar/transformacoes.json`. A pele HRA foi amostrada com o leitor indicado; distância superficial diagnóstica usa nearest vertex e é aproximada, não distância exata entre superfícies. Sem instalação de pacotes, sem commit e sem validação clínica.

#### Correcao da checagem de referencial

Correcao do coordenador: a checagem original do cranio era inaplicavel por erro da instrucao do coordenador e foi substituida pela checagem referencial abaixo; criterios, variantes e regra de parada permanecem intactos.

- Centroide das malhas `Allen*` do HRA: `(-0.292; -78.101; 753.035) mm RAS`.
- Centroide do cranio VHF apos A: `(3.865; -64.930; 748.649) mm RAS`; distancia ao centroide Allen `14.491 mm` (limite diagnostico `<=100 mm`: passou).
- O centroide craniano esta dentro da pele HRA fechada por voxelizacao de 3 mm e preenchimento por fatia axial: **sim**. As duas condicoes substitutas passam; prossegui as metricas.
- Diagnosticos de referencial, sem valor de aceitacao: altura z da pele HRA `1.657,78 mm`; pele body VHF `1.730,43 mm` antes e `1.769,41 mm` apos A; distancia simetrica media amostrada pele-pele `35,96 mm` (`28,43 mm` body->HRA; `43,49 mm` HRA->body; 50.000 pontos/direcao, seed 16001).

#### Interface nova: F1, F3 e F4

F1 mede vertices das 109 malhas VHF esqueleticas/articulares em RAS mm dentro da pele `VH_F_skin` HRA, fechada em voxel de 3 mm com `binary_fill_holes` por fatia axial. Mascara: 258.924 voxels de casca e 3.087.233 apos fechamento; volume fechado `83.355,291 cm3`, dos quais `76.364,343 cm3` foram acrescentados pelo preenchimento.

| Variante | Dentro | Fora | Estruturas com escape | F1 (>=99%) |
|---|---:|---:|---:|---|
| A | 778.783 / 1.016.501 (76,6141%) | 237.718 | 54 | **REPROVOU** |
| B | 803.058 / 1.016.501 (79,0022%) | 213.443 | 49 | **REPROVOU** |

Maiores escapes por contagem: A - tibia Denver direita 26.312; cartilagem do talus esquerda 20.001; falanges Denver direita 18.093 e esquerda 17.462; cranio TotalSegmentator 17.035. B - tibia Denver direita 27.175; cartilagem do talus esquerda 20.001; falanges Denver direita 18.093; tibia esquerda 13.740; fibula direita 9.179.

F3 avaliou apenas pares com caixas intersectantes entre as 109 malhas VHF e estruturas HRA fora de tegumentar; pele e exclusiva de F1. Aplicaram-se as exclusoes F3 v2 de `hra/vhf/avaliar_base.py`; relacoes equivalentes foram reconhecidas entre `total__skull` e subdivisoes `Allen*` (cerebro-cranio/cavidade) e entre sacro e ligamento uterossacral HRA (insercao). Grade 2 mm, ate 2.000 centros internos deterministas por malha e profundidade por EDT; malhas abertas nao tem interior volumetrico e foram omitidas.

| Variante | Pares fechados candidatos | Pares abertos omitidos | Pares com sobreposicao amostrada | Pares >=2% | Invasoes >=2% e >3 mm | F3 |
|---|---:|---:|---:|---:|---:|---|
| A | 142 | 1.921 | 15 | 9 | 6 | **REPROVOU** |
| B | 131 | 1.939 | 10 | 6 | 6 | **REPROVOU** |

Todos os pares que invadiram, com fracao maxima, profundidade e volume medio estimado pela amostragem:

| Variante | Par VHF x HRA | Fracao | Profundidade (mm) | Volume medio (cm3) |
|---|---|---:|---:|---:|
| A | costal cartilages x thymus lobe L | 19,30% | 8,72 | 6,936 |
| A | sternum x thymus lobe L | 20,30% | 10,00 | 7,736 |
| A | sternum x thymus lobe R | 49,80% | 10,00 | 11,823 |
| A | vertebrae C2 x Allen pyramidal part of medulla oblongata L | 16,42% | 4,47 | 0,050 |
| A | vertebrae C2 x Allen tegmentum of medulla oblongata L | 3,37% | 4,00 | 0,087 |
| A | pelvis bone right (Denver) x cardinal ligament of uterus right | 5,87% | 6,00 | 0,251 |
| B | costal cartilages x thymus lobe L | 16,85% | 10,00 | 6,218 |
| B | costal cartilages x thymus lobe R | 5,00% | 6,00 | 1,133 |
| B | rib left 2 x thymus lobe L | 3,40% | 4,90 | 0,476 |
| B | sternum x thymus lobe L | 16,35% | 9,80 | 5,955 |
| B | sternum x thymus lobe R | 51,05% | 10,00 | 12,654 |
| B | pelvis bone right (Denver) x cardinal ligament of uterus right | 27,39% | 10,95 | 1,233 |

F4 considera as estruturas importadas VHF (malhas HRA permanecem inalteradas): `80/80` com lateralidade coerente em A e `80/80` em B; **PASSOU** nas duas variantes.

#### F2 e medidas herdadas

- Variante B, emendas regionais, distancia minima superficie-superficie aproximada por vizinhos mais proximos dos vertices (C7 4.170/T1 4.550; T12 6.446/L1 10.983 vertices): C7/T1 `0,136 mm`; T12/L1 `0,717 mm`. Ambas `<=5 mm`, **PASSARAM**.
- Herdado do EXP-0015, sem remedicao: folgas do quadril por cartilagens Denver `0,014 mm` esquerda e `0,037 mm` direita (passaram); joelho esquerdo e costovertebral reprovaram; joelho direito e cranio-C1 passaram. F3 de mesma fonte herdado: 133 invasoes Denver-Denver e 90 TotalSegmentator-TotalSegmentator.

#### Saida e veredito da Rodada 2

- Construido `atlas/hib-f/0.1-0` com variante B, 932 estruturas/16 sistemas, `65.772.584 bytes` (`65,773 MB` decimal). Manifesto marca `rascunho, nao publicado, nao aceito`; 18 hashes SHA-256 verificados. Os 12 GLBs nao esqueletais existentes do HRA v1.10 e `tegumentar_leve.glb` sao copias byte a byte; os GLBs esqueletico/articular foram gerados das STLs RAS com `@gltf-transform/cli@4.5.1`, sem simplificacao, nomes e contagens de triangulos conferidos.
- F5: 24 capturas (4 vistas x 3 modos x 2 atlas), `comparacao.html` e `diferencas.json` em `web/testes/capturas/f5-hibrido/`. Capturas geradas em Next de desenvolvimento na porta 3137; console limpo. **Aprovacao humana F5 pendente.**
- **Veredito pela regra de parada:** A e B reprovaram F1 e F3 de interface. Hibrido **nao aceito**, mantem status de rascunho; encerra a rodada para decisao do coordenador. F4 passou e as emendas B passaram, mas isso nao supera F1/F3 nem as falhas herdadas. Sem validacao clinica e sem commit.

## 9. Rastreabilidade
- Protocolo: este arquivo (commit de registro).
- Scripts: `hra/hibrido/construir.py`, `hra/hibrido/avaliar.py`.

## Decisão de encerramento (2026-11-26)
Decisão do usuário após a revisão F5 e o resultado do `EXP-0016`: **manter o `hra-f/1.10-1` como atlas feminino do MVP e congelar a linha de pesquisa do corpo feminino**, dentro do teto de 5 dias úteis. Os pacotes `atlas/vhf-f/0.1-0` e `atlas/hib-f/0.1-0` ficam como rascunhos locais, não publicados e não aceitos (o `copiar-atlas` ignora rascunhos). As lacunas conhecidas do HRA (esqueleto remodelado, `EXP-0014`) continuam registradas. Sem validação clínica.
