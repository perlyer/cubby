import sys
from pathlib import Path

from cubby_tool import archive, config, style


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
