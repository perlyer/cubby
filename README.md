# cubby

Namespaced encrypted secret store for AI coding agents.

`cubby` keeps secrets encrypted on disk (via [`age`](https://github.com/FiloSottile/age))
and hands them to commands so their plaintext never lands in an agent's context: the
agent references a secret by name, `cubby` injects it into a child process's environment.

## Install

```bash
brew install age          # required: age + age-keygen
git clone <repo-url> cubby
ln -s "$PWD/cubby/cubby" ~/.local/bin/cubby   # put `cubby` on PATH
cubby init                # creates ~/.config/cubby, generates an age key
```

`cubby init --key-mode keychain` (macOS) stores the age key in the login Keychain so it
unlocks automatically at login. Default `--key-mode file` keeps it in
`~/.config/cubby/identity` (0600).

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

## Claude Code integration

Install the plugin in `plugin/` (skill + `/cubby` command), and merge
`docs/settings-snippet.json` into your `settings.json` so `cubby run/get/list/ns` run
without prompts while `--reveal` stays blocked.
