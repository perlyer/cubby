"""The opt-in audit log — a local record of when secret values leave the store.

Three events are recorded: `run` (a command was launched with the namespace's
secrets in its environment), `reveal` (a secret was printed via
`cubby get --reveal`), and `copy` (a secret value was copied to the clipboard
via `cubby get --copy`). Secret values are never written.
"""

from datetime import datetime, timezone
from pathlib import Path

MAX_DETAIL = 120


def log_path(home: Path) -> Path:
    return home / "audit.log"


def log_event(home: Path, enabled: bool, event: str, namespace: str,
              detail: str) -> None:
    """Append one audit line. A no-op when `enabled` is false."""
    if not enabled:
        return
    detail = detail.replace("\n", " ")
    if len(detail) > MAX_DETAIL:
        detail = detail[:MAX_DETAIL - 1] + "…"
    stamp = datetime.now(timezone.utc).isoformat()
    path = log_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"{stamp}  {event}  {namespace}  {detail}\n")
    path.chmod(0o600)


def read_log(home: Path) -> list[str]:
    """The audit log's lines (newlines stripped); [] if the file is absent."""
    path = log_path(home)
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def clear_log(home: Path) -> bool:
    """Truncate the audit log. Returns whether the file existed."""
    path = log_path(home)
    if not path.exists():
        return False
    path.write_text("", encoding="utf-8")
    return True
