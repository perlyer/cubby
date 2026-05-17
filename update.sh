#!/bin/sh
# cubby updater: updates an installed cubby to the latest release tag and
# refreshes agent integrations. Operates on the git checkout this script lives in.
set -eu

REPO="$(cd "$(dirname "$0")" && pwd)"

# --- styling (colour only on an interactive terminal, off when NO_COLOR is set) ---
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  C_GREEN="$(printf '\033[32m')"; C_DIM="$(printf '\033[2m')"
  C_BOLD="$(printf '\033[1m')";  C_CYAN="$(printf '\033[36m')"
  C_RESET="$(printf '\033[0m')"
else
  C_GREEN=""; C_DIM=""; C_BOLD=""; C_CYAN=""; C_RESET=""
fi
step()   { printf '%s\n' "${C_BOLD}==>${C_RESET} $1"; }
ok()     { printf '%s\n' "${C_GREEN}✓${C_RESET} $1"; }
note()   { printf '%s\n' "${C_DIM}$1${C_RESET}"; }
banner() {
  [ -t 1 ] || return 0
  printf '%s' "$C_CYAN"
  cat <<'ART'
         _    _
 __ _  _| |__| |__ _  _
/ _| || | '_ \ '_ \ || |
\__|\_,_|_.__/_.__/\_, |
                   |__/
  encrypted secret store
ART
  printf '%s\n' "$C_RESET"
}

banner

step "Checking the cubby checkout"
if ! git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1; then
  echo "cubby: $REPO is not a git checkout — cannot self-update" >&2
  exit 1
fi
if ! git -C "$REPO" remote get-url origin >/dev/null 2>&1; then
  echo "cubby: no 'origin' remote — cannot self-update" >&2
  exit 1
fi
if [ -n "$(git -C "$REPO" status --porcelain)" ]; then
  echo "cubby: working tree at $REPO is dirty — commit or stash, then retry" >&2
  exit 1
fi
ok "clean git checkout"

step "Fetching release tags"
git -C "$REPO" fetch --tags --quiet origin
LATEST="$(git -C "$REPO" tag --list 'v*' --sort=-v:refname | head -1)"
if [ -z "$LATEST" ]; then
  echo "cubby: no release tags found on origin" >&2
  exit 1
fi
ok "latest release is $LATEST"

CURRENT="$(git -C "$REPO" describe --tags --exact-match 2>/dev/null || echo '')"
if [ "$CURRENT" = "$LATEST" ]; then
  ok "already on the latest release $LATEST"
  exit 0
fi

step "Updating to $LATEST"
git -C "$REPO" checkout --quiet "$LATEST"
ok "updated → $LATEST"

step "Re-linking cubby onto your PATH"
mkdir -p "$HOME/.local/bin"
ln -sf "$REPO/cubby" "$HOME/.local/bin/cubby"
ok "linked $HOME/.local/bin/cubby"

step "Refreshing agent integrations"
"$REPO/cubby" agent refresh

ok "cubby updated to $LATEST"
