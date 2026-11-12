# Instruções para agentes que mantêm este repositório

Repositório de skills de análise e ciência de dados em português (Claude Code e Codex), distribuído como plugin do Claude Code.

## Estrutura

- `skills/analise-dados/`: skill orquestradora, `scripts/` (núcleo Python testado), `references/` e `assets/`.
- `skills/series-temporais/`, `skills/power-bi-mcp/`, `skills/dashboard-html/`: skills irmãs; usam os scripts de `analise-dados/scripts/`.
- `.claude-plugin/`: manifesto do plugin e do marketplace. `.mcp.json`: MCP local do Power BI registrado pelo plugin.
- `mcp/`: exemplos de configuração MCP. `docs/ecossistema.md`: quadro de ferramentas. `docs/manutencao.md`: versões, geral × específico, avaliação de ferramentas e revisão trimestral. `exemplos/`: gerador de dados sintéticos.
- `CHANGELOG.md`: o que mudou em cada versão. `CONTRIBUTING.md`: como outras pessoas propõem melhorias.
- `tests/`: testes de comportamento. `ferramentas/validar_skills.py`: validação estrutural.

## Regras

- Documentação, mensagens e nomes de arquivos em português do Brasil; identificadores de código podem ficar em inglês.
- A skill guarda só o que vale para qualquer projeto. Nome de coluna, de-para, peso, meta ou sigla de um projeto fica na pasta desse projeto (contrato da análise), nunca aqui.
- Toda mudança entra no topo do `CHANGELOG.md`, na versão marcada como não publicada, e segue a política de versões de `docs/manutencao.md`. O número fica igual em `.claude-plugin/plugin.json` e `pyproject.toml`.
- Ferramenta, skill, MCP ou biblioteca nova passa pelo roteiro de `docs/manutencao.md` e ganha linha no quadro de `docs/ecossistema.md`. Não copie arquivos de terceiros nem rode instalador que grave hook.
- Nada de dados reais, credenciais, PBIX ou saídas com dados de clientes no repositório. Exemplos e testes usam só `exemplos/gerar_dados_exemplo.py`.
- Antes de mudar qualquer instrução sobre o MCP do Power BI, confira a documentação oficial e atualize a data em `skills/power-bi-mcp/references/mcp-configuracao.md`.
- Não aceite EULA nem registre credenciais em nome do usuário.
- Mudança em script exige teste de comportamento, inclusive caminho de erro. Não enfraqueça travas de cardinalidade, separação temporal ou validação de entrada.
- Antes de concluir: `python -m pytest` e `python ferramentas/validar_skills.py` passando.
- Mudança visual no painel ou em qualquer HTML gerado: `conferir_painel.py` sem defeitos e as fotos olhadas (computador e celular, temas claro e escuro). A medição não vê corte nem sobreposição.
- SKILL.md com menos de 500 linhas; detalhe vai para `references/`.
