import os
import subprocess
import tempfile


def encrypt(plaintext: bytes, recipient: str) -> bytes:
    result = subprocess.run(
        ["age", "-r", recipient],
        input=plaintext, capture_output=True, check=True,
    )
    return result.stdout


def decrypt(ciphertext: bytes, identity_text: str) -> bytes:
    fd, tmp_path = tempfile.mkstemp(prefix="cubby-id-")
    try:
        os.fchmod(fd, 0o600)
        os.write(fd, identity_text.encode())
        os.close(fd)
        fd = -1  # mark closed so the finally block does not double-close
        result = subprocess.run(
            ["age", "-d", "-i", tmp_path],
            input=ciphertext, capture_output=True, check=True,
        )
        return result.stdout
    finally:
        if fd != -1:
            os.close(fd)
        os.unlink(tmp_path)
