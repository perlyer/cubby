import os
import sys

from cubby_tool import config, store, style


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
