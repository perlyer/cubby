import getpass
import json
import os
import subprocess
import sys
from pathlib import Path

from cubby_tool import agents, config, keyring, store, style


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
    if args.stdin:
        value = sys.stdin.read().rstrip("\n")
    else:
        value = getpass.getpass(f"value for '{args.name}': ")
    store.set_secret(home, ns, args.name, value, identity, recipient)
    if args.env:
        namespace.env_map[args.name] = args.env
        config.save_config(home, cfg)
    print(style.ok(f"secret '{args.name}' set in namespace '{ns}'"))
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
        print("WARNING: revealing secret plaintext to stdout", file=sys.stderr)
        print(entry["value"])
    else:
        namespace = cfg.namespaces.get(ns, config.Namespace())
        var = _resolve_env_var(namespace.env_map, args.name)
        kind = "override" if args.name in namespace.env_map else "default"
        lines = [
            f" {style.dim('name:')} {args.name}",
            f" {style.dim('namespace:')} {ns}",
            f" {style.dim('env var:')} {var} ({kind})",
            f" {style.dim('length:')} {len(entry['value'])}",
            f" {style.dim('updated:')} {entry.get('updated', '-')}",
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


def _env_var_name(secret_name: str) -> str:
    """Default environment-variable name for a secret: UPPER_SNAKE, no prefix."""
    return secret_name.upper().replace("-", "_")


def _resolve_env_var(env_map: dict, secret_name: str) -> str:
    """The environment variable a secret is injected as: its env_map override,
    or the upper_snake default."""
    return env_map.get(secret_name, _env_var_name(secret_name))


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
    values = store.read_values(home, ns, identity)
    env_map = cfg.namespaces.get(ns, config.Namespace()).env_map
    child_env = dict(os.environ)
    for name, value in values.items():
        child_env[_resolve_env_var(env_map, name)] = value
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


def cmd_import(args):
    home, cfg, ns, _ = _resolve(args)
    if args.from_env:
        path = Path(args.from_env)
        if not path.exists():
            print(style.fail(f"import: file not found: {args.from_env}"), file=sys.stderr)
            return 2
        pairs = _parse_env_file(path)
    elif args.from_aws:
        try:
            pairs = _fetch_aws_secret(args.from_aws, args.region)
        except FileNotFoundError:
            print(style.fail("import: aws CLI not found (install awscli)"), file=sys.stderr)
            return 2
    else:
        print(style.fail("import: specify --from-env or --from-aws"), file=sys.stderr)
        return 2
    identity = keyring.load_identity(home, cfg.key_mode)
    recipient = keyring.public_key(identity)
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
