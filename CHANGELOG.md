# Histórico de versões

O que mudou em cada versão. A política de versões (quando sobe o número maior, o menor ou a correção) está em [docs/manutencao.md](docs/manutencao.md). Para atualizar a sua instalação, veja "Como atualizar" no [README](README.md).

## 1.1.0 — 12/11/2026

### Acrescentado

- `conferir_painel.py`: conferência visual de qualquer HTML com o Playwright (opcional). Tira fotos em 1440 e 390 px, nos temas claro e escuro, e aponta erro de script, gráfico que não desenhou, página mais larga que a tela e texto com contraste abaixo de 4,5:1. Copia para o relatório os KPIs mostrados, para conferir com o pandas.
- Referência `etl-e-rotinas.md` (rotina repetível, contrato de entrada, histórico em cache, comparação entre cargas, agendamento), e ETL na descrição da skill `analise-dados`.
- Checklist de qualidade visual e "quando trocar de gráfico" em `visualizacao-e-entrega.md`.
- `docs/manutencao.md`: política de versões, regra "geral na skill, específico no projeto", roteiro para avaliar ferramentas e revisão a cada três meses.
- `docs/ecossistema.md` virou um quadro de ferramentas, com veredito e data de revisão em cada linha.
- `CONTRIBUTING.md` e a seção "Como atualizar" no README.
- Grupo de dependências opcional `visual` (Playwright, para quem usa `uv`). O Playwright também roda no CI.

### Mudado

- Painel: cabe no celular, sem rolagem para o lado a 390 px.
- Painel: contraste mínimo de 4,5:1 nos dois temas.
- Painel: nomes de coluna viram rótulos legíveis (`cod_loja` vira "Cód. loja").
- Painel: a medida "Linhas" passou a se chamar "Registros", e as medidas automáticas viraram "Total de valor" (antes, "Total valor").
- Painel: meses em português, milhar nos eixos e botões dos gráficos em português.
- Painel: visão 3D ajustada ao celular.

### Corrigido

- O painel gerado com `--cdn` volta a mostrar filtros e KPIs quando o Plotly não carrega da internet.
- `requirements.txt` passa a exigir o Plotly 7.1.0 ou mais novo, a versão testada e a mesma do `pyproject.toml` (antes aceitava 5.20).

## 1.0.0 — 05/11/2026

Primeira versão. Os acréscimos feitos no mesmo dia entraram sem mudar o número.

- Skills `analise-dados`, `series-temporais`, `dashboard-html` e `power-bi-mcp`, com scripts testados: perfil, cruzamento auditado, estatística, séries temporais, modelo estrela e painel HTML. Todos leem arquivos no padrão brasileiro.
- Plugin do Claude Code, que registra o MCP local do Power BI.
- Painel HTML com visão 3D interativa e movimento; correção do clique na visão 3D e da animação dos rankings.
- Correções na leitura de números com milhar sem vírgula decimal, na escolha automática de medidas do painel e no backtest de séries, que marcava "supera o modelo de referência" mesmo quando o vencedor era o próprio modelo de referência.
- Configuração opcional do Windows-MCP para operar o Power BI Desktop pela tela, fixada na versão 0.8.8.
