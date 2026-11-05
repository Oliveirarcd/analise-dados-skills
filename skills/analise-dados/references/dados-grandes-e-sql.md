# Dados grandes, SQL e DuckDB

## Quando sair do pandas

Os scripts carregam a base em memória. Regra prática: se o arquivo passa de um terço da RAM livre, ou são vários arquivos somando gigabytes, use DuckDB ou Polars, e só traga para o pandas o resultado agregado.

## DuckDB (SQL direto em CSV, Parquet e Excel)

```python
import duckdb
con = duckdb.connect()  # em memória; use um arquivo .duckdb para persistir
con.sql("""
    SELECT date_trunc('month', data) AS mes, regiao, sum(valor) AS total, count(*) AS linhas
    FROM read_csv('vendas_*.csv', delim=';', decimal_separator=',', dateformat='%d/%m/%Y', header=true)
    JOIN read_parquet('lojas.parquet') USING (cod_loja)
    GROUP BY ALL ORDER BY mes
""").df()
```

- `read_csv` com glob lê vários arquivos de uma vez; `union_by_name=true` alinha colunas diferentes.
- Converta CSVs grandes para Parquet uma vez (`COPY (SELECT ...) TO 'base.parquet' (FORMAT parquet)`) e trabalhe sobre o Parquet.
- Confira cardinalidade em SQL antes de juntar: `SELECT chave, count(*) FROM t GROUP BY 1 HAVING count(*) > 1`.

## MCP de banco de dados

Para consultar DuckDB/MotherDuck pelo agente, existe o servidor oficial `mcp-server-motherduck` (https://github.com/motherduckdb/mcp-server-motherduck). Exemplo de configuração local, sem nuvem, está em `mcp/duckdb.mcp.json` na raiz do repositório. Prefira modo somente leitura sobre cópias dos dados.

Para bancos corporativos (SQL Server, Postgres, Snowflake, BigQuery, Databricks), use o conector oficial do fornecedor ou o plugin `data` da Anthropic, que já traz os endereços. Nunca grave senha em arquivo do repositório; use variável de ambiente ou o cofre do sistema.

## Boas práticas de SQL analítico

- CTEs nomeadas por etapa (`WITH base AS (...), limpos AS (...)`), uma regra por etapa.
- Filtre cedo, agregue no nível certo antes de juntar, use `QUALIFY row_number() OVER (...) = 1` para deduplicar por regra explícita.
- Funções de janela para acumulados, médias móveis e variação contra o período anterior (`lag`).
- Datas: trunque com `date_trunc`, gere calendário completo com `generate_series` para não perder períodos sem movimento.
