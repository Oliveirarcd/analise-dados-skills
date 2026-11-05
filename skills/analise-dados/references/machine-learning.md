# Aprendizado de máquina aplicado

## Sumário
1. Enquadramento
2. Validação sem vazamento
3. Modelos de partida
4. Métricas
5. Interpretação
6. Segmentação e anomalias
7. Entrega

## 1. Enquadramento

Defina: o que será previsto, em que momento a previsão é feita, quais variáveis existem nesse momento, qual ação muda com a previsão e quanto custa cada tipo de erro. Se uma regra simples resolve, ela é o baseline e talvez a entrega.

## 2. Validação sem vazamento

- Divida antes de qualquer transformação. Imputação, escala, codificação de categorias, seleção de variáveis e balanceamento ficam dentro de um `sklearn.pipeline.Pipeline` ajustado só no treino.
- Tempo importa → `TimeSeriesSplit` ou corte por data. Mesmo cliente em várias linhas → `GroupKFold`. Classes raras → `StratifiedKFold`.
- Desconfie de desempenho bom demais: procure variável que só existe depois do evento (data de cancelamento, status final, ID sequencial correlacionado com o tempo).
- Guarde um conjunto de teste final que não é tocado durante o ajuste de hiperparâmetros.

```python
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit, cross_validate

prep = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)), ("esc", StandardScaler())]), num_cols),
    ("cat", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=20), cat_cols),
])
modelo = Pipeline([("prep", prep), ("clf", HistGradientBoostingClassifier())])
cv = cross_validate(modelo, X.sort_index(), y, cv=TimeSeriesSplit(5), scoring=["roc_auc", "average_precision"])
```

## 3. Modelos de partida

| Problema | Baseline | Bons primeiros modelos |
|---|---|---|
| Classificação | classe majoritária, regra de negócio | regressão logística, HistGradientBoosting, LightGBM/XGBoost |
| Regressão | média/mediana por segmento | regressão linear regularizada, gradient boosting |
| Ranking/propensão | ordem por uma variável-chave | gradient boosting com métrica de ranking |

Comece simples. Ganho pequeno sobre o baseline com muito mais complexidade raramente vale a manutenção.

## 4. Métricas

- Classificação desbalanceada: PR-AUC e recall/precisão no limiar escolhido, não acurácia. Escolha o limiar pelo custo dos erros e mostre a matriz de confusão.
- Probabilidades usadas como risco: verifique calibração (`CalibratedClassifierCV`, curva de confiabilidade, Brier).
- Regressão: MAE na unidade do negócio, RMSE se erros grandes pesam mais, MAPE só sem zeros.
- Reporte por segmento relevante (região, porte, canal) para achar onde o modelo falha.

## 5. Interpretação

- Importância por permutação no conjunto de validação (`sklearn.inspection.permutation_importance`) é mais confiável que a importância interna das árvores.
- Dependência parcial / ICE para o formato da relação. SHAP (`shap`) para explicações por linha, se instalado.
- Importância não é causalidade: a variável pode ser só um marcador.

## 6. Segmentação e anomalias

- Agrupamento: padronize, teste k com silhueta e com interpretabilidade (KMeans, ou HDBSCAN para formas irregulares). Descreva cada grupo com médias e tamanhos; nomeie pelo comportamento.
- RFM para clientes: recência, frequência, valor em quintis é muitas vezes suficiente e explicável.
- Anomalias em tabela: IsolationForest ou z robusto (mediana/MAD) por segmento; em série, ver skill `series-temporais`.

## 7. Entrega

Explique em linguagem de negócio: o que o modelo prevê, quão bem (com baseline ao lado), onde erra, quais variáveis pesam, como usar (limiar, frequência de atualização) e quando retreinar (queda de desempenho, mudança de distribuição). Salve o pipeline inteiro (`joblib`) e as versões das bibliotecas.
