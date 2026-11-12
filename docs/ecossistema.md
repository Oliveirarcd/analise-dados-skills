# Quadro de ferramentas: skills, plugins, MCPs e bibliotecas

Cada linha tem um veredito e a data em que deve ser revista. Os critérios e o roteiro de avaliação estão em [manutencao.md](manutencao.md). Nada destes projetos é copiado para cá: o que é adotado é reescrito em português ou entra como dependência opcional, com crédito e link; o resto é indicado para instalar da fonte, com a licença dele.

**Vereditos:** **adotar** = faz parte do pacote; **testar** = opcional, falta testar aqui; **observar** = complemento instalado da fonte; **descartar** = não serve aqui.

Última revisão geral: 12/11/2026. Próxima: 12/02/2027.

## Power BI e Microsoft Fabric

| Projeto | Veredito | Uso aqui | Licença | Revisar em |
|---|---|---|---|---|
| [microsoft/powerbi-modeling-mcp](https://github.com/microsoft/powerbi-modeling-mcp) | adotar | MCP oficial de modelagem, registrado pelo `.mcp.json` deste plugin. Conexão real não testada. Configuração em `skills/power-bi-mcp/references/mcp-configuracao.md` | MIT no repositório; o servidor pede aceite do EULA da Microsoft | 12/02/2027 |
| [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric) | observar | plugin `powerbi-authoring` (modelo semântico, relatório PBIR, `powerbi-report-cli`) e skills de Fabric: `/plugin marketplace add microsoft/skills-for-fabric` e `/plugin install powerbi-authoring@fabric-collection`. Se instalar, remova o MCP deste plugin para não duplicar | MIT | 12/02/2027 |
| [data-goblin/power-bi-agentic-development](https://github.com/data-goblin/power-bi-agentic-development) | observar | plugins `semantic-models`, `reports`, `pbip`, `pbi-desktop`, `tabular-editor`, `custom-visuals` e `fabric-cli`: `/plugin marketplace add data-goblin/power-bi-agentic-development`. Só indicação, nada copiado | GPL-3.0 | 12/02/2027 |

## Análise de dados e ciência

| Projeto | Veredito | Uso aqui | Licença | Revisar em |
|---|---|---|---|---|
| [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) | observar | plugin `data`: SQL, exploração, estatística, visualização, dashboards e conectores (BigQuery, Snowflake, Databricks, Hex, Amplitude) | Apache-2.0 | 12/02/2027 |
| [anthropics/skills](https://github.com/anthropics/skills) | observar | skills oficiais, incluindo `xlsx`, `pdf`, `docx` e `pptx` | licença em cada skill | 12/02/2027 |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | observar | mais de 170 skills científicas (estatística, bioinformática, química, bancos científicos) | MIT | 12/02/2027 |
| [Jeffallan/claude-skills](https://github.com/Jeffallan/claude-skills) | observar | skills de desenvolvimento, incluindo `pandas-pro` | MIT | 12/02/2027 |
| [krzjoa/awesome-python-data-science](https://github.com/krzjoa/awesome-python-data-science) | observar | índice de bibliotecas por assunto; dele vieram o pandera e o DataComPy. Texto não copiado | CC-BY-4.0 | 12/02/2027 |
| [microsoft/SandDance](https://github.com/microsoft/SandDance) | observar | explorar dados à mão fora do painel: aplicativo na web, extensão do VS Code e visual do Power BI. Não entra no painel, porque o pacote React/WebGL dele quebraria o arquivo único que abre sem internet. Não testado aqui | MIT | 12/02/2027 |
| [Avik-Jain/100-Days-Of-ML-Code](https://github.com/Avik-Jain/100-Days-Of-ML-Code) | descartar | roteiro de estudo, parado desde 2023 | MIT | — |
| [academic/awesome-datascience](https://github.com/academic/awesome-datascience) | descartar | lista de cursos e livros | MIT | — |
| [donnemartin/data-science-ipython-notebooks](https://github.com/donnemartin/data-science-ipython-notebooks) | descartar | notebooks de estudo antigos, com conteúdo de terceiros | variada, por item | — |

## ETL e rotinas de atualização

O guia está em [etl-e-rotinas.md](../skills/analise-dados/references/etl-e-rotinas.md).

| Projeto | Veredito | Uso aqui | Licença | Revisar em |
|---|---|---|---|---|
| [unionai-oss/pandera](https://github.com/unionai-oss/pandera) | testar | contrato de entrada (colunas, tipos e regras), citado como opcional no guia. O exemplo vem da documentação dele e não foi rodado aqui | MIT | 12/02/2027 |
| [capitalone/datacompy](https://github.com/capitalone/datacompy) | testar | o que mudou entre duas versões da mesma base, citado como opcional no guia. O exemplo vem da documentação dele e não foi rodado aqui | Apache-2.0 | 12/02/2027 |

## Bancos e SQL

| Projeto | Veredito | Uso aqui | Licença | Revisar em |
|---|---|---|---|---|
| [motherduckdb/mcp-server-motherduck](https://github.com/motherduckdb/mcp-server-motherduck) | adotar | MCP de DuckDB local (CSV, Parquet e Excel com SQL), em configuração de exemplo que o plugin não registra: `mcp/duckdb.mcp.json` ou `claude mcp add --scope user duckdb --transport stdio -- uvx mcp-server-motherduck --db-path :memory: --read-write` | MIT | 12/02/2027 |

## Operar o Windows

| Projeto | Veredito | Uso aqui | Licença | Revisar em |
|---|---|---|---|---|
| [CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP) | adotar | controle da tela do Windows (capturas, árvore de elementos, clique, digitação), só com ferramentas de tela e telemetria desligada: `mcp/windows.mcp.json`, versão fixada 0.8.8. Regras em `skills/power-bi-mcp/references/operar-windows.md`. O plugin não registra; não executado aqui | MIT | 12/02/2027 |
| [vercel-labs/agent-desktop](https://github.com/vercel-labs/agent-desktop) | testar | alternativa para o agente operar programas (Windows, macOS e Linux) pela árvore de acessibilidade, sem depender de imagem da tela. O README dele avisa que leituras de tela e da área de transferência podem conter conteúdo privado. Não testado aqui | Apache-2.0 | 12/02/2027 |

O Windows 11 tem conectores MCP nativos em prévia para participantes do Windows Insider desde dezembro de 2025. Eles só cobrem o Explorador de Arquivos e as Configurações, não programas como o Power BI Desktop.

## Qualidade visual e conferência de painéis

As regras adotadas estão reescritas em [visualizacao-e-entrega.md](../skills/analise-dados/references/visualizacao-e-entrega.md).

| Projeto | Veredito | Uso aqui | Licença | Revisar em |
|---|---|---|---|---|
| [microsoft/playwright](https://github.com/microsoft/playwright) | adotar | `conferir_painel.py` e testes: abre o painel sem janela, tira as fotos e mede os defeitos. Dependência opcional (`uv sync --group visual` ou `pip install playwright`); usa o Chrome ou o Edge instalados | Apache-2.0 | 12/02/2027 |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | adotar | regras reescritas: piso de qualidade e "modo operar", o dos painéis. O detector dele (`npx impeccable detect --json painel.html`) não foi rodado aqui, porque executa código baixado do npm; se usar, fixe a versão e rode com `DO_NOT_TRACK=1`. Não use o instalador, que grava um hook, nem o modo `live`, cujo botão Aplicar chama o Codex ou o Claude sem sandbox | Apache-2.0 | 12/02/2027 |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | adotar | regras reescritas: quando trocar de gráfico, limites de volume e alternativas acessíveis. O resto da skill é para sites e aplicativos | MIT | 12/02/2027 |
| [vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines) | adotar | regras reescritas de interface (foco, contraste, formulários, números). É a fonte da skill `web-design-guidelines` do [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills), repositório sem arquivo de licença | MIT | 12/02/2027 |
| [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) | observar | depurar com o agente uma página aberta (console, rede, desempenho). Envia estatísticas de uso ao Google por padrão: inicie com `--no-usage-statistics` e `--no-performance-crux`. Para a conferência de rotina, `conferir_painel.py` basta | Apache-2.0 | 12/02/2027 |
| [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | descartar | feita para sites de empresa, com fotos e efeitos, e registra um hook que roda ao fim de cada resposta | MIT | — |
| [21st-dev/magic-mcp](https://github.com/21st-dev/magic-mcp) | descartar | componentes React; o painel é um HTML único que abre sem internet | ISC | — |
| [Jpisnice/shadcn-ui-mcp-server](https://github.com/Jpisnice/shadcn-ui-mcp-server) | descartar | componentes React | MIT | — |

## Fora do escopo

| Projeto | Veredito | Motivo | Licença | Revisar em |
|---|---|---|---|---|
| [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) | descartar | SEO | MIT | — |
| [nexu-io/open-design](https://github.com/nexu-io/open-design) | descartar | ambiente de design com IA, não de dados | Apache-2.0 | — |

## Bibliotecas Python sugeridas por assunto

Instale só quando a análise pedir: `pandera` (contrato de entrada) e `datacompy` (comparação entre cargas) em rotinas de ETL; `duckdb`, `polars`, `pyarrow` (dados grandes); `rapidfuzz` (casamento aproximado mais rápido, usado automaticamente por `cruzar.py` se presente); `scikit-learn`, `lightgbm`, `shap` (ML); `statsforecast`, `mlforecast`, `prophet`, `sktime`, `ruptures`, `holidays` (séries); `dowhy`, `econml`, `linearmodels` (causalidade e econometria); `matplotlib`, `seaborn`, `kaleido` (gráficos estáticos).

## Como as skills deste repositório convivem com as outras

- `analise-dados` é a porta de entrada e encaminha para as irmãs (`series-temporais`, `power-bi-mcp`, `dashboard-html`) e para as skills instaladas que cobrem o resto.
- Com o plugin oficial `powerbi-authoring`, use as skills dele para escrever PBIR e as deste repositório para preparar os dados, propor o modelo e validar os números.
- O `dataviz` (skill embutida no Claude Code) é a referência de cores e acessibilidade; o gerador `dashboard_html.py` usa a paleta de referência dele, com tons mais escuros no texto secundário e nas cores de status do tema claro para passar de 4,5:1.
