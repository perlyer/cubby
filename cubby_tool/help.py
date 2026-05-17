"""The styled top-level help screen and the command catalogue.

The catalogue below is the single source of truth for the command list: it
drives both the rendered help screen and the known-command set used by
cli.main() to detect an unknown command.
"""

import argparse

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
        ("map", "show or change secret env vars"),
        ("rename", "rename a secret"),
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


def _with_banner(card: str) -> str:
    """Prepend the cyan banner above a card — only when frames are enabled."""
    if style.box_enabled():
        return style.cyan(BANNER) + "\n\n" + card
    return card


def render_help() -> str:
    """The full top-level help screen as a single string."""
    width = max(len(name) for name in command_names())
    lines = []
    for group, cmds in GROUPS:
        lines.append(" " + style.bold("▸ " + group))
        for name, desc in cmds:
            lines.append("   " + style.green(name.ljust(width)) + "  " + desc)
    card = style.box(lines, title=USAGE, footer=FOOTER)
    return _with_banner(card)


def render_command_help(parser, path, description=None) -> str:
    """Styled help for one (sub)command, introspected from its argparse parser.

    `path` is the command path as a list, e.g. ["cubby", "ns", "add"].
    `description` is the command's one-line help text, or None.
    """
    title = " ".join(path)
    if description:
        title = f"{title} · {description}"

    usage = " ".join(parser.format_usage().split())
    if usage.lower().startswith("usage:"):
        usage = usage[len("usage:"):].strip()

    sub_action = None
    positionals = []
    optionals = []
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            sub_action = action
        elif action.option_strings:
            optionals.append(action)
        else:
            positionals.append(action)

    groups = []  # (group title, [(name, help text), ...])
    if sub_action is not None:
        groups.append(("subcommands",
                        [(a.dest, a.help or "") for a in sub_action._get_subactions()]))
    if positionals:
        groups.append(("arguments",
                        [(a.metavar or a.dest, a.help or "") for a in positionals]))
    if optionals:
        groups.append(("options",
                        [(", ".join(a.option_strings), a.help or "") for a in optionals]))

    names = [name for _, items in groups for name, _ in items]
    width = max((len(n) for n in names), default=0)
    lines = [" " + style.dim("usage  ") + usage]
    for group, items in groups:
        lines.append(" " + style.bold("▸ " + group))
        for name, helptext in items:
            lines.append("   " + style.green(name.ljust(width)) + "  " + helptext)
    return _with_banner(style.box(lines, title=title))
