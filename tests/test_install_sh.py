import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL = REPO_ROOT / "install.sh"


def test_install_sh_exists_and_executable():
    assert INSTALL.exists()
    assert INSTALL.stat().st_mode & 0o111


def test_install_sh_has_posix_shebang():
    assert INSTALL.read_text().splitlines()[0] in ("#!/bin/sh", "#!/usr/bin/env sh")


def test_install_sh_passes_shellcheck_syntax():
    result = subprocess.run(["sh", "-n", str(INSTALL)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_install_sh_has_banner():
    assert "encrypted secret store" in INSTALL.read_text()
