#!/usr/bin/env sh
# Instala as skills em ~/.claude/skills (e em ~/.agents/skills com --codex).
# Não sobrescreve skill existente sem --sobrescrever; a versão anterior vira .bak-<data>.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
CODEX=0; SOBRE=0
for a in "$@"; do
  case "$a" in
    --codex) CODEX=1 ;;
    --sobrescrever) SOBRE=1 ;;
    *) echo "opção desconhecida: $a"; exit 2 ;;
  esac
done
DESTS="$HOME/.claude/skills"
[ "$CODEX" = 1 ] && DESTS="$DESTS $HOME/.agents/skills"
for dest in $DESTS; do
  mkdir -p "$dest"
  for s in "$DIR"/skills/*/; do
    nome=$(basename "$s"); alvo="$dest/$nome"
    if [ -e "$alvo" ]; then
      if [ "$SOBRE" = 0 ]; then echo "Já existe: $alvo (use --sobrescrever)"; continue; fi
      mv "$alvo" "$alvo.bak-$(date +%Y%m%d%H%M%S)"
    fi
    cp -R "$s" "$alvo"; echo "Instalada: $alvo"
  done
done
echo "Pronto. Dependências Python: pip install -r requirements.txt"
