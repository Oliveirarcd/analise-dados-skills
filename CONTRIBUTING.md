# Como contribuir

Sugestões e correções são bem-vindas. O repositório serve a projetos de qualquer área, então cada contribuição precisa valer para qualquer base de dados, não para um caso só.

## Antes de começar

- Abra uma issue descrevendo o problema ou a ideia, com um exemplo em **dados fictícios**. Nunca anexe dados reais de empresa ou de pessoa, nem prints com esses dados.
- Regra de um projeto específico (nomes de colunas, de-para, pesos, metas, siglas internas) não entra na skill. Veja "Geral na skill, específico no projeto" em [docs/manutencao.md](docs/manutencao.md).

## Mudanças no código ou na documentação

1. Siga as regras do [AGENTS.md](AGENTS.md): português do Brasil, só dados sintéticos de `exemplos/gerar_dados_exemplo.py` e SKILL.md com menos de 500 linhas.
2. Mudança em script vem com teste de comportamento, inclusive do caminho de erro.
3. Rode `python -m pytest` e `python ferramentas/validar_skills.py`. Os dois precisam passar.
4. Mudança visual no painel ou em HTML gerado: rode `conferir_painel.py` e olhe as fotos de computador e de celular, nos temas claro e escuro.
5. Registre a mudança no topo do [CHANGELOG.md](CHANGELOG.md), na versão marcada como "não publicada".

## Sugerir uma ferramenta, skill ou biblioteca

Use o roteiro de avaliação em [docs/manutencao.md](docs/manutencao.md): licença, manutenção, funcionamento sem internet, padrão brasileiro, segurança, peso e sobreposição. O que for adotado é reescrito em português, com crédito e link; arquivos de outros projetos não são copiados. Toda ferramenta avaliada ganha uma linha no [quadro de ferramentas](docs/ecossistema.md).

## Licença

Ao contribuir, você concorda que a sua contribuição seja distribuída sob a licença MIT do repositório ([LICENSE](LICENSE)).
