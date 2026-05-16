#!/bin/sh
# cubby bootstrap installer: puts cubby on PATH, runs init, installs agent integrations.
set -eu

REPO="$(cd "$(dirname "$0")" && pwd)"
KEY_MODE="file"
AGENTS=""

while [ $# -gt 0 ]; do
  case "$1" in
    --key-mode)
      [ $# -ge 2 ] || { echo "cubby: --key-mode requires a value" >&2; exit 2; }
      KEY_MODE="$2"; shift 2 ;;
    --agent)
      [ $# -ge 2 ] || { echo "cubby: --agent requires a value" >&2; exit 2; }
      AGENTS="$2"; shift 2 ;;
    -h|--help)
      echo "usage: ./install.sh [--key-mode file|keychain] [--agent name,name,...]"
      exit 0 ;;
    *) echo "cubby: unknown option: $1" >&2; exit 2 ;;
  esac
done

# 1. Python
if ! command -v python3 >/dev/null 2>&1; then
  echo "cubby: python3 (3.11+) is required" >&2
  exit 1
fi

# 2. age toolchain
if ! command -v age >/dev/null 2>&1 || ! command -v age-keygen >/dev/null 2>&1; then
  echo "cubby: the 'age' toolchain is required." >&2
  echo "  macOS:  brew install age" >&2
  echo "  Linux:  https://github.com/FiloSottile/age/releases" >&2
  exit 1
fi

# 3. cubby on PATH
mkdir -p "$HOME/.local/bin"
ln -sf "$REPO/cubby" "$HOME/.local/bin/cubby"
echo "cubby: linked $HOME/.local/bin/cubby -> $REPO/cubby"
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo "cubby: add ~/.local/bin to your PATH:" >&2
     echo '  export PATH="$HOME/.local/bin:$PATH"' >&2 ;;
esac

CUBBY="$REPO/cubby"

# 4. init
if [ -f "$HOME/.config/cubby/config.json" ]; then
  echo "cubby: already initialized"
else
  "$CUBBY" init --key-mode "$KEY_MODE"
fi

# 5. agent integrations
if [ -z "$AGENTS" ]; then
  echo "cubby: agent integration status —"
  "$CUBBY" agent list
  printf "cubby: agents to integrate (comma-separated, empty to skip): "
  read -r AGENTS || AGENTS=""
fi
if [ -n "$AGENTS" ]; then
  OLD_IFS="$IFS"
  IFS=","
  for a in $AGENTS; do
    IFS="$OLD_IFS"
    name="$(echo "$a" | tr -d ' ')"
    if [ -n "$name" ]; then
      "$CUBBY" agent add "$name" \
        || echo "cubby: warning: could not install '$name' — skipping" >&2
    fi
    IFS=","
  done
  IFS="$OLD_IFS"
fi

echo "cubby: done."
