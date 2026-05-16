---
name: cubby
description: Use when a task needs a password, API token, or connection string — resolve secrets through the `cubby` CLI instead of reading plaintext. Covers `cubby run`, `cubby get`, namespaces.
---

# cubby — using secrets safely

`cubby` is a namespaced encrypted secret store. Use it so secret values never enter your context.

## Rules

1. **To use a secret, wrap the command:** `cubby run -- <command>`. This injects the
   namespace's secrets as environment variables into the child process. You never see
   the values.
2. **Never run `cubby get <name> --reveal`.** `--reveal` prints plaintext and is for
   humans only. Use `cubby get <name>` (no flag) to confirm a secret exists — it shows
   only metadata.
3. **Namespaces are auto-detected from the working directory.** Check with `cubby ns`.
   Override with `-n <namespace>` when needed.

## Examples

Connect to a database without seeing the password:
```
cubby run -n nord -- psql -h 127.0.0.1 -p 5433 -U nord_admin -d nord_database
```

Check a secret exists (no value shown):
```
cubby get clickup-token -n nord
```

List secret names in a namespace:
```
cubby list -n nord
```
