import subprocess
from pathlib import Path

IDENTITY_SERVICE = "cubby-identity"
IDENTITY_ACCOUNT = "cubby"


def generate_identity() -> tuple[str, str]:
    """Run age-keygen; return (identity_text, public_key)."""
    result = subprocess.run(["age-keygen"], capture_output=True, text=True, check=True)
    text = result.stdout
    return text, public_key(text)


def public_key(identity_text: str) -> str:
    for line in identity_text.splitlines():
        if line.startswith("# public key:"):
            return line.split(":", 1)[1].strip()
    raise ValueError("identity text has no '# public key:' line")


def identity_file(home: Path) -> Path:
    return home / "identity"


def store_identity(home: Path, identity_text: str, mode: str) -> None:
    if mode == "file":
        home.mkdir(parents=True, exist_ok=True)
        path = identity_file(home)
        path.write_text(identity_text)
        path.chmod(0o600)
    elif mode == "keychain":
        subprocess.run(
            ["security", "add-generic-password", "-U",
             "-s", IDENTITY_SERVICE, "-a", IDENTITY_ACCOUNT, "-w", identity_text],
            check=True, capture_output=True, text=True,
        )
    else:
        raise ValueError(f"unknown key_mode: {mode}")


def load_identity(home: Path, mode: str) -> str:
    if mode == "file":
        return identity_file(home).read_text()
    elif mode == "keychain":
        result = subprocess.run(
            ["security", "find-generic-password", "-w",
             "-s", IDENTITY_SERVICE, "-a", IDENTITY_ACCOUNT],
            check=True, capture_output=True, text=True,
        )
        # `security -w` appends its own newline on top of the identity text's
        # trailing newline; normalize to exactly one so keychain mode matches
        # file mode byte-for-byte.
        return result.stdout.rstrip("\n") + "\n"
    else:
        raise ValueError(f"unknown key_mode: {mode}")
