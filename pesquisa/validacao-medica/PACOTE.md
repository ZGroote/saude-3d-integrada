# Pacote para validação médica do piloto

**Estado geral:** pendente de avaliação humana. Este pacote organiza decisões e textos já presentes no repositório; não é parecer clínico, validação do produto ou autorização para piloto. Nenhum dado de paciente foi usado.

**Identificação do revisor**

- Nome:
- CRM/UF:
- Data da revisão (AAAA-MM-DD):
- Itens revisados / ressalvas:
- Assinatura ou referência do parecer:

## Como revisar

Preencha os CSVs sem apagar o conteúdo original. Em cada linha, registre `correto? / sugestão`, estado, nome/CRM e data. Use “não se aplica” quando necessário e justifique. A origem por arquivo e linha está na coluna `origem`; quando o item deriva de índice gerado, a origem aponta para a linha correspondente no catálogo fonte e informa a versão do índice usada.

## A. Nomes anatômicos em português exibidos ao usuário

- [nomes_bp3d_m.csv](nomes_bp3d_m.csv): traduções não vazias do índice que o app carrega para o atlas masculino `bp3d-m` (2.234 entradas no índice; entram na planilha somente as que possuem nome em português).
- [nomes_hra_f.csv](nomes_hra_f.csv): traduções não vazias do índice que o app carrega para o atlas feminino `hra-f` (956 entradas no índice; entram na planilha somente as que possuem nome em português).
- No visualizador, o nome clicado é `nome_pt || nome_en`; o nome português pendente é exibido com aviso de tradução não revisada. As planilhas incluem somente nomes portugueses que podem aparecer no cartão/achado, não o catálogo inglês de fallback.

## B. CID-10 com sigilo automático

Veja [cid10_sigilo.csv](cid10_sigilo.csv). A lista reproduz os prefixos carregados nas migrações. O critério declarado é correspondência por prefixo: HIV (B20–B24 e Z21), violência (T74, Y05, Y07), saúde mental (F*) e aborto (O04–O07); a migração de gestação acrescenta O98.7 para HIV na gestação. A própria SPEC chama a lista de provisória e pendente de revisão médica. A planilha preserva motivo e origem, sem inferir uma lista adicional de códigos.

## C. Mapeamento `bodySite` e malha representante

Veja [bodysite_malhas.csv](bodysite_malhas.csv). São os 12 códigos do CSV de referência. A coluna de malha foi obtida do índice do atlas carregado, selecionando para cada identificador a malha principal pelo critério de software do motor (§5.4: mais triângulos; desempate pelo menor nome de malha). Isso registra a escolha efetiva do produto, não afirma que a malha seja clinicamente representativa do conceito SNOMED. Célula vazia/“sem correspondência” indica ausência de uma estrutura correspondente nesse atlas conforme a coluna ontológica usada; não foi preenchida por aproximação.

## D. Regras clínicas e de apresentação a revisar

Veja [regras_clinicas.csv](regras_clinicas.csv). Inclui idade mínima do corpo 3D, recorte gestacional pediátrico, DPP e registro de condição após encerramento. Há uma divergência importante para avaliação: o contrato exige validação da condição gestacional, mas `registrar_condicao_gestacao` não verifica `desfecho='em_curso'`; `encerrar_gestacao` verifica o estado antes de encerrar. O item foi descrito como implementação observada e questão de revisão, não como controle já assegurado.

## E. Perguntas abertas

Veja [perguntas_abertas.csv](perguntas_abertas.csv): alerta ao pediatra sobre possível exposição vertical sigilosa (incluindo HIV/sífilis) e sigilo de eventos importados. A SPEC registra que condições restritas não entram no recorte pediátrico de outra unidade e deixa o alerta sujeito a parecer médico e jurídico. Eventos FHIR são restritos à unidade que os importou e ainda não têm classificação de sigilo própria.

## Limites desta compilação

- As origens são arquivos versionados no repositório, não referências a diretrizes clínicas externas.
- “Naegele” é a formulação solicitada para revisão; a implementação encontrada calcula DUM + 280 dias. O pacote não assume que a fórmula esteja validada para todos os casos.
- A idade de 12 anos é o limite usado pelo código e pelo critério de Etapa 6; há comentário no código reconhecendo que §5.1 não fixa a idade.
- Não foi possível identificar, nos arquivos consultados, fonte clínica para afirmar que condições gestacionais só possam ser registradas enquanto a gestação está em curso. O estado atual da função é reportado na planilha para decisão.
- Nenhum dado pessoal ou de paciente foi copiado para este pacote.
