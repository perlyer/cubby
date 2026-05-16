from pathlib import Path

SECTION_START = "<!-- cubby:start -->"
SECTION_END = "<!-- cubby:end -->"


class Adapter:
    """Base class for per-agent integration adapters."""

    name = ""

    def detect(self) -> bool:
        raise NotImplementedError

    def install(self) -> None:
        raise NotImplementedError

    def uninstall(self) -> None:
        raise NotImplementedError

    def _installed(self) -> bool:
        raise NotImplementedError

    def status(self) -> str:
        if not self.detect():
            return "agent absent"
        return "installed" if self._installed() else "not installed"


def upsert_section(path: Path, body: str) -> None:
    """Insert or replace the cubby-delimited section in a text file."""
    section = f"{SECTION_START}\n{body.strip()}\n{SECTION_END}"
    if path.exists():
        text = path.read_text()
        start = text.find(SECTION_START)
        end = text.find(SECTION_END)
        if 0 <= start < end:
            text = text[:start] + section + text[end + len(SECTION_END):]
        else:
            # no markers, or markers present but inverted/corrupt — append fresh
            text = text.rstrip("\n") + "\n\n" + section + "\n"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = section + "\n"
    path.write_text(text)


def remove_section(path: Path) -> bool:
    """Remove the cubby-delimited section. Return True if it was present."""
    if not path.exists():
        return False
    text = path.read_text()
    start = text.find(SECTION_START)
    end = text.find(SECTION_END)
    if not (0 <= start < end):
        # no markers, or markers present but inverted/corrupt — leave file untouched
        return False
    end += len(SECTION_END)
    remainder = (text[:start].rstrip("\n") + "\n" + text[end:].lstrip("\n")).strip()
    if remainder:
        path.write_text(remainder + "\n")
    else:
        path.unlink()
    return True


def has_section(path: Path) -> bool:
    return path.exists() and SECTION_START in path.read_text()
