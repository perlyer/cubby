"""The styled top-level help screen and the command catalogue.

The catalogue below is the single source of truth for the command list: it
drives both the rendered help screen and the known-command set used by
cli.main() to detect an unknown command.
"""

from cubby_tool import style

BANNER = r"""         _    _
 __ _  _| |__| |__ _  _
/ _| || | '_ \ '_ \ || |
\__|\_,_|_.__/_.__/\_, |
                   |__/
  encrypted secret store"""

USAGE = "usage: cubby <command> [options]"
FOOTER = "cubby <command> -h  ·  command details"

# Ordered: (group title, [(command, one-line description), ...])
GROUPS = [
    ("secrets", [
        ("set", "store a secret"),
        ("get", "show secret metadata"),
        ("list", "list secret names"),
        ("rm", "delete a secret"),
        ("run", "run a command with secrets in env"),
        ("import", "bulk import from .env / AWS"),
    ]),
    ("namespaces", [
        ("ns", "manage namespaces"),
    ]),
    ("agents", [
        ("agent", "manage agent integrations"),
    ]),
    ("setup", [
        ("init", "first-run setup"),
    ]),
]


def command_names():
    """Every command name, in catalogue order."""
    return [name for _, cmds in GROUPS for name, _ in cmds]


def render_help() -> str:
    """The full top-level help screen as a single string."""
    width = max(len(name) for name in command_names())
    lines = []
    for group, cmds in GROUPS:
        lines.append(" " + style.bold("▸ " + group))
        for name, desc in cmds:
            lines.append("   " + style.green(name.ljust(width)) + "  " + desc)
    card = style.box(lines, title=USAGE, footer=FOOTER)
    if style.box_enabled():
        return style.cyan(BANNER) + "\n\n" + card
    return card
