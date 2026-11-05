"""Perfil e qualidade de uma tabela: tipos, nulos, chaves candidatas, outliers e alertas.

Uso:
  python perfil.py dados.csv --saida perfil.json [--chaves id] [--md perfil.md]

O perfil não exporta linhas individuais: só agregados e, para colunas de texto,
os valores mais frequentes (use --sem-exemplos em dados sensíveis).
"""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from io_br import guard_output, read_table, write_json


def _iqr_outliers(s: pd.Series) -> int:
    s = s.dropna()
    if len(s) < 8:
        return 0
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    if iqr == 0:
        return 0
    return int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())


def profile_column(s: pd.Series, examples: bool = True) -> dict:
    n = len(s)
    nulls = int(s.isna().sum())
    info = {
        "tipo": str(s.dtype),
        "nulos": nulls,
        "pct_nulos": round(nulls / n * 100, 2) if n else 0.0,
        "distintos": int(s.nunique(dropna=True)),
    }
    alerts = []
    if n and nulls == n:
        alerts.append("coluna vazia")
    elif info["distintos"] == 1:
        alerts.append("valor constante")
    if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
        d = s.dropna()
        if not d.empty:
            info.update({
                "min": d.min(), "p25": d.quantile(0.25), "mediana": d.median(), "media": d.mean(),
                "p75": d.quantile(0.75), "max": d.max(), "desvio": d.std(),
                "zeros": int((d == 0).sum()), "negativos": int((d < 0).sum()),
                "outliers_iqr": _iqr_outliers(d),
            })
            if info["outliers_iqr"] > 0.05 * len(d):
                alerts.append("muitos outliers (>5% pelo IQR)")
    elif pd.api.types.is_datetime64_any_dtype(s):
        d = s.dropna()
        if not d.empty:
            info.update({"min": d.min(), "max": d.max(), "dias_cobertos": int((d.max() - d.min()).days) + 1})
            if d.max() > pd.Timestamp.now() + pd.Timedelta(days=1):
                alerts.append("datas no futuro")
            if d.min() < pd.Timestamp("1900-01-01"):
                alerts.append("datas anteriores a 1900")
    else:
        txt = s.dropna().astype(str)
        if not txt.empty:
            stripped = txt.str.strip()
            info["comprimento_min"] = int(txt.str.len().min())
            info["comprimento_max"] = int(txt.str.len().max())
            ws = int((txt != stripped).sum())
            if ws:
                info["com_espacos_nas_pontas"] = ws
                alerts.append("espaços no início/fim")
            case_groups = stripped.str.lower().nunique()
            if case_groups < stripped.nunique():
                info["variantes_maiusc_minusc"] = int(stripped.nunique() - case_groups)
                alerts.append("mesmo valor com grafias diferentes (maiúsculas/minúsculas)")
            if examples:
                info["mais_frequentes"] = stripped.value_counts().head(5).to_dict()
    info["alertas"] = alerts
    return info


def candidate_keys(df: pd.DataFrame, max_combo: int = 2, max_cols: int = 30) -> list[list[str]]:
    """Colunas (ou pares) sem nulos e sem repetição."""
    n = len(df)
    cols = [c for c in df.columns if df[c].notna().all()][:max_cols]
    keys = [[c] for c in cols if df[c].nunique() == n]
    if keys or max_combo < 2:
        return keys
    for a, b in itertools.combinations(cols, 2):
        if not df.duplicated([a, b]).any():
            keys.append([a, b])
        if len(keys) >= 5:
            break
    return keys


def profile(df: pd.DataFrame, keys: list[str] | None = None, examples: bool = True) -> dict:
    result = {
        "linhas": len(df),
        "colunas": df.shape[1],
        "memoria_mb": round(df.memory_usage(deep=True).sum() / 1e6, 2),
        "linhas_duplicadas": int(df.duplicated().sum()),
        "colunas_detalhe": {c: profile_column(df[c], examples) for c in df.columns},
    }
    if keys:
        missing = [k for k in keys if k not in df.columns]
        if missing:
            raise KeyError(f"Chave inexistente: {missing}")
        dup = int(df.duplicated(keys).sum())
        nulls = int(df[keys].isna().any(axis=1).sum())
        result["chave_informada"] = {"colunas": keys, "duplicadas": dup, "nulas": nulls, "valida": dup == 0 and nulls == 0}
    else:
        result["chaves_candidatas"] = candidate_keys(df)
    alerts = []
    if result["linhas_duplicadas"]:
        alerts.append(f"{result['linhas_duplicadas']} linhas totalmente duplicadas")
    if keys and not result["chave_informada"]["valida"]:
        alerts.append("chave informada não é única ou tem nulos")
    for c, info in result["colunas_detalhe"].items():
        alerts += [f"{c}: {a}" for a in info["alertas"]]
    num = df.select_dtypes("number")
    if num.shape[1] >= 2:
        corr = num.corr().abs()
        high = [(a, b, round(corr.loc[a, b], 3)) for a, b in itertools.combinations(corr.columns, 2) if corr.loc[a, b] >= 0.95]
        if high:
            result["correlacoes_altas"] = high
            alerts += [f"{a} e {b} quase redundantes (|r|={r})" for a, b, r in high]
    result["alertas"] = alerts
    return result


def to_markdown(p: dict, name: str) -> str:
    lines = [f"# Perfil de `{name}`", "", f"- Linhas: {p['linhas']:,}".replace(",", "."),
             f"- Colunas: {p['colunas']}", f"- Linhas duplicadas: {p['linhas_duplicadas']}", ""]
    if "chave_informada" in p:
        ck = p["chave_informada"]
        lines.append(f"- Chave {ck['colunas']}: {'válida' if ck['valida'] else 'INVÁLIDA'} (duplicadas {ck['duplicadas']}, nulas {ck['nulas']})")
    elif p.get("chaves_candidatas"):
        lines.append(f"- Chaves candidatas: {p['chaves_candidatas']}")
    lines += ["", "| Coluna | Tipo | % nulos | Distintos | Alertas |", "|---|---|---:|---:|---|"]
    for c, i in p["colunas_detalhe"].items():
        lines.append(f"| {c} | {i['tipo']} | {i['pct_nulos']} | {i['distintos']} | {'; '.join(i['alertas'])} |")
    if p["alertas"]:
        lines += ["", "## Alertas", ""] + [f"- {a}" for a in p["alertas"]]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivo")
    ap.add_argument("--saida", required=True, help="JSON de saída")
    ap.add_argument("--md", help="Resumo em Markdown")
    ap.add_argument("--chaves", nargs="+", help="Colunas que deveriam identificar cada linha")
    ap.add_argument("--sep"), ap.add_argument("--encoding"), ap.add_argument("--aba", default=0)
    ap.add_argument("--texto", nargs="+", default=[], help="Colunas que devem continuar como texto")
    ap.add_argument("--sem-exemplos", action="store_true", help="Não incluir valores frequentes")
    ap.add_argument("--sobrescrever", action="store_true")
    a = ap.parse_args(argv)
    df = read_table(a.arquivo, a.sep, a.encoding, a.aba, keep_text=a.texto)
    p = profile(df, a.chaves, not a.sem_exemplos)
    write_json(p, a.saida, a.sobrescrever)
    if a.md:
        guard_output(a.md, a.sobrescrever).write_text(to_markdown(p, Path(a.arquivo).name), encoding="utf-8")
    print(f"{p['linhas']} linhas, {p['colunas']} colunas, {len(p['alertas'])} alertas -> {a.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
