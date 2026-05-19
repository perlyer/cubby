import json
import shutil
import sys

from cubby_tool import audit, completion, config, keyring, store, style
from cubby_tool.commands._common import (
    _format_relative, _is_expired, _resolve_env_var,
)
from cubby_tool.help import command_names


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
