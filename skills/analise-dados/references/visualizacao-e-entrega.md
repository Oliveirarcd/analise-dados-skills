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

## Quando trocar de gráfico

- Menos de 4 pontos no tempo: cartão com o número e a comparação, não linha.
- Mais de 6 séries numa linha: destaque uma ou duas e deixe o resto em cinza, ou use pequenos múltiplos.
- Mais de 15 categorias: top 15 e "outros", com a lista completa numa tabela (o painel já faz assim).
- Pizza: no máximo 5 fatias, sempre com o % escrito. Fatias com menos de 5 pontos percentuais de diferença não se distinguem; use barras.
- Dispersão: com menos de 20 pontos o padrão não se sustenta; acima de 1.000 pontos use `scattergl` (WebGL) ou agregue (mapa de calor, hexágonos).
- Mapa de calor com menos de 20 células: barras leem melhor. Escreva o valor na célula quando couber.
- Funil só para etapas em sequência com valores que caem; se algum valor sobe no meio, são barras.

## Qualidade visual antes de entregar

- **Cabe no celular:** nada corta nem rola para o lado a 390 px de largura; gráfico que não cabe ganha versão simplificada (menos rótulos, sem legenda lateral).
- **Contraste:** texto comum com pelo menos 4,5:1 sobre o fundo e texto grande (24 px, ou 18,7 px em negrito) com 3:1, nos dois temas. Texto secundário cinza-claro sobre branco é o erro mais comum; cor de status usada como texto (verde, vermelho) costuma precisar de um tom mais escuro.
- **Números:** milhar também nos eixos e nas tabelas (1.400, não 1400 nem 1.4k), algarismos de largura fixa nas colunas numéricas (`font-variant-numeric: tabular-nums`), unidade no título ou no rótulo (R$, %, un.) e casas decimais iguais dentro da mesma coluna.
- **Texto para gente:** nada de nome de coluna na tela (`cod_loja` vira "Cód. loja"), meses em português (jan/24), botões e mensagens do gráfico em português, título que diz a conclusão.
- **Estados:** o que aparece com filtro sem dados, com um ponto só, com valores negativos ou nulos e sem WebGL. Nenhum deles pode virar tela em branco ou erro de script.
- **Teclado e leitor de tela:** foco visível em todo controle, nome em botão que só tem ícone (`aria-label`), tabela de apoio para quem não enxerga a cor ou precisa do número exato. Cor nunca é o único código.
- **Movimento:** curto, com função (mostrar o que mudou) e desligado quando o sistema pede "reduzir movimento"; o que gira ou se repete tem botão de pausa. Em painel de trabalho, clareza vale mais que efeito: antes de acrescentar um, diga que informação ele mostra.
- **Conferência:** rode `scripts/conferir_painel.py` e abra as fotos de computador e de celular nos dois temas. Ele mede erro de script, gráfico sem desenho, rolagem horizontal e contraste; corte, sobreposição e desalinhamento só aparecem olhando.

## Bibliotecas

- **Plotly** (instalado): interativo, exporta HTML autônomo (`fig.write_html(..., include_plotlyjs=True)`) e imagem com `kaleido`.
- **matplotlib/seaborn**: gráficos estáticos para relatório e PDF.
- Painel completo com filtros: `dashboard_html.py` (skill `dashboard-html`). Power BI: skill `power-bi-mcp`.
- **Playwright** (opcional, `pip install playwright` ou `uv sync --group visual`): abre o HTML num navegador sem janela para conferir e fotografar (`conferir_painel.py`). Usa o Chrome ou o Edge instalados.

## Narrativa da entrega

1. Resposta em uma ou duas frases, com o número.
2. Três a cinco achados, cada um com evidência e "e daí" para o negócio.
3. Limitações que podem mudar a conclusão.
4. Recomendação proporcional à evidência e próximo passo.

Antes de entregar, confira: totais batem com a origem? Filtros e período estão ditos? Os gráficos abrem e mostram o que o texto diz (a conferência visual passou e as fotos foram vistas)? Algum dado pessoal aparece sem necessidade?

## Fontes

As regras de "Quando trocar de gráfico" e "Qualidade visual" foram reescritas em português a partir destes projetos, sem copiar arquivos: [vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines) (MIT), [pbakaus/impeccable](https://github.com/pbakaus/impeccable) (Apache-2.0; o "modo operar" dele é o que vale para painéis), [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (MIT; tabela de tipos de gráfico com limites de volume e alternativas acessíveis) e a skill `dataviz`. Avaliação completa em `docs/ecossistema.md` na raiz do repositório.
