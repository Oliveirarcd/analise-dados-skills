"""Leitura robusta de tabelas no padrão brasileiro e utilidades comuns aos scripts.

Detecta separador (; , tab |), codificação (UTF-8, UTF-8 com BOM, cp1252/latin-1),
vírgula decimal e datas dd/mm/aaaa. Mantém códigos (CNPJ, CEP, matrícula com zeros
à esquerda) como texto: a conversão numérica só acontece quando a coluna inteira
tem cara de número e não começa com zero.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")
_NUM_BR = re.compile(r"^-?(\d{1,3}(\.\d{3})+|\d+)(,\d+)?$")
_NUM_US = re.compile(r"^-?(\d{1,3}(,\d{3})+|\d+)(\.\d+)?$")
_DATE_BR = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}( \d{1,2}:\d{2}(:\d{2})?)?$")
_DATE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?")


def detect_encoding(path: Path) -> str:
    raw = Path(path).read_bytes()[:200_000]
    for enc in ENCODINGS:
        try:
            raw.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


def detect_separator(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,\t|").delimiter
    except csv.Error:
        counts = {s: sample.count(s) for s in ";,\t|"}
        return max(counts, key=counts.get)


def _looks_code(s: pd.Series) -> bool:
    """Coluna de identificador: zeros à esquerda ou máscara (CNPJ/CPF/CEP)."""
    s = s.dropna().astype(str).str.strip()
    s = s[s != ""]
    if s.empty:
        return False
    lead_zero = s.str.match(r"^0\d").mean() > 0.05
    masked = s.str.match(r"^\d{2,3}[./-]\d{3}[./-]\d{3}").mean() > 0.5
    return bool(lead_zero or masked)


def coerce_numeric(s: pd.Series) -> pd.Series:
    """Converte texto numérico (BR ou US) em float; devolve a série original se não for numérica."""
    if not (s.dtype == object or pd.api.types.is_string_dtype(s)):
        return s
    txt = s.astype("string").str.strip().str.replace(r"^R\$\s*", "", regex=True).str.replace("%", "", regex=False)
    non_empty = txt.dropna()
    non_empty = non_empty[non_empty != ""]
    if non_empty.empty or _looks_code(s):
        return s
    br = non_empty.str.match(_NUM_BR).mean()
    us = non_empty.str.match(_NUM_US).mean()
    if max(br, us) < 0.98:
        return s
    # Empate (ex.: "12" ou "1.234"): vírgula presente decide BR; sem vírgula e com ponto de milhar ambíguo prefere BR.
    has_comma = non_empty.str.contains(",", regex=False).any()
    if br >= us and (has_comma or not non_empty.str.match(r"^-?\d+\.\d+$").all()):
        out = txt.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    else:
        out = txt.str.replace(",", "", regex=False)
    return pd.to_numeric(out.replace("", pd.NA), errors="coerce").astype("float64")


def coerce_datetime(s: pd.Series) -> pd.Series:
    if not (s.dtype == object or pd.api.types.is_string_dtype(s)):
        return s
    txt = s.astype("string").str.strip()
    non_empty = txt.dropna()
    non_empty = non_empty[non_empty != ""]
    if non_empty.empty:
        return s
    if non_empty.str.match(_DATE_BR).mean() >= 0.98:
        return pd.to_datetime(txt, dayfirst=True, errors="coerce")
    if non_empty.str.match(_DATE_ISO).mean() >= 0.98:
        return pd.to_datetime(txt, errors="coerce", format="mixed")
    return s


def infer_types(df: pd.DataFrame, keep_text: list[str] | None = None) -> pd.DataFrame:
    keep_text = set(keep_text or [])
    out = df.copy()
    for col in out.columns:
        if col in keep_text:
            continue
        original = out[col]  # cada out[col] é um objeto novo no pandas 3: guardar para comparar identidade
        converted = coerce_datetime(original)
        if converted is original:
            converted = coerce_numeric(original)
        out[col] = converted
    return out


def read_table(path: str | Path, sep: str | None = None, encoding: str | None = None,
               sheet: str | int | None = 0, keep_text: list[str] | None = None,
               infer: bool = True) -> pd.DataFrame:
    """Lê CSV/TXT, Excel, Parquet ou JSON. Tudo entra como texto e depois é tipado com segurança."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    ext = path.suffix.lower()
    if ext in (".xlsx", ".xlsm", ".xls"):
        df = pd.read_excel(path, sheet_name=sheet, dtype=str)
    elif ext == ".parquet":
        return pd.read_parquet(path)
    elif ext == ".json":
        df = pd.read_json(path, dtype=False)
        df = df.astype({c: "string" for c in df.columns if df[c].dtype == object})
    else:
        encoding = encoding or detect_encoding(path)
        if sep is None:
            with open(path, encoding=encoding, errors="replace") as fh:
                sep = detect_separator(fh.read(50_000))
        df = pd.read_csv(path, sep=sep, encoding=encoding, dtype=str, keep_default_na=False,
                         na_values=["", "NA", "N/A", "#N/D", "#N/A", "null", "NULL", "-"])
    df.columns = [str(c).strip() for c in df.columns]
    return infer_types(df, keep_text) if infer else df


def to_jsonable(obj):
    """Converte tipos numpy/pandas para JSON."""
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if not np.isfinite(obj) else float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    if obj is pd.NA or obj is pd.NaT:
        return None
    return obj


def write_json(data, path: str | Path, overwrite: bool = False) -> Path:
    path = Path(path)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Saída já existe (use --sobrescrever): {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_jsonable(data), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def guard_output(path: str | Path, overwrite: bool = False) -> Path:
    path = Path(path)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Saída já existe (use --sobrescrever): {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
