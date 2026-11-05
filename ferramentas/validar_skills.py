"""Valida a estrutura do repositório: frontmatter das skills, links locais, JSON e scripts.

Uso: python ferramentas/validar_skills.py   (sai com código 1 se houver erro)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
if not skills:
    errors.append("nenhuma skill encontrada")
names = set()
for sk in skills:
    text = sk.read_text(encoding="utf-8")
    fm = frontmatter(text)
    folder = sk.parent.name
    if fm.get("name") != folder:
        errors.append(f"{sk}: name '{fm.get('name')}' difere da pasta '{folder}'")
    if not (50 <= len(fm.get("description", "")) <= 1024):
        errors.append(f"{sk}: description ausente ou fora de 50-1024 caracteres")
    if fm.get("name") in names:
        errors.append(f"{sk}: nome duplicado")
    names.add(fm.get("name"))
    if len(text.splitlines()) > 500:
        errors.append(f"{sk}: mais de 500 linhas")

for md in list((ROOT / "skills").rglob("*.md")) + [ROOT / "README.md"] + list((ROOT / "docs").glob("*.md")):
    for link in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if link.startswith(("http://", "https://", "mailto:")):
            continue
        if not (md.parent / link).exists():
            errors.append(f"{md.relative_to(ROOT)}: link quebrado -> {link}")

for js in [*ROOT.glob(".claude-plugin/*.json"), ROOT / ".mcp.json", *ROOT.glob("mcp/*.json")]:
    try:
        json.loads(js.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        errors.append(f"{js.relative_to(ROOT)}: JSON inválido ({e})")

scripts = ROOT / "skills" / "analise-dados" / "scripts"
for py in sorted(scripts.glob("*.py")):
    if py.name == "io_br.py":
        continue
    r = subprocess.run([sys.executable, str(py), "--help"], capture_output=True, text=True, cwd=scripts)
    if r.returncode != 0:
        errors.append(f"{py.name} --help falhou: {r.stderr.strip()[-300:]}")

if errors:
    print("ERROS:\n- " + "\n- ".join(errors))
    sys.exit(1)
print(f"OK: {len(skills)} skills, links, JSON e {len(list(scripts.glob('*.py'))) - 1} scripts válidos")
