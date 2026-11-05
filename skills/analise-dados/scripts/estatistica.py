"""Testes estatísticos com escolha justificada e tamanho de efeito.

Subcomandos:
  comparar     variável numérica entre grupos (2 grupos: Welch ou Mann-Whitney; 3+: ANOVA/Welch ou Kruskal-Wallis)
  associacao   duas variáveis categóricas (qui-quadrado ou Fisher) com V de Cramér
  correlacao   matriz de Pearson e Spearman com p-valores corrigidos (Holm)
  ab           teste A/B de proporções (conversões / total por grupo)

Exemplos:
  python estatistica.py comparar dados.csv --valor ticket --grupo regiao --saida comp.json
  python estatistica.py associacao dados.csv --x canal --y churn --saida assoc.json
  python estatistica.py correlacao dados.csv --colunas preco qtd desconto --saida corr.json
  python estatistica.py ab --conversoes 120 150 --totais 2400 2410 --saida ab.json
"""
from __future__ import annotations

import argparse
import itertools
import sys

import numpy as np
import pandas as pd
from scipy import stats

from io_br import read_table, write_json


def holm(pvals: list[float]) -> list[float]:
    order = np.argsort(pvals)
    m = len(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj.tolist()


def compare_groups(df: pd.DataFrame, value: str, group: str, alpha: float = 0.05, min_n: int = 3) -> dict:
    d = df[[value, group]].dropna()
    groups = {str(k): g[value].astype(float).values for k, g in d.groupby(group)}
    small = [k for k, v in groups.items() if len(v) < min_n]
    groups = {k: v for k, v in groups.items() if len(v) >= min_n}
    if len(groups) < 2:
        raise ValueError("Precisa de pelo menos 2 grupos com dados suficientes")
    desc = {k: {"n": len(v), "media": v.mean(), "mediana": np.median(v), "desvio": v.std(ddof=1)} for k, v in groups.items()}
    normal = all(len(v) > 50 or (len(v) >= 3 and stats.shapiro(v).pvalue > alpha) for v in groups.values())
    vals = list(groups.values())
    out = {"descritivas": desc, "grupos_ignorados_por_n_pequeno": small, "normalidade_aproximada": normal}
    if len(vals) == 2:
        a, b = vals
        if normal:
            r = stats.ttest_ind(a, b, equal_var=False)
            pooled = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
            eff = {"d_cohen": (a.mean() - b.mean()) / pooled if pooled else None}
            ci = r.confidence_interval(1 - alpha)
            out.update(teste="t de Welch", estatistica=r.statistic, p_valor=r.pvalue,
                       ic_diferenca_medias=[ci.low, ci.high], efeito=eff)
        else:
            r = stats.mannwhitneyu(a, b, alternative="two-sided")
            out.update(teste="Mann-Whitney U", estatistica=r.statistic, p_valor=r.pvalue,
                       efeito={"correlacao_rank_biserial": 1 - 2 * r.statistic / (len(a) * len(b))})
    else:
        if normal:
            r = stats.f_oneway(*vals)
            grand = np.concatenate(vals)
            ss_b = sum(len(v) * (v.mean() - grand.mean()) ** 2 for v in vals)
            ss_t = ((grand - grand.mean()) ** 2).sum()
            out.update(teste="ANOVA de um fator", estatistica=r.statistic, p_valor=r.pvalue,
                       efeito={"eta_quadrado": ss_b / ss_t if ss_t else None})
        else:
            r = stats.kruskal(*vals)
            n = sum(len(v) for v in vals)
            out.update(teste="Kruskal-Wallis", estatistica=r.statistic, p_valor=r.pvalue,
                       efeito={"epsilon_quadrado": r.statistic / (n - 1)})
        pairs = list(itertools.combinations(groups, 2))
        ps = [(stats.ttest_ind(groups[x], groups[y], equal_var=False) if normal else
               stats.mannwhitneyu(groups[x], groups[y])).pvalue for x, y in pairs]
        out["pares_holm"] = [{"a": x, "b": y, "p_ajustado": p} for (x, y), p in zip(pairs, holm(ps))]
    out["significativo"] = out["p_valor"] < alpha
    out["leitura"] = ("diferença estatisticamente significativa" if out["significativo"] else
                      "sem evidência de diferença") + f" (alfa={alpha}); significância não mede relevância de negócio: veja o efeito."
    return out


def association(df: pd.DataFrame, x: str, y: str, alpha: float = 0.05) -> dict:
    tab = pd.crosstab(df[x], df[y])
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        raise ValueError("Cada variável precisa de pelo menos 2 categorias")
    chi2, p, dof, exp = stats.chi2_contingency(tab)
    out = {"tabela": tab.to_dict(), "esperado_min": float(exp.min())}
    if tab.shape == (2, 2) and exp.min() < 5:
        res = stats.fisher_exact(tab.values)
        out.update(teste="exato de Fisher", odds_ratio=res.statistic, p_valor=res.pvalue)
    else:
        out.update(teste="qui-quadrado", estatistica=chi2, gl=dof, p_valor=p)
        if (exp < 5).mean() > 0.2:
            out["aviso"] = "mais de 20% das células com esperado < 5; agrupe categorias raras"
    n = tab.values.sum()
    out["v_cramer"] = float(np.sqrt(chi2 / (n * (min(tab.shape) - 1))))
    out["significativo"] = out["p_valor"] < alpha
    return out


def correlation(df: pd.DataFrame, cols: list[str] | None = None) -> dict:
    num = df[cols] if cols else df.select_dtypes("number")
    num = num.apply(pd.to_numeric, errors="coerce")
    pairs, ps = [], []
    for a, b in itertools.combinations(num.columns, 2):
        d = num[[a, b]].dropna()
        if len(d) < 4:
            continue
        pr = stats.pearsonr(d[a], d[b])
        sr = stats.spearmanr(d[a], d[b])
        pairs.append({"a": a, "b": b, "n": len(d), "pearson": pr.statistic, "spearman": sr.statistic})
        ps.append(sr.pvalue)
    for row, p in zip(pairs, holm(ps) if ps else []):
        row["p_spearman_holm"] = p
    pairs.sort(key=lambda r: -abs(r["spearman"]))
    return {"pares": pairs, "aviso": "correlação não implica causalidade; confira gráficos de dispersão e confundidores"}


def ab_test(conv: list[int], totals: list[int], alpha: float = 0.05) -> dict:
    if len(conv) != 2 or len(totals) != 2:
        raise ValueError("Informe 2 conversões e 2 totais (A e B)")
    if any(t <= 0 for t in totals) or any(c < 0 or c > t for c, t in zip(conv, totals)):
        raise ValueError("Conversões devem estar entre 0 e o total, e totais > 0")
    (ca, cb), (na, nb) = conv, totals
    pa, pb = ca / na, cb / nb
    pool = (ca + cb) / (na + nb)
    se = np.sqrt(pool * (1 - pool) * (1 / na + 1 / nb))
    z = (pb - pa) / se if se else 0.0
    p = 2 * stats.norm.sf(abs(z))
    se_d = np.sqrt(pa * (1 - pa) / na + pb * (1 - pb) / nb)
    zc = stats.norm.ppf(1 - alpha / 2)
    return {"taxa_a": pa, "taxa_b": pb, "diferenca_abs": pb - pa, "lift_relativo": (pb - pa) / pa if pa else None,
            "z": z, "p_valor": p, "ic_diferenca": [pb - pa - zc * se_d, pb - pa + zc * se_d],
            "significativo": p < alpha,
            "aviso": "pare o teste no tamanho de amostra planejado; olhar o p-valor todo dia infla falso positivo"}


def sample_size_proportions(p_base: float, mde_abs: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Tamanho por grupo para detectar diferença absoluta mde_abs."""
    p2 = p_base + mde_abs
    za, zb = stats.norm.ppf(1 - alpha / 2), stats.norm.ppf(power)
    pbar = (p_base + p2) / 2
    n = (za * np.sqrt(2 * pbar * (1 - pbar)) + zb * np.sqrt(p_base * (1 - p_base) + p2 * (1 - p2))) ** 2 / mde_abs ** 2
    return int(np.ceil(n))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comando", choices=["comparar", "associacao", "correlacao", "ab", "amostra"])
    ap.add_argument("arquivo", nargs="?")
    ap.add_argument("--valor"), ap.add_argument("--grupo"), ap.add_argument("--x"), ap.add_argument("--y")
    ap.add_argument("--colunas", nargs="+")
    ap.add_argument("--conversoes", nargs=2, type=int), ap.add_argument("--totais", nargs=2, type=int)
    ap.add_argument("--taxa-base", type=float), ap.add_argument("--efeito-minimo", type=float)
    ap.add_argument("--alfa", type=float, default=0.05)
    ap.add_argument("--saida", required=True), ap.add_argument("--sobrescrever", action="store_true")
    a = ap.parse_args(argv)
    if a.comando == "ab":
        res = ab_test(a.conversoes, a.totais, a.alfa)
    elif a.comando == "amostra":
        res = {"n_por_grupo": sample_size_proportions(a.taxa_base, a.efeito_minimo, a.alfa)}
    else:
        if not a.arquivo:
            ap.error("informe o arquivo")
        df = read_table(a.arquivo)
        if a.comando == "comparar":
            res = compare_groups(df, a.valor, a.grupo, a.alfa)
        elif a.comando == "associacao":
            res = association(df, a.x, a.y, a.alfa)
        else:
            res = correlation(df, a.colunas)
    write_json(res, a.saida, a.sobrescrever)
    print(f"ok -> {a.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
