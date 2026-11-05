# Checklist de validação antes de entregar

## Números

- [ ] Total de cada medida principal sem filtros = total calculado na origem (pandas/SQL), com diferença zero ou explicada.
- [ ] Os mesmos totais por um recorte conhecido (mês, região) batem.
- [ ] Linha "(Em branco)" nos visuais investigada (chave órfã ou nula) e tratada ou explicada.
- [ ] Medidas de percentual conferidas no total e no detalhe (o total não é soma dos percentuais).
- [ ] Inteligência de tempo conferida em um mês de virada de ano e no ano corrente incompleto.
- [ ] Contagens distintas conferidas (não somar distintos de grupos).

Consulta DAX de conferência (rodar com `dax_query_operations`):

```dax
EVALUATE
SUMMARIZECOLUMNS(
    'Calendario'[Ano],
    "Vendas", [Total Vendas],
    "Linhas", [Qtd Vendas],
    "AA", [Vendas AA]
)
ORDER BY 'Calendario'[Ano]
```

E na origem:

```python
df.groupby(df["data"].dt.year)["valor"].agg(["sum", "count"])
```

## Modelo

- [ ] Relacionamentos 1:* com filtro único; nenhum muitos-para-muitos sem justificativa.
- [ ] Calendário marcado como tabela de datas, contínuo, anos completos; Data/hora automática desligada.
- [ ] Chaves e colunas técnicas ocultas; nomes em português de negócio; descrições nas medidas.
- [ ] Formatos definidos em todas as medidas; pastas de exibição organizadas.
- [ ] Sem colunas não usadas; tipos corretos (códigos como texto).

## Desempenho

- [ ] Nenhum visual acima de ~1 s no Performance Analyzer (ou `AnalyzeDAXQuery`).
- [ ] Tamanho do modelo compatível com a capacidade/licença.

## Segurança e governança

- [ ] RLS testado com "Exibir como" para pelo menos um usuário de cada papel.
- [ ] Nenhum dado pessoal desnecessário visível; colunas sensíveis removidas ou mascaradas.
- [ ] Credenciais não gravadas em parâmetros versionados.
- [ ] Publicação somente no workspace autorizado, com atualização agendada configurada pelo responsável.

## Relatório

- [ ] Abriu no Desktop e cada página renderiza sem erro.
- [ ] Filtros sincronizados entre páginas e botão de limpar.
- [ ] Data de atualização e fontes visíveis.
- [ ] Texto alternativo e ordem de tabulação definidos.

Na resposta ao usuário, separe: aplicado no modelo / validado por DAX / entregue como artefato para aplicar / não verificado.
