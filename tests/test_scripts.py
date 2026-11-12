"""Testes de comportamento dos scripts, só com dados sintéticos."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "exemplos"))

import conferir_painel  # noqa: E402
import cruzar  # noqa: E402
import dashboard_html  # noqa: E402
import estatistica  # noqa: E402
import io_br  # noqa: E402
import modelo_estrela  # noqa: E402
import perfil  # noqa: E402
import serie  # noqa: E402
from gerar_dados_exemplo import generate  # noqa: E402


@pytest.fixture(scope="module")
def dados(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("dados")
    for name, df in generate(7).items():
        df.to_csv(pasta / f"{name}.csv", sep=";", decimal=",", index=False, encoding="utf-8-sig")
    return pasta

# ------------------------------------------------------------ io_br

def test_le_csv_brasileiro_sem_perder_zeros(dados):
    df = io_br.read_table(dados / "vendas.csv")
    assert pd.api.types.is_datetime64_any_dtype(df["data"])
    assert pd.api.types.is_float_dtype(df["valor"])
    lojas = io_br.read_table(dados / "lojas.csv")
    assert lojas["cod_loja"].iloc[0] == "0001"  # zero à esquerda preservado


def test_numero_br_com_milhar_e_cp1252(tmp_path):
    p = tmp_path / "x.csv"
    p.write_bytes("nome;valor\nJoão;1.234,56\nAção;-10,5\n".encode("cp1252"))
    df = io_br.read_table(p)
    assert df["nome"].tolist() == ["João", "Ação"]
    assert df["valor"].tolist() == [1234.56, -10.5]


def test_saida_existente_e_recusada(tmp_path):
    p = tmp_path / "a.json"
    io_br.write_json({"a": 1}, p)
    with pytest.raises(FileExistsError):
        io_br.write_json({"a": 2}, p)

# ------------------------------------------------------------ perfil

def test_perfil_detecta_duplicadas_e_nulos(dados):
    df = io_br.read_table(dados / "vendas.csv")
    p = perfil.profile(df, keys=["id_venda"])
    assert p["linhas_duplicadas"] == 5
    assert p["chave_informada"]["valida"] is False
    assert p["colunas_detalhe"]["valor"]["nulos"] >= 15


def test_perfil_sem_exemplos_nao_expoe_valores(dados):
    df = io_br.read_table(dados / "lojas.csv")
    p = perfil.profile(df, examples=False)
    assert all("mais_frequentes" not in c for c in p["colunas_detalhe"].values())
    assert ["cod_loja"] in p["chaves_candidatas"]

# ------------------------------------------------------------ cruzar

def test_cruzamento_auditado_m1(dados):
    v = io_br.read_table(dados / "vendas.csv")
    l = io_br.read_table(dados / "lojas.csv")
    m, audit, ol, _ = cruzar.audited_join(v, l, ["cod_loja"], sum_cols=["valor"])
    assert len(m) == len(v)  # left m:1 não muda linhas
    assert audit["resultado"]["so_esquerda"] == 8  # lojas 9999
    assert len(ol) == 8
    assert audit["reconciliacao"]["valor"]["diferenca"] == pytest.approx(0)
    assert audit["diagnostico"]["cardinalidade_observada"] == "m:1"


def test_cruzamento_recusa_cardinalidade_violada():
    left = pd.DataFrame({"k": ["1", "2"], "a": [1, 2]})
    right = pd.DataFrame({"k": ["1", "1", "2"], "b": [1, 2, 3]})
    with pytest.raises(ValueError, match="Cardinalidade"):
        cruzar.audited_join(left, right, ["k"], cardinality="m:1")


def test_normalizacao_casa_chaves_sujas():
    left = pd.DataFrame({"k": [" 001", "São Paulo", "ab-1"]})
    right = pd.DataFrame({"k": ["1", "SAO PAULO", "AB1"], "v": [1, 2, 3]})
    m, audit, *_ = cruzar.audited_join(left, right, ["k"], normalize=True)
    assert audit["resultado"]["casadas"] == 3
    assert audit["diagnostico"]["ganho_com_normalizacao"] == 3
    m2, audit2, *_ = cruzar.audited_join(left, right, ["k"], normalize=False)
    assert audit2["resultado"]["casadas"] == 0


def test_chave_inexistente():
    with pytest.raises(KeyError):
        cruzar.audited_join(pd.DataFrame({"a": [1]}), pd.DataFrame({"b": [1]}), ["a"], ["c"])


def test_sugestao_aproximada():
    left = pd.DataFrame({"k": ["Mercado Central"]})
    right = pd.DataFrame({"k": ["Mercado Centrall"], "v": [1]})
    _, audit, *_ = cruzar.audited_join(left, right, ["k"], suggest=True)
    assert audit["sugestoes_aproximadas"][0]["sugestao"] == "mercadocentrall"

# ------------------------------------------------------------ séries

def _serie_mensal(dados):
    df = io_br.read_table(dados / "serie_mensal.csv")
    s, info = serie.prepare_series(df, "mes", "receita", "MS")
    return s, info


def test_diagnostico_acha_tendencia_e_sazonalidade(dados):
    s, info = _serie_mensal(dados)
    assert info["lacunas"] == 0
    d = serie.diagnose(s, 12)
    assert d["tendencia"]["leitura"] == "crescente"
    assert d["sazonalidade"]["forca_sazonal"] > 0.6


def test_backtest_supera_baseline_e_nao_vaza(dados):
    s, _ = _serie_mensal(dados)
    res, fc = serie.backtest(s, 6, 12, models=["ingenuo", "sazonal_ingenuo", "ets"])
    assert res["melhor_supera_baseline"]
    assert (fc["data"] > fc["origem"]).all()  # toda previsão é para depois da origem


def test_modelo_so_recebe_passado(dados, monkeypatch):
    s, _ = _serie_mensal(dados)
    vistos = []

    def espiao(y, h, m):
        vistos.append(len(y))
        return np.repeat(y[-1], h)
    monkeypatch.setitem(serie.MODELS, "espiao", espiao)
    _, fc = serie.backtest(s, 6, 12, min_train=30, step=6, models=["espiao"])
    origens = sorted(fc["origem"].unique())
    assert vistos == [s.index.get_loc(o) + 1 for o in origens]


def test_backtest_exige_tratar_lacunas():
    idx = pd.date_range("2024-01-01", periods=40, freq="D")
    s = pd.Series(np.arange(40.0), index=idx)
    s.iloc[10] = np.nan
    with pytest.raises(ValueError, match="lacunas"):
        serie.backtest(s, 5)


def test_datas_repetidas_exigem_agregacao():
    df = pd.DataFrame({"d": ["01/01/2024", "01/01/2024", "02/01/2024", "03/01/2024"], "v": [1, 2, 3, 4]})
    with pytest.raises(ValueError, match="agregar"):
        serie.prepare_series(df, "d", "v", "D")
    s, _ = serie.prepare_series(df, "d", "v", "D", agg="soma")
    assert s.tolist() == [3, 3, 4]


def test_soma_preserva_lacuna_real():
    df = pd.DataFrame({"d": ["01/01/2024", "03/01/2024"], "v": [1, 2]})
    s, info = serie.prepare_series(df, "d", "v", "D", agg="soma")
    assert info["lacunas"] == 1 and np.isnan(s.iloc[1])


def test_metricas_com_zero_no_real():
    m = serie.metrics(np.array([0.0, 2.0]), np.array([1.0, 2.0]), np.array([1.0, 2.0, 3.0]), None)
    assert m["mape_pct"] == 0.0  # ignora o zero no denominador
    assert m["mae"] == 0.5


def test_previsao_com_intervalo(dados):
    s, _ = _serie_mensal(dados)
    res, fc = serie.backtest(s, 6, 12, models=["sazonal_ingenuo", "ets"])
    out = serie.forecast(s, 6, 12, res["melhor"], fc)
    assert len(out) == 6 and out["data"].min() > s.index.max()
    assert (out["limite_inferior"] <= out["limite_superior"]).all()

# ------------------------------------------------------------ estatística

def test_comparar_grupos_diferentes():
    rng = np.random.default_rng(1)
    df = pd.DataFrame({"v": np.r_[rng.normal(10, 1, 80), rng.normal(12, 1, 80)], "g": ["a"] * 80 + ["b"] * 80})
    r = estatistica.compare_groups(df, "v", "g")
    assert r["teste"] == "t de Welch" and r["significativo"]


def test_kruskal_para_dados_assimetricos():
    rng = np.random.default_rng(2)
    df = pd.DataFrame({"v": np.r_[rng.exponential(1, 30), rng.exponential(1, 30), rng.exponential(3, 30)],
                       "g": ["a"] * 30 + ["b"] * 30 + ["c"] * 30})
    r = estatistica.compare_groups(df, "v", "g")
    assert r["teste"] == "Kruskal-Wallis" and len(r["pares_holm"]) == 3


def test_ab_valida_entradas():
    with pytest.raises(ValueError):
        estatistica.ab_test([10, 200], [100, 100])
    r = estatistica.ab_test([100, 150], [1000, 1000])
    assert r["significativo"] and r["diferenca_abs"] == pytest.approx(0.05)


def test_holm_monotono():
    assert estatistica.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def test_tamanho_amostra():
    n = estatistica.sample_size_proportions(0.10, 0.02)
    assert 3500 < n < 4200

# ------------------------------------------------------------ modelo estrela

def test_modelo_estrela(dados):
    tabs = {n: io_br.read_table(dados / f"{n}.csv") for n in ("vendas", "lojas", "produtos")}
    rels = modelo_estrela.find_relationships(tabs)
    pares = {(r["de_tabela"], r["de_coluna"], r["para_tabela"]) for r in rels}
    assert ("vendas", "cod_loja", "lojas") in pares
    assert ("vendas", "cod_produto", "produtos") in pares
    roles = modelo_estrela.classify(tabs, rels)
    assert roles["vendas"]["papel"] == "fato" and roles["lojas"]["papel"] == "dimensao"
    ms = modelo_estrela.build_measures(roles)
    nomes = {m["nome"] for m in ms}
    assert "Total valor" in nomes and "Total valor Var % AA" in nomes
    assert "DIVIDE" in next(m["expressao"] for m in ms if m["nome"] == "Total valor Var % AA")
    assert "CALENDAR" in modelo_estrela.calendar_dax(roles)
    loja = next(r for r in rels if r["de_coluna"] == "cod_loja")
    assert loja["orfaos"] == 8

# ------------------------------------------------------------ dashboard

def test_dashboard_offline(dados, tmp_path):
    out = tmp_path / "p.html"
    dashboard_html.main([str(dados / "vendas.csv"), "--saida", str(out), "--titulo", "Teste <b>",
                         "--filtros", "canal", "cod_loja", "--medidas", "valor:soma", "valor:media", "id_venda:distintos"])
    h = out.read_text(encoding="utf-8")
    assert "Teste &lt;b&gt;" in h  # título escapado
    assert '<script src="https://cdn.plot.ly' not in h and len(h) > 3_000_000  # Plotly embutido
    data = json.loads(h.split("const D = ", 1)[1].split(";\n", 1)[0])  # JSON compacto: não tem quebra de linha
    assert data["n"] == 9005 and not data["preagregado"]
    assert "type:'mesh3d'" in h and "function fail3d" in h  # visão 3D com saída segura sem WebGL
    assert "prefers-reduced-motion" in h and "RM.matches" in h  # movimento desliga a pedido do sistema
    assert "moduleType:'locale',name:'pt-BR'" in h and "separatethousands:true" in h  # Plotly em português, 1.400 nos eixos
    assert data["rotulos"]["cod_loja"] == "Cód. loja" and data["medidas"][0]["nome"] == "Total de valor"


def test_dashboard_cdn_usa_mesma_versao_do_plotly_embutido(dados, tmp_path):
    import plotly.offline
    out = tmp_path / "c.html"
    dashboard_html.main([str(dados / "vendas.csv"), "--saida", str(out), "--cdn"])
    h = out.read_text(encoding="utf-8")
    assert f"plotly-{plotly.offline.get_plotlyjs_version()}.min.js" in h and len(h) < 3_000_000


def test_dashboard_preagregado_preserva_soma(dados, tmp_path):
    df = io_br.read_table(dados / "vendas.csv")
    date, f, m = dashboard_html.auto_config(df, "data", ["canal"], ["valor:soma"])
    p = dashboard_html.build_payload(df, date, f, m, max_rows=100)
    assert p["preagregado"] and p["n"] < len(df)
    assert sum(x or 0 for x in p["valores"]["valor"]["s"]) == pytest.approx(df["valor"].sum(), rel=1e-9)
    assert sum(p["linhas"]) == len(df)
    with pytest.raises(ValueError, match="distintos"):
        dashboard_html.build_payload(df, date, f, [{"col": "id_venda", "agg": "distintos", "nome": "x"}], 100)


def test_dashboard_rejeita_agregacao_invalida(dados):
    df = io_br.read_table(dados / "lojas.csv")
    with pytest.raises(ValueError):
        dashboard_html.auto_config(df, None, [], ["regiao:soma"])


def test_milhar_sem_virgula_depende_do_separador(tmp_path):
    br = tmp_path / "br.csv"
    br.write_text("valor;cod\n1.500;0012\n12.000;0013\n", encoding="utf-8")
    assert io_br.read_table(br)["valor"].tolist() == [1500.0, 12000.0]
    us = tmp_path / "us.csv"
    us.write_text("valor,cod\n1.500,0012\n12.000,0013\n", encoding="utf-8")
    assert io_br.read_table(us)["valor"].tolist() == [1.5, 12.0]
    dec = tmp_path / "dec.csv"
    dec.write_text("valor;x\n12.50;a\n3.75;b\n", encoding="utf-8")  # 2 casas: não é milhar
    assert io_br.read_table(dec)["valor"].tolist() == [12.5, 3.75]


def test_baseline_vencedor_nao_conta_como_superado(dados):
    s, _ = _serie_mensal(dados)
    res, _ = serie.backtest(s, 6, 12, models=["sazonal_ingenuo"])
    assert res["melhor"] == "sazonal_ingenuo" and res["melhor_supera_baseline"] is False


def test_dashboard_modo_automatico_escolhe_medidas(dados):
    df = io_br.read_table(dados / "vendas.csv")
    date, filters, measures = dashboard_html.auto_config(df, None, None, None)
    cols = {m["col"] for m in measures}
    assert date == "data"
    assert {"quantidade", "valor"} <= cols and "id_venda" not in cols
    assert "canal" in filters


def test_rotulos_legiveis():
    r = dashboard_html.rotulo
    assert r("cod_loja") == "Cód. loja" and r("id_venda") == "ID venda" and r("valor_total") == "Valor total"
    assert r("qtd") == "Qtd." and r("Agência") == "Agência" and r("Valor Total") == "Valor Total"  # já legíveis
    df = pd.DataFrame({"data": pd.to_datetime(["2025-01-01", "2025-02-01"]), "cod_loja": ["1", "2"], "vlr_venda": [1.0, 2.0]})
    date, f, m = dashboard_html.auto_config(df, None, ["cod_loja"], ["vlr_venda:soma", "cod_loja:distintos"])
    assert [x["nome"] for x in m] == ["Total de valor venda", "Distintos de cód. loja"]
    p = dashboard_html.build_payload(df, date, f, m, 1000)
    assert p["rotulos"] == {"data": "Data", "cod_loja": "Cód. loja", "vlr_venda": "Valor venda"}

# ------------------------------------------------------------ conferência visual do painel


def _conferir(arquivo, saida, **kw):
    pytest.importorskip("playwright.sync_api")
    try:
        return conferir_painel.conferir(arquivo, saida, **kw)
    except conferir_painel.NavegadorAusente as e:
        pytest.skip(str(e))


def test_conferencia_avalia_limites_de_contraste_e_rolagem():
    texto = {"elemento": "p", "cor": "#bbbbbb", "fundo": "#ffffff", "px": 14, "grande": False}
    medida = {"largura_pagina": 900, "largura_tela": 390, "culpados": ["div (900 px)"], "graficos": 1,
              "sem_desenho": [], "nao_medidos": 0, "indicadores": [],
              "textos": [{**texto, "texto": "apagado", "razao": 1.92},
                         {**texto, "texto": "título", "razao": 3.2, "px": 26, "grande": True},  # grande: mínimo 3:1
                         {**texto, "texto": "nota", "razao": 7.0, "px": 9}]}
    t = conferir_painel.avaliar(medida)
    assert t["rolagem_horizontal"] and t["culpados"] == ["div (900 px)"]
    assert [f["exemplo"] for f in t["contraste_falhas"]] == ["apagado"] and t["defeitos"] == 2
    assert [f["exemplo"] for f in t["texto_pequeno"]] == ["nota"] and t["avisos"] == 1


def test_conferencia_sem_arquivo_playwright_ou_navegador(tmp_path, monkeypatch, capsys):
    assert conferir_painel.main([str(tmp_path / "nao_existe.html"), "--saida", str(tmp_path / "c")]) == 2
    assert "não encontrado" in capsys.readouterr().err
    pagina = tmp_path / "p.html"
    pagina.write_text("<p>oi</p>", encoding="utf-8")

    def sem_playwright(*a, **k):
        raise ImportError("playwright")
    monkeypatch.setattr(conferir_painel, "conferir", sem_playwright)
    assert conferir_painel.main([str(pagina), "--saida", str(tmp_path / "c")]) == 2
    assert "pip install playwright" in capsys.readouterr().err

    def sem_navegador(*a, **k):
        raise conferir_painel.NavegadorAusente("Nenhum navegador encontrado")
    monkeypatch.setattr(conferir_painel, "conferir", sem_navegador)
    assert conferir_painel.main([str(pagina), "--saida", str(tmp_path / "c")]) == 2
    assert "Nenhum navegador" in capsys.readouterr().err


def test_conferencia_aponta_defeitos_no_navegador(tmp_path):
    ruim = tmp_path / "ruim.html"
    ruim.write_text('<!DOCTYPE html><html lang="pt-BR"><body style="margin:0;background:#fff">'
                    '<p style="color:#bbb">texto apagado</p><div style="width:900px;height:20px"></div>'
                    '<script>throw new Error("falha proposital")</script></body></html>', encoding="utf-8")
    rel = _conferir(ruim, tmp_path / "c", larguras=[390], temas=["claro"])
    tela = rel["telas"][0]
    assert tela["rolagem_horizontal"] and tela["culpados"] == ["html > body > div (900 px)"]
    assert any("falha proposital" in e for e in tela["erros"])
    assert [f["exemplo"] for f in tela["contraste_falhas"]] == ["texto apagado"]
    assert rel["defeitos"] == 3 and Path(tela["foto"]).stat().st_size > 0
    assert json.loads((tmp_path / "c" / "relatorio.json").read_text(encoding="utf-8"))["defeitos"] == 3


def test_painel_gerado_passa_na_conferencia_e_bate_com_pandas(dados, tmp_path):
    painel = tmp_path / "painel.html"
    dashboard_html.main([str(dados / "vendas.csv"), "--saida", str(painel), "--filtros", "canal", "cod_loja",
                         "--medidas", "valor:soma", "quantidade:soma"])
    rel = _conferir(painel, tmp_path / "c")  # computador e celular, temas claro e escuro
    assert rel["defeitos"] == 0, conferir_painel.resumo(rel)
    assert {t["largura"] for t in rel["telas"]} == {1440, 390} and all(t["graficos"] >= 3 for t in rel["telas"])
    df = io_br.read_table(dados / "vendas.csv")
    kpi = {k["rotulo"]: k["valor"] for k in rel["indicadores"]}
    assert kpi["Registros"] == f"{len(df):,}".replace(",", ".")
    assert kpi["Total de quantidade"] == f"{int(df['quantidade'].sum()):,}".replace(",", ".")
    assert float(kpi["Total de valor"].removesuffix(" mi").replace(",", ".")) == pytest.approx(df["valor"].sum() / 1e6, abs=0.005)
