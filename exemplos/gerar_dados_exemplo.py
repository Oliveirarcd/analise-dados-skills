"""Gera dados 100% sintéticos para testar as skills (nenhum dado real).

Cria em exemplos/dados/:
  vendas.csv    fato diário de vendas (padrão brasileiro: ; e vírgula decimal, datas dd/mm/aaaa)
  lojas.csv     dimensão de lojas (códigos com zeros à esquerda)
  produtos.csv  dimensão de produtos
  serie_mensal.csv  série mensal com tendência e sazonalidade

Uso: python exemplos/gerar_dados_exemplo.py [--semente 42]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def generate(seed: int = 42) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    lojas = pd.DataFrame({
        "cod_loja": [f"{i:04d}" for i in range(1, 13)],
        "nome_loja": [f"Loja {c}" for c in "ABCDEFGHIJKL"],
        "regiao": ["Sudeste"] * 5 + ["Sul"] * 3 + ["Nordeste"] * 2 + ["Centro-Oeste", "Norte"],
        "uf": ["SP", "SP", "RJ", "MG", "ES", "PR", "SC", "RS", "BA", "PE", "GO", "AM"],
    })
    produtos = pd.DataFrame({
        "cod_produto": [f"P{i:03d}" for i in range(1, 21)],
        "categoria": (["Eletrônicos"] * 5 + ["Casa"] * 5 + ["Moda"] * 5 + ["Mercado"] * 5),
        "preco_lista": np.round(rng.uniform(15, 900, 20), 2),
    })
    dias = pd.date_range("2024-01-01", "2025-12-31", freq="D")
    n = 9000
    d = rng.choice(dias, n)
    loja = rng.choice(lojas["cod_loja"], n, p=np.linspace(2, 0.5, 12) / np.linspace(2, 0.5, 12).sum())
    prod = rng.choice(produtos["cod_produto"], n)
    qtd = rng.integers(1, 6, n)
    preco = produtos.set_index("cod_produto").loc[prod, "preco_lista"].to_numpy()
    sazonal = 1 + 0.25 * np.sin(2 * np.pi * (pd.DatetimeIndex(d).day_of_year / 365.25)) + \
        0.35 * (pd.DatetimeIndex(d).month == 12)
    desconto = np.round(rng.choice([0, 0, 0, 0.05, 0.1, 0.2], n), 2)
    valor = np.round(qtd * preco * (1 - desconto) * sazonal, 2)
    vendas = pd.DataFrame({
        "id_venda": np.arange(1, n + 1),
        "data": pd.DatetimeIndex(d).strftime("%d/%m/%Y"),
        "cod_loja": loja, "cod_produto": prod,
        "canal": rng.choice(["Loja física", "Site", "App"], n, p=[0.55, 0.3, 0.15]),
        "quantidade": qtd, "desconto": desconto, "valor": valor,
    })
    # problemas de qualidade propositais
    vendas.loc[rng.choice(n, 15, replace=False), "valor"] = np.nan
    vendas.loc[rng.choice(n, 8, replace=False), "cod_loja"] = "9999"  # loja inexistente
    vendas = pd.concat([vendas, vendas.iloc[:5]], ignore_index=True)  # 5 duplicadas
    meses = pd.date_range("2018-01-01", periods=96, freq="MS")
    t = np.arange(96)
    serie = pd.DataFrame({"mes": meses.strftime("%d/%m/%Y"),
                          "receita": np.round(1000 + 12 * t + 180 * np.sin(2 * np.pi * t / 12) + rng.normal(0, 40, 96), 2)})
    return {"vendas": vendas, "lojas": lojas, "produtos": produtos, "serie_mensal": serie}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--semente", type=int, default=42)
    ap.add_argument("--pasta", default=str(Path(__file__).parent / "dados"))
    a = ap.parse_args()
    out = Path(a.pasta)
    out.mkdir(parents=True, exist_ok=True)
    for name, df in generate(a.semente).items():
        df.to_csv(out / f"{name}.csv", sep=";", decimal=",", index=False, encoding="utf-8-sig")
        print(f"{name}.csv: {len(df)} linhas")


if __name__ == "__main__":
    main()
