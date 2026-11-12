# Manutenção e evolução

Como o repositório muda sem quebrar quem já usa: versões, o que é da skill e o que é do projeto, como avaliar uma ferramenta nova e a revisão a cada três meses.

## Versões

O número segue MAIOR.MENOR.CORREÇÃO e é o mesmo em `.claude-plugin/plugin.json`, `pyproject.toml` e no topo do [CHANGELOG.md](../CHANGELOG.md).

| Sobe | Quando | Exemplo |
|---|---|---|
| MAIOR | quebra quem já usa: opção de script removida ou renomeada, arquivo de saída de script (JSON, CSV, modelo) com estrutura diferente, skill removida ou renomeada | `--chaves` passar a se chamar `--chave` |
| MENOR | acrescenta sem quebrar: script, opção, referência ou skill nova | a referência de ETL |
| CORREÇÃO | conserta sem mudar o uso: erro, texto, visual | o contraste do painel |

Textos de tela do painel, inclusive o cabeçalho do CSV que a pessoa baixa dele, não contam como quebra.

A versão em preparo fica no topo do CHANGELOG marcada como "não publicada" e recebe cada mudança assim que ela é feita. Ao publicar, ela ganha a data, o número é conferido nos três lugares e a versão vira uma release no GitHub com o mesmo texto. Quem usa atualiza como explica o README.

## Geral na skill, específico no projeto

A skill serve a projetos de qualquer área. Por isso:

- **Fica na skill** o que vale para qualquer base: leitura no padrão brasileiro, perfil, cruzamento auditado, estatística, séries, painel, Power BI e ETL.
- **Fica na pasta do projeto** o que é de um projeto só: nomes de colunas, de-para, pesos, metas, siglas internas, caminhos de arquivos e regras de negócio. O lugar é o contrato da análise ([modelo](../skills/analise-dados/assets/contrato-analise.md)), preenchido e salvo na pasta do projeto, junto com o `AGENTS.md` ou o `CLAUDE.md` do próprio projeto.
- Exemplos e testes usam só dados fictícios ([gerador](../exemplos/gerar_dados_exemplo.py)). Um exemplo que nasceu de um caso real é reescrito de forma genérica antes de entrar.
- Teste rápido: a regra faria sentido para uma loja, uma clínica e uma prefeitura? Se não fizer, ela é do projeto.

## Avaliar uma ferramenta nova

Vale para qualquer sugestão: repositório favoritado, skill, plugin, MCP ou biblioteca.

| Critério | Pergunta | Se falhar |
|---|---|---|
| Licença | Permite usar e citar? MIT, Apache-2.0 e BSD sim; GPL só como indicação externa, sem copiar nada | descartar ou só indicar |
| Manutenção | Teve mudança nos últimos 12 meses e não está arquivado? | observar |
| Sem internet e sem conta | Funciona sem internet e sem cadastro pago? | só como opcional |
| Padrão brasileiro | Entende, ou pelo menos não atrapalha, `;`, vírgula decimal, datas dd/mm/aaaa e zeros à esquerda? | adaptar antes de adotar |
| Segurança | Instala hook, roda código baixado, executa agente sem sandbox ou liga telemetria? | não instalar; no máximo citar com o aviso |
| Peso | Cabe no que já existe (painel em arquivo único, dependências opcionais)? | observar ou descartar |
| Sobreposição | O pacote já faz isso? | descartar, ou substituir dizendo por quê |

Passos:

1. Ler o README, a licença, a data do último commit e o que o instalador faz.
2. Passar pelos critérios.
3. Dar o veredito:
   - **adotar:** faz parte do pacote, como código, configuração ou regra reescrita;
   - **testar:** promissor e opcional, mas falta testar aqui;
   - **observar:** complemento indicado, instalado da fonte, que não faz parte do pacote;
   - **descartar:** não serve aqui; o motivo fica escrito.
4. Adotar significa reescrever em português o que serve, sem copiar arquivos, ou entrar como dependência opcional com teste. Sempre com crédito, link e registro no CHANGELOG.
5. Registrar a linha no [quadro de ferramentas](ecossistema.md), com veredito e data para rever (a próxima revisão trimestral). Descartados ficam sem data e só voltam se alguém propuser de novo.

## Revisão a cada três meses

Próxima: **12/02/2027**. Depois, a cada três meses.

1. Rodar `python -m pytest`, `python ferramentas/validar_skills.py` e a conferência visual do painel de exemplo (`conferir_painel.py`).
2. Atualizar as dependências (`uv lock --upgrade` ou `pip list --outdated`) e rodar os testes de novo.
3. Conferir as versões fixadas na documentação, como `windows-mcp@0.8.8`, e o que mudou nelas antes de trocar.
4. MCP do Power BI: conferir a documentação oficial e atualizar a data em `skills/power-bi-mcp/references/mcp-configuracao.md`.
5. Rever as linhas do quadro de ferramentas com data vencida: licença, manutenção e veredito.
6. Conferir os links externos do README e das referências.
7. Registrar no CHANGELOG o que mudou e publicar a versão, se houve mudança.
8. Atualizar aqui a data da próxima revisão.
