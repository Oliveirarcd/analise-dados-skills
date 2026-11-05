# PBIP, TMDL e PBIR

## Por que usar PBIP

O formato Power BI Project (Arquivo → Salvar como → .pbip) grava o relatório como pastas de texto: o modelo em **TMDL** e o relatório em **PBIR** (JSON por página e por visual). Assim o Git mostra cada mudança que o agente fez, dá para revisar o diff e desfazer. É o jeito mais seguro de deixar um agente editar Power BI.

Estrutura típica:

```
Vendas.pbip
Vendas.SemanticModel/
  definition/
    model.tmdl
    relationships.tmdl
    tables/vendas.tmdl, lojas.tmdl, Calendario.tmdl, _Medidas.tmdl
Vendas.Report/
  definition/
    report.json
    pages/<id>/page.json
    pages/<id>/visuals/<id>/visual.json
```

Pode ser necessário habilitar o recurso de visualização "Power BI Project" e o formato PBIR nas opções do Desktop, conforme a versão.

## TMDL (modelo)

Indentação com tabulação; propriedades abaixo do objeto:

```tmdl
table _Medidas

	measure 'Total Vendas' = SUM('vendas'[valor])
		formatString: #,0.00
		displayFolder: Vendas

	measure 'Vendas Var % AA' =
			VAR Atual = [Total Vendas]
			VAR Anterior = [Vendas AA]
			RETURN DIVIDE(Atual - Anterior, Anterior)
		formatString: 0.0%;-0.0%;0.0%
		displayFolder: Vendas\Tempo
```

Caminhos de edição:

1. **Pelo MCP** (recomendado): `Open semantic model from PBIP folder '<...>\Vendas.SemanticModel\definition'`, aplique mudanças com as ferramentas e salve/exporte TMDL (`database_operations`). O servidor valida a sintaxe.
2. **Editando o texto**: possível para mudanças pequenas, mas feche o projeto no Desktop antes e reabra depois. Erro de indentação impede a abertura.

`modelo_estrela.py` produz `modelo.json` com nome, expressão, formato e pasta de cada medida, no formato que se passa direto para `measure_operations`.

## PBIR (relatório)

Cada visual é um `visual.json` com tipo, posição, campos (consultas) e formatação, validado por esquema JSON publicado pela Microsoft (o `$schema` no topo de cada arquivo aponta a versão). O MCP de modelagem **não** edita PBIR. Opções:

- Skill `powerbi-report-cli` do plugin oficial `powerbi-authoring` (repositório `microsoft/skills-for-fabric`): cria, edita e valida páginas e visuais PBIR e gera um roteiro de design.
- Plugins `pbip` e `reports` de `data-goblin/power-bi-agentic-development`.
- Copiar um visual existente feito no Desktop e ajustar campos e posição, mantendo o `$schema` original. Sempre reabra no Desktop para conferir que renderiza.

Sem nenhuma dessas ferramentas, entregue um roteiro (página, visual, campos, filtros, formatação) e deixe a montagem para o Desktop. Não escreva PBIR de memória sem validar no esquema.

## Git

- `.gitignore` do PBIP gerado pelo Desktop já exclui `cache.abf` e `localSettings.json`; mantenha.
- Commits pequenos por etapa (modelo, medidas, páginas), mensagem dizendo o que muda para o usuário final.
- Não versione dados: modo Importação em PBIP não grava os dados no TMDL, mas parâmetros com caminhos e credenciais podem aparecer; revise antes de enviar para repositório remoto.
