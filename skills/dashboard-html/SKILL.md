---
name: dashboard-html
description: Gera painéis (dashboards) HTML interativos de arquivo único para abrir localmente no navegador, sem servidor e sem internet — filtros de período e por dimensão com busca, filtro cruzado ao clicar, KPIs animados com variação contra o período anterior, visão 3D interativa, evolução no tempo com granularidade, rankings, tabela-resumo, tabela de detalhe com busca/ordenação/paginação, exportação CSV, tema claro/escuro e impressão. Use sempre que o usuário pedir um painel, dashboard, visualização interativa, relatório visual em HTML, "algo para abrir no navegador", "para mandar para o gestor filtrar", ou quiser explorar CSV/Excel com filtros sem Power BI.
---

# Dashboard HTML local

`dashboard_html.py` (em `../analise-dados/scripts/`) transforma uma tabela em um painel interativo de arquivo único. Os dados e o Plotly vão embutidos, então o arquivo abre com duplo clique, funciona offline e pode ser enviado por e-mail ou compartilhado em pasta.

## Uso

```bash
S=../analise-dados/scripts
# automático: detecta data, dimensões (2 a 60 valores) e medidas numéricas
python $S/dashboard_html.py vendas.csv --titulo "Vendas 2025" --saida painel.html

# explícito
python $S/dashboard_html.py vendas.csv --titulo "Vendas" --data data \
  --filtros regiao canal produto \
  --medidas valor:soma valor:media quantidade:soma id_pedido:distintos \
  --saida painel.html
```

Agregações: `soma`, `media`, `contagem` (não nulos), `min`, `max`, `distintos`. A medida "Linhas" sempre entra. `--cdn` gera arquivo pequeno que carrega o Plotly da internet. `--texto col` mantém códigos como texto.

## O que o painel entrega

- Faixa de filtros: período (de/até), atalhos (30/90 dias, 12 meses, ano), granularidade (dia, semana ISO, mês, trimestre, ano), seleção múltipla por dimensão com busca, "Limpar filtros" e chips com os filtros ativos.
- KPIs com variação contra o período imediatamente anterior de mesma duração e minigráfico de tendência.
- Evolução no tempo da medida escolhida, com área em degradê.
- Visão 3D: barras por período × item da dimensão escolhida (até 8 itens e 24 períodos), cor pela grandeza em um só tom, giro automático lento, arrastar para girar, roda para aproximar, clique numa barra para filtrar. Ela serve para explorar o padrão; os valores exatos ficam nos rankings, no resumo e no passar do mouse. Sem WebGL (alguns computadores corporativos), o cartão mostra um aviso e o resto do painel segue normal.
- Ranking por dimensão (top 15). Clicar numa barra filtra o painel todo; clicar de novo desfaz. Cada ranking ignora o próprio filtro para continuar mostrando as alternativas.
- Resumo por dimensão escolhida, com total e % das linhas, exportável em CSV.
- Detalhe linha a linha com busca, ordenação por coluna, paginação e exportação CSV do que está filtrado (`;` e vírgula decimal, abre direto no Excel).
- Movimento com função: números contam até o valor novo, barras e linhas fazem transição ao filtrar, cartões entram em sequência e inclinam em 3D sob o mouse. Tudo desliga quando o sistema pede "reduzir movimento".
- Tema claro/escuro, impressão (a visão 3D não sai no papel), números no padrão brasileiro, paleta acessível.

## Por que 3D só nesse cartão

Barra, pizza ou linha em 3D distorcem a leitura: a perspectiva faz itens iguais parecerem diferentes. Por isso os gráficos de leitura continuam planos, e o 3D fica no cartão em que a terceira dimensão carrega dado de verdade (período × item × valor). Se o usuário pedir 3D num ranking ou numa pizza, explique isso e ofereça a visão 3D.

## Volume de dados

Até `--max-linhas` (200 mil por padrão) o painel guarda as linhas. Acima disso, pré-agrega por dia e dimensões com soma, contagem, mínimo e máximo, o que mantém totais e médias exatos; `distintos` e a tabela de detalhe deixam de existir nesse modo, e o script avisa. Para bases muito maiores, agregue antes (DuckDB) e gere o painel sobre o agregado.

## Antes de entregar

1. Abra o HTML no navegador e confira se KPIs e gráficos aparecem.
2. Compare pelo menos um total e um recorte com o pandas (os testes do repositório fazem isso para os dados de exemplo).
3. O arquivo contém **todos os dados** usados. Se houver dados pessoais ou sigilosos, remova colunas desnecessárias antes (`--filtros`/`--medidas` explícitos limitam o que entra) e avise o usuário antes de ele compartilhar.

## Quando ir além do gerador

Para layout sob medida (vários painéis, mapas, gráficos de dispersão, metas), escreva um HTML próprio partindo deste: o modelo de dados embutido (`const D`) e as funções `filtered`, `aggregate` e `groupBy` do script são reaproveitáveis. Siga a skill `dataviz` para cores e acessibilidade. Para um painel publicado e atualizado automaticamente na empresa, use a skill `power-bi-mcp`.
