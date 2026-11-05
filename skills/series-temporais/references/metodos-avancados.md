# Métodos avançados de séries temporais

## Sumário
1. Decomposição e múltiplas sazonalidades
2. Variáveis externas e feriados
3. Muitas séries (ML global)
4. Hierarquia e reconciliação
5. Demanda intermitente
6. Anomalias e mudança estrutural
7. Comparação de períodos
8. Bibliotecas

## 1. Decomposição e múltiplas sazonalidades

- `statsmodels.tsa.seasonal.STL(y, period=m, robust=True)` para uma sazonalidade; `MSTL(y, periods=(7, 365))` para semana + ano em dados diários.
- Força de sazonalidade = 1 − Var(resíduo)/Var(sazonal + resíduo). Acima de 0,6 a sazonalidade domina; o `serie.py diagnostico` já calcula.
- Transformação log ou Box-Cox quando a amplitude sazonal cresce com o nível (sazonalidade multiplicativa).

## 2. Variáveis externas e feriados

- SARIMAX: `SARIMAX(y, exog=X, order=..., seasonal_order=...)`. As variáveis exógenas precisam existir no futuro (calendário, preço planejado, campanhas agendadas). Variável que só se conhece depois não serve.
- Feriados brasileiros: pacote `holidays` (`holidays.Brazil(subdiv="SP", years=...)`) para criar colunas indicadoras, incluindo vésperas e pontes quando o negócio sente.
- Prophet (`prophet`) aceita feriados e regressores, mas compare com ETS/SARIMA no mesmo backtest; não é melhor por padrão.

## 3. Muitas séries (ML global)

Para centenas de produtos ou lojas, um modelo global de gradient boosting (LightGBM) com variáveis de defasagem (`lag_1`, `lag_7`, `lag_364`), médias móveis deslocadas, calendário e identificador da série costuma vencer modelos individuais.

- Calcule defasagens e janelas com `shift` antes do `rolling`, por série (`groupby('serie')`), para não vazar.
- Valide com corte temporal único para todas as séries, respeitando o horizonte (para prever 7 dias à frente, a menor defasagem é 7 ou a previsão é recursiva).
- Bibliotecas: `mlforecast`, `statsforecast` e `neuralforecast` (Nixtla), `sktime`, `darts`.

## 4. Hierarquia e reconciliação

Total = soma das regiões = soma das lojas. Previsões independentes não somam. Use reconciliação (bottom-up, top-down por proporção histórica, ou MinT em `hierarchicalforecast`) e mostre a diferença.

## 5. Demanda intermitente

Muitos zeros (peças, itens de cauda longa): Croston, SBA ou TSB (`statsforecast`). Avalie com MAE e viés, nunca MAPE. Muitas vezes o mais útil é prever a probabilidade de venda e o tamanho separadamente.

## 6. Anomalias e mudança estrutural

- Ponto fora do normal: z robusto do resíduo STL (|z| > 3,5), já no `diagnostico`. Para fluxo contínuo, compare com a previsão de um passo e o intervalo.
- Mudança de nível ou tendência: `ruptures` (PELT, Binseg) ou teste de Chow em data candidata.
- Efeito de intervenção (campanha, mudança de preço): série interrompida com variável degrau/rampa no SARIMAX, ou modelo estrutural bayesiano (`tfcausalimpact`) com séries de controle não afetadas.

## 7. Comparação de períodos

- Mês contra mês do ano anterior, acumulado no ano contra acumulado do ano anterior até a mesma data, média móvel de 3/12 meses para suavizar.
- Ajuste por dias úteis quando o mês tem número diferente de dias de operação: compare médias diárias.
- Em DAX: `SAMEPERIODLASTYEAR`, `DATESYTD`, `DATEADD`, `DATESINPERIOD` (ver skill `power-bi-mcp`).

## 8. Bibliotecas

| Biblioteca | Para quê |
|---|---|
| statsmodels (instalada) | STL/MSTL, ETS, SARIMAX, Theta, testes |
| statsforecast | AutoARIMA/AutoETS rápidos para muitas séries, intermitente |
| mlforecast / lightgbm | modelos globais com defasagens |
| prophet | sazonalidades múltiplas e feriados com poucos ajustes |
| sktime / darts | interface única para muitos modelos e validação |
| ruptures | pontos de mudança |
| holidays | feriados nacionais, estaduais e municipais |

Instale só o que a análise precisar e registre a versão.
