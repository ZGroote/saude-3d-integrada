# CID-10 (DATASUS) — Origem, Versão e Termos de Uso

## Origem e Download

- **URL do arquivo baixado:** `http://www2.datasus.gov.br/cid10/V2008/downloads/CID10CSV.zip`
- **Página oficial de tabelas:** `http://www2.datasus.gov.br/cid10/V2008/download.htm`
- **Portal oficial da CID-10 (DATASUS):** `http://www2.datasus.gov.br/cid10/V2008/cid10.htm`
- **Data do download:** `2026-11-25`
- **Versão oficial informada:** `Versão: 2008` (cabeçalho HTTP `Last-Modified` do arquivo no servidor DATASUS: `Mon, 13 Oct 2014 22:05:10 GMT`, tamanho `306066` bytes)

## Termos de Uso e Copyright

Fonte oficial: `http://www2.datasus.gov.br/cid10/V2008/copyright.htm` (texto citado literalmente):

> "Os arquivos contidos neste CD-ROM são de distribuição gratuita, não podendo ser comercializados sob nenhuma forma. Os arquivos não substituem a CID-10 em formato livro, apenas auxilia paralelamente os codificadores."
>
> "O copyright da CID-10 pertence à Organização Mundial de Saúde - OMS, Genebra, Suiça. Os direitos de tradução da CID-10 para a língua portuguesa são reservados ao Centro Colaborador da OMS para a Classificação de Doenças em Português (Centro Brasileiro de Classificação de Doenças) - CBCD / Faculdade de Saúde Pública da Universidade de São Paulo FSP-USP. Os direitos de publicação e distribuição da CID-10 em português pertencem à Edusp - Editora da Universidade de São Paulo."
>
> "Os arquivos em formato eletrônico da CID-10 (formato Help, HTML, texto, de pesquisa) foram elaborados para CBCD. Estes arquivos podem ser utilizados livremente em instalações de usuários. Desenvolvedores de sistemas também podem utilizá-los, desde que sejam dados os devidos créditos e não seja cobrado pelo seu uso."

## Processamento realizado (`cid10.csv`)

- Arquivos de origem em `supabase/dados/bruto/` (fora do git):
  - `CID-10-CATEGORIAS.CSV` (2.045 categorias de 3 caracteres, codificação `ISO-8859-1`, separador `;`)
  - `CID-10-SUBCATEGORIAS.CSV` (12.451 entradas, sendo 263 categorias sem subcategoria e 12.188 subcategorias de 4 caracteres, codificação `ISO-8859-1`, separador `;`)
- Saída gerada em `supabase/dados/cid10.csv`:
  - Codificação `UTF-8`, separador `,`, cabeçalho `codigo,descricao`
  - Categorias preservadas com 3 caracteres (ex.: `I50`) e subcategorias formatadas com ponto após o 3º caractere (ex.: `I50.0`)
  - Total de `14.233` códigos únicos (`14.234` linhas com cabeçalho), sem códigos duplicados.
