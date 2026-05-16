"""Canonical cubby usage convention, rendered by each agent adapter."""

GUIDANCE = """\
cubby is a namespaced encrypted secret store. Use it so secret values never enter your context.

1. To use a secret, wrap the command: `cubby run -- <command>`. cubby injects the
   namespace's secrets as environment variables into the child process — you never
   see the values.
2. Never run `cubby get <name> --reveal`. The `--reveal` flag prints plaintext and is
   for humans only. Use `cubby get <name>` (no flag) to check that a secret exists.
3. Namespaces are auto-detected from the working directory. Check with `cubby ns`;
   override with `-n <namespace>`.
"""
