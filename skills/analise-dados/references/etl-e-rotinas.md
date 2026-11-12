# ETL e rotinas de atualização

Para quando a análise vira rotina: o mesmo relatório exportado de um sistema toda semana, juntado a um histórico e entregue em painel ou planilha. A meta é que rodar de novo seja seguro (mesma entrada, mesmo resultado) e que toda mudança entre uma carga e outra tenha explicação.

## 1. Três pastas

- `entrada/`: arquivos como vieram do sistema. Nunca edite à mão; corrija na transformação.
- `tratado/`: base padronizada, de preferência em Parquet (guarda os tipos e lê rápido; requer `pyarrow`).
- `entrega/`: painel, Excel ou relatório para pessoas.

Cada rodada refaz `tratado/` e `entrega/` a partir de `entrada/`. Assim, rodar duas vezes não duplica nada.

## 2. Extração

- Escolha o arquivo pelo padrão do nome **e** pela extensão. "O mais novo da pasta" sozinho falha no dia em que alguém salva ali um histórico ou uma cópia. Fixe uma extensão por fonte: CSV para exportação de sistema e Excel só quando a fonte é mesmo uma planilha.
- Leia com `io_br.read_table` (separador, vírgula decimal, datas brasileiras, zeros à esquerda) e registre: arquivo, data de modificação e linhas lidas.
- Se o arquivo do dia não chegou, avise e **não** sobrescreva a entrega anterior.

## 3. Contrato de entrada

Valide antes de transformar: colunas obrigatórias, tipos, chave sem duplicata, valores permitidos e faixas (data dentro do período, valor não negativo).

- Problema que invalida a carga (coluna sumiu, chave duplicada) para a rotina com mensagem clara.
- Linha ruim isolada (sem chave, categoria nova) sai com aviso e contagem, sem derrubar o resto.
- `scripts/perfil.py` acha os problemas na primeira vez. Para regras fixas que rodam toda vez, o [pandera](https://github.com/unionai-oss/pandera) (MIT, opcional) escreve o contrato em código:

```python
import pandera.pandas as pa

contrato = pa.DataFrameSchema({
    "valor": pa.Column(float, pa.Check.ge(0)),
    "canal": pa.Column(str, pa.Check.isin(["Loja física", "Site", "App"])),
})
contrato.validate(df)  # erro se alguma regra falhar
```

A unicidade da chave continua conferida no pandas (`df["id"].duplicated().sum()`) ou no `perfil.py`.

## 4. Transformação

- Regras de negócio num lugar só (de-para, pesos, faixas), com data de vigência quando mudam com o tempo.
- Antes de aplicar um de-para, normalize o texto da categoria (caixa, acento, espaços). Valor que não tem regra vira aviso com contagem, nunca zero silencioso.
- Histórico mais carga atual: defina qual vence quando a mesma chave aparece nos dois (em geral, a carga atual) e conte quantas linhas foram substituídas.
- Cruzamento com cadastro: `scripts/cruzar.py` ([cruzamento-e-conciliacao.md](cruzamento-e-conciliacao.md)). Cada exclusão vai para o registro de tratamento ([qualidade-e-limpeza.md](qualidade-e-limpeza.md)).

## 5. Histórico pesado

Leia o histórico uma vez e guarde em cache (Parquet ou pickle) com uma chave formada por nome, tamanho e data do arquivo **e** um resumo (hash) do código que o transforma. Assim, se mudar o arquivo ou a regra, o cache se refaz sozinho. O cache é descartável: apagá-lo só deixa a próxima rodada mais lenta. Pickle só para cache gerado na própria máquina; nunca abra pickle recebido de outra pessoa.

## 6. Comparar com a carga anterior

- Guarde um resumo por carga (linhas, chaves distintas, soma das medidas principais, período coberto) e compare com o anterior. Variação grande sem explicação segura a entrega até alguém olhar.
- Para saber o que mudou linha a linha entre duas versões da mesma base, use o [DataComPy](https://github.com/capitalone/datacompy) (Apache-2.0, opcional). Leia as duas versões com `io_br.read_table` e compare em Python (não foi confirmado se o comando `datacompy compare` entende `;` e vírgula decimal):

```python
from datacompy.pandas import PandasCompare

cmp = PandasCompare(anterior, atual, join_columns="id", abs_tol=0.01, df1_name="anterior", df2_name="atual")
print(cmp.report())  # linhas que só existem num lado, colunas com diferença e exemplos
```

`cruzar.py` serve para tabelas diferentes (fato × cadastro); o DataComPy, para duas versões da mesma tabela.

## 7. Carga e agendamento

- Grave a entrega num arquivo temporário e só no fim troque pelo definitivo: se a rotina cair no meio, a entrega de ontem continua inteira.
- Agende um script que não pede nada na tela: no Windows, pelo Agendador de Tarefas (`schtasks`); no Linux e no macOS, pelo `cron`.
- Cada rodada deixa uma linha de registro: início, fim, arquivos lidos, linhas, avisos e resultado.
- Base que passa de alguns milhões de linhas: DuckDB ou Polars ([dados-grandes-e-sql.md](dados-grandes-e-sql.md)).
