"""Propõe um modelo estrela para o Power BI a partir de várias tabelas e gera as medidas DAX.

Para cada par de tabelas, procura colunas cujos valores estão contidos na chave
única da outra tabela (relacionamento muitos-para-um). Classifica fatos e
dimensões, recomenda tabela Calendário e escreve:

  modelo.json   tabelas, papéis, chaves, relacionamentos e medidas (pronto para o MCP do Power BI)
  modelo.md     resumo com diagrama Mermaid e alertas
  medidas.dax   tabela Calendário e medidas base + inteligência de tempo

Uso:
  python modelo_estrela.py vendas.csv lojas.csv produtos.csv --saida pasta_modelo [--contencao 0.95]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

from io_br import guard_output, read_table, write_json

KEY_HINT = re.compile(r"(^id$|^id_|_id$|^cod|codigo|^cd_|^sk_|^chave|^cnpj|^cpf|^matricula)", re.I)


def _key_cols(df: pd.DataFrame) -> list[str]:
    n = len(df)
    return [c for c in df.columns if n and df[c].notna().all() and df[c].nunique() == n
            and not pd.api.types.is_float_dtype(df[c]) and not pd.api.types.is_datetime64_any_dtype(df[c])]


def _norm(s: pd.Series) -> pd.Series:
    if pd.api.types.is_float_dtype(s) and (s.dropna() % 1 == 0).all():
        s = s.astype("Int64")
    return s.astype("string").str.strip()


def find_relationships(tables: dict[str, pd.DataFrame], containment: float = 0.95) -> list[dict]:
    keys = {t: _key_cols(df) for t, df in tables.items()}
    rels = []
    for many, dfm in tables.items():
        for one, dfo in tables.items():
            if many == one:
                continue
            for k in keys[one]:
                kv = set(_norm(dfo[k]).dropna())
                for c in dfm.columns:
                    if c in keys[many] and len(dfm) <= len(dfo):
                        continue  # chave da própria tabela não vira FK, salvo tabela maior (fato com id único)
                    if pd.api.types.is_float_dtype(dfm[c]) and not (dfm[c].dropna() % 1 == 0).all():
                        continue
                    if pd.api.types.is_datetime64_any_dtype(dfm[c]):
                        continue
                    vals = _norm(dfm[c]).dropna()
                    if vals.empty:
                        continue
                    cont = vals.isin(kv).mean()
                    name_bonus = c.lower() == k.lower() or bool(KEY_HINT.search(c))
                    if cont >= containment and (name_bonus or vals.nunique() > 1):
                        rels.append({"de_tabela": many, "de_coluna": c, "para_tabela": one, "para_coluna": k,
                                     "cardinalidade": "muitos-para-um", "contencao": round(float(cont), 4),
                                     "orfaos": int((~vals.isin(kv)).sum()), "nomes_compativeis": name_bonus,
                                     "filtro": "único (dimensão filtra fato)"})
    # mantém o melhor candidato por coluna de origem
    best = {}
    for r in sorted(rels, key=lambda r: (not r["nomes_compativeis"], -r["contencao"])):
        best.setdefault((r["de_tabela"], r["de_coluna"]), r)
    return list(best.values())


def classify(tables: dict[str, pd.DataFrame], rels: list[dict]) -> dict:
    roles = {}
    for t, df in tables.items():
        out_rels = [r for r in rels if r["de_tabela"] == t]
        in_rels = [r for r in rels if r["para_tabela"] == t]
        fk_cols = {r["de_coluna"] for r in out_rels}
        nums = [c for c in df.select_dtypes("number").columns if c not in fk_cols and not KEY_HINT.search(c)]
        dates = list(df.select_dtypes("datetime").columns)
        role = "fato" if out_rels and (nums or dates) and len(df) >= max((len(tables[r["para_tabela"]]) for r in out_rels), default=0) else \
               "dimensao" if in_rels else ("fato" if nums and dates else "dimensao")
        roles[t] = {"papel": role, "linhas": len(df), "chaves": _key_cols(df), "medidas_candidatas": nums if role == "fato" else [],
                    "colunas_data": dates}
    return roles


def _q(name: str) -> str:
    return "'" + name.replace("'", "''") + "'"


def build_measures(roles: dict) -> list[dict]:
    ms = []
    for t, info in roles.items():
        if info["papel"] != "fato":
            continue
        ms.append({"nome": f"Qtd Linhas {t}", "tabela": "_Medidas", "expressao": f"COUNTROWS({_q(t)})",
                   "formato": "#,0", "pasta": t})
        for c in info["medidas_candidatas"]:
            base = f"Total {c}"
            ms.append({"nome": base, "tabela": "_Medidas", "expressao": f"SUM({_q(t)}[{c}])", "formato": "#,0.00", "pasta": t})
            ms.append({"nome": f"Média {c}", "tabela": "_Medidas", "expressao": f"AVERAGE({_q(t)}[{c}])", "formato": "#,0.00", "pasta": t})
            if info["colunas_data"]:
                ti = f"{t}/Tempo"
                ms += [
                    {"nome": f"{base} AA", "tabela": "_Medidas", "pasta": ti, "formato": "#,0.00",
                     "expressao": f"CALCULATE([{base}], SAMEPERIODLASTYEAR('Calendario'[Data]))"},
                    {"nome": f"{base} Var % AA", "tabela": "_Medidas", "pasta": ti, "formato": "0.0%;-0.0%;0.0%",
                     "expressao": f"VAR Atual = [{base}]\nVAR Anterior = [{base} AA]\nRETURN DIVIDE(Atual - Anterior, Anterior)"},
                    {"nome": f"{base} Acum Ano", "tabela": "_Medidas", "pasta": ti, "formato": "#,0.00",
                     "expressao": f"TOTALYTD([{base}], 'Calendario'[Data])"},
                    {"nome": f"{base} Mês Anterior", "tabela": "_Medidas", "pasta": ti, "formato": "#,0.00",
                     "expressao": f"CALCULATE([{base}], DATEADD('Calendario'[Data], -1, MONTH))"},
                    {"nome": f"{base} Var % MM", "tabela": "_Medidas", "pasta": ti, "formato": "0.0%;-0.0%;0.0%",
                     "expressao": f"DIVIDE([{base}] - [{base} Mês Anterior], [{base} Mês Anterior])"},
                    {"nome": f"{base} Média Móvel 3M", "tabela": "_Medidas", "pasta": ti, "formato": "#,0.00",
                     "expressao": f"AVERAGEX(DATESINPERIOD('Calendario'[Data], MAX('Calendario'[Data]), -3, MONTH), [{base}])"},
                ]
    return ms


def calendar_dax(roles: dict) -> str | None:
    cols = [(t, c) for t, i in roles.items() if i["papel"] == "fato" for c in i["colunas_data"]]
    if not cols:
        return None
    mins = ", ".join(f"MIN({_q(t)}[{c}])" for t, c in cols)
    maxs = ", ".join(f"MAX({_q(t)}[{c}])" for t, c in cols)
    mn = f"MINX({{{mins}}}, [Value])" if len(cols) > 1 else mins
    mx = f"MAXX({{{maxs}}}, [Value])" if len(cols) > 1 else maxs
    return f"""Calendario =
VAR Inicio = DATE(YEAR({mn}), 1, 1)
VAR Fim = DATE(YEAR({mx}), 12, 31)
RETURN
ADDCOLUMNS(
    SELECTCOLUMNS(CALENDAR(Inicio, Fim), "Data", [Date]),
    "Ano", YEAR([Data]),
    "Mes Num", MONTH([Data]),
    "Mes", FORMAT([Data], "mmm", "pt-BR"),
    "Ano Mes", FORMAT([Data], "yyyy-mm"),
    "Trimestre", "T" & QUARTER([Data]),
    "Dia Semana Num", WEEKDAY([Data], 2),
    "Dia Semana", FORMAT([Data], "ddd", "pt-BR"),
    "Fim de Semana", WEEKDAY([Data], 2) > 5
)
// Marque como tabela de datas (coluna Data) e classifique Mes por Mes Num.
// Relacione 'Calendario'[Data] com: {", ".join(f"{t}[{c}]" for t, c in cols)} (use só uma ativa por fato; as outras com USERELATIONSHIP)."""


def to_markdown(roles: dict, rels: list[dict], measures: list[dict]) -> str:
    lines = ["# Modelo estrela proposto", "", "| Tabela | Papel | Linhas | Chaves |", "|---|---|---:|---|"]
    for t, i in roles.items():
        lines.append(f"| {t} | {i['papel']} | {i['linhas']} | {', '.join(i['chaves']) or '-'} |")
    lines += ["", "```mermaid", "erDiagram"]
    for r in rels:
        lines.append(f'    {r["para_tabela"]} ||--o{{ {r["de_tabela"]} : "{r["de_coluna"]}"')
    lines += ["```", "", "## Relacionamentos", ""]
    for r in rels:
        warn = f" — **{r['orfaos']} valores órfãos**" if r["orfaos"] else ""
        lines.append(f"- {r['de_tabela']}[{r['de_coluna']}] → {r['para_tabela']}[{r['para_coluna']}] "
                     f"(muitos-para-um, contenção {r['contencao']:.1%}){warn}")
    alerts = []
    facts = [t for t, i in roles.items() if i["papel"] == "fato"]
    if not facts:
        alerts.append("nenhuma tabela de fato identificada: confira se as medidas numéricas estão tipadas como número")
    for t, i in roles.items():
        if i["papel"] == "dimensao" and not i["chaves"]:
            alerts.append(f"dimensão {t} sem chave única: deduplique antes de relacionar")
    isolated = [t for t in roles if not any(t in (r["de_tabela"], r["para_tabela"]) for r in rels)]
    if isolated and len(roles) > 1:
        alerts.append(f"tabelas sem relacionamento detectado: {', '.join(isolated)}")
    if any(r["orfaos"] for r in rels):
        alerts.append("há chaves no fato sem correspondência na dimensão: aparecerão como (Em branco) nos visuais")
    if alerts:
        lines += ["", "## Alertas", ""] + [f"- {a}" for a in alerts]
    lines += ["", f"## Medidas geradas: {len(measures)}", "", "Veja `medidas.dax`. Crie a tabela `_Medidas` vazia para agrupá-las."]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivos", nargs="+")
    ap.add_argument("--saida", required=True, help="Pasta de saída")
    ap.add_argument("--contencao", type=float, default=0.95, help="Fração mínima de valores da FK presentes na chave")
    ap.add_argument("--texto", nargs="+", default=[], help="Colunas que devem continuar como texto")
    ap.add_argument("--sobrescrever", action="store_true")
    a = ap.parse_args(argv)
    tables = {Path(f).stem: read_table(f, keep_text=a.texto) for f in a.arquivos}
    rels = find_relationships(tables, a.contencao)
    roles = classify(tables, rels)
    measures = build_measures(roles)
    cal = calendar_dax(roles)
    out = Path(a.saida)
    write_json({"tabelas": roles, "relacionamentos": rels, "medidas": measures, "calendario_dax": cal},
               out / "modelo.json", a.sobrescrever)
    guard_output(out / "modelo.md", a.sobrescrever).write_text(to_markdown(roles, rels, measures), encoding="utf-8")
    dax = ([f"// ---------- Tabela calculada\n{cal}\n"] if cal else []) + \
          [f"// [{m['pasta']}] formato: {m['formato']}\n{m['nome']} =\n{m['expressao']}\n" for m in measures]
    guard_output(out / "medidas.dax", a.sobrescrever).write_text("\n".join(dax), encoding="utf-8")
    print(f"{len(roles)} tabelas, {len(rels)} relacionamentos, {len(measures)} medidas -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
