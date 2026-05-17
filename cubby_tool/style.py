"""Terminal styling — ANSI colour, status symbols, message helpers.

Colour is emitted only when stdout is a TTY and NO_COLOR is unset, so piped
or scripted output stays plain and machine-readable.
"""

import os
import re
import sys

RESET = "\033[0m"
_CODES = {
    "green": "\033[32m",
    "red": "\033[31m",
    "dim": "\033[2m",
    "bold": "\033[1m",
    "cyan": "\033[36m",
}

OK_MARK = "✓"
DOT_MARK = "·"
CROSS_MARK = "✗"

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def color_enabled() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def paint(text: str, code: str) -> str:
    if not color_enabled():
        return text
    return f"{_CODES[code]}{text}{RESET}"


def green(text: str) -> str:
    return paint(text, "green")


def red(text: str) -> str:
    return paint(text, "red")


def dim(text: str) -> str:
    return paint(text, "dim")


def bold(text: str) -> str:
    return paint(text, "bold")


def ok(msg: str) -> str:
    """A success line: green check mark + message."""
    return f"{green(OK_MARK)} {msg}"


def fail(msg: str) -> str:
    """An error line: red cross + message."""
    return f"{red(CROSS_MARK)} {msg}"


def cyan(text: str) -> str:
    return paint(text, "cyan")


def visible_width(s: str) -> int:
    """Display width of s, ignoring ANSI escape sequences."""
    return len(_ANSI_RE.sub("", s))


def box_enabled() -> bool:
    """Frames are drawn only on an interactive terminal."""
    return sys.stdout.isatty()


def box(lines: list[str], title: str | None = None, footer: str | None = None) -> str:
    """Render lines as a framed card — title in the top border, footer in the
    bottom border. When stdout is not a TTY, draw no frame: title and footer
    become plain lines instead, so no information is lost."""
    if not box_enabled():
        plain = []
        if title is not None:
            plain.append(title)
        plain.extend(lines)
        if footer is not None:
            plain.append(footer)
        return "\n".join(plain)

    widths = [visible_width(l) for l in lines]
    if title is not None:
        widths.append(visible_width(title) + 2)
    if footer is not None:
        widths.append(visible_width(footer) + 2)
    inner = max(widths) if widths else 0

    def border(label, left, right):
        if label is not None:
            dashes = max(inner - visible_width(label) - 1, 0)
            return left + "─ " + label + " " + "─" * dashes + right
        return left + "─" * (inner + 2) + right

    rows = [dim(border(title, "┌", "┐"))]
    for l in lines:
        pad = " " * (inner - visible_width(l))
        rows.append(dim("│") + " " + l + pad + " " + dim("│"))
    rows.append(dim(border(footer, "└", "┘")))
    return "\n".join(rows)
