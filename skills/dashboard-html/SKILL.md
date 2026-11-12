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

Agregações: `soma`, `media`, `contagem` (não nulos), `min`, `max`, `distintos`. A medida "Registros" (contagem de linhas) sempre entra. `--cdn` gera arquivo pequeno que carrega o Plotly da internet. `--texto col` mantém códigos como texto.

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
- Texto para gente ler: nomes de coluna viram rótulos (`cod_loja` vira "Cód. loja", `id_venda` vira "ID venda"; nome com maiúscula ou espaço fica como está), meses em português (jan/24, T1/24), milhar também nos eixos (1.400, 15.000), botões dos gráficos em português e contraste de pelo menos 4,5:1 nos dois temas. O CSV do detalhe mantém os nomes originais das colunas.
- Cabe no celular: sem rolagem para o lado a 390 px, KPIs em duas colunas e visão 3D com câmera mais afastada e sem a escala de cor.

## Por que 3D só nesse cartão

Barra, pizza ou linha em 3D distorcem a leitura: a perspectiva faz itens iguais parecerem diferentes. Por isso os gráficos de leitura continuam planos, e o 3D fica no cartão em que a terceira dimensão carrega dado de verdade (período × item × valor). Se o usuário pedir 3D num ranking ou numa pizza, explique isso e ofereça a visão 3D.

## Volume de dados

Até `--max-linhas` (200 mil por padrão) o painel guarda as linhas. Acima disso, pré-agrega por dia e dimensões com soma, contagem, mínimo e máximo, o que mantém totais e médias exatos; `distintos` e a tabela de detalhe deixam de existir nesse modo, e o script avisa. Para bases muito maiores, agregue antes (DuckDB) e gere o painel sobre o agregado.

## Antes de entregar

1. Rode a conferência visual e **abra as fotos**:
   ```bash
   python $S/conferir_painel.py painel.html --saida conferencia/
   ```
   Ela abre o painel no Chrome ou no Edge sem janela, em 1440 px e 390 px, nos temas claro e escuro, e aponta erro de script, gráfico que não desenhou, rolagem horizontal e contraste abaixo de 4,5:1. Sai com código 1 se achar defeito. Precisa do Playwright (`pip install playwright`); sem ele, abra o HTML no navegador e confira à mão, inclusive com a janela estreita. A medição não vê tudo: foto cortada ou desalinhada só aparece olhando.
2. Compare pelo menos um total e um recorte com o pandas. O `relatorio.json` da conferência traz os KPIs mostrados na tela; os testes do repositório fazem essa comparação para os dados de exemplo.
3. O arquivo contém **todos os dados** usados. Se houver dados pessoais ou sigilosos, remova colunas desnecessárias antes (`--filtros`/`--medidas` explícitos limitam o que entra) e avise o usuário antes de ele compartilhar.

## Quando ir além do gerador

Para layout sob medida (vários painéis, mapas, gráficos de dispersão, metas), escreva um HTML próprio partindo deste: o modelo de dados embutido (`const D`) e as funções `filtered`, `aggregate` e `groupBy` do script são reaproveitáveis. Siga a skill `dataviz` para cores e acessibilidade e o checklist de qualidade visual em `../analise-dados/references/visualizacao-e-entrega.md`, e confira o HTML próprio com `conferir_painel.py` do mesmo jeito. Para um painel publicado e atualizado automaticamente na empresa, use a skill `power-bi-mcp`.
