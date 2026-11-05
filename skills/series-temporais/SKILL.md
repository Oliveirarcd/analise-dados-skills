---
name: series-temporais
description: Análise de séries temporais e previsão — tendência, sazonalidade (STL), estacionariedade (ADF/KPSS), anomalias, comparação de períodos, backtest com origem móvel sem vazamento e previsão com intervalo (ingênuo, sazonal, ETS/Holt-Winters, Theta, SARIMA). Use sempre que o usuário quiser prever vendas, demanda, receita, chamados ou qualquer indicador por dia/semana/mês, entender sazonalidade, detectar picos e quedas fora do normal, comparar ano contra ano, medir efeito de uma data ou avaliar se uma previsão é boa, mesmo que ele não fale em "série temporal".
---

# Séries temporais

Uma previsão só vale se for comparada com o que um método ingênuo faria e se cada ponto testado tiver sido previsto apenas com o passado. Esta skill garante as duas coisas com `serie.py`, que fica em `../analise-dados/scripts/` (a skill `analise-dados` precisa estar instalada junto).

## Fluxo

1. **Prepare a série.** Uma linha por período, frequência explícita (`D`, `W`, `MS`, `QS`, `h`). Várias linhas por data exigem `--agregar soma|media|contagem`. Lacunas reais ficam como nulo; decida o tratamento (`--preencher interpolar|zero|anterior`) e justifique: sem venda num domingo é zero, sem coleta é lacuna.
2. **Diagnostique.** `serie.py diagnostico` informa frequência, lacunas, tendência (Kendall), força de tendência e de sazonalidade (STL), estacionariedade (ADF e KPSS juntos), autocorrelação e anomalias por z robusto do resíduo.
3. **Faça o backtest.** `serie.py backtest` compara modelos em janelas expansivas e ranqueia por MASE (erro dividido pelo erro do ingênuo sazonal no treino: abaixo de 1 é melhor que o ingênuo). Informe se o melhor supera o baseline.
4. **Preveja.** `serie.py prever` ajusta o melhor modelo (ou `--modelo`) em toda a série e devolve o intervalo empírico tirado dos erros do backtest em cada passo do horizonte (80% por padrão, `--nivel`).
5. **Comunique.** Ponto e intervalo, horizonte, modelo, erro no backtest em unidade de negócio, premissas (sem mudança de preço, sem ruptura) e o que faria a previsão errar.

```bash
S=../analise-dados/scripts
python $S/serie.py diagnostico vendas.csv --data data --valor valor --freq D --agregar soma --preencher zero --sazonal 7 --saida diag.json
python $S/serie.py backtest serie.csv --data mes --valor receita --freq MS --sazonal 12 --horizonte 6 --saida bt.json
python $S/serie.py prever serie.csv --data mes --valor receita --freq MS --sazonal 12 --horizonte 6 --saida previsao.csv
```

`backtest` grava também `bt.previsoes.csv` (cada origem, passo, real e previsto) para gráficos de erro.

## Escolhas que mudam o resultado

| Decisão | Orientação |
|---|---|
| Período sazonal | 7 em dados diários (semana), 12 mensal, 4 trimestral, 52 semanal, 24 horário. Dados diários com efeito anual precisam de 2+ anos e modelos com múltiplas sazonalidades (MSTL, Prophet) |
| Horizonte | igual ao uso real (o planejamento é de 3 meses? horizonte 3). Erro cresce com o passo: mostre por passo |
| Treino mínimo | pelo menos 2 ciclos sazonais; `--treino-minimo` |
| Métrica | MASE para comparar modelos; MAE em R$/unidades para o negócio; MAPE só se não houver zeros; viés para saber se superestima |
| Agregação | prever no nível em que se decide (loja × mês) e conferir se a soma das partes bate com o total |

## Modelos disponíveis

`ingenuo`, `media`, `deriva`, `sazonal_ingenuo` (baselines), `ets` (Holt-Winters aditivo com tendência amortecida), `theta`, `sarima` (1,1,1)(1,0,1,m). Para além deles, veja [references/metodos-avancados.md](references/metodos-avancados.md): variáveis externas, feriados brasileiros, hierarquia, demanda intermitente, múltiplas séries com ML e detecção de mudança estrutural.

## Cuidados

- Nada do futuro entra no treino: nem médias calculadas na série inteira, nem variáveis conhecidas só depois (ex.: preço realizado). Os testes do repositório verificam isso com um modelo espião.
- Mudança estrutural (pandemia, troca de sistema, nova loja) quebra o histórico: corte, modele com variável de intervenção ou trate como série nova, e diga.
- Intervalo empírico depende de haver várias origens no backtest; com poucas, ele é pouco confiável e isso precisa ser dito.
- Comparação ano contra ano usa mesmo número de dias úteis e mesmo calendário de feriados quando isso importa (Carnaval, Páscoa mudam de mês).
- Em Power BI, as medidas de inteligência de tempo (AA, acumulado, média móvel) vêm do `modelo_estrela.py` na skill `power-bi-mcp`.
