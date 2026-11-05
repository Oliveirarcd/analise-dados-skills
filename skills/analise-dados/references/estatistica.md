# Estatística, experimentos e causalidade

## Sumário
1. Escolha do teste
2. Tamanho de efeito e relevância
3. Comparações múltiplas
4. Testes A/B
5. Regressão
6. Causalidade com dados observacionais
7. Armadilhas

## 1. Escolha do teste

| Pergunta | Dados | Teste (script) |
|---|---|---|
| Média difere entre 2 grupos? | numérico, aproximadamente normal | t de Welch (`comparar`) |
| Idem, assimétrico ou n pequeno | numérico | Mann-Whitney (`comparar`) |
| Difere entre 3+ grupos? | numérico | ANOVA ou Kruskal-Wallis + pares com Holm (`comparar`) |
| Antes × depois no mesmo indivíduo | pareado | t pareado / Wilcoxon (`scipy.stats.ttest_rel`, `wilcoxon`) |
| Duas categóricas associadas? | contagens | qui-quadrado / Fisher, V de Cramér (`associacao`) |
| Duas numéricas andam juntas? | numérico | Pearson e Spearman com Holm (`correlacao`) |
| Proporção A × B | conversões | z de duas proporções (`ab`) |
| Distribuição mudou? | numérico | Kolmogorov-Smirnov (`scipy.stats.ks_2samp`) |

`estatistica.py comparar` decide entre paramétrico e não paramétrico pelo Shapiro-Wilk (n ≤ 50) e assume normalidade aproximada acima disso (teorema central do limite). Em amostras grandes, qualquer diferença minúscula vira "significativa": o efeito é o que importa.

## 2. Tamanho de efeito e relevância

Sempre reporte a diferença na unidade do negócio (R$, dias, pontos percentuais) com intervalo de confiança, e um efeito padronizado: d de Cohen (0,2 pequeno, 0,5 médio, 0,8 grande), correlação rank-biserial, eta² ou epsilon², V de Cramér. "Significativo" sem efeito é meia resposta.

## 3. Comparações múltiplas

Testar 20 recortes a 5% gera, em média, um falso positivo. Corrija (Holm controla erro familiar; Benjamini-Hochberg controla taxa de falsas descobertas, útil em triagem) e declare quantos testes foram feitos, inclusive os que não deram nada.

## 4. Testes A/B

1. Antes: métrica principal, efeito mínimo relevante, alfa, poder → tamanho de amostra (`estatistica.py amostra`). Unidade de randomização igual à unidade de análise.
2. Durante: confira o balanceamento (sample ratio mismatch: proporção A/B muito diferente do planejado invalida o teste). Não pare quando "deu significativo"; espiar e parar infla o falso positivo. Se precisar parar cedo, use teste sequencial.
3. Depois: diferença absoluta, lift relativo, intervalo, efeito em métricas de proteção (cancelamento, reclamação) e segmentos definidos antes.

## 5. Regressão

- `statsmodels.formula.api.ols('y ~ x1 + C(regiao)', df).fit(cov_type='HC3')` para erros robustos. Para contagens, Poisson/binomial negativa; para sim/não, logística.
- Confira resíduos (padrão, heterocedasticidade), multicolinearidade (VIF > 10), pontos influentes (distância de Cook).
- Coeficiente é associação condicionada às variáveis do modelo, não efeito causal.

## 6. Causalidade com dados observacionais

| Situação | Desenho |
|---|---|
| Tratamento em um grupo a partir de uma data, com grupo comparável | diferenças em diferenças (confira tendências paralelas antes) |
| Uma unidade tratada, várias de controle | controle sintético |
| Regra de corte (nota ≥ 7 recebe benefício) | regressão descontínua |
| Série única com intervenção | série interrompida / modelo estrutural (BSTS, `CausalImpact`) |
| Muitas covariáveis observadas | pareamento por escore de propensão, ponderação, DoubleML (`econml`, `dowhy`) |

Declare as hipóteses que sustentam o desenho e teste o que for testável (placebo, períodos anteriores).

## 7. Armadilhas

- **Paradoxo de Simpson:** a relação se inverte ao segmentar. Compare agregado e por estrato.
- **Viés de sobrevivência e de seleção:** quem está na base pode não representar a população.
- **Regressão à média:** os piores do mês tendem a melhorar sozinhos.
- **Média de percentuais:** pondere pelo denominador.
- **p-hacking:** escolher recortes depois de ver os dados. Registre o plano antes.
