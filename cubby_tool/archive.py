"""Backup bundles — the cubby store packed as a tar archive.

`build_tar` / `extract_tar` are pure (a {arcname: bytes} mapping ↔ tar bytes).
`export_bundle` / `restore_bundle` add the age passphrase-encryption layer by
shelling out to the `age` CLI, which prompts for the passphrase itself.
"""

import io
import subprocess
import tarfile
from pathlib import Path

from cubby_tool import config, keyring


def build_tar(members: dict) -> bytes:
    """Pack a {arcname: bytes} mapping into an uncompressed tar archive."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for arcname, data in sorted(members.items()):
            info = tarfile.TarInfo(name=arcname)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _store_members(home: Path) -> dict:
    """The {arcname: bytes} backup payload: the age identity, config.json, and
    every namespace file. The audit log is deliberately excluded."""
    cfg = config.load_config(home)
    identity = keyring.load_identity(home, cfg.key_mode)
    members = {
        "identity": identity.encode(),
        "config.json": config.config_path(home).read_bytes(),
    }
    secrets_dir = home / "secrets"
    if secrets_dir.is_dir():
        for f in sorted(secrets_dir.glob("*.age")):
            members[f"secrets/{f.name}"] = f.read_bytes()
    return members


def export_bundle(home: Path, dest: Path) -> None:
    """Write a passphrase-encrypted backup of the whole store to `dest`.
    `age` prompts for the passphrase interactively."""
    tar_bytes = build_tar(_store_members(home))
    subprocess.run(["age", "--passphrase", "--output", str(dest)],
                   input=tar_bytes, check=True)


def extract_tar(data: bytes) -> dict:
    """Unpack a tar archive into a {arcname: bytes} mapping. Rejects any
    member whose name is absolute or escapes the archive root."""
    members = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as tar:
        for info in tar.getmembers():
            name = info.name
            if name.startswith("/") or ".." in Path(name).parts:
                raise ValueError(f"unsafe tar member path: {name}")
            if info.isfile():
                fh = tar.extractfile(info)
                if fh is not None:
                    members[name] = fh.read()
    return members
