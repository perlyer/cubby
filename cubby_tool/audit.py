"""The opt-in audit log — a local record of when secret values leave the store.

Three events are recorded: `run` (a command was launched with the namespace's
secrets in its environment), `reveal` (a secret was printed via
`cubby get --reveal`), and `copy` (a secret value was copied to the clipboard
via `cubby get --copy`). Secret values are never written.
"""

from datetime import datetime, timezone
from pathlib import Path

MAX_DETAIL = 120
MAX_LOG_BYTES = 1_000_000


def log_path(home: Path) -> Path:
    return home / "audit.log"


def _rotated_path(home: Path) -> Path:
    return home / "audit.log.1"


def log_event(home: Path, enabled: bool, event: str, namespace: str,
              detail: str) -> None:
    """Append one audit line. A no-op when `enabled` is false. When the log
    would exceed MAX_LOG_BYTES it is first rotated to audit.log.1."""
    if not enabled:
        return
    detail = detail.replace("\n", " ")
    if len(detail) > MAX_DETAIL:
        detail = detail[:MAX_DETAIL - 1] + "…"
    stamp = datetime.now(timezone.utc).isoformat()
    line = f"{stamp}  {event}  {namespace}  {detail}\n"
    path = log_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size + len(line.encode()) > MAX_LOG_BYTES:
        path.replace(_rotated_path(home))
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
    path.chmod(0o600)


def read_log(home: Path) -> list[str]:
    """The audit log's lines (newlines stripped); [] if the file is absent."""
    path = log_path(home)
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def read_all(home: Path) -> list[str]:
    """Lines from the rotated log (if any) followed by the current log."""
    lines = []
    rotated = _rotated_path(home)
    if rotated.exists():
        lines += rotated.read_text(encoding="utf-8").splitlines()
    return lines + read_log(home)


def clear_log(home: Path) -> bool:
    """Remove the audit log and its rotated generation. Returns whether
    either file existed."""
    existed = False
    for path in (log_path(home), _rotated_path(home)):
        if path.exists():
            path.unlink()
            existed = True
    return existed
