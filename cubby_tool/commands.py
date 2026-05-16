import os
import sys

from cubby_tool import config


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
