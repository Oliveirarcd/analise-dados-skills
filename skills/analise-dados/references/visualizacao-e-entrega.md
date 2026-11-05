# Visualização, narrativa e entrega

## Escolha do gráfico pela tarefa

| O leitor precisa... | Use | Evite |
|---|---|---|
| ver um número-chave | cartão de KPI com comparação | gráfico de um ponto só |
| acompanhar evolução | linha (barras se poucos períodos) | pizza, área empilhada com muitas séries |
| comparar categorias | barras horizontais ordenadas | pizza com mais de 3 fatias |
| ver composição | barras empilhadas 100% ou treemap | rosca 3D |
| ver distribuição | histograma, boxplot, violino | média sozinha |
| ver relação entre duas numéricas | dispersão (com linha de tendência) | dois eixos Y |
| ver dois níveis de categoria | mapa de calor, pequenos múltiplos | barras agrupadas com 10 cores |
| localizar no mapa | coroplético com taxa (não total) | mapa de bolhas sem legenda de escala |

## Regras de leitura

- Título diz a conclusão ("Vendas do Site caíram 12% no 2º semestre"), subtítulo diz métrica, unidade e período.
- Eixo de barras começa em zero. Um único eixo Y; medidas de escala diferente vão para gráficos separados ou índice base 100.
- Ordene categorias por valor, não alfabeticamente (salvo ordem natural: meses, faixas).
- Cor tem função: uma cor para a série, destaque só no que importa, cores de status (verde/vermelho) reservadas para bom/ruim e sempre com ícone ou texto. Paletas seguras para daltonismo; a skill `dataviz` tem validador de paleta.
- Números no padrão brasileiro: `1.234,56`, `R$`, `%` com uma casa. Em Python: `f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")`; em matplotlib, `FuncFormatter`.
- Rótulos diretos em poucas séries em vez de legenda distante; tabela de apoio para quem precisa do número exato.

## Bibliotecas

- **Plotly** (instalado): interativo, exporta HTML autônomo (`fig.write_html(..., include_plotlyjs=True)`) e imagem com `kaleido`.
- **matplotlib/seaborn**: gráficos estáticos para relatório e PDF.
- Painel completo com filtros: `dashboard_html.py` (skill `dashboard-html`). Power BI: skill `power-bi-mcp`.

## Narrativa da entrega

1. Resposta em uma ou duas frases, com o número.
2. Três a cinco achados, cada um com evidência e "e daí" para o negócio.
3. Limitações que podem mudar a conclusão.
4. Recomendação proporcional à evidência e próximo passo.

Antes de entregar, confira: totais batem com a origem? Filtros e período estão ditos? Os gráficos abrem e mostram o que o texto diz? Algum dado pessoal aparece sem necessidade?
