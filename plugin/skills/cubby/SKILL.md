---
name: cubby
description: Use when a task needs a password, API token, or connection string — resolve secrets through the `cubby` CLI instead of reading plaintext.
---

# cubby — using secrets safely

cubby is a namespaced encrypted secret store. Use it so secret values never enter your context.

1. To use a secret, wrap the command: `cubby run -- <command>`. cubby injects the
   namespace's secrets as environment variables into the child process — you never
   see the values.
2. Never run `cubby get <name> --reveal` or `cubby get <name> --copy`. Both disclose
   the plaintext — `--reveal` prints it, `--copy` copies it to the clipboard — and are
   for humans only. Use `cubby get <name>` (no flag) to check that a secret exists.
3. Namespaces are auto-detected from the working directory. Check with `cubby ns`;
   override with `-n <namespace>`.
