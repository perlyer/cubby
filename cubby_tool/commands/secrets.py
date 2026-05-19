import getpass
import shutil
import subprocess
import sys

from cubby_tool import audit, config, keyring, store, style
from cubby_tool.commands._common import (
    _env_var_clash, _env_var_name, _format_relative, _resolve,
    _resolve_env_var, _ttl_to_expires,
)


def cmd_set(args):
    home, cfg, ns, _ = _resolve(args)
    identity = keyring.load_identity(home, cfg.key_mode)
    recipient = keyring.public_key(identity)
    namespace = cfg.namespaces.setdefault(ns, config.Namespace())
    if args.env:
        names = store.list_names(home, ns, identity)
        clash = _env_var_clash(namespace.env_map, names, args.env, args.name)
        if clash:
            print(style.fail(f"env var '{args.env}' already used by secret '{clash}'"),
                  file=sys.stderr)
            return 4
    meta = None
    if args.ttl is not None:
        meta = {"ttl": args.ttl, "expires": _ttl_to_expires(args.ttl)}
    if args.stdin:
        value = sys.stdin.read().rstrip("\n")
    else:
        value = getpass.getpass(f"value for '{args.name}': ")
    store.set_secret(home, ns, args.name, value, identity, recipient, meta=meta)
    if args.env:
        namespace.env_map[args.name] = args.env
        config.save_config(home, cfg)
    print(style.ok(f"secret '{args.name}' set in namespace '{ns}'"))
    return 0


def cmd_rotate(args):
    home, cfg, ns, _ = _resolve(args)
    identity = keyring.load_identity(home, cfg.key_mode)
    recipient = keyring.public_key(identity)
    entries = store.read_entries(home, ns, identity)
    if args.name not in entries:
        print(style.fail(f"secret '{args.name}' not found in namespace '{ns}'"),
              file=sys.stderr)
        return 4
    prev = entries[args.name]
    if args.ttl == "none":
        meta = {}
    elif args.ttl is not None:
        meta = {"ttl": args.ttl, "expires": _ttl_to_expires(args.ttl)}
    elif prev.get("ttl"):
        meta = {"ttl": prev["ttl"], "expires": _ttl_to_expires(prev["ttl"])}
    else:
        meta = {}
    if args.stdin:
        value = sys.stdin.read().rstrip("\n")
    else:
        value = getpass.getpass(f"new value for '{args.name}': ")
    store.rotate_secret(home, ns, args.name, value, identity, recipient, meta=meta)
    print(style.ok(f"secret '{args.name}' rotated in namespace '{ns}'"))
    return 0


def cmd_ttl(args):
    home, cfg, ns, _ = _resolve(args)
    identity = keyring.load_identity(home, cfg.key_mode)
    recipient = keyring.public_key(identity)
    entries = store.read_entries(home, ns, identity)

    if args.name is None:
        if not entries:
            print(style.dim(f"no secrets in namespace '{ns}'"))
            return 0
        width = max(len(n) for n in entries)
        lines = []
        for name in sorted(entries):
            exp = entries[name].get("expires")
            if not exp:
                detail = style.dim("no expiry")
            else:
                detail = f"{exp}  {style.dim('(' + _format_relative(exp) + ')')}"
            lines.append(f" {name.ljust(width)}  {detail}")
        print(style.box(lines, title=f"ttl · {ns}"))
        return 0

    if args.name not in entries:
        print(style.fail(f"secret '{args.name}' not found in namespace '{ns}'"),
              file=sys.stderr)
        return 4
    entry = entries[args.name]

    if args.duration is None:
        exp = entry.get("expires")
        if not exp:
            print(f"{args.name}: no expiry")
        else:
            print(f"{args.name}: expires {exp} ({_format_relative(exp)})")
        return 0

    if args.duration == "none":
        if "ttl" not in entry and "expires" not in entry:
            print(style.dim(f"'{args.name}' has no expiry"))
            return 0
        entry.pop("ttl", None)
        entry.pop("expires", None)
        store.write_entries(home, ns, entries, recipient)
        print(style.ok(f"expiry cleared for '{args.name}'"))
        return 0

    entry["ttl"] = args.duration
    entry["expires"] = _ttl_to_expires(args.duration)
    store.write_entries(home, ns, entries, recipient)
    print(style.ok(f"'{args.name}' expires {entry['expires']} "
                   f"({_format_relative(entry['expires'])})"))
    return 0


def cmd_map(args):
    home, cfg, ns, _ = _resolve(args)
    namespace = cfg.namespaces.get(ns, config.Namespace())
    identity = keyring.load_identity(home, cfg.key_mode)
    names = store.list_names(home, ns, identity)

    if args.name is None:
        if not names:
            print(style.dim(f"no secrets in namespace '{ns}'"))
            return 0
        width = max(len(n) for n in names)
        lines = []
        for name in names:
            var = _resolve_env_var(namespace.env_map, name)
            kind = "override" if name in namespace.env_map else "default"
            lines.append(f" {name.ljust(width)}  {style.green(var)}  {style.dim(kind)}")
        print(style.box(lines, title=f"env map · {ns}"))
        return 0

    if args.name not in names:
        print(style.fail(f"secret '{args.name}' not found in namespace '{ns}'"),
              file=sys.stderr)
        return 4

    if args.reset:
        namespace = cfg.namespaces.setdefault(ns, config.Namespace())
        if args.name in namespace.env_map:
            del namespace.env_map[args.name]
            config.save_config(home, cfg)
            print(style.ok(f"'{args.name}' reset to default env var "
                           f"'{_env_var_name(args.name)}'"))
        else:
            print(style.dim(f"'{args.name}' already uses the default env var"))
        return 0

    if args.var is not None:
        clash = _env_var_clash(namespace.env_map, names, args.var, args.name)
        if clash:
            print(style.fail(f"env var '{args.var}' already used by secret '{clash}'"),
                  file=sys.stderr)
            return 4
        namespace = cfg.namespaces.setdefault(ns, config.Namespace())
        namespace.env_map[args.name] = args.var
        config.save_config(home, cfg)
        print(style.ok(f"'{args.name}' → env var '{args.var}'"))
        return 0

    var = _resolve_env_var(namespace.env_map, args.name)
    kind = "override" if args.name in namespace.env_map else "default"
    print(f"{args.name} → {var} ({kind})")
    return 0


def cmd_get(args):
    home, cfg, ns, _ = _resolve(args)
    identity = keyring.load_identity(home, cfg.key_mode)
    entries = store.read_entries(home, ns, identity)
    if args.name not in entries:
        print(style.fail(f"secret '{args.name}' not found in namespace '{ns}'"),
              file=sys.stderr)
        return 4
    entry = entries[args.name]
    if args.reveal:
        audit.log_event(home, cfg.audit, "reveal", ns, args.name)
        print("WARNING: revealing secret plaintext to stdout", file=sys.stderr)
        print(entry["value"])
    elif args.copy:
        try:
            tool = _copy_to_clipboard(entry["value"])
        except RuntimeError as e:
            print(style.fail(str(e)), file=sys.stderr)
            return 2
        audit.log_event(home, cfg.audit, "copy", ns, args.name)
        print(style.ok(f"copied '{args.name}' to clipboard ({tool})"))
    else:
        namespace = cfg.namespaces.get(ns, config.Namespace())
        var = _resolve_env_var(namespace.env_map, args.name)
        kind = "override" if args.name in namespace.env_map else "default"
        exp = entry.get("expires")
        expires_line = f"{exp} ({_format_relative(exp)})" if exp else "never"
        rotated = entry.get("rotated", 0)
        rotated_line = "never" if rotated == 0 else (
            f"{rotated} time{'s' if rotated != 1 else ''}")
        lines = [
            f" {style.dim('name:')} {args.name}",
            f" {style.dim('namespace:')} {ns}",
            f" {style.dim('env var:')} {var} ({kind})",
            f" {style.dim('length:')} {len(entry['value'])}",
            f" {style.dim('updated:')} {entry.get('updated', '-')}",
            f" {style.dim('expires:')} {expires_line}",
            f" {style.dim('rotated:')} {rotated_line}",
        ]
        print(style.box(lines, title=f"secret '{args.name}'"))
    return 0


def cmd_list(args):
    home, cfg, ns, _ = _resolve(args)
    identity = keyring.load_identity(home, cfg.key_mode)
    for name in store.list_names(home, ns, identity):
        print(name)
    return 0


def cmd_rm(args):
    home, cfg, ns, _ = _resolve(args)
    identity = keyring.load_identity(home, cfg.key_mode)
    recipient = keyring.public_key(identity)
    existed = store.delete_secret(home, ns, args.name, identity, recipient)
    if not existed:
        print(style.fail(f"secret '{args.name}' not found in namespace '{ns}'"),
              file=sys.stderr)
        return 4
    print(style.ok(f"secret '{args.name}' removed from namespace '{ns}'"))
    return 0


def cmd_rename(args):
    home, cfg, ns, _ = _resolve(args)
    identity = keyring.load_identity(home, cfg.key_mode)
    recipient = keyring.public_key(identity)
    result = store.rename_secret(home, ns, args.old, args.new, identity, recipient)
    if result == "missing":
        print(style.fail(f"secret '{args.old}' not found in namespace '{ns}'"),
              file=sys.stderr)
        return 4
    if result == "exists":
        print(style.fail(f"secret '{args.new}' already exists in namespace '{ns}'"),
              file=sys.stderr)
        return 4
    namespace = cfg.namespaces.get(ns)
    if namespace is not None and args.old in namespace.env_map:
        namespace.env_map[args.new] = namespace.env_map.pop(args.old)
        config.save_config(home, cfg)
    print(style.ok(f"secret '{args.old}' renamed to '{args.new}' in namespace '{ns}'"))
    return 0


def _copy_or_move(args, *, move: bool):
    """Shared body for cmd_cp / cmd_mv. The active namespace is the source;
    args.dest is the destination namespace."""
    verb = "mv" if move else "cp"
    home, cfg, ns, _ = _resolve(args)
    if args.dest == ns:
        print(style.fail(f"{verb}: source and destination are the same "
                         f"namespace '{ns}' — use `cubby rename`"), file=sys.stderr)
        return 4
    if args.dest not in cfg.namespaces:
        print(style.fail(f"{verb}: namespace '{args.dest}' not found"),
              file=sys.stderr)
        return 4
    identity = keyring.load_identity(home, cfg.key_mode)
    recipient = keyring.public_key(identity)
    result = store.copy_secret(home, ns, args.dest, args.name, identity, recipient)
    if result == "missing":
        print(style.fail(f"{verb}: secret '{args.name}' not found in "
                         f"namespace '{ns}'"), file=sys.stderr)
        return 4
    if result == "exists":
        print(style.fail(f"{verb}: secret '{args.name}' already exists in "
                         f"namespace '{args.dest}'"), file=sys.stderr)
        return 4
    if move:
        store.delete_secret(home, ns, args.name, identity, recipient)
    src_ns = cfg.namespaces.get(ns)
    if src_ns is not None and args.name in src_ns.env_map:
        if move:
            cfg.namespaces[args.dest].env_map[args.name] = \
                src_ns.env_map.pop(args.name)
        else:
            cfg.namespaces[args.dest].env_map[args.name] = src_ns.env_map[args.name]
        config.save_config(home, cfg)
    done = "moved" if move else "copied"
    print(style.ok(f"{done} '{args.name}' from '{ns}' to '{args.dest}'"))
    return 0


def cmd_cp(args):
    return _copy_or_move(args, move=False)


def cmd_mv(args):
    return _copy_or_move(args, move=True)


def _copy_to_clipboard(text: str) -> str:
    """Copy `text` to the system clipboard via the first available tool.
    Returns the tool name; raises RuntimeError if none is found."""
    tools = [["pbcopy"], ["wl-copy"], ["xclip", "-selection", "clipboard"]]
    for tool in tools:
        if shutil.which(tool[0]):
            subprocess.run(tool, input=text, text=True, check=True)
            return tool[0]
    raise RuntimeError("no clipboard tool found "
                       "(install pbcopy, wl-copy, or xclip)")
