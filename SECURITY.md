# Security

`cubby` exists to keep secrets out of an AI agent's context. It is important to be
precise about what that does and does not buy you.

## Threat model

### What cubby protects against

- **Secrets in an agent's context/transcript.** The agent runs `cubby run -- <cmd>`;
  `cubby` injects secret values into the child process's environment and never prints
  them. The agent sees the command's output, not the secret. `cubby get` shows only
  metadata unless `--reveal` is passed.
- **Plaintext secrets at rest.** Each namespace is stored as an `age`-encrypted file.
  Nothing is written to disk in cleartext.
- **Secrets in shell history / process arguments.** `cubby set` reads the value from a
  hidden prompt (or stdin), never from `argv`.
- **Wrong-namespace leakage.** Namespace resolution matches working-directory prefixes
  on path boundaries, so `/p/project` is never treated as part of `/p/proj`.

### What cubby does NOT protect against

- **A compromised machine or a malicious local user with your privileges.** Anyone who
  can read the age identity (`~/.config/cubby/identity`, mode `0600`, or the login
  Keychain) *and* the encrypted namespace files can decrypt every secret. `cubby` does
  not defend against an attacker who is already you on your machine.
- **An agent that runs arbitrary code.** An agent is not sandboxed by `cubby`. It can
  run `cubby get --reveal`, read the identity file directly, or `cubby run` a command
  that exfiltrates the value. The integration (`cubby agent`) installs a *convention*
  that well-behaved agents follow — it is a guardrail against accidental leakage, not
  an enforcement boundary.
- **Other processes you own.** A decrypted value lives in the environment of the child
  process spawned by `cubby run`. On some platforms another process running as the same
  user can inspect that environment.
- **Key loss.** If you lose the age identity, the encrypted namespaces are
  unrecoverable. `cubby` has no escrow or recovery mechanism. Back up the identity
  yourself.

In short: `cubby` raises the floor — secrets stop leaking into prompts, logs, and
transcripts by accident — but it trusts your machine and the code your agent runs.

## Hardening for AI agents

`cubby get --reveal` prints a secret in plaintext — it is the one deliberate escape
hatch, meant for a human at a terminal. The `cubby agent` integration *asks* an agent
not to use it, but that is a convention, not a wall.

Where your agent has a permission system, turn the convention into an enforced rule.
For **Claude Code**, add a deny rule to `~/.claude/settings.json`:

```json
{
  "permissions": {
    "deny": ["Bash(cubby get* --reveal*)"]
  }
}
```

With this in place Claude Code refuses to run any `cubby get … --reveal` invocation —
the agent cannot reveal a secret even if instructed to. Other agents that support
command allow/deny lists can be locked down the same way.

This does not close every hole — an agent that runs arbitrary code can still read the
identity file or `cubby run` a command that exfiltrates the value (see above) — but it
removes the easiest one.

## Reporting a vulnerability

Please do not open a public issue for security problems. Report them privately via
GitHub's [security advisory](https://github.com/perlyer/cubby/security/advisories/new)
form. You will get an acknowledgement, and a fix or mitigation will be coordinated
before any public disclosure.
