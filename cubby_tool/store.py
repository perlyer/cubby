import json
from datetime import datetime, timezone
from pathlib import Path

from cubby_tool import backend


def secrets_path(home: Path, namespace: str) -> Path:
    return home / "secrets" / f"{namespace}.age"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_entries(home: Path, namespace: str, identity_text: str) -> dict:
    path = secrets_path(home, namespace)
    if not path.exists():
        return {}
    plaintext = backend.decrypt(path.read_bytes(), identity_text)
    return json.loads(plaintext.decode())


def write_entries(home: Path, namespace: str, entries: dict, recipient: str) -> None:
    path = secrets_path(home, namespace)
    path.parent.mkdir(parents=True, exist_ok=True)
    ciphertext = backend.encrypt(json.dumps(entries).encode(), recipient)
    path.write_bytes(ciphertext)
    path.chmod(0o600)


def read_values(home: Path, namespace: str, identity_text: str) -> dict:
    return {n: e["value"] for n, e in read_entries(home, namespace, identity_text).items()}


def set_secret(home, namespace, name, value, identity_text, recipient, *, meta=None) -> None:
    entries = read_entries(home, namespace, identity_text)
    entry = {"value": value, "updated": _now()}
    if meta:
        entry.update(meta)
    entries[name] = entry
    write_entries(home, namespace, entries, recipient)


def rotate_secret(home, namespace, name, value, identity_text, recipient, *, meta=None) -> str:
    """Rotate an existing secret's value. Returns 'ok' or 'missing'. Increments
    the 'rotated' counter and merges the caller-resolved `meta` (ttl/expires)."""
    entries = read_entries(home, namespace, identity_text)
    if name not in entries:
        return "missing"
    entry = {
        "value": value,
        "updated": _now(),
        "rotated": entries[name].get("rotated", 0) + 1,
    }
    if meta:
        entry.update(meta)
    entries[name] = entry
    write_entries(home, namespace, entries, recipient)
    return "ok"


def delete_secret(home, namespace, name, identity_text, recipient) -> bool:
    entries = read_entries(home, namespace, identity_text)
    if name not in entries:
        return False
    del entries[name]
    write_entries(home, namespace, entries, recipient)
    return True


def list_names(home, namespace, identity_text) -> list:
    return sorted(read_entries(home, namespace, identity_text).keys())


def rename_secret(home, namespace, old, new, identity_text, recipient) -> str:
    """Rename a secret entry. Returns 'ok', 'missing', or 'exists'."""
    entries = read_entries(home, namespace, identity_text)
    if old not in entries:
        return "missing"
    if new in entries:
        return "exists"
    entries[new] = entries.pop(old)
    write_entries(home, namespace, entries, recipient)
    return "ok"


def rename_namespace_file(home, old, new) -> None:
    """Rename a namespace's encrypted file, if it exists."""
    src = secrets_path(home, old)
    if src.exists():
        src.rename(secrets_path(home, new))
