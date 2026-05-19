import os
import sys

from cubby_tool import audit, config, keyring, store, style
from cubby_tool.commands._common import (
    _format_relative, _is_expired, _resolve, _resolve_env_var,
)


def cmd_run(args):
    home, cfg, ns, _ = _resolve(args)
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print(style.fail("run: no command given (usage: cubby run -- <cmd>)"),
              file=sys.stderr)
        return 2
    identity = keyring.load_identity(home, cfg.key_mode)
    entries = store.read_entries(home, ns, identity)
    if args.only is not None:
        wanted = [n.strip() for n in args.only.split(",") if n.strip()]
        missing = [n for n in wanted if n not in entries]
        if missing:
            print(style.fail(f"run: no such secret(s): {', '.join(missing)}"),
                  file=sys.stderr)
            return 4
        entries = {n: entries[n] for n in wanted}
    elif args.exclude is not None:
        unwanted = [n.strip() for n in args.exclude.split(",") if n.strip()]
        missing = [n for n in unwanted if n not in entries]
        if missing:
            print(style.fail(f"run: no such secret(s): {', '.join(missing)}"),
                  file=sys.stderr)
            return 4
        entries = {n: e for n, e in entries.items() if n not in unwanted}
    env_map = cfg.namespaces.get(ns, config.Namespace()).env_map
    child_env = dict(os.environ)
    for name, entry in entries.items():
        if _is_expired(entry):
            print(f"cubby: warning: secret '{name}' in namespace '{ns}' "
                  f"{_format_relative(entry['expires'])}", file=sys.stderr)
        child_env[_resolve_env_var(env_map, name)] = entry["value"]
    audit.log_event(home, cfg.audit, "run", ns, " ".join(command))
    try:
        os.execvpe(command[0], command, child_env)
    except FileNotFoundError:
        print(style.fail(f"run: command not found: {command[0]}"), file=sys.stderr)
        return 2
