# MCP do Power BI: instalação e conexão

Fontes conferidas em 05/11/2026: repositório https://github.com/microsoft/powerbi-modeling-mcp (pacote npm `@microsoft/powerbi-modeling-mcp`, versão 1.0.0) e documentação https://learn.microsoft.com/power-bi/developer/mcp/power-bi-authoring-mcp. Confira de novo antes de mudar a configuração: o produto evolui rápido.

## Duas formas do mesmo servidor

| | Local (GA) | Hospedado (preview) |
|---|---|---|
| Transporte | stdio no seu computador | HTTP, servidor da Microsoft |
| Instalação | Node.js 18+ e `npx`, extensão do VS Code ou executável | nenhuma |
| Power BI Desktop aberto | sim | não |
| Pastas PBIP/TMDL no disco | sim | não |
| Modelo em workspace do Fabric | sim (XMLA leitura/gravação na capacidade) | sim (configuração de locatário habilitada pelo administrador) |
| Transações e rastreamento | sim | não |
| Sistema | Windows (não roda em macOS) | qualquer |

Registre **apenas um** dos dois. Com os dois ativos, o agente vê ferramentas duplicadas e gasta contexto à toa.

## Instalação local no Claude Code

O plugin deste repositório já registra o servidor local (arquivo `.mcp.json` na raiz). Para registrar à mão:

```bash
claude mcp add powerbi-modeling --scope user -- npx -y @microsoft/powerbi-modeling-mcp@latest --start
```

No Codex:

```bash
codex mcp add powerbi-modeling -- npx -y @microsoft/powerbi-modeling-mcp@latest --start
```

JSON equivalente (VS Code, Cursor e outros clientes): ver `mcp/powerbi-local.mcp.json`.

### EULA

O servidor bloqueia as ferramentas até o EULA ser aceito. O agente pode chamar `accept_eula` **depois que o usuário autorizar explicitamente**; a aceitação fica salva na máquina. Para execução sem interação, o próprio usuário pode adicionar `--accepteula` ou `PBI_MODELING_MCP_ACCEPT_EULA=true`. Este repositório não faz isso por ele.

## Servidor hospedado

```json
{ "mcpServers": { "powerbi-authoring-remote": { "type": "http", "url": "https://api.fabric.microsoft.com/v1/mcp/powerbi/authoring" } } }
```

Exige login Microsoft Entra e a configuração de locatário "Users can use the Power BI Model Context Protocol server endpoint". Alguns clientes dependem de registro dinâmico OAuth, que o Entra não suporta; nesse caso use o servidor local ou registre um aplicativo Entra próprio (ver documentação "Register the hosted Power BI MCP servers with external MCP clients").

## Conectar a um modelo

Diga ao agente, em linguagem natural:

- Power BI Desktop: `Connect to 'Vendas' in Power BI Desktop` (o arquivo precisa estar aberto).
- Fabric: `Connect to semantic model 'Vendas' in Fabric workspace 'Comercial'`.
- PBIP: `Open semantic model from PBIP folder 'C:\projetos\Vendas\Vendas.SemanticModel\definition'`.

Primeiro passo sempre de leitura: `List the tables and measures in this model`.

## Ferramentas do servidor (README oficial)

`connection_operations`, `database_operations` (inclui importar/exportar TMDL e implantar no Fabric), `transaction_operations`, `model_operations`, `table_operations`, `column_operations`, `measure_operations`, `relationship_operations`, `dax_query_operations`, `trace_operations`, `partition_operations`, `user_hierarchy_operations`, `calculation_group_operations`, `security_role_operations`, `perspective_operations`, `named_expression_operations` (parâmetros do Power Query), `function_operations` (funções DAX definidas pelo usuário), `culture_operations`, `object_translation_operations`, `calendar_operations`, `query_group_operations`.

Prompts prontos do servidor: `CreateDAXQuery`, `RunDAXQueryWithMetrics`, `AnalyzeDAXQuery`, `ConnectToPowerBIDesktop`, `ConnectToFabric`, `ConnectToPBIP`.

Os nomes reais expostos no cliente podem ter prefixo (por exemplo `mcp__powerbi-modeling__measure_operations`). Use os que aparecerem na sessão.

## Limites conhecidos

- Só operações de modelagem: não cria páginas, visuais nem layout do diagrama.
- Consultas DAX limitadas a 100.000 linhas.
- Com permissão só de Build no modelo, consegue consultar DAX mas não alterar.
- Metadados e resultados de consulta vão para o provedor do modelo de linguagem: cuidado com dados sensíveis.

## Problemas comuns

| Sintoma | O que verificar |
|---|---|
| Ferramentas não aparecem | Node.js instalado (`node --version`), servidor listado em `claude mcp list`, reiniciar a sessão |
| Toda chamada responde pedindo EULA | usuário ainda não aceitou; pedir autorização |
| Não acha o arquivo do Desktop | o .pbix precisa estar aberto; use o nome que aparece na barra de título |
| Lê mas não grava | falta permissão de escrita ou XMLA leitura/gravação na capacidade |
| Reconecta a cada operação (hospedado) | cliente não reenvia `mcp-Session-Id`; use o local |
| Mudanças erradas ou travadas | quebrar o pedido em passos menores, dar mais contexto, usar transação |

Guia de solução de problemas oficial: https://github.com/microsoft/powerbi-modeling-mcp/blob/main/TROUBLESHOOTING.md
