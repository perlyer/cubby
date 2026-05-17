"""Terminal styling — ANSI colour, status symbols, message helpers.

Colour is emitted only when stdout is a TTY and NO_COLOR is unset, so piped
or scripted output stays plain and machine-readable.
"""

import os
import sys

RESET = "\033[0m"
_CODES = {
    "green": "\033[32m",
    "red": "\033[31m",
    "dim": "\033[2m",
    "bold": "\033[1m",
}

OK_MARK = "✓"
DOT_MARK = "·"
CROSS_MARK = "✗"


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
