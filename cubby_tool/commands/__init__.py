import getpass
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cubby_tool import agents, archive, audit, completion, config, keyring, store, style
from cubby_tool.help import command_names


def _resolve(args):
    """Return (home, cfg, namespace, reason)."""
    home = config.get_home()
    cfg = config.load_config(home)
    ns, reason = config.resolve_namespace(
        cfg,
        flag=getattr(args, "namespace", None),
        env=os.environ.get("CUBBY_NS"),
        cwd=os.getcwd(),
    )
    return home, cfg, ns, reason


def cmd_ns(args):
    home = config.get_home()
    cfg = config.load_config(home)

    if args.ns_cmd == "add":
        cfg.namespaces[args.name] = config.Namespace(cwd_prefix=args.cwd_prefix, env_map={})
        if not cfg.default_namespace:
            cfg.default_namespace = args.name
        config.save_config(home, cfg)
        print(style.ok(f"namespace '{args.name}' added"))
        return 0

    if args.ns_cmd == "rm":
        if args.name not in cfg.namespaces:
            print(style.fail(f"namespace '{args.name}' not found"), file=sys.stderr)
            return 4
        del cfg.namespaces[args.name]
        config.save_config(home, cfg)
        print(style.ok(f"namespace '{args.name}' removed"))
        return 0

    if args.ns_cmd == "use":
        if args.name not in cfg.namespaces:
            print(style.fail(f"namespace '{args.name}' not found"), file=sys.stderr)
            return 4
        cfg.default_namespace = args.name
        config.save_config(home, cfg)
        print(style.ok(f"default namespace set to '{args.name}'"))
        return 0

    if args.ns_cmd == "rename":
        if args.old not in cfg.namespaces:
            print(style.fail(f"namespace '{args.old}' not found"), file=sys.stderr)
            return 4
        if args.new in cfg.namespaces:
            print(style.fail(f"namespace '{args.new}' already exists"), file=sys.stderr)
            return 4
        cfg.namespaces[args.new] = cfg.namespaces.pop(args.old)
        if cfg.default_namespace == args.old:
            cfg.default_namespace = args.new
        store.rename_namespace_file(home, args.old, args.new)
        config.save_config(home, cfg)
        print(style.ok(f"namespace '{args.old}' renamed to '{args.new}'"))
        return 0

    # bare `cubby ns` or `cubby ns list` — list every namespace
    if not cfg.namespaces:
        print(style.fail("no namespaces — run `cubby ns add <name>`"), file=sys.stderr)
        return 4
    try:
        active, _ = config.resolve_namespace(
            cfg, env=os.environ.get("CUBBY_NS"), cwd=os.getcwd()
        )
    except LookupError:
        active = None
    width = max(len(n) for n in cfg.namespaces)
    lines = []
    for name in sorted(cfg.namespaces):
        ns = cfg.namespaces[name]
        mark = style.green(style.OK_MARK) if name == active else " "
        tags = []
        if name == cfg.default_namespace:
            tags.append("default")
        if name == active:
            tags.append("active")
        suffix = style.dim(f"  ({', '.join(tags)})") if tags else ""
        prefix = style.dim(ns.cwd_prefix or "—")
        lines.append(f" {mark}  {name.ljust(width)}  {prefix}{suffix}")
    print(style.box(lines, title="namespaces"))
    return 0


def cmd_init(args):
    home = config.get_home()
    if config.config_path(home).exists():
        print(style.fail("already initialized — delete the config dir to re-init"),
              file=sys.stderr)
        return 4
    identity_text, _ = keyring.generate_identity()
    keyring.store_identity(home, identity_text, args.key_mode)
    ns_name = args.namespace or "default"
    cfg = config.Config(
        default_namespace=ns_name,
        key_mode=args.key_mode,
        namespaces={ns_name: config.Namespace(cwd_prefix=args.cwd_prefix, env_map={})},
    )
    config.save_config(home, cfg)
    print(style.ok(
        f"initialized at {home} (namespace '{ns_name}', key mode '{args.key_mode}')"))
    return 0


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


def _env_var_name(secret_name: str) -> str:
    """Default environment-variable name for a secret: UPPER_SNAKE, no prefix."""
    return secret_name.upper().replace("-", "_")


_DURATION_RE = re.compile(r"^(\d+)([hdw])$")
_DURATION_UNITS = {"h": "hours", "d": "days", "w": "weeks"}


def _parse_duration(text: str) -> timedelta:
    """Parse a TTL duration like '12h', '30d', '2w' into a timedelta.
    Raises ValueError on anything else."""
    match = _DURATION_RE.match(text.strip())
    if not match:
        raise ValueError(
            f"invalid duration '{text}' — use <int><unit>, unit h/d/w (e.g. 30d)")
    amount = int(match.group(1))
    if amount <= 0:
        raise ValueError(f"invalid duration '{text}' — must be a positive amount")
    return timedelta(**{_DURATION_UNITS[match.group(2)]: amount})


def _ttl_to_expires(ttl: str) -> str:
    """Absolute ISO-8601 expiry for a duration string, measured from now."""
    return (datetime.now(timezone.utc) + _parse_duration(ttl)).isoformat()


def _format_relative(iso_timestamp: str) -> str:
    """Render an ISO-8601 timestamp as a human phrase relative to now, with no
    surrounding parentheses: 'in 89 days', 'in 5 hours', 'expired 3 days ago',
    'expires today', 'expired today'."""
    when = datetime.fromisoformat(iso_timestamp)
    secs = (when - datetime.now(timezone.utc)).total_seconds()
    future = secs >= 0
    secs = abs(secs)
    if secs < 3600:
        return "expires today" if future else "expired today"
    if secs < 86400:
        n, unit = round(secs / 3600), "hour"
        if n >= 24:
            n, unit = 1, "day"
    else:
        n, unit = round(secs / 86400), "day"
    plural = "" if n == 1 else "s"
    return f"in {n} {unit}{plural}" if future else f"expired {n} {unit}{plural} ago"


def _is_expired(entry: dict) -> bool:
    """True when the entry has an 'expires' timestamp that is in the past."""
    exp = entry.get("expires")
    if not exp:
        return False
    return datetime.fromisoformat(exp) < datetime.now(timezone.utc)


def _resolve_env_var(env_map: dict, secret_name: str) -> str:
    """The environment variable a secret is injected as: its env_map override,
    or the upper_snake default."""
    return env_map.get(secret_name, _env_var_name(secret_name))


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


def _env_var_clash(env_map: dict, secret_names, target_var: str, this_secret: str):
    """If a secret other than this_secret already resolves to target_var,
    return that secret's name; else None."""
    for name in secret_names:
        if name == this_secret:
            continue
        if _resolve_env_var(env_map, name) == target_var:
            return name
    return None


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


def _parse_env_file(path: Path) -> dict:
    result = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        result[key.strip()] = value
    return result


def _fetch_aws_secret(secret_id: str, region: str | None) -> dict:
    cmd = ["aws", "secretsmanager", "get-secret-value",
           "--secret-id", secret_id, "--query", "SecretString", "--output", "text"]
    if region:
        cmd += ["--region", region]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def _parse_json_file(path: Path) -> dict:
    """Parse a flat JSON object {name: value} into a dict of string values."""
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"import: {path} must contain a flat JSON object")
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            raise ValueError(f"import: {path} value for '{key}' must be a scalar, "
                             f"not a {type(value).__name__}")
    return {k: str(v) for k, v in data.items()}


def _fetch_1password(vault: str) -> dict:
    """Fetch every item from a 1Password vault via the `op` CLI. One secret per
    item: name = item title, value = the item's password (else first concealed)
    field. Items with no such field are skipped."""
    listing = subprocess.run(
        ["op", "item", "list", "--vault", vault, "--format", "json"],
        capture_output=True, text=True, check=True)
    pairs = {}
    for item in json.loads(listing.stdout):
        detail = subprocess.run(
            ["op", "item", "get", item["id"], "--format", "json"],
            capture_output=True, text=True, check=True)
        fields = json.loads(detail.stdout).get("fields", [])
        value = next((f["value"] for f in fields
                      if f.get("purpose") == "PASSWORD" and f.get("value")), None)
        if value is None:
            value = next((f["value"] for f in fields
                          if f.get("type") == "CONCEALED" and f.get("value")), None)
        if value is not None:
            pairs[item["title"]] = value
    return pairs


def cmd_import(args):
    home, cfg, ns, _ = _resolve(args)
    identity = keyring.load_identity(home, cfg.key_mode)
    recipient = keyring.public_key(identity)

    if args.source_type in ("dotenv", "json"):
        path = Path(args.source)
        if not path.exists():
            print(style.fail(f"import: file not found: {args.source}"), file=sys.stderr)
            return 2
        pairs = _parse_env_file(path) if args.source_type == "dotenv" \
            else _parse_json_file(path)
    elif args.source_type == "aws":
        try:
            pairs = _fetch_aws_secret(args.source, args.region)
        except FileNotFoundError:
            print(style.fail("import: aws CLI not found (install awscli)"),
                  file=sys.stderr)
            return 2
    elif args.source_type == "1password":
        try:
            pairs = _fetch_1password(args.source)
        except FileNotFoundError:
            print(style.fail("import: op CLI not found (install the 1Password CLI)"),
                  file=sys.stderr)
            return 2
    elif args.source_type == "ns":
        if args.source == ns:
            print(style.fail(f"import: cannot import namespace '{ns}' onto itself"),
                  file=sys.stderr)
            return 4
        if args.source not in cfg.namespaces:
            print(style.fail(f"import: namespace '{args.source}' not found"),
                  file=sys.stderr)
            return 4
        pairs = store.read_values(home, args.source, identity)
    else:  # unreachable — argparse `choices` guards the type
        print(style.fail(f"import: unknown source type '{args.source_type}'"),
              file=sys.stderr)
        return 2

    for name, value in pairs.items():
        store.set_secret(home, ns, name, str(value), identity, recipient)
    print(style.ok(f"imported {len(pairs)} secret(s) into namespace '{ns}'"))
    return 0


def cmd_agent(args):
    if args.agent_cmd is None:
        print(style.fail("usage: cubby agent {list|add|rm|refresh}"), file=sys.stderr)
        return 2
    if args.agent_cmd == "list":
        names = agents.names()
        width = max(len(n) for n in names)
        marks = {
            "installed": style.green(style.OK_MARK),
            "not installed": style.dim(style.DOT_MARK),
            "agent absent": style.dim(style.CROSS_MARK),
        }
        counts = {"installed": 0, "not installed": 0, "agent absent": 0}
        lines = []
        for name in names:
            st = agents.ADAPTERS[name].status()
            counts[st] = counts.get(st, 0) + 1
            lines.append(f" {marks.get(st, ' ')}  {name.ljust(width)}  {style.dim(st)}")
        summary = (
            f"{counts['installed']} installed · "
            f"{counts['not installed']} available · "
            f"{counts['agent absent']} not found"
        )
        print(style.box(lines, title="agent integrations", footer=summary))
        return 0
    if args.agent_cmd == "refresh":
        refreshed = []
        for name in agents.names():
            adapter = agents.ADAPTERS[name]
            if adapter.status() == "installed":
                adapter.install()
                refreshed.append(name)
        print()
        for name in refreshed:
            print(style.ok(f"refreshed {name}"))
        if refreshed:
            print()
            print(style.dim(f"  refreshed {len(refreshed)} agent integration(s)"))
        else:
            print(style.dim("  no agent integrations installed"))
        return 0
    adapter = agents.get(args.name)
    if adapter is None:
        print(style.fail(f"unknown agent '{args.name}' — see `cubby agent list`"),
              file=sys.stderr)
        return 4
    if args.agent_cmd == "add":
        adapter.install()
        print(style.ok(f"integration installed for {adapter.name}"))
        return 0
    if args.agent_cmd == "rm":
        adapter.uninstall()
        print(style.ok(f"integration removed for {adapter.name}"))
        return 0
    print(style.fail("usage: cubby agent {list|add|rm|refresh}"), file=sys.stderr)
    return 2


def cmd_doctor(args):
    home = config.get_home()
    checks = []  # (status, message); status is "ok" | "warn" | "fail"

    if shutil.which("age") and shutil.which("age-keygen"):
        checks.append(("ok", "age and age-keygen on PATH"))
    else:
        checks.append(("fail", "age / age-keygen not found on PATH"))

    cfg = None
    cfg_path = config.config_path(home)
    if not cfg_path.exists():
        checks.append(("fail", f"no config at {cfg_path} — run 'cubby init'"))
    else:
        try:
            cfg = config.load_config(home)
            checks.append(("ok", "config.json parses"))
        except (ValueError, json.JSONDecodeError) as e:
            checks.append(("fail", f"config.json is invalid ({e})"))

    identity = None
    if cfg is not None:
        try:
            identity = keyring.load_identity(home, cfg.key_mode)
            checks.append(("ok", f"age identity loads (key mode '{cfg.key_mode}')"))
        except Exception as e:  # noqa: BLE001 - doctor reports any failure
            checks.append(("fail", f"age identity does not load ({e})"))

    if cfg is not None and identity is not None:
        for ns_name, namespace in sorted(cfg.namespaces.items()):
            try:
                entries = store.read_entries(home, ns_name, identity)
            except Exception as e:  # noqa: BLE001 - doctor reports any failure
                checks.append(("fail", f"namespace '{ns_name}' does not decrypt ({e})"))
                continue
            checks.append(("ok", f"namespace '{ns_name}' decrypts "
                                 f"({len(entries)} secret(s))"))
            for mapped in namespace.env_map:
                if mapped not in entries:
                    checks.append(("warn", f"namespace '{ns_name}': env_map entry "
                                           f"'{mapped}' points to a missing secret"))
            seen = {}
            for name in entries:
                var = _resolve_env_var(namespace.env_map, name)
                if var in seen:
                    checks.append(("fail", f"namespace '{ns_name}': secrets "
                                           f"'{seen[var]}' and '{name}' both map to "
                                           f"env var '{var}'"))
                else:
                    seen[var] = name
            for name, entry in entries.items():
                if _is_expired(entry):
                    checks.append(("warn", f"namespace '{ns_name}': secret "
                                           f"'{name}' {_format_relative(entry['expires'])}"))

    if cfg is not None and not cfg.audit:
        checks.append(("warn", "audit logging is off "
                               "(enable with cubby audit --enable)"))

    marks = {
        "ok": style.green(style.OK_MARK),
        "warn": style.dim(style.DOT_MARK),
        "fail": style.red(style.CROSS_MARK),
    }
    lines = [f" {marks[s]}  {m}" for s, m in checks]
    failed = sum(1 for s, _ in checks if s == "fail")
    summary = "all checks passed" if failed == 0 else f"{failed} check(s) failed"
    print(style.box(lines, title="cubby doctor", footer=summary))
    return 0 if failed == 0 else 2


def cmd_export(args):
    home = config.get_home()
    if not config.config_path(home).exists():
        print(style.fail("not initialized — run 'cubby init' first"),
              file=sys.stderr)
        return 4
    dest = Path(args.file)
    archive.export_bundle(home, dest)
    print(style.ok(f"backup written to {dest}"))
    return 0


def cmd_restore(args):
    home = config.get_home()
    src = Path(args.file)
    if not src.exists():
        print(style.fail(f"restore: file not found: {args.file}"), file=sys.stderr)
        return 2
    if config.config_path(home).exists() and not args.force:
        print(style.fail(f"restore: a store already exists at {home} "
                         f"— pass --force to overwrite"), file=sys.stderr)
        return 4
    original_key_mode = archive.restore_bundle(src, home)
    print(style.ok(f"store restored to {home}"))
    if original_key_mode == "keychain":
        print(style.dim("note: backup used keychain key-mode — "
                        "restored as file key-mode"))
    return 0


def cmd_audit(args):
    home = config.get_home()
    if not config.config_path(home).exists():
        print(style.fail("not initialized — run 'cubby init' first"), file=sys.stderr)
        return 4
    cfg = config.load_config(home)

    if sum(bool(f) for f in (args.enable, args.disable, args.clear)) > 1:
        print(style.fail("audit: --enable, --disable and --clear are "
                         "mutually exclusive"), file=sys.stderr)
        return 2

    if args.enable or args.disable:
        cfg.audit = bool(args.enable)
        config.save_config(home, cfg)
        print(style.ok(f"audit logging {'enabled' if cfg.audit else 'disabled'}"))
        return 0

    if args.clear:
        if audit.clear_log(home):
            print(style.ok("audit log cleared"))
        else:
            print(style.dim("audit log is already empty"))
        return 0

    lines = audit.read_all(home) if args.show_all else audit.read_log(home)
    if not lines:
        print(style.dim("no audit entries"))
        return 0
    shown = lines if args.show_all else lines[-20:]
    footer = None if cfg.audit else "audit logging is currently off"
    print(style.box([f" {ln}" for ln in shown], title="audit log", footer=footer))
    return 0


def cmd_completion(args):
    print(completion.render(args.shell, command_names()))
    return 0
