import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UNINSTALL = REPO_ROOT / "uninstall.sh"


def test_uninstall_sh_exists_and_executable():
    assert UNINSTALL.exists()
    assert UNINSTALL.stat().st_mode & 0o111


def test_uninstall_sh_has_posix_shebang():
    assert UNINSTALL.read_text().splitlines()[0] in ("#!/bin/sh", "#!/usr/bin/env sh")


def test_uninstall_sh_passes_syntax_check():
    result = subprocess.run(["sh", "-n", str(UNINSTALL)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_uninstall_sh_mentions_purge_flag():
    assert "--purge" in UNINSTALL.read_text()
