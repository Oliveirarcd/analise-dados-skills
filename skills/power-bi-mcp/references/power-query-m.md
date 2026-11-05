# Power Query (M)

## Princípios

- Limpeza e padronização ficam no Power Query (ou na origem); cálculo de negócio que depende de filtro fica em DAX.
- Mantenha a **dobra de consulta** (query folding) em bancos: filtros, remoção de colunas e agregações no início, antes de passos que quebram a dobra (colunas personalizadas complexas, `Table.Buffer`, mesclas com fontes diferentes). Clique com o botão direito no passo → "Exibir consulta nativa" para conferir.
- Parametrize caminhos e servidores (`named_expression_operations` no MCP) para trocar de ambiente sem editar cada consulta.

## CSV brasileiro

```m
let
    Fonte = Csv.Document(File.Contents(PastaDados & "vendas.csv"),
        [Delimiter = ";", Encoding = 1252, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {
        {"data", type date}, {"valor", type number}, {"quantidade", Int64.Type},
        {"cod_loja", type text}, {"cod_produto", type text}}, "pt-BR")
in
    Tipos
```

O terceiro argumento `"pt-BR"` faz `1.234,56` e `31/12/2025` serem lidos corretamente. Use `Encoding = 65001` para UTF-8. Códigos (loja, CNPJ, CEP) sempre como `type text`.

## Pasta com vários arquivos

```m
let
    Arquivos = Folder.Files(PastaDados & "mensal\"),
    SoCsv = Table.SelectRows(Arquivos, each Text.Lower([Extension]) = ".csv" and not Text.StartsWith([Name], "~")),
    Conteudo = Table.AddColumn(SoCsv, "Dados", each Table.PromoteHeaders(
        Csv.Document([Content], [Delimiter = ";", Encoding = 1252]), [PromoteAllScalars = true])),
    Expandido = Table.ExpandTableColumn(Table.SelectColumns(Conteudo, {"Name", "Dados"}), "Dados",
        Table.ColumnNames(Conteudo{0}[Dados]))
in
    Expandido
```

Guarde o nome do arquivo (`Name`) para rastrear a origem de cada linha.

## Limpeza frequente

```m
// aparar e padronizar texto
Table.TransformColumns(T, {{"cidade", each Text.Proper(Text.Trim(_)), type text}})
// zeros à esquerda
Table.TransformColumns(T, {{"cod_loja", each Text.PadStart(Text.From(_), 4, "0"), type text}})
// remover linhas de total que vêm da planilha
Table.SelectRows(T, each not Text.StartsWith(Text.Lower([descricao] ?? ""), "total"))
// despivotar meses em colunas
Table.UnpivotOtherColumns(T, {"loja", "indicador"}, "mes", "valor")
// deduplicar mantendo o registro mais recente
Table.Distinct(Table.Sort(T, {{"atualizado_em", Order.Descending}}), {"id"})
```

`Table.Distinct` depois de `Table.Sort` mantém o primeiro, mas a ordem pode não ser preservada sem `Table.Buffer`; envolva o resultado ordenado em `Table.Buffer` antes de deduplicar em fontes que não dobram.

## Tratamento de erros

```m
Table.ReplaceErrorValues(T, {{"valor", null}})
// ou isolar os erros para auditoria
Table.SelectRowsWithErrors(T, {"valor"})
```

Crie uma consulta "Erros de carga" com as linhas descartadas e mostre a contagem em uma página de qualidade do relatório.

## Mesclar com cuidado

`Table.NestedJoin` equivale ao merge do pandas: confira se a tabela da direita tem chave única antes (`Table.RowCount(Table.Distinct(Dim, {"chave"})) = Table.RowCount(Dim)`), senão as linhas do fato se multiplicam.
