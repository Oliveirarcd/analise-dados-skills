"""Confere um painel (ou qualquer página HTML) no navegador, sem janela, antes de entregar.

Abre o arquivo em tamanho de computador e de celular, nos temas claro e escuro, com a
preferência "reduzir movimento" ligada (a página aparece no estado final, sem animação),
tira uma foto da página inteira de cada tela e procura o que o olho deixa passar:

- erro de script (console e exceções da página);
- gráfico Plotly que não desenhou;
- página mais larga que a tela (rolagem horizontal), com os elementos que causam;
- texto com contraste abaixo de 4,5:1 (3:1 para texto grande), medido nas cores que o
  navegador calculou, inclusive nos textos dos gráficos;
- texto menor que 11 px (aviso, não conta como defeito).

Copia para o relatório os indicadores (KPIs) mostrados, para conferir com o pandas.
Texto sobre degradê ou imagem não é medido e aparece como "não medido".

Uso:
  python conferir_painel.py painel.html --saida conferencia/
         [--larguras 1440 390] [--temas claro escuro] [--navegador chrome|msedge|chromium]

Requer o Playwright para Python (`pip install playwright` ou `uv sync --group visual`).
Usa o Chrome ou o Edge já instalados; sem eles, rode `playwright install chromium`.
A pasta de saída é reescrita a cada conferência (fotos tela_<largura>_<tema>.png e
relatorio.json). Sai com código 0 sem defeitos, 1 com defeitos e 2 se não conseguir conferir.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

NAVEGADORES = ("chromium", "chrome", "msedge")
TEMAS = ("claro", "escuro")


class NavegadorAusente(RuntimeError):
    """Nenhum navegador compatível com o Playwright foi encontrado."""


# Roda dentro da página. Devolve medidas cruas; a contagem de defeitos fica no Python.
MEDIR_JS = r"""
() => {
  const vw = window.innerWidth;
  const out = {largura_pagina: document.documentElement.scrollWidth, largura_tela: vw, culpados: [],
               graficos: 0, sem_desenho: [], textos: [], nao_medidos: 0, indicadores: []};
  const desc = (el, nivel = 0) => {  // tag#id ou tag.classe; sem nenhum dos dois, sobe até 2 pais para dar contexto
    let s = el.tagName.toLowerCase();
    if (el.id) return s + '#' + el.id;
    const cls = typeof el.className === 'string' ? el.className : (el.className && el.className.baseVal) || '';
    if (cls.trim()) return s + '.' + cls.trim().split(/\s+/).slice(0, 2).join('.');
    return el.parentElement && nivel < 2 ? desc(el.parentElement, nivel + 1) + ' > ' + s : s;
  };
  const visivel = el => {
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    for (let a = el; a; a = a.parentElement) {
      const cs = getComputedStyle(a);
      if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.1) return false;
    }
    return true;
  };
  // rolagem horizontal: o primeiro elemento de cada ramo que passa da borda e não está numa caixa com rolagem própria
  if (out.largura_pagina > vw + 1) {
    const recortado = el => { for (let a = el.parentElement; a && a !== document.body; a = a.parentElement)
      if (getComputedStyle(a).overflowX !== 'visible') return true; return false; };
    for (const el of document.body.querySelectorAll('*')) {
      const r = el.getBoundingClientRect(), p = el.parentElement.getBoundingClientRect();
      if (r.right > vw + 1 && p.right <= vw + 1 && !recortado(el)) {
        out.culpados.push(desc(el) + ' (' + Math.round(r.width) + ' px)');
        if (out.culpados.length >= 8) break;
      }
    }
  }
  for (const g of document.querySelectorAll('.js-plotly-plot')) {
    if (!visivel(g)) continue;
    out.graficos++;
    if (!g.querySelector('svg.main-svg, canvas')) out.sem_desenho.push(desc(g));
  }
  // contraste: cor do texto composta sobre as camadas de fundo até a primeira opaca
  const cor = s => { const m = /rgba?\(([^)]+)\)/.exec(s || ''); if (!m) return null;
    const p = m[1].split(/[\s,/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
  const mix = (cima, base) => [0, 1, 2].map(i => cima[i] * cima[3] + base[i] * (1 - cima[3])).concat(1);
  const lum = c => { const f = v => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const hex = c => '#' + c.slice(0, 3).map(v => Math.round(v).toString(16).padStart(2, '0')).join('');
  const fundo = el => {
    const camadas = [];
    for (let a = el; a; a = a.parentElement) {
      const cs = getComputedStyle(a);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') return null;
      const c = cor(cs.backgroundColor);
      if (c && c[3] > 0) { camadas.push(c); if (c[3] >= 1) break; }
    }
    let base = [255, 255, 255, 1];
    for (let i = camadas.length - 1; i >= 0; i--) base = mix(camadas[i], base);
    return base;
  };
  const vistos = new Set();
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const el = n.parentElement;
    if (!n.nodeValue.trim() || !el || vistos.has(el) || /^(SCRIPT|STYLE|OPTION|TEXTAREA)$/.test(el.tagName)) continue;
    vistos.add(el);
    if (!visivel(el)) continue;
    const cs = getComputedStyle(el), svg = el instanceof SVGElement;
    const fg = cor(svg ? cs.fill : cs.color), bg = fundo(el);
    if (!fg || !bg) { out.nao_medidos++; continue; }
    const fo = parseFloat(cs.fillOpacity);
    let op = svg && !isNaN(fo) ? fo : 1;
    for (let a = el; a; a = a.parentElement) { const o = parseFloat(getComputedStyle(a).opacity); if (!isNaN(o)) op *= o; }
    if (fg[3] * op < 0.1) continue;  // texto transparente não aparece para ninguém
    const f = mix([fg[0], fg[1], fg[2], fg[3] * op], bg), L1 = lum(f), L2 = lum(bg);
    const px = parseFloat(cs.fontSize), peso = parseInt(cs.fontWeight, 10) || 400;
    out.textos.push({texto: n.nodeValue.trim().slice(0, 40), elemento: desc(el), cor: hex(f), fundo: hex(bg),
      razao: (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05), px, grande: px >= 24 || (px >= 18.66 && peso >= 700)});
  }
  for (const k of document.querySelectorAll('.kpi')) {
    const lbl = k.querySelector('.lbl'), val = k.querySelector('.val');
    if (lbl && val) out.indicadores.push({rotulo: lbl.textContent.trim(), valor: val.textContent.trim()});
  }
  return out;
}
"""


def _agrupar(itens: list[dict], limite: int = 15) -> list[dict]:
    """Junta falhas iguais (mesmo elemento, cor e fundo) e guarda um exemplo de texto."""
    grupos: dict[tuple, dict] = {}
    for t in itens:
        chave = (t["elemento"], t["cor"], t["fundo"], t.get("minimo"))
        g = grupos.setdefault(chave, {**t, "exemplo": t["texto"], "ocorrencias": 0})
        g["ocorrencias"] += 1
    saida = sorted(grupos.values(), key=lambda g: -g["ocorrencias"])[:limite]
    for g in saida:
        g.pop("texto", None)
        g["razao"] = round(g["razao"], 2)
    return saida


def avaliar(medida: dict) -> dict:
    """Transforma as medidas cruas de uma tela em defeitos e avisos."""
    falhas, pequenos = [], []
    for t in medida["textos"]:
        minimo = 3.0 if t["grande"] else 4.5
        if t["razao"] < minimo:
            falhas.append({**t, "minimo": minimo})
        if t["px"] < 11:
            pequenos.append(t)
    rolagem = medida["largura_pagina"] > medida["largura_tela"] + 1
    tela = {"graficos": medida["graficos"], "sem_desenho": medida["sem_desenho"],
            "largura_pagina": medida["largura_pagina"], "rolagem_horizontal": rolagem,
            "culpados": medida["culpados"] if rolagem else [],
            "textos_medidos": len(medida["textos"]), "nao_medidos": medida["nao_medidos"],
            "contraste_falhas": _agrupar(falhas), "texto_pequeno": _agrupar(pequenos)}
    tela["defeitos"] = len(medida["sem_desenho"]) + int(rolagem) + len(tela["contraste_falhas"])
    tela["avisos"] = len(tela["texto_pequeno"])
    return tela


def _abrir(p, preferido: str | None):
    falhas = []
    for nome in [preferido] if preferido else NAVEGADORES:
        try:
            return p.chromium.launch(channel=None if nome == "chromium" else nome), nome
        except Exception as e:  # noqa: BLE001 - o Playwright usa o mesmo erro genérico para navegador ausente
            falhas.append(f"{nome}: {str(e).splitlines()[0][:120]}")
    raise NavegadorAusente("Nenhum navegador encontrado (" + "; ".join(falhas) + "). "
                           "Instale o Chrome ou o Edge, ou rode: playwright install chromium")


def conferir(arquivo, saida, larguras=(1440, 390), temas=TEMAS, navegador=None, altura=900) -> dict:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    arquivo, saida = Path(arquivo).resolve(), Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    rel = {"arquivo": str(arquivo), "telas": [], "indicadores": [], "defeitos": 0, "avisos": 0}
    with sync_playwright() as p:
        browser, nome = _abrir(p, navegador)
        rel["navegador"] = f"{nome} {browser.version}"
        try:
            for largura in larguras:
                for tema in temas:
                    ctx = browser.new_context(viewport={"width": largura, "height": altura}, reduced_motion="reduce",
                                              color_scheme="dark" if tema == "escuro" else "light")
                    page = ctx.new_page()
                    erros: list[str] = []
                    page.on("console", lambda m, e=erros: e.append(m.text) if m.type == "error" else None)
                    page.on("pageerror", lambda exc, e=erros: e.append(str(exc)))
                    page.goto(arquivo.as_uri(), wait_until="load", timeout=60_000)
                    try:
                        page.wait_for_load_state("networkidle", timeout=15_000)
                    except PlaywrightError:
                        pass  # página que nunca para de pedir rede: confere assim mesmo
                    page.wait_for_timeout(700)  # gráficos 3D e transições do Plotly terminam de desenhar
                    medida = page.evaluate(MEDIR_JS)
                    foto = saida / f"tela_{largura}_{tema}.png"
                    page.screenshot(path=str(foto), full_page=True)
                    ctx.close()
                    tela = {"largura": largura, "tema": tema, "foto": str(foto), "erros": erros, **avaliar(medida)}
                    tela["defeitos"] += len(erros)
                    rel["telas"].append(tela)
                    rel["indicadores"] = rel["indicadores"] or medida["indicadores"]
        finally:
            browser.close()
    rel["defeitos"] = sum(t["defeitos"] for t in rel["telas"])
    rel["avisos"] = sum(t["avisos"] for t in rel["telas"])
    (saida / "relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
    return rel


def _br(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def resumo(rel: dict) -> str:
    linhas = [f"Navegador: {rel.get('navegador', '?')}"]
    for t in rel["telas"]:
        linhas.append(f"Tela {t['largura']} px, tema {t['tema']}: {t['defeitos']} defeito(s), {t['avisos']} aviso(s), "
                      f"{t['graficos']} gráfico(s), {t['textos_medidos']} textos medidos -> {t['foto']}")
        linhas += [f"  - erro de script: {e[:160]}" for e in t["erros"]]
        linhas += [f"  - gráfico não desenhou: {g}" for g in t["sem_desenho"]]
        if t["rolagem_horizontal"]:
            linhas.append(f"  - página com {t['largura_pagina']} px numa tela de {t['largura']} px; passam da borda: "
                          + ", ".join(t["culpados"][:4]))
        linhas += [f"  - contraste {_br(f['razao'])}:1 (mínimo {_br(f['minimo'])}) em {f['elemento']} "
                   f"\"{f['exemplo']}\" ({f['cor']} sobre {f['fundo']}, {f['ocorrencias']}x)" for f in t["contraste_falhas"]]
        linhas += [f"  - aviso: texto de {_br(f['px'])} px em {f['elemento']} \"{f['exemplo']}\"" for f in t["texto_pequeno"]]
    if rel["indicadores"]:
        linhas.append("Indicadores: " + "; ".join(f"{k['rotulo']} = {k['valor']}" for k in rel["indicadores"]))
    linhas.append(f"Total: {rel['defeitos']} defeito(s), {rel['avisos']} aviso(s). Abra as fotos antes de entregar.")
    return "\n".join(linhas)


def main(argv=None) -> int:
    for fluxo in (sys.stdout, sys.stderr):  # saída redirecionada no Windows sairia em cp1252, com acentos trocados
        try:
            fluxo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivo")
    ap.add_argument("--saida", required=True, help="Pasta para as fotos e o relatorio.json")
    ap.add_argument("--larguras", nargs="+", type=int, default=[1440, 390])
    ap.add_argument("--temas", nargs="+", choices=TEMAS, default=list(TEMAS))
    ap.add_argument("--navegador", choices=NAVEGADORES, help="Padrão: o primeiro que abrir, nesta ordem")
    a = ap.parse_args(argv)
    if not Path(a.arquivo).is_file():
        print(f"Arquivo não encontrado: {a.arquivo}", file=sys.stderr)
        return 2
    try:
        rel = conferir(a.arquivo, a.saida, a.larguras, a.temas, a.navegador)
    except ImportError:
        print("Falta o Playwright para Python: pip install playwright (ou uv sync --group visual).", file=sys.stderr)
        return 2
    except NavegadorAusente as e:
        print(e, file=sys.stderr)
        return 2
    print(resumo(rel))
    return 1 if rel["defeitos"] else 0


if __name__ == "__main__":
    sys.exit(main())
