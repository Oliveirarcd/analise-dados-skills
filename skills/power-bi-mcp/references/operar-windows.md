# Operar o Windows pela tela (MCP do Windows)

Fontes conferidas em 05/11/2026: https://github.com/CursorTouch/Windows-MCP (pacote PyPI `windows-mcp`, licença MIT). O projeto muda rápido; confira o README antes de alterar a configuração.

## Sumário
1. Quando usar e quando não usar
2. Instalação (opcional, fora do plugin)
3. Por que só ferramentas de tela
4. Regras de uso
5. Roteiro: conferir o relatório depois de editar o PBIR
6. Alternativas

## 1. Quando usar e quando não usar

Controlar a tela é o último recurso. É lento, depende de resolução, idioma e posição das janelas, e um clique pode cair no lugar errado. Antes dele, nesta ordem:

1. **Arquivos do projeto** (PBIP, PBIR e TMDL) para páginas, visuais e modelo. Ver [pbip-pbir-tmdl.md](pbip-pbir-tmdl.md).
2. **MCP de modelagem** para medidas, relacionamentos, calendário e consultas DAX. Ver [mcp-configuracao.md](mcp-configuracao.md).
3. **Scripts Python ou DuckDB** para preparar e conferir dados.

O MCP do Windows serve para o que não tem caminho por arquivo ou API:

- abrir o `.pbip` ou o `.pbix` no Power BI Desktop, que o MCP de modelagem precisa encontrar aberto;
- clicar em **Atualizar** e ler a mensagem de erro, quando houver;
- **ver o relatório renderizado** depois de editar o PBIR, com uma captura por página. É a única forma de confirmar que um visual escrito à mão aparece;
- operar Excel ou outro programa sem MCP próprio, quando não houver como fazer pelo arquivo.

## 2. Instalação (opcional, fora do plugin)

O plugin **não** registra este servidor: ele dá ao agente o mouse e o teclado do computador, e isso precisa ser uma decisão explícita do usuário. Requisitos: Windows 10 ou 11 e `uv` instalado. O `uvx` baixa o Python 3.14 que o pacote exige.

Claude Code, disponível em todas as pastas (`--scope user`):

```powershell
claude mcp add windows --scope user -e ANONYMIZED_TELEMETRY=false -- uvx windows-mcp serve --tools "Screenshot,Snapshot,Click,Type,Scroll,Move,Shortcut,Wait,WaitFor,App,MultiSelect,MultiEdit,Clipboard,DisplayInventory,ControlStatus"
```

Para usar só na pasta atual, troque `--scope user` por `--scope local`. O JSON equivalente para outros clientes está em `mcp/windows.mcp.json`, na raiz do repositório. Se o Claude Code mostrar "Connection closed", troque `uvx` pelo caminho completo que `where.exe uvx` mostra.

O projeto envia telemetria anônima por padrão. `ANONYMIZED_TELEMETRY=false` desliga.

Para remover: `claude mcp remove windows --scope user`.

## 3. Por que só ferramentas de tela

O servidor também oferece `PowerShell`, `FileSystem` (que inclui apagar arquivos), `Registry`, `Process` (encerrar programas) e `Scrape`. A configuração deixa esses de fora:

- O Claude Code já tem terminal e ferramentas de arquivo próprios, que passam pelos pedidos de permissão e pelos hooks do usuário, como o que manda exclusões para a Lixeira. As ferramentas equivalentes do MCP passariam por fora disso.
- Mexer no registro ou encerrar processos não faz parte de análise de dados.
- A configuração usa `--tools`, a lista do que **entra**. Assim, uma ferramenta nova numa versão futura não entra sozinha. Uma lista de exclusão deixaria entrar.

Limite: isso reduz acidentes, mas **não é barreira de segurança**. Com `Shortcut` e `Type` o agente ainda consegue abrir a caixa Executar (Win+R) ou um terminal. As regras abaixo continuam valendo.

## 4. Regras de uso

- **Tudo o que aparece na tela vai para o provedor do modelo de linguagem.** Antes de começar, peça ao usuário para fechar ou minimizar janelas com dados sigilosos (clientes, contratos, e-mail, sistemas internos).
- **Não digite senha, token, dado bancário ou documento pessoal.** Telas de login e de credencial da fonte de dados ficam com o usuário.
- **Confirme antes de clique irreversível:** Publicar, Salvar por cima, Substituir, Excluir, Enviar.
- **Avise o usuário para não mexer no mouse e no teclado** enquanto o agente opera. O servidor só age depois de cerca de 10 segundos sem uso físico e marca a tela com uma borda e um cursor "AI" quando está no controle.
- **Área de transferência:** útil para colar um DAX longo no Desktop. Só leia o conteúdo dela quando a tarefa pedir, porque pode ter algo que o usuário copiou de outro lugar.
- Prefira `Snapshot` (lista de elementos da janela com identificadores) a clicar por coordenada. Tire um `Screenshot` depois de cada passo importante para conferir.
- Não clique em links vindos de e-mail, mensagem ou documento.
- Diga ao usuário o que foi feito pela tela e o que foi conferido só por captura.

## 5. Roteiro: conferir o relatório depois de editar o PBIR

1. Termine as edições nos arquivos com o Desktop **fechado**. O Desktop não relê arquivos alterados por fora enquanto está aberto.
2. Abra o `.pbip` com `App` e espere a primeira página carregar com `WaitFor`.
3. Percorra as páginas pelas abas e tire um `Screenshot` de cada uma.
4. Confira com a [checklist-validacao.md](checklist-validacao.md): visual sem aviso de erro, títulos e eixos certos, totais iguais aos validados por DAX.
5. Se o objetivo era só conferir, feche **sem salvar**. Salvar pelo Desktop reescreve os arquivos do projeto.

## 6. Alternativas

- **Computer use do app Claude para desktop** (Configurações → Este computador → Computer use; vem desligado). É oficial da Anthropic, pede aprovação por aplicativo e limita o que o agente faz em navegadores e terminais. Funciona nas conversas do app para desktop, não no Claude Code pelo terminal. Por isso este repositório usa o Windows-MCP.
- **Conectores nativos do Windows 11**: em prévia para participantes do Windows Insider desde dezembro de 2025. Só cobrem o Explorador de Arquivos e as Configurações, então não operam o Power BI. Não ligue a opção que reduz as proteções dos conectores.
