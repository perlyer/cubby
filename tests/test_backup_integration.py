import fcntl
import os
import pty
import select
import shutil
import subprocess
import sys
import termios
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CUBBY = REPO_ROOT / "cubby"


def _run_under_pty(argv, env, passphrase, timeout=20):
    """Run argv under a pseudo-terminal, typing `passphrase` once for each
    'passphrase' prompt age emits. Returns the process exit code.

    Uses TIOCSCTTY to make the pty slave the controlling terminal of the child
    process so that age can open /dev/tty for passphrase input.

    Output is accumulated into a buffer before counting prompts so that a
    prompt fragmented across multiple reads (e.g. "Enter pass" / "phrase:")
    is still detected correctly on loaded CI machines.
    """
    master, slave = pty.openpty()

    def _preexec():
        os.setsid()
        fcntl.ioctl(slave, termios.TIOCSCTTY, 0)

    proc = subprocess.Popen(
        argv, stdin=slave, stdout=slave, stderr=slave,
        env=env, preexec_fn=_preexec, close_fds=True,
    )
    os.close(slave)
    buf = b""
    sent = 0
    try:
        while True:
            ready, _, _ = select.select([master], [], [], timeout)
            if not ready:
                break
            try:
                chunk = os.read(master, 1024)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
            prompts = buf.lower().count(b"passphrase")
            while sent < prompts:
                os.write(master, (passphrase + "\n").encode())
                sent += 1
    finally:
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
        os.close(master)
    return proc.returncode


@pytest.mark.skipif(shutil.which("age") is None, reason="age not installed")
def test_export_restore_round_trip(tmp_path):
    home = tmp_path / "cubby"
    env = {"CUBBY_HOME": str(home), "PATH": os.environ["PATH"]}

    subprocess.run([sys.executable, str(CUBBY), "init"],
                   env=env, check=True, capture_output=True)
    subprocess.run([sys.executable, str(CUBBY), "set", "tok", "--stdin"],
                   env=env, input="s3cret\n", text=True, check=True,
                   capture_output=True)

    bundle = tmp_path / "backup.age"
    assert _run_under_pty(
        [sys.executable, str(CUBBY), "export", str(bundle)], env, "hunter2") == 0
    assert bundle.exists()

    shutil.rmtree(home)
    assert _run_under_pty(
        [sys.executable, str(CUBBY), "restore", str(bundle)], env, "hunter2") == 0

    result = subprocess.run(
        [sys.executable, str(CUBBY), "get", "tok", "--reveal"],
        env=env, capture_output=True, text=True, check=True)
    assert "s3cret" in result.stdout
