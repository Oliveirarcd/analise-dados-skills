# Modelagem semântica e padrões DAX

## Sumário
1. Modelo estrela
2. Relacionamentos
3. Tabela Calendário
4. Medidas base
5. Inteligência de tempo
6. Participação, ranking e top N
7. Padrões úteis
8. Grupos de cálculo e funções
9. Segurança em nível de linha (RLS)
10. Desempenho

## 1. Modelo estrela

- **Fato**: eventos ou medições (vendas, vistorias, chamados), muitas linhas, chaves estrangeiras + valores numéricos + datas.
- **Dimensão**: quem, o quê, onde (cliente, produto, loja, calendário), uma linha por chave, atributos de texto para filtrar e agrupar.
- Achate cadeias de dimensões (produto → subcategoria → categoria) numa só tabela de produto. Floco de neve só em dimensões enormes.
- Fatos com granularidades diferentes (meta mensal × venda diária) ficam em tabelas separadas, ligadas pelas dimensões comuns no nível que ambas têm (mês, loja).
- Colunas que não serão usadas saem do modelo (Power Query), não só ficam ocultas: reduzem tamanho e tempo de carga.

## 2. Relacionamentos

- Um-para-muitos, dimensão (lado 1) filtrando o fato (lado *), direção única.
- A chave da dimensão precisa ser única e sem nulos; chave órfã no fato gera a linha "(Em branco)". `modelo_estrela.py` mostra órfãos por relacionamento.
- Duas datas no mesmo fato (pedido e entrega): um relacionamento ativo e outro inativo, ativado na medida com `USERELATIONSHIP`.
- Muitos-para-muitos: prefira tabela ponte. Filtro bidirecional só quando necessário e documentado, porque cria ambiguidade e lentidão.

## 3. Tabela Calendário

`modelo_estrela.py` gera esta versão (anos completos, colunas em português):

```dax
Calendario =
VAR Inicio = DATE(YEAR(MIN('vendas'[data])), 1, 1)
VAR Fim = DATE(YEAR(MAX('vendas'[data])), 12, 31)
RETURN
ADDCOLUMNS(
    SELECTCOLUMNS(CALENDAR(Inicio, Fim), "Data", [Date]),
    "Ano", YEAR([Data]),
    "Mes Num", MONTH([Data]),
    "Mes", FORMAT([Data], "mmm", "pt-BR"),
    "Ano Mes", FORMAT([Data], "yyyy-mm"),
    "Trimestre", "T" & QUARTER([Data]),
    "Dia Semana Num", WEEKDAY([Data], 2),
    "Dia Semana", FORMAT([Data], "ddd", "pt-BR"),
    "Fim de Semana", WEEKDAY([Data], 2) > 5
)
```

Depois: marcar como tabela de datas (coluna `Data`), classificar `Mes` por `Mes Num` e `Dia Semana` por `Dia Semana Num`, desativar "Data/hora automática" nas opções. Para feriados, junte uma tabela de feriados por `Data` e crie a coluna `Dia Util`. O servidor MCP tem `calendar_operations` para os grupos de colunas de inteligência de tempo.

## 4. Medidas base

```dax
Total Vendas = SUM('vendas'[valor])
Qtd Vendas = COUNTROWS('vendas')
Ticket Medio = DIVIDE([Total Vendas], [Qtd Vendas])
Clientes Ativos = DISTINCTCOUNT('vendas'[id_cliente])
Margem % = DIVIDE([Total Vendas] - [Custo Total], [Total Vendas])
```

Sempre `DIVIDE` (evita erro de divisão por zero), formato e pasta de exibição. Medidas de outras medidas, não de colunas repetidas.

## 5. Inteligência de tempo

```dax
Vendas AA = CALCULATE([Total Vendas], SAMEPERIODLASTYEAR('Calendario'[Data]))
Vendas Var % AA = DIVIDE([Total Vendas] - [Vendas AA], [Vendas AA])
Vendas Acum Ano = TOTALYTD([Total Vendas], 'Calendario'[Data])
Vendas Acum Ano AA = CALCULATE([Vendas Acum Ano], SAMEPERIODLASTYEAR('Calendario'[Data]))
Vendas Mes Anterior = CALCULATE([Total Vendas], DATEADD('Calendario'[Data], -1, MONTH))
Vendas Media Movel 3M =
    AVERAGEX(DATESINPERIOD('Calendario'[Data], MAX('Calendario'[Data]), -3, MONTH), [Total Vendas])
Vendas 12M = CALCULATE([Total Vendas], DATESINPERIOD('Calendario'[Data], MAX('Calendario'[Data]), -12, MONTH))
```

Atenção: com o ano corrente incompleto, comparar o acumulado inteiro do ano anterior distorce. Limite o período anterior até a última data com dados:

```dax
Vendas AA ate Hoje =
VAR UltimaData = CALCULATE(MAX('vendas'[data]), ALL('vendas'))
RETURN CALCULATE([Vendas AA], KEEPFILTERS('Calendario'[Data] <= EDATE(UltimaData, -12)))
```

## 6. Participação, ranking e top N

```dax
% do Total = DIVIDE([Total Vendas], CALCULATE([Total Vendas], ALLSELECTED('lojas')))
% da Regiao = DIVIDE([Total Vendas], CALCULATE([Total Vendas], ALLEXCEPT('lojas', 'lojas'[regiao])))
Ranking Loja = IF(HASONEVALUE('lojas'[nome_loja]), RANKX(ALLSELECTED('lojas'[nome_loja]), [Total Vendas], , DESC, DENSE))
Vendas Top 5 Lojas =
    CALCULATE([Total Vendas], KEEPFILTERS(TOPN(5, ALL('lojas'[nome_loja]), [Total Vendas])))
Curva ABC % Acumulado =
VAR Atual = [Total Vendas]
RETURN DIVIDE(
    SUMX(FILTER(ALLSELECTED('produtos'[cod_produto]), [Total Vendas] >= Atual), [Total Vendas]),
    CALCULATE([Total Vendas], ALLSELECTED('produtos')))
```

## 7. Padrões úteis

- **Valor no último dia com dados** (estoques, saldos): `CALCULATE(SUM(saldo[valor]), LASTNONBLANK('Calendario'[Data], CALCULATE(COUNTROWS(saldo))))`.
- **Novos clientes**: clientes cuja primeira compra está no período: `COUNTROWS(FILTER(VALUES(vendas[id_cliente]), CALCULATE(MIN(vendas[data]), ALL('Calendario')) >= MIN('Calendario'[Data])))`.
- **Meta × realizado** em granularidade mensal: relacione a meta ao Calendário pelo primeiro dia do mês ou use `TREATAS`.
- **Título dinâmico**: `"Vendas — " & SELECTEDVALUE('lojas'[regiao], "Todas as regiões")`.
- **Cor condicional**: medida que devolve código de cor (`IF([Var % AA] < 0, "#e34948", "#008300")`) usada em formatação condicional.
- **Parâmetro de campo** para o usuário trocar a métrica do gráfico (Modelagem → Novo parâmetro → Campos).

## 8. Grupos de cálculo e funções

Quando as mesmas variações de tempo se repetem para muitas medidas (AA, Acum, Var %), use um grupo de cálculo com `SELECTEDMEASURE()` em vez de dezenas de medidas:

```dax
-- item "AA"
CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR('Calendario'[Data]))
-- item "Var % AA"
VAR A = SELECTEDMEASURE()
VAR B = CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR('Calendario'[Data]))
RETURN DIVIDE(A - B, B)
```

Defina `formatStringDefinition` para percentuais. O MCP cria isso com `calculation_group_operations`. Funções DAX definidas pelo usuário (`function_operations`) servem para lógica reutilizada entre medidas; confira se a versão do Desktop do usuário suporta.

## 9. Segurança em nível de linha (RLS)

```dax
-- papel "Regional", filtro na tabela lojas
'lojas'[email_gerente] = USERPRINCIPALNAME()
```

Prefira uma tabela de acesso (usuário × região) relacionada à dimensão. Teste com "Exibir como" no Desktop e com `security_role_operations`. RLS não protege quem tem permissão de edição no workspace.

## 10. Desempenho

- Importação com colunas enxutas e tipos corretos; datas sem hora quando a hora não é usada; texto de alta cardinalidade (IDs, descrições longas) fora quando possível.
- Evite `FILTER` sobre a tabela inteira dentro de `CALCULATE` quando um filtro de coluna resolve (`CALCULATE([x], 'lojas'[regiao] = "Sul")`).
- Use variáveis (`VAR`) para não recalcular a mesma expressão.
- `SUMX` sobre fatos grandes com lógica linha a linha é caro; prefira pré-calcular no Power Query.
- Meça com `RunDAXQueryWithMetrics` / `AnalyzeDAXQuery` do MCP ou o Performance Analyzer do Desktop. Visuais com mais de 1 segundo merecem revisão.
