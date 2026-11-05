"""Séries temporais: diagnóstico, backtest sem vazamento e previsão com intervalo empírico.

Subcomandos:
  diagnostico  frequência, lacunas, tendência, sazonalidade (STL), estacionariedade (ADF/KPSS), anomalias
  backtest     compara modelos em janelas expansivas (origem móvel); cada previsão só vê o passado
  prever       ajusta o modelo (ou o melhor do backtest) em toda a série e projeta o horizonte

Exemplos:
  python serie.py diagnostico vendas.csv --data data --valor valor --freq D --saida diag.json
  python serie.py backtest vendas.csv --data data --valor valor --freq D --sazonal 7 --horizonte 14 --saida bt.json
  python serie.py prever vendas.csv --data data --valor valor --freq MS --sazonal 12 --horizonte 6 --saida prev.csv

--freq usa os códigos do pandas: D (dia), W (semana), MS (mês, início), QS (trimestre), h (hora).
Se a tabela tiver várias linhas por período, use --agregar soma|media|contagem.
"""
from __future__ import annotations

import argparse
import sys
import warnings

import numpy as np
import pandas as pd

from io_br import guard_output, read_table, write_json

warnings.filterwarnings("ignore")


def _quiet():
    """statsmodels força avisos de convergência no import; silencia só durante o ajuste."""
    ctx = warnings.catch_warnings()
    ctx.__enter__()
    warnings.simplefilter("ignore")
    return ctx

# ---------------------------------------------------------------- preparação

def prepare_series(df: pd.DataFrame, date: str, value: str, freq: str | None = None,
                   agg: str | None = None, fill: str = "nenhum") -> tuple[pd.Series, dict]:
    for c in (date, value):
        if c not in df.columns:
            raise KeyError(f"Coluna inexistente: {c}")
    d = pd.to_datetime(df[date], dayfirst=True, errors="coerce")
    v = pd.to_numeric(df[value], errors="coerce") if agg != "contagem" else pd.Series(1.0, index=df.index)
    bad_dates = int(d.isna().sum())
    s = pd.Series(v.values, index=d.values).loc[lambda x: x.index.notna()].sort_index()
    info = {"datas_invalidas": bad_dates, "valores_nulos": int(s.isna().sum())}
    dup = int(s.index.duplicated().sum())
    info["datas_repetidas"] = dup
    if freq is None:
        freq = pd.infer_freq(s.index.unique()[:500]) if s.index.nunique() >= 3 else None
        if freq is None:
            raise ValueError("Não foi possível inferir a frequência; informe --freq")
    info["frequencia"] = freq
    if dup or agg:
        how = {"soma": "sum", "media": "mean", "contagem": "sum", None: "sum"}[agg]
        if dup and not agg:
            raise ValueError(f"{dup} datas repetidas; informe --agregar soma|media|contagem")
        s = s.resample(freq).agg(how)
        if how == "sum":  # resample com soma transforma período sem dados em 0; preserva lacuna real como nulo
            counts = pd.Series(1, index=pd.DatetimeIndex(d.dropna())).resample(freq).count()
            s[counts.reindex(s.index, fill_value=0) == 0] = np.nan
    else:
        s = s.asfreq(freq)
    info["periodos"] = len(s)
    info["lacunas"] = int(s.isna().sum())
    info["inicio"], info["fim"] = s.index.min(), s.index.max()
    if fill == "interpolar":
        s = s.interpolate(limit_direction="both")
    elif fill == "zero":
        s = s.fillna(0.0)
    elif fill == "anterior":
        s = s.ffill().bfill()
    info["preenchimento"] = fill
    return s, info

# ---------------------------------------------------------------- diagnóstico

def diagnose(s: pd.Series, season: int | None = None, z: float = 3.5) -> dict:
    out = {}
    y = s.dropna()
    if len(y) < 8:
        raise ValueError("Série curta demais para diagnóstico (mínimo 8 pontos)")
    t = np.arange(len(y))
    slope = np.polyfit(t, y.values, 1)[0]
    from scipy.stats import kendalltau
    tau, p = kendalltau(t, y.values)
    out["tendencia"] = {"inclinacao_por_periodo": slope, "kendall_tau": tau, "p_valor": p,
                        "leitura": "crescente" if p < 0.05 and tau > 0 else "decrescente" if p < 0.05 and tau < 0 else "sem tendência significativa"}
    try:
        from statsmodels.tsa.stattools import adfuller, kpss
        adf_p = adfuller(y.values, autolag="AIC")[1]
        kpss_p = kpss(y.values, regression="c", nlags="auto")[1]
        out["estacionariedade"] = {"adf_p": adf_p, "kpss_p": kpss_p,
                                   "leitura": "estacionária" if adf_p < 0.05 and kpss_p > 0.05 else
                                   "não estacionária (diferenciar ou modelar tendência)" if adf_p >= 0.05 and kpss_p <= 0.05 else "inconclusivo"}
    except Exception as e:  # noqa: BLE001
        out["estacionariedade"] = {"erro": str(e)}
    resid = None
    if season and len(y) >= 2 * season + 1 and s.isna().sum() == 0:
        from statsmodels.tsa.seasonal import STL
        r = STL(y, period=season, robust=True).fit()
        var_r = np.var(r.resid)
        out["sazonalidade"] = {
            "periodo": season,
            "forca_tendencia": max(0.0, 1 - var_r / np.var(r.trend + r.resid)),
            "forca_sazonal": max(0.0, 1 - var_r / np.var(r.seasonal + r.resid)),
        }
        idx = pd.Series(r.seasonal.values, index=y.index)
        pos = np.arange(len(idx)) % season
        perfil = idx.groupby(pos).mean()
        out["sazonalidade"]["perfil_medio_por_posicao"] = perfil.round(4).tolist()
        resid = pd.Series(r.resid.values, index=y.index)
    elif season:
        out["sazonalidade"] = {"aviso": "precisa de 2 ciclos completos e série sem lacunas (use --preencher)"}
    base = resid if resid is not None else y - y.rolling(7, center=True, min_periods=1).median()
    med = np.median(base)
    mad = np.median(np.abs(base - med)) or np.std(base) or 1.0
    rz = 0.6745 * (base - med) / mad
    an = rz[np.abs(rz) > z]
    out["anomalias"] = [{"data": i, "valor": float(y.loc[i]), "z_robusto": float(rz.loc[i])} for i in an.index]
    out["autocorrelacao"] = {f"lag_{k}": float(y.autocorr(k)) for k in sorted({1, 2, season or 1, 2 * (season or 1)}) if k < len(y) - 2}
    return out

# ---------------------------------------------------------------- modelos

def f_naive(y, h, m):
    return np.repeat(y[-1], h)


def f_mean(y, h, m):
    return np.repeat(np.mean(y), h)


def f_drift(y, h, m):
    slope = (y[-1] - y[0]) / max(len(y) - 1, 1)
    return y[-1] + slope * np.arange(1, h + 1)


def f_seasonal_naive(y, h, m):
    if not m or len(y) < m:
        return f_naive(y, h, m)
    last = y[-m:]
    return np.array([last[i % m] for i in range(h)])


def f_ets(y, h, m):
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    seasonal = "add" if m and len(y) >= 2 * m else None
    model = ExponentialSmoothing(y, trend="add", damped_trend=True, seasonal=seasonal,
                                 seasonal_periods=m if seasonal else None, initialization_method="estimated")
    return model.fit(optimized=True).forecast(h)


def f_theta(y, h, m):
    from statsmodels.tsa.forecasting.theta import ThetaModel
    deseason = bool(m and m > 1 and len(y) >= 2 * m)
    return np.asarray(ThetaModel(y, period=m if deseason else 1, deseasonalize=deseason).fit().forecast(h))


def f_sarima(y, h, m):
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    seas = (1, 0, 1, m) if m and m > 1 and len(y) >= 3 * m else (0, 0, 0, 0)
    return SARIMAX(y, order=(1, 1, 1), seasonal_order=seas, enforce_stationarity=False,
                   enforce_invertibility=False).fit(disp=False).forecast(h)


MODELS = {"ingenuo": f_naive, "media": f_mean, "deriva": f_drift, "sazonal_ingenuo": f_seasonal_naive,
          "ets": f_ets, "theta": f_theta, "sarima": f_sarima}

# ---------------------------------------------------------------- métricas

def metrics(actual: np.ndarray, pred: np.ndarray, train: np.ndarray, m: int | None) -> dict:
    e = actual - pred
    nz = actual != 0
    denom = np.abs(actual) + np.abs(pred)
    lag = m if m and len(train) > m else 1
    scale = np.mean(np.abs(train[lag:] - train[:-lag])) if len(train) > lag else np.nan
    return {
        "mae": float(np.mean(np.abs(e))),
        "rmse": float(np.sqrt(np.mean(e ** 2))),
        "mape_pct": float(np.mean(np.abs(e[nz] / actual[nz])) * 100) if nz.any() else None,
        "smape_pct": float(np.mean(np.where(denom == 0, 0, 2 * np.abs(e) / np.where(denom == 0, 1, denom))) * 100),
        "vies": float(np.mean(pred - actual)),
        "mase": float(np.mean(np.abs(e)) / scale) if scale and np.isfinite(scale) and scale > 0 else None,
    }


def backtest(s: pd.Series, horizon: int, season: int | None = None, min_train: int | None = None,
             step: int | None = None, models: list[str] | None = None) -> tuple[dict, pd.DataFrame]:
    if s.isna().any():
        raise ValueError("Série com lacunas: decida o tratamento (--preencher interpolar|zero|anterior) antes do backtest")
    y = s.values.astype(float)
    n = len(y)
    min_train = min_train or max(2 * (season or 1), 3 * horizon, 10)
    step = step or horizon
    if n < min_train + horizon:
        raise ValueError(f"Série com {n} pontos; precisa de pelo menos {min_train + horizon} (treino mínimo + horizonte)")
    models = models or list(MODELS)
    rows, errors = [], {}
    for origin in range(min_train, n - horizon + 1, step):
        train, test = y[:origin], y[origin:origin + horizon]  # o modelo só recebe o passado
        for name in models:
            ctx = _quiet()
            try:
                pred = np.asarray(MODELS[name](train.copy(), horizon, season), dtype=float)
                if not np.all(np.isfinite(pred)):
                    raise ValueError("previsão não finita")
            except Exception as e:  # noqa: BLE001
                errors.setdefault(name, str(e))
                continue
            finally:
                ctx.__exit__(None, None, None)
            for k in range(horizon):
                rows.append({"modelo": name, "origem": s.index[origin - 1], "data": s.index[origin + k],
                             "passo": k + 1, "real": test[k], "previsto": pred[k]})
    fc = pd.DataFrame(rows)
    if fc.empty:
        raise RuntimeError(f"Nenhum modelo rodou: {errors}")
    summary = {}
    for name, g in fc.groupby("modelo"):
        train_scale = y[:min_train]
        summary[name] = metrics(g["real"].values, g["previsto"].values, train_scale, season)
        summary[name]["origens"] = int(g["origem"].nunique())
    key = "mase" if all(v["mase"] is not None for v in summary.values()) else "mae"
    ranking = sorted(summary, key=lambda k: summary[k][key])
    base = "sazonal_ingenuo" if season else "ingenuo"
    result = {"horizonte": horizon, "sazonalidade": season, "treino_minimo": min_train, "passo": step,
              "criterio": key, "ranking": ranking, "melhor": ranking[0], "metricas": summary,
              "modelos_com_erro": errors}
    if base in summary:
        result["melhor_supera_baseline"] = summary[ranking[0]][key] < summary[base][key] or ranking[0] == base
        result["baseline"] = base
    return result, fc


def forecast(s: pd.Series, horizon: int, season: int | None, model: str, backtest_fc: pd.DataFrame | None = None,
             level: float = 0.8) -> pd.DataFrame:
    if s.isna().any():
        raise ValueError("Série com lacunas: use --preencher")
    pred = np.asarray(MODELS[model](s.values.astype(float), horizon, season), dtype=float)
    idx = pd.date_range(s.index[-1], periods=horizon + 1, freq=s.index.freq or pd.infer_freq(s.index))[1:]
    out = pd.DataFrame({"data": idx, "previsto": pred, "modelo": model})
    if backtest_fc is not None and not backtest_fc.empty:
        g = backtest_fc[backtest_fc["modelo"] == model].assign(erro=lambda d: d["real"] - d["previsto"])
        lo_q, hi_q = (1 - level) / 2, 1 - (1 - level) / 2
        q = g.groupby("passo")["erro"].quantile([lo_q, hi_q]).unstack()
        out["limite_inferior"] = [pred[i] + q.loc[i + 1, lo_q] if i + 1 in q.index else np.nan for i in range(horizon)]
        out["limite_superior"] = [pred[i] + q.loc[i + 1, hi_q] if i + 1 in q.index else np.nan for i in range(horizon)]
        out["nivel_intervalo"] = level
    return out

# ---------------------------------------------------------------- CLI

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comando", choices=["diagnostico", "backtest", "prever"])
    ap.add_argument("arquivo")
    ap.add_argument("--data", required=True), ap.add_argument("--valor", required=True)
    ap.add_argument("--freq"), ap.add_argument("--agregar", choices=["soma", "media", "contagem"])
    ap.add_argument("--preencher", default="nenhum", choices=["nenhum", "interpolar", "zero", "anterior"])
    ap.add_argument("--sazonal", type=int, help="Período sazonal: 7 diário-semanal, 12 mensal, 4 trimestral, 52 semanal")
    ap.add_argument("--horizonte", type=int, default=12)
    ap.add_argument("--treino-minimo", type=int), ap.add_argument("--passo", type=int)
    ap.add_argument("--modelos", nargs="+", choices=list(MODELS))
    ap.add_argument("--modelo", choices=list(MODELS) + ["melhor"], default="melhor")
    ap.add_argument("--nivel", type=float, default=0.8)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--sobrescrever", action="store_true")
    a = ap.parse_args(argv)
    _quiet()  # CLI: sem avisos de convergência na saída
    df = read_table(a.arquivo)
    s, info = prepare_series(df, a.data, a.valor, a.freq, a.agregar, a.preencher)
    if a.comando == "diagnostico":
        write_json({"serie": info, **diagnose(s, a.sazonal)}, a.saida, a.sobrescrever)
    elif a.comando == "backtest":
        res, fc = backtest(s, a.horizonte, a.sazonal, a.treino_minimo, a.passo, a.modelos)
        write_json({"serie": info, **res}, a.saida, a.sobrescrever)
        fc.to_csv(guard_output(a.saida.rsplit(".", 1)[0] + ".previsoes.csv", a.sobrescrever), index=False)
        print(f"melhor: {res['melhor']} ({res['criterio']}={res['metricas'][res['melhor']][res['criterio']]:.4g})")
    else:
        res, fc = backtest(s, a.horizonte, a.sazonal, a.treino_minimo, a.passo, a.modelos)
        model = res["melhor"] if a.modelo == "melhor" else a.modelo
        out = forecast(s, a.horizonte, a.sazonal, model, fc, a.nivel)
        out.to_csv(guard_output(a.saida, a.sobrescrever), index=False)
        print(f"modelo {model}; {len(out)} períodos -> {a.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
