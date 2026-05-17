import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UPDATE = REPO_ROOT / "update.sh"


def test_update_sh_exists_and_executable():
    assert UPDATE.exists()
    assert UPDATE.stat().st_mode & 0o111


def test_update_sh_has_posix_shebang():
    assert UPDATE.read_text().splitlines()[0] in ("#!/bin/sh", "#!/usr/bin/env sh")


def test_update_sh_passes_syntax_check():
    result = subprocess.run(["sh", "-n", str(UPDATE)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_update_sh_refreshes_agents():
    assert "agent refresh" in UPDATE.read_text()


def test_update_sh_has_banner():
    assert "encrypted secret store" in UPDATE.read_text()
