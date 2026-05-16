import getpass
import os
import sys

from cubby_tool import config, keyring, store


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
        print(f"cubby: namespace '{args.name}' added")
        return 0

    if args.ns_cmd == "rm":
        if args.name not in cfg.namespaces:
            print(f"cubby: namespace '{args.name}' not found", file=sys.stderr)
            return 4
        del cfg.namespaces[args.name]
        config.save_config(home, cfg)
        print(f"cubby: namespace '{args.name}' removed")
        return 0

    if args.ns_cmd == "list":
        for name, ns in sorted(cfg.namespaces.items()):
            print(f"{name}\t{ns.cwd_prefix or '-'}")
        return 0

    # bare `cubby ns` — status
    try:
        ns, reason = config.resolve_namespace(
            cfg, env=os.environ.get("CUBBY_NS"), cwd=os.getcwd()
        )
    except LookupError:
        print("cubby: no namespace resolved (run `cubby ns add`)", file=sys.stderr)
        return 4
    print(f"active namespace: {ns} (resolved via: {reason})")
    return 0


def cmd_init(args):
    home = config.get_home()
    if config.config_path(home).exists():
        print("cubby: already initialized (delete the config dir to re-init)", file=sys.stderr)
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
    print(f"cubby: initialized at {home} (namespace '{ns_name}', key mode '{args.key_mode}')")
    return 0


def cmd_set(args):
    home, cfg, ns, _ = _resolve(args)
    identity = keyring.load_identity(home, cfg.key_mode)
    recipient = keyring.public_key(identity)
    if args.stdin:
        value = sys.stdin.read().rstrip("\n")
    else:
        value = getpass.getpass(f"value for '{args.name}': ")
    store.set_secret(home, ns, args.name, value, identity, recipient)
    print(f"cubby: secret '{args.name}' set in namespace '{ns}'")
    return 0


def cmd_get(args):
    home, cfg, ns, _ = _resolve(args)
    identity = keyring.load_identity(home, cfg.key_mode)
    entries = store.read_entries(home, ns, identity)
    if args.name not in entries:
        print(f"cubby: secret '{args.name}' not found in namespace '{ns}'", file=sys.stderr)
        return 4
    entry = entries[args.name]
    if args.reveal:
        print("WARNING: revealing secret plaintext to stdout", file=sys.stderr)
        print(entry["value"])
    else:
        print(f"name: {args.name}")
        print(f"namespace: {ns}")
        print(f"length: {len(entry['value'])}")
        print(f"updated: {entry.get('updated', '-')}")
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
        print(f"cubby: secret '{args.name}' not found in namespace '{ns}'", file=sys.stderr)
        return 4
    print(f"cubby: secret '{args.name}' removed from namespace '{ns}'")
    return 0


def _env_var_name(secret_name: str) -> str:
    return "CUBBY_" + secret_name.upper().replace("-", "_")


def cmd_run(args):
    home, cfg, ns, _ = _resolve(args)
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("cubby run: no command given (usage: cubby run -- <cmd>)", file=sys.stderr)
        return 2
    identity = keyring.load_identity(home, cfg.key_mode)
    values = store.read_values(home, ns, identity)
    env_map = cfg.namespaces.get(ns, config.Namespace()).env_map
    child_env = dict(os.environ)
    for name, value in values.items():
        child_env[env_map.get(name, _env_var_name(name))] = value
    try:
        os.execvpe(command[0], command, child_env)
    except FileNotFoundError:
        print(f"cubby run: command not found: {command[0]}", file=sys.stderr)
        return 2
