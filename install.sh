#!/bin/sh
# cubby bootstrap installer: puts cubby on PATH, runs init, installs agent integrations.
set -eu

REPO="$(cd "$(dirname "$0")" && pwd)"
KEY_MODE="file"
AGENTS=""

# --- styling (colour only on an interactive terminal, off when NO_COLOR is set) ---
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  C_GREEN="$(printf '\033[32m')"; C_DIM="$(printf '\033[2m')"
  C_BOLD="$(printf '\033[1m')";  C_RESET="$(printf '\033[0m')"
else
  C_GREEN=""; C_DIM=""; C_BOLD=""; C_RESET=""
fi
step() { printf '%s\n' "${C_BOLD}==>${C_RESET} $1"; }
ok()   { printf '%s\n' "${C_GREEN}✓${C_RESET} $1"; }
note() { printf '%s\n' "${C_DIM}$1${C_RESET}"; }

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

step "Checking prerequisites"
if ! command -v python3 >/dev/null 2>&1; then
  echo "cubby: python3 (3.11+) is required" >&2
  exit 1
fi
if ! command -v age >/dev/null 2>&1 || ! command -v age-keygen >/dev/null 2>&1; then
  echo "cubby: the 'age' toolchain is required." >&2
  echo "  macOS:  brew install age" >&2
  echo "  Linux:  https://github.com/FiloSottile/age/releases" >&2
  exit 1
fi
ok "python3 and age found"

step "Linking cubby onto your PATH"
mkdir -p "$HOME/.local/bin"
ln -sf "$REPO/cubby" "$HOME/.local/bin/cubby"
ok "linked $HOME/.local/bin/cubby"
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) note "add ~/.local/bin to your PATH:"
     note '  export PATH="$HOME/.local/bin:$PATH"' ;;
esac

CUBBY="$REPO/cubby"

step "Initializing the secret store"
if [ -f "$HOME/.config/cubby/config.json" ]; then
  note "already initialized"
else
  "$CUBBY" init --key-mode "$KEY_MODE"
fi

step "Agent integrations"
if [ -z "$AGENTS" ]; then
  "$CUBBY" agent list
  printf 'cubby: agents to integrate (comma-separated, empty to skip): '
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

ok "cubby is installed — run 'cubby ns' to get started"
