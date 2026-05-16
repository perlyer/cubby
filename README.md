# cubby

Namespaced encrypted secret store for AI coding agents.

`cubby` keeps secrets encrypted on disk (via [`age`](https://github.com/FiloSottile/age))
and hands them to commands so their plaintext never lands in an agent's context: the
agent references a secret by name, `cubby` injects it into a child process's environment.

## Install

```bash
brew install age          # required: age + age-keygen (Linux: github.com/FiloSottile/age/releases)
git clone <repo-url> cubby && cd cubby && ./install.sh
```

`install.sh` puts `cubby` on your PATH, runs `cubby init`, and offers to install the
integration into any AI coding agents it finds. Non-interactive:

```bash
./install.sh --key-mode keychain --agent claude-code,codex
```

`--key-mode keychain` (macOS) stores the age key in the login Keychain so it unlocks
automatically at login; default `--key-mode file` keeps it in `~/.config/cubby/identity` (0600).

## Namespaces

A namespace is a workspace/environment (`work`, `personal`, …). The active namespace is
resolved per command: `-n <name>` flag → `$CUBBY_NS` → working-directory prefix match →
default.

```bash
cubby ns add work --cwd-prefix ~/projects/work
cubby ns                  # show active namespace and why
```

Per-namespace `env_map` (which env var each secret becomes under `cubby run`) is edited
directly in `~/.config/cubby/config.json`, e.g. `"db-prod-password": "PGPASSWORD"`.

## Usage

```bash
cubby set db-prod-password          # hidden prompt; or: cubby set NAME --stdin
cubby get db-prod-password          # metadata only — no value printed
cubby list                          # secret names
cubby run -- psql -h 127.0.0.1 ...  # secrets injected as env vars
cubby import --from-env .env        # bulk import; also --from-aws <secret-id>
```

`cubby get <name> --reveal` prints plaintext — for human use only.

## Agent integration

`cubby agent` installs a small integration (a skill / instructions file, plus permissions
where supported) so an agent uses `cubby run` for secrets instead of reading plaintext.

```bash
cubby agent list                 # adapters and their status
cubby agent add claude-code      # install integration for one agent
cubby agent rm claude-code       # remove it
```

Supported agents: `claude-code`, `codex`, `gemini`, `cursor`, `copilot`.

Claude Code users can alternatively use the native plugin marketplace:

```
/plugin marketplace add <repo-url>
/plugin install cubby
```
