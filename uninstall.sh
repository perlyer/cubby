#!/bin/sh
# cubby uninstaller: removes the cubby symlink and agent integrations.
# The secret store ~/.config/cubby/ is kept unless --purge is given or you
# confirm at the interactive prompt.
set -eu

PURGE=0
STORE="${CUBBY_HOME:-$HOME/.config/cubby}"

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
    --purge) PURGE=1; shift ;;
    -h|--help)
      echo "usage: ./uninstall.sh [--purge]"
      echo "  --purge   also delete the secret store ($STORE)"
      exit 0 ;;
    *) echo "cubby: unknown option: $1" >&2; exit 2 ;;
  esac
done

CUBBY="$HOME/.local/bin/cubby"

step "Removing agent integrations"
if [ -x "$CUBBY" ]; then
  # agent list — keep in sync with cubby_tool/agents/__init__.py
  for agent in claude-code codex gemini cursor copilot; do
    "$CUBBY" agent rm "$agent" >/dev/null 2>&1 || true
  done
  ok "agent integrations removed"
else
  note "cubby not on PATH — skipping agent integrations"
fi

step "Removing the cubby symlink"
if [ -L "$CUBBY" ]; then
  rm -f "$CUBBY"
  ok "removed $CUBBY"
else
  note "no symlink at $CUBBY"
fi

step "Secret store"
if [ ! -d "$STORE" ]; then
  note "no secret store at $STORE"
elif [ "$PURGE" -eq 1 ]; then
  rm -rf "$STORE"
  ok "purged secret store $STORE"
elif [ -t 0 ]; then
  printf 'delete the secret store %s? [y/N] ' "$STORE"
  read -r answer || answer=""
  case "$answer" in
    [yY]*) rm -rf "$STORE"; ok "purged secret store $STORE" ;;
    *)     note "kept secret store $STORE" ;;
  esac
else
  note "kept secret store $STORE (pass --purge to delete it)"
fi

ok "cubby uninstalled"
