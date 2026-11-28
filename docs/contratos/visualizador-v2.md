# Contrato — melhorias do visualizador 3D (referência de UX: app Anatomy 3D Atlas; nada copiado dele)

Regras gerais: nada de copiar textos, ícones ou arte de outro app. Acessibilidade: todo botão com texto ou aria-label em português, alvo ≥ 36 px, foco visível, funciona por teclado. Não quebrar o contrato SPEC §5.4 nem os testes existentes. Nenhum dado de paciente em console/log.

## Tipos novos (packages/motor-anatomico/src/tipos.ts)
```ts
export type NomeVista = 'anterior' | 'posterior' | 'direita' | 'esquerda' | 'superior' | 'inferior';
/** Estado de câmera no espaço do mundo do atlas (metros). Só vale para o mesmo atlas e atlas_versao. */
export type VistaCamera = { atlas: string; atlas_versao: string; posicao: Vetor3; alvo: Vetor3; sistemas: string[] };
export type ComandoCamera =
  | { seq: number; acao: 'enquadrar' }                       // corpo inteiro (enquadramento inicial)
  | { seq: number; acao: 'focar' }                           // centraliza o marcador selecionado
  | { seq: number; acao: 'vista'; vista: NomeVista }         // vistas anatômicas (direita = lado direito DO PACIENTE)
  | { seq: number; acao: 'restaurar'; vista: VistaCamera };  // ignora se atlas/versão diferem
```
`seq` crescente: o motor executa cada comando uma vez (comando com seq já visto é ignorado).

## Props novas do MotorAnatomico (todas opcionais; sem elas o comportamento atual não muda)
- `comandoCamera?: ComandoCamera`
- `onVista?: (v: Omit<VistaCamera,'sistemas'>) => void` — chamada no fim de cada interação de órbita e depois de cada comando executado.
- `ocultas?: string[]` — nomes de malha não desenhados e fora do raycast.
- `isoladas?: string[] | null` — se não nulo, só essas malhas (e os marcadores) são desenhadas.
- `transparencia?: boolean` — com true, malhas dos sistemas visíveis que não sejam `esqueletico`/`articular` e não estejam em `isoladas` ficam com opacidade 0.3 (depthWrite false); a regra da pele (SPEC §7.2) continua valendo.
- `camadasRemovidas?: number` e `onCamadas?: (total: number) => void` — camadas musculares aproximadas (ver abaixo).
- Ao mudar `selecionado` para um marcador posicionado, o motor **centraliza** nele (anima o alvo da órbita até o marcador em ~400 ms; se a câmera estiver mais longe que 0,5× a distância de enquadramento, aproxima para 0,5×). Respeitar `prefers-reduced-motion` (sem animação).

### Vistas
Eixos (conferido nos dois manifestos publicados: `"x esquerda do paciente, y cima, z frente"`, unidade m): `anterior` = câmera em +Z olhando o centro; `posterior` = −Z; `direita` (lado direito do paciente) = câmera em −X; `esquerda` = +X; `superior` = +Y e `inferior` = −Y, com `up` = +Z nessas duas (ou −Z na inferior, de modo que a frente do corpo fique para cima na tela). Teste de sanidade: na vista `direita`, uma malha com `lateralidade: right` (ex.: fêmur direito) fica mais perto da câmera que a esquerda. Distância = enquadramento do corpo inteiro. Teste unitário da função pura que calcula posição/alvo/up por vista.

### Camadas musculares (aproximação, rotulada como tal na UI)
Para cada malha do sistema `muscular` carregado: profundidade = distância do centro da caixa da malha até a superfície da pele (`tegumentar`, usar BVH `closestPointToPoint`; se a pele não estiver carregada, baixar a geometria completa da pele só para isso via o mecanismo `completos`). Dividir as profundidades em até 10 faixas por quantis → `total` = nº de faixas (chamar `onCamadas`). `camadasRemovidas = k` oculta as k faixas mais superficiais. Função pura de binning com teste unitário. Atlas sem sistema muscular → `onCamadas(0)`.

## UI (web/src/components/anatomia/visualizador-atlas.tsx)
Barra de ferramentas sobre o canvas (canto superior direito, sem cobrir a atribuição):
1. **Corpo inteiro** (enquadrar) e **Focar achado** (habilitado com achado selecionado).
2. **Vistas**: Anterior, Posterior, Lateral direita, Lateral esquerda, Superior, Inferior (grupo de botões com rótulo "Vista").
3. **Transparência** (botão alternável, `aria-pressed`).
4. **Camadas musculares**: "− n +" (só quando o sistema muscular está ligado e `total > 0`), com o texto "camadas aproximadas".
5. **Mostrar tudo** (aparece quando há oculta/isolada).

Card da estrutura clicada (no /dev/motor já existe "Ponto selecionado"; no prontuário criar um card "Estrutura selecionada" abaixo do corpo que aparece após um clique):
- nome em português e, abaixo, o nome em inglês (`nome_en`) quando diferente;
- botões **Ocultar estrutura** e **Isolar estrutura**;
- no prontuário: lista **"Achados nesta estrutura"** — marcadores cujo `ancora.estrutura` (ou `ancora.malha` se estrutura nula) é igual ao da estrutura clicada; cada item é um botão que seleciona o achado (`onSelecionarMarcador`). O texto de cada item vem de uma prop nova `rotulos?: Record<string, string>` no tipo `Prontuario` (o painel de achados monta: CID + descrição curta + data). Sem achados: "Nenhum achado nesta estrutura."
- O fluxo atual de registrar achado ao clicar continua igual.

## Leva B — vista salva com o achado (depende do banco)
- Banco (migração `supabase/migrations/0010_vista_achado.sql`): coluna `achados.vista jsonb NULL`; validação por função IMMUTABLE usada em CHECK: objeto com exatamente as chaves `atlas` (texto ≤ 40), `atlas_versao` (texto ≤ 20), `posicao` e `alvo` (arrays de 3 números, |v| ≤ 10), `sistemas` (array de 0–20 textos ≤ 40, só `[a-z_]`); tamanho total ≤ 2.000 bytes. `registrar_achado` ganha o último parâmetro `p_vista jsonb DEFAULT NULL` (DROP da assinatura antiga + CREATE; manter SECURITY DEFINER, `search_path = ''`, a checagem de sessão do 0009, auditoria, REVOKE/GRANT iguais). `listar_achados` e `historico_achado` passam a devolver `vista`. Importação FHIR grava `vista` nula. Nada de vista no export FHIR.
- Web: ao registrar, enviar a última `VistaCamera` (onVista + sistemas visíveis); ao selecionar achado com `vista` do mesmo atlas/versão, enviar `comandoCamera {acao:'restaurar'}` e ligar os sistemas dela; senão, focar o marcador. Texto pequeno no detalhe do achado: "Vista salva no registro".

## Correções pós-revisão (2026-11-27)
1. **`up` na vista (alta):** `VistaCamera` ganha `up?: Vetor3` (opcional, para não invalidar vistas já gravadas). O motor informa `up` em `onVista`; `restaurar` aplica `camera.up` (padrão `[0,1,0]` se ausente). Como o `OrbitControls` fixa o eixo de órbita a partir de `camera.up` na criação, a troca de `up` (vistas superior/inferior e restauração) precisa atualizar esse eixo (recriar/atualizar o quaternion interno, ou recriar o controle) — com teste que orbita depois da vista superior sem inverter a cena.
2. **Banco (alta):** `vista_valida` aceita a chave opcional `up` (array de 3 números, cada |v| ≤ 1). `registrar_achado` recusa (22023) `p_vista` não nula quando `p_ancora` é nula ou quando `vista.atlas`/`vista.atlas_versao` diferem de `ancora.atlas`/`ancora.atlas_versao`.
3. **Rótulo das camadas (média):** texto "Camadas musculares aproximadas" e descrição acessível: "agrupadas pela distância até a pele; não são planos anatômicos".
4. **Memória (média):** o mapa de materiais originais remove as malhas que deixaram de estar em uso (substituição leve → completa e sistemas descartados) a cada atualização, sem esperar a desmontagem.
