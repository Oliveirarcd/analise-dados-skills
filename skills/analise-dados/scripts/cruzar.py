"""Cruzamento auditado de duas tabelas.

Antes de juntar, diagnostica as chaves: nulos, duplicadas, cardinalidade real e
quantas chaves só casariam depois de normalizar (espaços, maiúsculas, acentos,
zeros à esquerda, pontuação). Depois junta com validação de cardinalidade,
reconcilia totais e grava as exceções de cada lado.

Uso:
  python cruzar.py esquerda.csv direita.csv --chaves codigo --saida cruzado.csv
       [--chave-direita cod] [--como left|inner|outer] [--cardinalidade m:1]
       [--normalizar] [--somar valor] [--sugerir-aproximado]

Gera: cruzado.csv, cruzado.auditoria.json, cruzado.so_esquerda.csv, cruzado.so_direita.csv
"""
from __future__ import annotations

import argparse
import difflib
import sys
import unicodedata
from pathlib import Path

import pandas as pd

from io_br import guard_output, read_table, write_json

CARD = {"1:1": "one_to_one", "1:m": "one_to_many", "m:1": "many_to_one", "m:m": "many_to_many"}


def normalize_key(s: pd.Series) -> pd.Series:
    """Normaliza chave de texto: sem acento, minúscula, sem pontuação/espaços, sem zeros à esquerda."""
    def _one(v):
        if pd.isna(v):
            return v
        v = unicodedata.normalize("NFKD", str(v)).encode("ascii", "ignore").decode()
        v = "".join(ch for ch in v.lower() if ch.isalnum())
        return (v.lstrip("0") or "0") if v.isdigit() else v
    return s.map(_one)


def _as_key(df: pd.DataFrame, cols: list[str], normalize: bool) -> pd.Series:
    parts = []
    for c in cols:
        s = df[c]
        if pd.api.types.is_float_dtype(s) and (s.dropna() % 1 == 0).all():
            s = s.astype("Int64")
        s = s.astype("string")
        parts.append(normalize_key(s) if normalize else s.str.strip())
    key = parts[0]
    for p in parts[1:]:
        key = key + "\x1f" + p
    return key


def diagnose(left: pd.DataFrame, right: pd.DataFrame, lk: list[str], rk: list[str]) -> dict:
    out = {}
    for side, df, keys in (("esquerda", left, lk), ("direita", right, rk)):
        missing = [k for k in keys if k not in df.columns]
        if missing:
            raise KeyError(f"Chave inexistente na {side}: {missing}")
        k = _as_key(df, keys, False)
        out[side] = {
            "linhas": len(df),
            "chaves_nulas": int(k.isna().sum()),
            "chaves_distintas": int(k.nunique()),
            "chaves_repetidas": int(k.dropna().duplicated().sum()),
            "unica": bool(k.notna().all() and not k.duplicated().any()),
        }
    kl, kr = _as_key(left, lk, False), _as_key(right, rk, False)
    nl, nr = _as_key(left, lk, True), _as_key(right, rk, True)
    raw = set(kl.dropna()) & set(kr.dropna())
    norm = set(nl.dropna()) & set(nr.dropna())
    lu, ru = out["esquerda"]["unica"], out["direita"]["unica"]
    out["cardinalidade_observada"] = {(True, True): "1:1", (False, True): "m:1", (True, False): "1:m", (False, False): "m:m"}[(lu, ru)]
    out["chaves_em_comum"] = len(raw)
    out["chaves_em_comum_normalizando"] = len(norm)
    out["ganho_com_normalizacao"] = len(norm) - len(raw)
    out["cobertura_esquerda_pct"] = round(kl.isin(raw).mean() * 100, 2) if len(kl) else 0.0
    out["cobertura_direita_pct"] = round(kr.isin(raw).mean() * 100, 2) if len(kr) else 0.0
    return out


def fuzzy_suggestions(unmatched: list[str], candidates: list[str], limit: int = 200, cutoff: float = 0.85) -> list[dict]:
    """Sugestões de pareamento aproximado (para revisão humana; nunca aplicadas automaticamente)."""
    try:
        from rapidfuzz import process, fuzz  # opcional, bem mais rápido
        res = []
        for u in unmatched[:limit]:
            m = process.extractOne(u, candidates, scorer=fuzz.WRatio, score_cutoff=cutoff * 100)
            if m:
                res.append({"chave": u, "sugestao": m[0], "similaridade": round(m[1] / 100, 3)})
        return res
    except ImportError:
        res = []
        for u in unmatched[:limit]:
            m = difflib.get_close_matches(u, candidates, n=1, cutoff=cutoff)
            if m:
                res.append({"chave": u, "sugestao": m[0], "similaridade": round(difflib.SequenceMatcher(None, u, m[0]).ratio(), 3)})
        return res


def audited_join(left: pd.DataFrame, right: pd.DataFrame, lk: list[str], rk: list[str] | None = None,
                 how: str = "left", cardinality: str | None = "m:1", normalize: bool = False,
                 sum_cols: list[str] | None = None, suggest: bool = False):
    rk = rk or lk
    if len(lk) != len(rk):
        raise ValueError("Número de colunas de chave diferente entre os lados")
    diag = diagnose(left, right, lk, rk)
    if cardinality and cardinality not in CARD:
        raise ValueError(f"Cardinalidade inválida: {cardinality} (use 1:1, 1:m, m:1, m:m)")
    L, R = left.copy(), right.copy()
    L["__k"], R["__k"] = _as_key(L, lk, normalize), _as_key(R, rk, normalize)
    nulls_l = L["__k"].isna()
    R = R[R["__k"].notna()]
    try:
        merged = L.merge(R, on="__k", how=how,
                         suffixes=("", "_dir"), indicator="__origem",
                         validate=CARD[cardinality] if cardinality else None)
    except pd.errors.MergeError as e:
        raise ValueError(f"Cardinalidade esperada {cardinality} violada: {e}. Observada: {diag['cardinalidade_observada']}. "
                         "Deduplique ou agregue o lado repetido antes de cruzar.") from e
    only_left = L[~L["__k"].isin(R["__k"])].drop(columns="__k")
    only_right = R[~R["__k"].isin(L["__k"])].drop(columns="__k")
    audit = {"diagnostico": diag, "parametros": {"chaves_esquerda": lk, "chaves_direita": rk, "como": how,
             "cardinalidade_esperada": cardinality, "normalizar": normalize},
             "resultado": {"linhas_saida": len(merged),
                           "casadas": int((merged["__origem"] == "both").sum()),
                           "so_esquerda": int((merged["__origem"] == "left_only").sum()),
                           "so_direita": int((merged["__origem"] == "right_only").sum()),
                           "linhas_esquerda_com_chave_nula": int(nulls_l.sum())}}
    if how == "left" and len(merged) != len(left):
        audit["resultado"]["alerta"] = "número de linhas da esquerda mudou: a direita tem chave repetida"
    if sum_cols:
        rec = {}
        for c in sum_cols:
            if c in left.columns:
                before = float(pd.to_numeric(left[c], errors="coerce").sum())
                after_col = c if c in merged.columns else None
                after = float(pd.to_numeric(merged.loc[merged["__origem"] != "right_only", after_col], errors="coerce").sum()) if after_col else None
                rec[c] = {"origem": before, "apos_cruzamento": after, "diferenca": None if after is None else round(after - before, 6)}
        audit["reconciliacao"] = rec
    if suggest and len(only_left):
        ul = only_left.pipe(lambda d: _as_key(d, lk, True)).dropna().unique().tolist()
        cands = _as_key(only_right, rk, True).dropna().unique().tolist() if len(only_right) else []
        audit["sugestoes_aproximadas"] = fuzzy_suggestions(ul, cands) if cands else []
    merged = merged.drop(columns="__k").rename(columns={"__origem": "_origem"})
    merged["_origem"] = merged["_origem"].map({"both": "ambos", "left_only": "so_esquerda", "right_only": "so_direita"})
    return merged, audit, only_left, only_right


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("esquerda"), ap.add_argument("direita")
    ap.add_argument("--chaves", nargs="+", required=True)
    ap.add_argument("--chave-direita", nargs="+")
    ap.add_argument("--como", default="left", choices=["left", "inner", "outer"])
    ap.add_argument("--cardinalidade", default="m:1", help="1:1, 1:m, m:1, m:m ou 'nenhuma'")
    ap.add_argument("--normalizar", action="store_true", help="Casar chaves ignorando acento, caixa, pontuação e zeros à esquerda")
    ap.add_argument("--somar", nargs="+", help="Colunas numéricas para reconciliar totais")
    ap.add_argument("--sugerir-aproximado", action="store_true")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--sobrescrever", action="store_true")
    a = ap.parse_args(argv)
    keep = list(set(a.chaves + (a.chave_direita or [])))
    L = read_table(a.esquerda, keep_text=keep)
    R = read_table(a.direita, keep_text=keep)
    card = None if a.cardinalidade == "nenhuma" else a.cardinalidade
    merged, audit, ol, orr = audited_join(L, R, a.chaves, a.chave_direita, a.como, card, a.normalizar, a.somar, a.sugerir_aproximado)
    out = Path(a.saida)
    stem = out.with_suffix("")
    for path, df in ((out, merged), (Path(f"{stem}.so_esquerda.csv"), ol), (Path(f"{stem}.so_direita.csv"), orr)):
        df.to_csv(guard_output(path, a.sobrescrever), index=False, sep=";", decimal=",", encoding="utf-8-sig")
    write_json(audit, f"{stem}.auditoria.json", a.sobrescrever)
    r = audit["resultado"]
    print(f"casadas {r['casadas']}, só esquerda {r['so_esquerda']}, só direita {r['so_direita']} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
