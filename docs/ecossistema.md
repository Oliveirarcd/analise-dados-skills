# Ecossistema: skills, plugins e MCPs que complementam

Conferido em 05/11/2026. Os projetos abaixo não são copiados para este repositório: são indicados com link para que cada um seja instalado da fonte, com a licença dele.

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

## Bibliotecas Python sugeridas por assunto

Instale só quando a análise pedir: `duckdb`, `polars`, `pyarrow` (dados grandes); `rapidfuzz` (casamento aproximado mais rápido, usado automaticamente por `cruzar.py` se presente); `scikit-learn`, `lightgbm`, `shap` (ML); `statsforecast`, `mlforecast`, `prophet`, `sktime`, `ruptures`, `holidays` (séries); `dowhy`, `econml`, `linearmodels` (causalidade e econometria); `matplotlib`, `seaborn`, `kaleido` (gráficos estáticos).

## Como as skills deste repositório convivem com as outras

- `analise-dados` é a porta de entrada e encaminha para as irmãs (`series-temporais`, `power-bi-mcp`, `dashboard-html`) e para as skills instaladas que cobrem o resto.
- Com o plugin oficial `powerbi-authoring`, use as skills dele para escrever PBIR e as deste repositório para preparar os dados, propor o modelo e validar os números.
- O `dataviz` (skill embutida no Claude Code) é a referência de cores e acessibilidade; o gerador `dashboard_html.py` usa a paleta de referência dele.
