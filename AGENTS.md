# Instruções para agentes que mantêm este repositório

Repositório de skills de análise e ciência de dados em português (Claude Code e Codex), distribuído como plugin do Claude Code.

## Estrutura

- `skills/analise-dados/`: skill orquestradora, `scripts/` (núcleo Python testado), `references/` e `assets/`.
- `skills/series-temporais/`, `skills/power-bi-mcp/`, `skills/dashboard-html/`: skills irmãs; usam os scripts de `analise-dados/scripts/`.
- `.claude-plugin/`: manifesto do plugin e do marketplace. `.mcp.json`: MCP local do Power BI registrado pelo plugin.
- `mcp/`: exemplos de configuração MCP. `docs/`: ecossistema e guias. `exemplos/`: gerador de dados sintéticos.
- `tests/`: testes de comportamento. `ferramentas/validar_skills.py`: validação estrutural.

## Regras

- Documentação, mensagens e nomes de arquivos em português do Brasil; identificadores de código podem ficar em inglês.
- Nada de dados reais, credenciais, PBIX ou saídas com dados de clientes no repositório. Exemplos e testes usam só `exemplos/gerar_dados_exemplo.py`.
- Antes de mudar qualquer instrução sobre o MCP do Power BI, confira a documentação oficial e atualize a data em `skills/power-bi-mcp/references/mcp-configuracao.md`.
- Não aceite EULA nem registre credenciais em nome do usuário.
- Mudança em script exige teste de comportamento, inclusive caminho de erro. Não enfraqueça travas de cardinalidade, separação temporal ou validação de entrada.
- Antes de concluir: `python -m pytest` e `python ferramentas/validar_skills.py` passando.
- SKILL.md com menos de 500 linhas; detalhe vai para `references/`.
