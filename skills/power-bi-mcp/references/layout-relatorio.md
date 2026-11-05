# Layout e design do relatório

## Estrutura de páginas

1. **Visão geral**: 4 a 6 KPIs com comparação (AA ou meta), uma evolução no tempo, um ou dois rankings. Responde "como estamos?" em 5 segundos.
2. **Páginas de análise** por pergunta (por região, por produto, por canal), com segmentação e detalhamento (drill-through).
3. **Detalhe**: tabela com filtros e exportação, acessada por drill-through.
4. **Qualidade e notas**: data de atualização, fontes, linhas descartadas, definições das medidas.

## Grade e leitura

- Tela 16:9 (1280 × 720). Margem de 16–24 px, espaçamento uniforme entre visuais.
- Leitura em Z: KPIs no topo, evolução no meio, detalhe embaixo. Filtros numa faixa fixa no topo ou à esquerda, iguais em todas as páginas (sincronize segmentações).
- No máximo 6 a 8 visuais por página. Mais que isso vira página nova.
- Título de visual diz a conclusão ou a pergunta; use títulos dinâmicos com o filtro ativo.

## Escolha de visuais

| Necessidade | Visual |
|---|---|
| número-chave | Cartão (novo cartão permite rótulo de referência com AA/meta) |
| evolução | Gráfico de linhas, eixo contínuo de data |
| comparação | Barras horizontais classificadas por valor |
| meta | Cartão com rótulo de referência ou gráfico de marcadores; evite medidor (gauge) |
| composição | Barras 100% empilhadas; pizza só com 2–3 fatias |
| matriz | Matriz com formatação condicional leve (barras de dados ou ícones com texto) |
| geografia | Mapa coroplético com taxa, não total |
| explicação | Árvore de decomposição, Principais influenciadores (com cautela: associação, não causa) |

## Cores e acessibilidade

- Tema JSON com paleta segura para daltonismo; uma cor principal, cinza para contexto, cores de status só para bom/ruim e sempre com ícone ou texto.
- Contraste de texto 4,5:1. Fonte mínima 10 pt em rótulos.
- Defina texto alternativo nos visuais, ordem de tabulação e títulos significativos.
- Formatos no padrão brasileiro: configure a localidade do modelo/relatório como pt-BR; formatos `#,0.00`, `0.0%`, `"R$" #,0.00`.

## Interação

- Interações entre visuais: filtrar (não realçar) quando o objetivo é recortar.
- Dicas de ferramenta (tooltip) com página de tooltip para contexto extra.
- Indicadores (bookmarks) para alternar visões; botões de limpar filtros.
- Drill-through para a página de detalhe, com botão Voltar.

## Desempenho do relatório

- Menos visuais por página, menos medidas complexas por visual.
- Segmentações com muitos valores: use busca ou hierarquia.
- Teste no Performance Analyzer e no serviço após publicar.
