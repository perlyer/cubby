# Contributing to cubby

Thanks for your interest in `cubby`. Bug reports, fixes, and new agent adapters are all
welcome.

## Development setup

`cubby` is Python 3.11+ and depends only on the standard library — the only external
runtime requirement is the [`age`](https://github.com/FiloSottile/age) binary. `pytest`
is the sole development dependency.

```bash
git clone https://github.com/perlyer/cubby.git
cd cubby
python3 -m venv .venv
.venv/bin/pip install pytest
brew install age            # Linux: github.com/FiloSottile/age/releases
```

Run the test suite:

```bash
.venv/bin/pytest
```

The tests use the real `age` binary (no mocks) and run against temporary directories,
so they are safe to run anywhere.

## Ground rules

- **Standard library only.** `cubby` has zero runtime dependencies and intends to keep
  it that way. Do not add packages from PyPI.
- **Test-driven.** Every change comes with tests. Write the failing test first.
- **Small, focused commits** with plain, descriptive messages.

## Adding a new agent adapter

Agent integrations are deliberately easy to add — one file each.

1. Create `cubby_tool/agents/<name>.py` with a class that extends
   `cubby_tool.agents.base.Adapter` and implements `detect()`, `install()`,
   `uninstall()`, and `_installed()`. Render the integration text from the shared
   `cubby_tool.agents.guidance.GUIDANCE` constant — do not hand-write a new copy.
   Expose a module-level `adapter` instance.
2. Register it in `cubby_tool/agents/__init__.py` by adding `<name>.adapter` to the
   `ADAPTERS` tuple.
3. Add `tests/test_agent_<name>.py` covering `detect`, `install`, idempotency,
   `uninstall`, and `status` against a faked `$HOME`.

The existing adapters (`codex.py` for the section-in-a-shared-file pattern, `cursor.py`
for the standalone-file pattern) are good templates.

## Pull requests

Open a PR against `main` with a clear description of what changed and why. Make sure
`.venv/bin/pytest` is green. For anything security-sensitive, see [SECURITY.md](SECURITY.md).
