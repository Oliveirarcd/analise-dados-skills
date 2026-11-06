---
name: power-bi-mcp
description: Construção de dashboards e modelos semânticos no Power BI com apoio do MCP oficial da Microsoft (Power BI Authoring/Modeling MCP) — modelo estrela, relacionamentos, tabela calendário, medidas DAX (inteligência de tempo, variação, acumulado, ranking), Power Query M, RLS, PBIP/TMDL/PBIR, validação de números, boas práticas de layout e, com o MCP do Windows, abrir o Power BI Desktop e conferir os visuais pela tela. Use sempre que o usuário falar em Power BI, PBIX, PBIP, DAX, Power Query, modelo semântico, Fabric, relatório ou painel corporativo no Power BI, ou pedir para transformar planilhas em um dashboard Power BI, mesmo sem citar MCP.
---

# Power BI com MCP

O MCP oficial da Microsoft deixa o agente ler e alterar o **modelo semântico** (tabelas, colunas, medidas, relacionamentos, partições, RLS, calendário) e executar DAX. Ele **não** cria páginas nem visuais do relatório. Páginas e visuais se fazem no Power BI Desktop ou editando os arquivos PBIR de um projeto PBIP. Planeje a entrega com essa divisão em mente.

## 1. Descubra o ambiente antes de prometer

1. Verifique quais ferramentas MCP existem de fato na sessão (procure nomes como `connection_operations`, `measure_operations`, `dax_query_operations`). Não invente nomes de ferramenta e não afirme conexão só porque existe um arquivo de configuração.
2. Sem MCP disponível: gere os artefatos (modelo proposto, `medidas.dax`, Power Query M, roteiro de visuais) para o usuário aplicar, e diga como instalar o MCP ([references/mcp-configuracao.md](references/mcp-configuracao.md)).
3. Aceitar o EULA do servidor e fazer login na conta Microsoft é decisão do usuário. Peça autorização explícita antes de chamar `accept_eula`; nunca adicione `--accepteula` por conta própria.
4. Antes de qualquer escrita: confirme que existe backup do modelo ou que ele está em PBIP sob Git. O agente pode errar e algumas mudanças não têm desfazer.

## 2. Fluxo de construção

1. **Entenda os dados** com a skill `analise-dados` (perfil e qualidade de cada tabela).
2. **Proponha o modelo estrela** com `modelo_estrela.py` (em `../analise-dados/scripts/`):
   ```bash
   python ../analise-dados/scripts/modelo_estrela.py vendas.csv lojas.csv produtos.csv --saida modelo_pbi
   ```
   Saídas: `modelo.json` (tabelas, papéis fato/dimensão, relacionamentos com contenção e órfãos, medidas), `modelo.md` (diagrama Mermaid e alertas) e `medidas.dax` (tabela Calendário e medidas base com inteligência de tempo). Revise os alertas: chave órfã vira "(Em branco)" nos visuais.
3. **Conecte** pelo MCP (`Connect to '<arquivo>' in Power BI Desktop`, ou modelo no Fabric, ou pasta PBIP) e faça uma leitura sem alterar nada: liste tabelas, colunas e medidas.
4. **Aplique em lotes pequenos**, com transação quando o servidor local permitir: tabela Calendário marcada como tabela de datas → relacionamentos 1:* com filtro único → tabela `_Medidas` → medidas com formato e pasta → ocultar chaves e colunas técnicas → descrições.
5. **Valide com DAX** cada medida contra o total conhecido da origem (ver [references/checklist-validacao.md](references/checklist-validacao.md)). Use `EVALUATE SUMMARIZECOLUMNS(...)` e compare com o pandas.
6. **Monte o relatório**: siga [references/layout-relatorio.md](references/layout-relatorio.md). Com PBIP, as páginas podem ser escritas em PBIR (ver [references/pbip-pbir-tmdl.md](references/pbip-pbir-tmdl.md)); sem PBIP, entregue o roteiro de páginas e visuais para o usuário montar no Desktop. Se o MCP do Windows estiver ativo na sessão, abra o projeto no Desktop e confira cada página por captura de tela ([references/operar-windows.md](references/operar-windows.md)); sem ele, diga que os visuais não foram vistos renderizados.
7. **Publique só com autorização** e no workspace que o usuário indicar.

## 3. Referências

| Tarefa | Arquivo |
|---|---|
| Instalar e conectar o MCP (local ou hospedado), problemas comuns | [mcp-configuracao.md](references/mcp-configuracao.md) |
| Modelo estrela, relacionamentos, calendário, padrões DAX | [modelagem-e-dax.md](references/modelagem-e-dax.md) |
| Power Query M: limpeza, padrão brasileiro, parâmetros, dobra de consulta | [power-query-m.md](references/power-query-m.md) |
| PBIP, TMDL e PBIR: editar o projeto como texto, Git | [pbip-pbir-tmdl.md](references/pbip-pbir-tmdl.md) |
| Páginas, visuais, cores, acessibilidade, desempenho | [layout-relatorio.md](references/layout-relatorio.md) |
| Conferir números, desempenho e segurança antes de entregar | [checklist-validacao.md](references/checklist-validacao.md) |
| Operar o Power BI Desktop pela tela (MCP do Windows, opcional): abrir, atualizar, conferir visuais | [operar-windows.md](references/operar-windows.md) |

## 4. Regras

- Modelo estrela: fatos no centro, dimensões em volta, relacionamentos um-para-muitos com filtro em direção única. Muitos-para-muitos e filtro bidirecional só com justificativa escrita.
- Toda medida explícita (nada de somar coluna arrastada), com `DIVIDE` em divisões, formato definido e pasta de exibição. Colunas calculadas só quando o valor é necessário linha a linha (segmentar, relacionar); o resto é medida.
- Uma única tabela Calendário contínua, marcada como tabela de datas, cobrindo anos completos. Desative "Data/hora automática".
- Nomes de negócio em português nos objetos visíveis; chaves e colunas técnicas ocultas.
- Os dados e metadados do modelo passam pelo provedor do modelo de linguagem. Não use o MCP em modelo com dados sensíveis sem autorização, e não cole resultados com dados pessoais na conversa sem necessidade.
- Diga o que foi aplicado no modelo, o que foi validado por DAX e o que ficou só como artefato para o usuário aplicar.

## 5. Complementos recomendados

- Plugin oficial `powerbi-authoring` (Microsoft, `microsoft/skills-for-fabric`, MIT): traz skills de modelagem e de relatório PBIR e registra o MCP. Se instalado, não registre o MCP de novo por aqui (duas cópias confundem o agente).
- `data-goblin/power-bi-agentic-development` (GPL-3.0): plugins para Tabular Editor, PBIP, relatórios e Fabric CLI.
- Links, licenças e comandos em `docs/ecossistema.md` na raiz do repositório.
