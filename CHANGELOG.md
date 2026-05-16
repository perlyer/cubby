# Changelog

All notable changes to `cubby` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project adheres to
[Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-05-17

First release.

### Added

- Namespaced encrypted secret store — secrets per namespace in `age`-encrypted files,
  with `init`, `set`, `get`, `list`, `rm`, and `ns` commands.
- `cubby run -- <command>` — runs a command with the namespace's secrets injected as
  environment variables; values never reach stdout or the caller's context.
- `--reveal` flag on `cubby get` — the single, explicit path to plaintext, for human use.
- `cubby import` — bulk import from a `.env` file or AWS Secrets Manager.
- `cubby agent` — one-command integration for Claude Code, Codex, Gemini CLI, Cursor,
  and Copilot CLI, driven by a pluggable adapter system.
- `install.sh` — bootstrap installer: puts `cubby` on `PATH`, runs `init`, installs
  agent integrations.
- Claude Code plugin marketplace manifest for native `/plugin` installation.
- Two key-storage modes: an `0600` identity file, or the macOS login Keychain.

[0.1.0]: https://github.com/perlyer/cubby/releases/tag/v0.1.0
