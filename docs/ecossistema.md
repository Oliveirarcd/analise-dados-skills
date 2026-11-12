# Ecossistema: skills, plugins e MCPs que complementam

Conferido em 05/11/2026; a seção de qualidade visual, em 12/11/2026. Os projetos abaixo não são copiados para este repositório: são indicados com link para que cada um seja instalado da fonte, com a licença dele.

## Power BI e Microsoft Fabric

| Projeto | O que traz | Licença | Instalação |
|---|---|---|---|
| [microsoft/powerbi-modeling-mcp](https://github.com/microsoft/powerbi-modeling-mcp) | MCP oficial de modelagem (Power BI Authoring MCP, local) | EULA Microsoft | já registrado pelo `.mcp.json` deste plugin; ver `skills/power-bi-mcp/references/mcp-configuracao.md` |
| [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric) | plugin `powerbi-authoring` (skills de modelo semântico e de relatório PBIR, `powerbi-report-cli`) e skills de Fabric | MIT | Claude Code: `/plugin marketplace add microsoft/skills-for-fabric` e depois `/plugin install powerbi-authoring@fabric-collection`. Se instalar, remova o MCP deste plugin para não duplicar |
| [data-goblin/power-bi-agentic-development](https://github.com/data-goblin/power-bi-agentic-development) | plugins `semantic-models`, `reports`, `pbip`, `pbi-desktop`, `tabular-editor`, `custom-visuals`, `fabric-cli` | GPL-3.0 | `/plugin marketplace add data-goblin/power-bi-agentic-development` |

## Análise de dados e ciência

| Projeto | O que traz | Licença |
|---|---|---|
| [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) | plugin `data`: SQL, exploração, estatística, visualização, dashboards e conectores (BigQuery, Snowflake, Databricks, Hex, Amplitude) | ver repositório |
| [anthropics/skills](https://github.com/anthropics/skills) | skills oficiais, incluindo `xlsx`, `pdf`, `docx`, `pptx` | ver repositório |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | mais de 170 skills científicas (estatística, bioinformática, química, bancos científicos) | MIT |
| [Jeffallan/claude-skills](https://github.com/Jeffallan/claude-skills) | skills de desenvolvimento, incluindo `pandas-pro` | ver repositório |

## Bancos e SQL

| Projeto | O que traz | Configuração |
|---|---|---|
| [motherduckdb/mcp-server-motherduck](https://github.com/motherduckdb/mcp-server-motherduck) | MCP de DuckDB local (CSV, Parquet, Excel com SQL) e MotherDuck | `mcp/duckdb.mcp.json` ou `claude mcp add --scope user duckdb --transport stdio -- uvx mcp-server-motherduck --db-path :memory: --read-write` |

## Operar o Windows

| Projeto | O que traz | Licença | Configuração |
|---|---|---|---|
| [CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP) | controle da tela do Windows: capturas, árvore de elementos, clique, digitação, atalhos, janelas. Telemetria anônima ligada por padrão | MIT | `mcp/windows.mcp.json`, só com ferramentas de tela e telemetria desligada. Comando e regras em `skills/power-bi-mcp/references/operar-windows.md`. Não é registrado pelo plugin |

O Windows 11 tem conectores MCP nativos em prévia para participantes do Windows Insider desde dezembro de 2025. Eles só cobrem o Explorador de Arquivos e as Configurações, não programas como o Power BI Desktop.

## Qualidade visual e conferência de painéis

Só o Playwright é usado pelo código. Os demais entram como referência: as regras foram reescritas em português em [visualizacao-e-entrega.md](../skills/analise-dados/references/visualizacao-e-entrega.md), sem copiar arquivos.

| Projeto | Uso aqui | Licença | Observações |
|---|---|---|---|
| [microsoft/playwright](https://github.com/microsoft/playwright) | `conferir_painel.py` e testes: abre o painel sem janela, tira as fotos e mede os defeitos | Apache-2.0 | dependência opcional (`uv sync --group visual` ou `pip install playwright`); usa o Chrome ou o Edge instalados, sem baixar navegador |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | referência: piso de qualidade (contraste, números, estados, foco) e o "modo operar", que é o dos painéis | Apache-2.0 | o detector dele (`npx impeccable detect --json painel.html`, 62 regras, sem IA) **não foi rodado aqui**, porque executa código baixado do npm. Se for usar, fixe a versão e rode com `DO_NOT_TRACK=1`. Não use o instalador, que grava um hook que roda a cada edição, nem o modo `live`, cujo botão Aplicar chama o Codex ou o Claude sem sandbox e sem pedir permissão |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | referência: tabela de 25 tipos de gráfico com quando não usar, limite de volume e alternativa acessível | MIT | o resto da skill é para sites e aplicativos (estilos, fontes, ícones); não vale instalar para painéis de dados |
| [vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines) | referência: regras de interface (foco, contraste, formulários, números) | MIT | é a fonte da skill `web-design-guidelines` do [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills), repositório que não tem arquivo de licença |
| [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) | opcional, para depurar com o agente uma página aberta (console, rede, desempenho) | Apache-2.0 | envia estatísticas de uso ao Google por padrão: inicie com `--no-usage-statistics` e `--no-performance-crux`. Para a conferência de rotina, `conferir_painel.py` basta |

Avaliados e não usados: [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) (MIT; feita para sites de empresa, com fotos e efeitos, e registra um hook que roda ao fim de cada resposta), [21st-dev/magic-mcp](https://github.com/21st-dev/magic-mcp) e [Jpisnice/shadcn-ui-mcp-server](https://github.com/Jpisnice/shadcn-ui-mcp-server) (componentes React; o painel é um HTML único que abre sem internet) e [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) (MIT; SEO).

## Bibliotecas Python sugeridas por assunto

Instale só quando a análise pedir: `duckdb`, `polars`, `pyarrow` (dados grandes); `rapidfuzz` (casamento aproximado mais rápido, usado automaticamente por `cruzar.py` se presente); `scikit-learn`, `lightgbm`, `shap` (ML); `statsforecast`, `mlforecast`, `prophet`, `sktime`, `ruptures`, `holidays` (séries); `dowhy`, `econml`, `linearmodels` (causalidade e econometria); `matplotlib`, `seaborn`, `kaleido` (gráficos estáticos).

## Como as skills deste repositório convivem com as outras

- `analise-dados` é a porta de entrada e encaminha para as irmãs (`series-temporais`, `power-bi-mcp`, `dashboard-html`) e para as skills instaladas que cobrem o resto.
- Com o plugin oficial `powerbi-authoring`, use as skills dele para escrever PBIR e as deste repositório para preparar os dados, propor o modelo e validar os números.
- O `dataviz` (skill embutida no Claude Code) é a referência de cores e acessibilidade; o gerador `dashboard_html.py` usa a paleta de referência dele, com tons mais escuros no texto secundário e nas cores de status do tema claro para passar de 4,5:1.
