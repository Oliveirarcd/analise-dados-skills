"""Gera um dashboard HTML interativo, em um único arquivo, para abrir localmente no navegador.

Recursos: filtro de período (de/até e atalhos), granularidade (dia/semana/mês/trimestre/ano),
filtros por dimensão com busca e seleção múltipla, filtro cruzado ao clicar nas barras,
cartões de KPI com variação contra o período anterior equivalente, gráfico de evolução,
ranking por dimensão, tabela-resumo por dimensão, tabela de detalhe com busca, ordenação
e paginação, exportação CSV do que está filtrado, tema claro/escuro e impressão.

Funciona sem internet: o Plotly vai embutido no arquivo (~5 MB). Use --cdn para um
arquivo pequeno que carrega o Plotly da internet.

Uso:
  python dashboard_html.py vendas.csv --saida painel.html --titulo "Vendas"
         [--data data] [--filtros regiao canal produto] [--medidas valor:soma ticket:media id_pedido:distintos]
         [--max-linhas 200000] [--cdn]

Agregações: soma, media, contagem (não nulos), min, max, distintos (só com dados linha a linha).
A medida "Linhas" (contagem de registros) é sempre incluída.
Acima de --max-linhas, os dados são pré-agregados por dia + filtros (soma, contagem, mín e máx
preservam o resultado exato; distintos deixa de estar disponível).
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from io_br import guard_output, read_table

AGGS = {"soma", "media", "contagem", "min", "max", "distintos"}
LABEL = {"soma": "Total", "media": "Média", "contagem": "Qtd", "min": "Mín", "max": "Máx", "distintos": "Distintos"}


def auto_config(df: pd.DataFrame, date: str | None, filters: list[str] | None, measures: list[str] | None):
    if date is None:
        dts = list(df.select_dtypes("datetime").columns)
        date = dts[0] if dts else None
    if filters is None:
        filters = []
        for c in df.columns:
            if c == date or pd.api.types.is_numeric_dtype(df[c]) or pd.api.types.is_datetime64_any_dtype(df[c]):
                continue
            k = df[c].nunique()
            if 2 <= k <= 60 and k < 0.5 * len(df):
                filters.append(c)
        filters = filters[:6]
    if measures is None:
        skip = {"id", "cod", "codigo", "cep", "cnpj", "cpf", "ano", "mes", "dia", "num", "nr", "sk", "chave"}
        measures = [f"{c}:soma" for c in df.select_dtypes("number").columns
                    if not skip & set(re.split(r"[_\W]+", c.lower()))][:6]  # tokens inteiros: "quantidade" não é "id"
    parsed = []
    for m in measures:
        col, _, agg = m.partition(":")
        agg = agg or "soma"
        if col not in df.columns:
            raise KeyError(f"Coluna de medida inexistente: {col}")
        if agg not in AGGS:
            raise ValueError(f"Agregação inválida em '{m}'. Use: {', '.join(sorted(AGGS))}")
        if agg != "distintos" and agg != "contagem" and not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f"Coluna '{col}' não é numérica; use contagem ou distintos")
        parsed.append({"col": col, "agg": agg, "nome": f"{LABEL[agg]} {col}"})
    for f in filters:
        if f not in df.columns:
            raise KeyError(f"Coluna de filtro inexistente: {f}")
    if date and date not in df.columns:
        raise KeyError(f"Coluna de data inexistente: {date}")
    return date, filters, parsed


def _encode_cat(s: pd.Series):
    s = s.astype("string").fillna("(vazio)").str.strip().replace("", "(vazio)")
    codes, uniques = pd.factorize(s, sort=True)
    return codes.tolist(), [str(u) for u in uniques]


def build_payload(df: pd.DataFrame, date: str | None, filters: list[str], measures: list[dict], max_rows: int):
    n = len(df)
    preagg = n > max_rows
    if preagg and any(m["agg"] == "distintos" for m in measures):
        raise ValueError(f"{n} linhas > --max-linhas {max_rows}: 'distintos' exige dados linha a linha. "
                         "Aumente --max-linhas ou remova a medida.")
    work = df.copy()
    if date:
        work["__d"] = pd.to_datetime(work[date], errors="coerce").dt.normalize()
    for f in filters:
        work[f] = work[f].astype("string").fillna("(vazio)")
    cols = sorted({m["col"] for m in measures})
    payload = {"n": 0, "preagregado": preagg, "dims": {}, "medidas": measures, "tem_data": bool(date)}
    if preagg:
        keys = (["__d"] if date else []) + filters
        g = work.groupby(keys, dropna=False)
        agg = g.size().rename("__linhas").to_frame()
        for c in cols:
            num = pd.to_numeric(work[c], errors="coerce")
            gg = num.groupby([work[k] for k in keys], dropna=False)
            agg[f"{c}__s"], agg[f"{c}__c"] = gg.sum(), gg.count()
            agg[f"{c}__min"], agg[f"{c}__max"] = gg.min(), gg.max()
        base = agg.reset_index()
    else:
        base = work
    payload["n"] = len(base)
    if date:
        payload["datas"] = [None if pd.isna(x) else x.strftime("%Y-%m-%d") for x in base["__d"]]
    for f in filters:
        codes, uniques = _encode_cat(base[f])
        payload["dims"][f] = {"codigos": codes, "valores": uniques}
    vals = {}
    def _clean(a):
        return [None if (x is None or (isinstance(x, float) and not np.isfinite(x))) else round(float(x), 6) for x in a]
    for c in cols:
        if preagg:
            vals[c] = {"s": _clean(base[f"{c}__s"]), "c": base[f"{c}__c"].astype(int).tolist(),
                       "min": _clean(base[f"{c}__min"]), "max": _clean(base[f"{c}__max"])}
        else:
            raw = base[c]
            if pd.api.types.is_numeric_dtype(raw):
                vals[c] = {"v": _clean(raw.to_numpy(dtype=float, na_value=np.nan))}
            else:  # distintos/contagem de texto
                codes, uniques = _encode_cat(raw.where(raw.notna(), None))
                null_code = uniques.index("(vazio)") if "(vazio)" in uniques else -2
                vals[c] = {"t": [None if k == null_code else k for k in codes]}
    payload["valores"] = vals
    payload["linhas"] = base["__linhas"].astype(int).tolist() if preagg else None
    if not preagg:
        detail_cols = ([date] if date else []) + filters + [c for c in cols if c not in filters]
        det = base[detail_cols].copy()
        for c in det.columns:
            if pd.api.types.is_datetime64_any_dtype(det[c]):
                det[c] = det[c].dt.strftime("%d/%m/%Y")
        payload["detalhe"] = {"colunas": detail_cols,
                              "linhas": det.astype(object).where(det.notna(), None).values.tolist()}
    return payload


def render(payload: dict, title: str, cdn: bool) -> str:
    if cdn:
        plotly_tag = '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>'
    else:
        import plotly.offline
        plotly_tag = "<script>" + plotly.offline.get_plotlyjs() + "</script>"
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return (TEMPLATE.replace("__TITLE__", html.escape(title)).replace("__PLOTLY__", plotly_tag)
            .replace("__DATA__", data))


TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
__PLOTLY__
<style>
:root{color-scheme:light;--surface-0:#f3f3f1;--surface-1:#fcfcfb;--border:#dedcd6;--text-primary:#0b0b0b;--text-secondary:#52514e;--muted:#8a8984;
--series-1:#2a78d6;--series-1-soft:#b7d3f6;--good:#008300;--critical:#e34948;--grid:#ebeae6}
:root[data-theme="dark"]{color-scheme:dark;--surface-0:#111110;--surface-1:#1a1a19;--border:#33322f;--text-primary:#f0efec;--text-secondary:#c3c2b7;--muted:#8d8c85;
--series-1:#3987e5;--series-1-soft:#184f95;--good:#2fa82f;--critical:#e66767;--grid:#2a2a28}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,"Segoe UI",Roboto,sans-serif;background:var(--surface-0);color:var(--text-primary)}
header{display:flex;align-items:center;gap:12px;padding:14px 20px;background:var(--surface-1);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:5}
header h1{font-size:18px;margin:0;flex:1}header .meta{color:var(--text-secondary);font-size:12px}
button,select,input{font:inherit;color:var(--text-primary);background:var(--surface-1);border:1px solid var(--border);border-radius:6px;padding:5px 9px}
button{cursor:pointer}button:hover{border-color:var(--series-1)}button:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid var(--series-1);outline-offset:1px}
.filters{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;padding:12px 20px;background:var(--surface-1);border-bottom:1px solid var(--border)}
.filters label{display:flex;flex-direction:column;gap:3px;font-size:12px;color:var(--text-secondary)}
.ms{position:relative}.ms>button{min-width:150px;text-align:left}.ms .pop{display:none;position:absolute;top:100%;left:0;z-index:20;margin-top:4px;width:260px;max-height:320px;overflow:auto;background:var(--surface-1);border:1px solid var(--border);border-radius:8px;padding:8px;box-shadow:0 6px 24px rgba(0,0,0,.18)}
.ms.open .pop{display:block}.ms .pop input[type=search]{width:100%;margin-bottom:6px}.ms .opt{display:flex;gap:6px;align-items:center;padding:3px 2px;color:var(--text-primary);font-size:13px}
.ms .acts{display:flex;gap:6px;margin-bottom:6px}.ms .acts button{padding:2px 6px;font-size:12px}
.chips{display:flex;flex-wrap:wrap;gap:6px;padding:8px 20px 0}.chip{background:var(--surface-1);border:1px solid var(--border);border-radius:999px;padding:2px 10px;font-size:12px;color:var(--text-secondary)}
main{padding:16px 20px;display:grid;gap:16px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}
.card{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;padding:14px}
.kpi .lbl{color:var(--text-secondary);font-size:12px}.kpi .val{font-size:26px;font-weight:600;margin-top:2px;font-variant-numeric:tabular-nums}
.kpi .delta{font-size:12px;margin-top:4px;color:var(--text-secondary)}.up{color:var(--good)}.down{color:var(--critical)}
.row{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:16px}
.card h2{font-size:14px;margin:0 0 8px;display:flex;gap:8px;align-items:center;justify-content:space-between}
.chart{height:340px}
table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}th,td{padding:6px 8px;border-bottom:1px solid var(--grid);text-align:left;white-space:nowrap}
th{cursor:pointer;color:var(--text-secondary);font-weight:600;position:sticky;top:0;background:var(--surface-1)}td.n,th.n{text-align:right}
.tablewrap{max-height:460px;overflow:auto}.pager{display:flex;gap:8px;align-items:center;margin-top:8px;color:var(--text-secondary);font-size:12px}
.note{color:var(--muted);font-size:12px}
@media print{header button,.filters,.pager,.noprint{display:none!important}.card{break-inside:avoid}}
</style>
</head>
<body>
<header><h1>__TITLE__</h1><span class="meta" id="meta"></span>
<button id="btnTema" aria-label="Alternar tema claro/escuro">Tema</button><button onclick="window.print()">Imprimir</button></header>
<div class="filters" id="filters" role="region" aria-label="Filtros"></div>
<div class="chips" id="chips" aria-live="polite"></div>
<main>
<section class="kpis" id="kpis" aria-label="Indicadores"></section>
<section class="row" id="rowTempo"><div class="card"><h2><span id="tTempo">Evolução</span><select id="selMedTempo" aria-label="Medida do gráfico de evolução"></select></h2><div id="chTempo" class="chart"></div></div></section>
<section class="row" id="rowDims"></section>
<section class="card"><h2><span>Resumo por dimensão</span><span class="noprint"><select id="selDimResumo" aria-label="Dimensão do resumo"></select> <button id="btnCsvResumo">Exportar CSV</button></span></h2><div class="tablewrap"><table id="tblResumo"></table></div></section>
<section class="card" id="secDetalhe"><h2><span>Detalhe</span><span class="noprint"><input type="search" id="busca" placeholder="Buscar..." aria-label="Buscar no detalhe"> <button id="btnCsv">Exportar CSV</button></span></h2><div class="tablewrap"><table id="tblDetalhe"></table></div><div class="pager"><button id="pgAnt">‹</button><span id="pgInfo"></span><button id="pgProx">›</button></div></section>
<p class="note" id="nota"></p>
</main>
<script>
const D = __DATA__;
const NF = new Intl.NumberFormat('pt-BR',{maximumFractionDigits:2});
const NF0 = new Intl.NumberFormat('pt-BR',{maximumFractionDigits:0});
const NF2 = new Intl.NumberFormat('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
const PF = new Intl.NumberFormat('pt-BR',{style:'percent',maximumFractionDigits:1,signDisplay:'always'});
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const fmt = v => v==null||!isFinite(v) ? '–' : (Math.abs(v)>=1e6 ? NF.format(v/1e6)+' mi' : (Number.isInteger(v)?NF0:NF2).format(v));
const dims = Object.keys(D.dims);
const MEDS = [{nome:'Linhas',agg:'linhas'}].concat(D.medidas);
const state = {de:null, ate:null, gran:'mes', sel:{}, medTempo:1<MEDS.length?1:0, dimResumo:dims[0]||null, busca:'', pagina:0, ord:{col:null,asc:true}};
dims.forEach(d=>state.sel[d]=null);
let minD=null,maxD=null;
if(D.tem_data){for(const x of D.datas){if(!x)continue;if(!minD||x<minD)minD=x;if(!maxD||x>maxD)maxD=x;}state.de=minD;state.ate=maxD;}

// ------------------------------------------------ agregação
function rowsCount(i){return D.preagregado?D.linhas[i]:1}
function newAcc(){return {s:0,c:0,min:Infinity,max:-Infinity,set:null,l:0}}
function addAcc(a,m,i){
  a.l+=rowsCount(i);
  if(m.agg==='linhas')return;
  const v=D.valores[m.col];
  if(D.preagregado){a.s+=v.s[i]||0;a.c+=v.c[i];if(v.min[i]!=null&&v.min[i]<a.min)a.min=v.min[i];if(v.max[i]!=null&&v.max[i]>a.max)a.max=v.max[i];return;}
  const x=v.v?v.v[i]:v.t[i];
  if(x==null)return;
  if(m.agg==='distintos'){(a.set||(a.set=new Set())).add(x);return;}
  a.c++; if(v.v){a.s+=x;if(x<a.min)a.min=x;if(x>a.max)a.max=x;}
}
function result(a,m){
  switch(m.agg){case 'linhas':return a.l;case 'soma':return a.s;case 'media':return a.c?a.s/a.c:null;case 'contagem':return a.c;
  case 'min':return a.c?a.min:null;case 'max':return a.c?a.max:null;case 'distintos':return a.set?a.set.size:0;}
}
function aggregate(idx,m){const a=newAcc();for(const i of idx)addAcc(a,m,i);return result(a,m)}
function groupBy(idx,keyFn,m){const g=new Map();for(const i of idx){const k=keyFn(i);if(k==null)continue;let a=g.get(k);if(!a){a=newAcc();g.set(k,a)}addAcc(a,m,i)}return [...g].map(([k,a])=>[k,result(a,m)])}

// ------------------------------------------------ filtros
function filtered(opts={}){
  const de=opts.de!==undefined?opts.de:state.de, ate=opts.ate!==undefined?opts.ate:state.ate, ex=opts.exceto;
  const out=[];
  outer: for(let i=0;i<D.n;i++){
    if(D.tem_data&&(de||ate)){const x=D.datas[i];if(!x||(de&&x<de)||(ate&&x>ate))continue;}
    for(const d of dims){if(d===ex)continue;const s=state.sel[d];if(s&&!s.has(D.dims[d].codigos[i]))continue outer;}
    out.push(i);
  }
  return out;
}
function periodKey(x,g){
  if(!x)return null;
  if(g==='dia')return x; if(g==='ano')return x.slice(0,4); if(g==='mes')return x.slice(0,7);
  if(g==='trimestre'){return x.slice(0,4)+'-T'+(Math.floor((+x.slice(5,7)-1)/3)+1)}
  const t=new Date(x+'T00:00:00Z');const wd=(t.getUTCDay()+6)%7;t.setUTCDate(t.getUTCDate()-wd);return t.toISOString().slice(0,10);
}
function shift(x,days){const t=new Date(x+'T00:00:00Z');t.setUTCDate(t.getUTCDate()+days);return t.toISOString().slice(0,10)}
function daysBetween(a,b){return Math.round((new Date(b)-new Date(a))/864e5)}

function buildFilters(){
  const f=document.getElementById('filters');
  if(D.tem_data){
    f.insertAdjacentHTML('beforeend',`<label>De<input type="date" id="fDe" value="${minD}" min="${minD}" max="${maxD}"></label>
    <label>Até<input type="date" id="fAte" value="${maxD}" min="${minD}" max="${maxD}"></label>
    <label>Atalho<select id="fAtalho"><option value="">—</option><option value="30">Últimos 30 dias</option><option value="90">Últimos 90 dias</option><option value="365">Últimos 12 meses</option><option value="ano">Ano atual dos dados</option><option value="tudo">Tudo</option></select></label>
    <label>Granularidade<select id="fGran"><option value="dia">Dia</option><option value="semana">Semana</option><option value="mes" selected>Mês</option><option value="trimestre">Trimestre</option><option value="ano">Ano</option></select></label>`);
    fDe.onchange=e=>{state.de=e.target.value||null;update()};fAte.onchange=e=>{state.ate=e.target.value||null;update()};
    fGran.onchange=e=>{state.gran=e.target.value;update()};
    fAtalho.onchange=e=>{const v=e.target.value;if(!v)return;if(v==='tudo'){state.de=minD;state.ate=maxD}else if(v==='ano'){state.de=maxD.slice(0,4)+'-01-01';state.ate=maxD}else{state.de=shift(maxD,-(+v)+1);state.ate=maxD}
      if(state.de<minD)state.de=minD;fDe.value=state.de;fAte.value=state.ate;update()};
  }
  dims.forEach((d,k)=>{
    const vals=D.dims[d].valores;
    const opts=vals.map((v,i)=>`<label class="opt"><input type="checkbox" data-d="${k}" value="${i}" checked> ${esc(v)}</label>`).join('');
    f.insertAdjacentHTML('beforeend',`<label>${esc(d)}<div class="ms" id="ms${k}"><button type="button" aria-haspopup="true" aria-expanded="false">Todos</button><div class="pop">
      <input type="search" placeholder="Buscar..." aria-label="Buscar em ${esc(d)}"><div class="acts"><button type="button" data-a="all">Todos</button><button type="button" data-a="none">Nenhum</button></div>${opts}</div></div></label>`);
    const ms=document.getElementById('ms'+k), btn=ms.querySelector('button');
    btn.onclick=e=>{e.stopPropagation();document.querySelectorAll('.ms.open').forEach(o=>{if(o!==ms)o.classList.remove('open')});ms.classList.toggle('open');btn.setAttribute('aria-expanded',ms.classList.contains('open'))};
    ms.querySelector('.pop').onclick=e=>e.stopPropagation();
    ms.querySelector('input[type=search]').oninput=e=>{const q=e.target.value.toLowerCase();ms.querySelectorAll('.opt').forEach(o=>o.style.display=o.textContent.toLowerCase().includes(q)?'':'none')};
    ms.querySelectorAll('.acts button').forEach(b=>b.onclick=()=>{const on=b.dataset.a==='all';ms.querySelectorAll('.opt input').forEach(c=>{if(c.parentElement.style.display!=='none')c.checked=on});readMs(k)});
    ms.querySelectorAll('.opt input').forEach(c=>c.onchange=()=>readMs(k));
  });
  if(dims.length||D.tem_data)f.insertAdjacentHTML('beforeend','<button id="btnLimpar" type="button">Limpar filtros</button>');
  const bl=document.getElementById('btnLimpar'); if(bl)bl.onclick=clearAll;
  document.addEventListener('click',()=>document.querySelectorAll('.ms.open').forEach(o=>o.classList.remove('open')));
}
function readMs(k){const d=dims[k];const ms=document.getElementById('ms'+k);const boxes=[...ms.querySelectorAll('.opt input')];
  const on=boxes.filter(b=>b.checked).map(b=>+b.value);state.sel[d]=on.length===boxes.length?null:new Set(on);syncMs(k);update()}
function syncMs(k){const d=dims[k],ms=document.getElementById('ms'+k),s=state.sel[d];
  ms.querySelectorAll('.opt input').forEach(b=>b.checked=!s||s.has(+b.value));
  ms.querySelector('button').textContent=!s?'Todos':s.size===1?D.dims[d].valores[[...s][0]]:`${s.size} selecionados`}
function toggleValue(d,code){const k=dims.indexOf(d);const s=state.sel[d];
  if(s&&s.size===1&&s.has(code))state.sel[d]=null;else state.sel[d]=new Set([code]);syncMs(k);update()}
function clearAll(){dims.forEach((d,k)=>{state.sel[d]=null;syncMs(k)});if(D.tem_data){state.de=minD;state.ate=maxD;fDe.value=minD;fAte.value=maxD;fAtalho.value=''}update()}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}

// ------------------------------------------------ visuais
function layout(extra){return Object.assign({margin:{l:60,r:16,t:8,b:40},paper_bgcolor:css('--surface-1'),plot_bgcolor:css('--surface-1'),
  font:{family:'system-ui,Segoe UI,sans-serif',color:css('--text-secondary'),size:12},separators:',.',
  xaxis:{gridcolor:css('--grid'),linecolor:css('--border'),zeroline:false},yaxis:{gridcolor:css('--grid'),linecolor:css('--border'),zeroline:false,rangemode:'tozero'},
  hoverlabel:{bgcolor:css('--surface-1'),bordercolor:css('--border'),font:{color:css('--text-primary')}},showlegend:false},extra||{})}
const CFG={displaylogo:false,responsive:true,locale:'pt-BR',modeBarButtonsToRemove:['lasso2d','select2d']};

function renderKpis(idx){
  const box=document.getElementById('kpis');let prevIdx=null;
  if(D.tem_data&&state.de&&state.ate){const len=daysBetween(state.de,state.ate)+1;const pa=shift(state.de,-len),pb=shift(state.de,-1);
    if(pb>=minD)prevIdx=filtered({de:pa,ate:pb});}
  box.innerHTML=MEDS.map(m=>{const v=aggregate(idx,m);let d='';
    if(prevIdx){const p=aggregate(prevIdx,m);if(p){const r=(v-p)/Math.abs(p);d=`<div class="delta"><span class="${r>=0?'up':'down'}">${r>=0?'▲':'▼'} ${PF.format(r)}</span> vs período anterior (${fmt(p)})</div>`}}
    return `<div class="card kpi"><div class="lbl">${esc(m.nome)}</div><div class="val">${fmt(v)}</div>${d||'<div class="delta">&nbsp;</div>'}</div>`}).join('');
}
function renderTempo(idx){
  if(!D.tem_data){document.getElementById('rowTempo').style.display='none';return}
  const m=MEDS[state.medTempo];const g=groupBy(idx,i=>periodKey(D.datas[i],state.gran),m).sort((a,b)=>a[0]<b[0]?-1:1);
  Plotly.react('chTempo',[{x:g.map(r=>r[0]),y:g.map(r=>r[1]),type:'scatter',mode:g.length>60?'lines':'lines+markers',
    line:{color:css('--series-1'),width:2},marker:{size:8,color:css('--series-1'),line:{color:css('--surface-1'),width:2}},
    hovertemplate:'%{x}<br><b>%{y:,.2f}</b><extra>'+esc(m.nome)+'</extra>'}],layout({hovermode:'x unified',xaxis:{type:'category',gridcolor:css('--grid'),linecolor:css('--border'),nticks:12}}),CFG);
  document.getElementById('tTempo').textContent='Evolução — '+m.nome;
}
function renderDims(){
  const row=document.getElementById('rowDims');
  if(!row.dataset.ok){row.innerHTML=dims.map((d,k)=>`<div class="card"><h2><span>${esc(d)}</span><span class="note">clique para filtrar</span></h2><div id="chDim${k}" class="chart"></div></div>`).join('');row.dataset.ok=1;}
  const m=MEDS[state.medTempo];
  dims.forEach((d,k)=>{
    const idx=filtered({exceto:d});const vals=D.dims[d].valores;
    let g=groupBy(idx,i=>D.dims[d].codigos[i],m).sort((a,b)=>(b[1]??-Infinity)-(a[1]??-Infinity));
    const extra=g.length>15?g.slice(15):[];g=g.slice(0,15).reverse();
    const s=state.sel[d];const soft=css('--series-1-soft'),strong=css('--series-1');
    const el=document.getElementById('chDim'+k);
    Plotly.react(el,[{y:g.map(r=>vals[r[0]]),x:g.map(r=>r[1]),customdata:g.map(r=>r[0]),type:'bar',orientation:'h',
      marker:{color:g.map(r=>!s||s.has(r[0])?strong:soft),line:{color:css('--surface-1'),width:2}},
      hovertemplate:'%{y}<br><b>%{x:,.2f}</b><extra>'+esc(m.nome)+'</extra>'}],
      layout({margin:{l:130,r:16,t:8,b:36},yaxis:{type:'category',automargin:true,gridcolor:'rgba(0,0,0,0)',linecolor:css('--border')},bargap:.25,
      annotations:extra.length?[{text:`+${extra.length} itens fora do top 15`,xref:'paper',yref:'paper',x:1,y:-0.12,showarrow:false,font:{size:11,color:css('--muted')}}]:[]}),CFG);
    if(!el.dataset.bound){el.on('plotly_click',ev=>toggleValue(d,ev.points[0].customdata));el.dataset.bound=1}
  });
}
let resumoRows=[];
function renderResumo(idx){
  const t=document.getElementById('tblResumo');const d=state.dimResumo;
  const keyFn=d?(i=>D.dims[d].codigos[i]):(i=>0);const names=d?D.dims[d].valores:['Total'];
  const per=MEDS.map(m=>new Map(groupBy(idx,keyFn,m)));
  const keys=[...per[0].keys()].sort((a,b)=>(per[0].get(b)||0)-(per[0].get(a)||0));
  resumoRows=keys.map(k=>[names[k]].concat(per.map(p=>p.get(k))));
  const tot=['Total'].concat(MEDS.map(m=>aggregate(idx,m)));
  t.innerHTML=`<thead><tr><th>${esc(d||'')}</th>${MEDS.map(m=>`<th class="n">${esc(m.nome)}</th>`).join('')}<th class="n">% Linhas</th></tr></thead><tbody>`+
   resumoRows.map(r=>`<tr><td>${esc(r[0])}</td>${r.slice(1).map(v=>`<td class="n">${fmt(v)}</td>`).join('')}<td class="n">${tot[1]?NF.format(r[1]/tot[1]*100)+'%':'–'}</td></tr>`).join('')+
   `</tbody><tfoot><tr><th>Total</th>${tot.slice(1).map(v=>`<th class="n">${fmt(v)}</th>`).join('')}<th class="n">100%</th></tr></tfoot>`;
}
const PAGE=100;let detRows=[];
function renderDetalhe(idx){
  const sec=document.getElementById('secDetalhe');
  if(!D.detalhe){sec.style.display='none';return}
  const cols=D.detalhe.colunas;const q=state.busca.toLowerCase();
  detRows=idx.map(i=>D.detalhe.linhas[i]);
  if(q)detRows=detRows.filter(r=>r.some(v=>v!=null&&String(v).toLowerCase().includes(q)));
  if(state.ord.col!=null){const c=state.ord.col,s=state.ord.asc?1:-1;const isDate=D.tem_data&&c===0;
    const key=v=>isDate&&v?v.split('/').reverse().join(''):v;
    detRows.sort((a,b)=>{const x=key(a[c]),y=key(b[c]);if(x==null)return 1;if(y==null)return -1;return (x>y?1:x<y?-1:0)*s})}
  const pages=Math.max(1,Math.ceil(detRows.length/PAGE));if(state.pagina>=pages)state.pagina=pages-1;
  const slice=detRows.slice(state.pagina*PAGE,(state.pagina+1)*PAGE);
  const t=document.getElementById('tblDetalhe');
  t.innerHTML=`<thead><tr>${cols.map((c,j)=>`<th data-c="${j}" class="${typeof (slice[0]||[])[j]==='number'?'n':''}">${esc(c)}${state.ord.col===j?(state.ord.asc?' ▲':' ▼'):''}</th>`).join('')}</tr></thead><tbody>`+
   slice.map(r=>`<tr>${r.map(v=>typeof v==='number'?`<td class="n">${fmt(v)}</td>`:`<td>${v==null?'':esc(v)}</td>`).join('')}</tr>`).join('')+'</tbody>';
  t.querySelectorAll('th').forEach(th=>th.onclick=()=>{const c=+th.dataset.c;state.ord=state.ord.col===c?{col:c,asc:!state.ord.asc}:{col:c,asc:true};renderDetalhe(filtered())});
  document.getElementById('pgInfo').textContent=`${NF0.format(detRows.length)} linhas · página ${state.pagina+1} de ${pages}`;
}
function csvDownload(name,header,rows){
  const q=v=>v==null?'':(typeof v==='number'?String(v).replace('.',','):'"'+String(v).replace(/"/g,'""')+'"');
  const txt='﻿'+[header.map(q).join(';')].concat(rows.map(r=>r.map(q).join(';'))).join('\r\n');
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([txt],{type:'text/csv;charset=utf-8'}));a.download=name;a.click();URL.revokeObjectURL(a.href);
}
function renderChips(){
  const c=[];if(D.tem_data&&(state.de!==minD||state.ate!==maxD))c.push(`Período: ${fmtD(state.de)} a ${fmtD(state.ate)}`);
  dims.forEach(d=>{const s=state.sel[d];if(s)c.push(`${d}: ${[...s].slice(0,3).map(k=>D.dims[d].valores[k]).join(', ')}${s.size>3?' +'+(s.size-3):''}`)});
  document.getElementById('chips').innerHTML=c.map(x=>`<span class="chip">${esc(x)}</span>`).join('');
}
function fmtD(x){return x?x.split('-').reverse().join('/'):'…'}
function update(){
  state.pagina=0;const idx=filtered();
  renderChips();renderKpis(idx);renderTempo(idx);renderDims();renderResumo(idx);renderDetalhe(idx);
  document.getElementById('meta').textContent=`${NF0.format(MEDS[0].agg==='linhas'?aggregate(idx,MEDS[0]):idx.length)} registros no filtro`;
}
// ------------------------------------------------ inicialização
buildFilters();
const sm=document.getElementById('selMedTempo');sm.innerHTML=MEDS.map((m,i)=>`<option value="${i}" ${i===state.medTempo?'selected':''}>${esc(m.nome)}</option>`).join('');
sm.onchange=e=>{state.medTempo=+e.target.value;update()};
const sd=document.getElementById('selDimResumo');sd.innerHTML=dims.length?dims.map(d=>`<option>${esc(d)}</option>`).join(''):'<option value="">(sem dimensões)</option>';
sd.onchange=e=>{state.dimResumo=e.target.value||null;renderResumo(filtered())};
document.getElementById('busca').oninput=e=>{state.busca=e.target.value;state.pagina=0;renderDetalhe(filtered())};
pgAnt.onclick=()=>{if(state.pagina>0){state.pagina--;renderDetalhe(filtered())}};
pgProx.onclick=()=>{state.pagina++;renderDetalhe(filtered())};
btnCsv.onclick=()=>csvDownload('detalhe_filtrado.csv',D.detalhe.colunas,detRows);
btnCsvResumo.onclick=()=>csvDownload('resumo.csv',[state.dimResumo||''].concat(MEDS.map(m=>m.nome)),resumoRows);
btnTema.onclick=()=>{const r=document.documentElement;r.dataset.theme=r.dataset.theme==='dark'?'light':'dark';localStorage.setItem('tema',r.dataset.theme);update()};
if(localStorage.getItem('tema')==='dark'||(!localStorage.getItem('tema')&&matchMedia('(prefers-color-scheme: dark)').matches))document.documentElement.dataset.theme='dark';
document.getElementById('nota').textContent=(D.preagregado?'Dados pré-agregados por dia e filtros para caber no navegador; médias são recalculadas a partir de soma e contagem. ':'')+
 'Variação dos KPIs: compara o período filtrado com o período imediatamente anterior de mesma duração. Gerado por analise-dados-skills.';
update();
</script>
</body>
</html>
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivo")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--titulo", default="Painel de dados")
    ap.add_argument("--data", help="Coluna de data (padrão: primeira coluna de data)")
    ap.add_argument("--filtros", nargs="*", help="Colunas de dimensão para filtrar (padrão: automático)")
    ap.add_argument("--medidas", nargs="*", help="coluna:agregacao, ex.: valor:soma ticket:media")
    ap.add_argument("--max-linhas", type=int, default=200_000)
    ap.add_argument("--texto", nargs="+", default=[], help="Colunas que devem continuar como texto")
    ap.add_argument("--cdn", action="store_true", help="Carregar Plotly da internet (arquivo menor)")
    ap.add_argument("--sobrescrever", action="store_true")
    a = ap.parse_args(argv)
    df = read_table(a.arquivo, keep_text=a.texto)
    date, filters, measures = auto_config(df, a.data, a.filtros, a.medidas)
    payload = build_payload(df, date, filters, measures, a.max_linhas)
    out = guard_output(a.saida, a.sobrescrever)
    out.write_text(render(payload, a.titulo, a.cdn), encoding="utf-8")
    print(f"{len(df)} linhas, {len(filters)} filtros, {len(measures)} medidas"
          f"{' (pré-agregado)' if payload['preagregado'] else ''} -> {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
