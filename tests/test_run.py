import os
import subprocess
import sys
from pathlib import Path

from cubby_tool import config, keyring, store

REPO_ROOT = Path(__file__).resolve().parents[1]
CUBBY = REPO_ROOT / "cubby"


def _setup(home, identity, recipient, env_map=None):
    keyring.store_identity(home, identity, "file")
    cfg = config.Config(
        default_namespace="test",
        key_mode="file",
        namespaces={"test": config.Namespace(env_map=env_map or {})},
    )
    config.save_config(home, cfg)
    store.set_secret(home, "test", "db-pass", "s3cret", identity, recipient)


def _run(home, args):
    return subprocess.run(
        [sys.executable, str(CUBBY), *args],
        env={"CUBBY_HOME": str(home), "PATH": os.environ["PATH"]},
        capture_output=True, text=True,
    )


def test_run_injects_secret_as_default_env_var(home, identity, recipient):
    _setup(home, identity, recipient)
    result = _run(home, ["run", "-n", "test", "--", "sh", "-c", "echo $DB_PASS"])
    assert result.returncode == 0
    assert result.stdout.strip() == "s3cret"


def test_run_honors_env_map(home, identity, recipient):
    _setup(home, identity, recipient, env_map={"db-pass": "PGPASSWORD"})
    result = _run(home, ["run", "-n", "test", "--", "sh", "-c", "echo $PGPASSWORD"])
    assert result.stdout.strip() == "s3cret"


def test_run_does_not_leak_secret_when_child_is_silent(home, identity, recipient):
    _setup(home, identity, recipient)
    result = _run(home, ["run", "-n", "test", "--", "true"])
    assert result.returncode == 0
    assert "s3cret" not in result.stdout
    assert "s3cret" not in result.stderr


def test_run_without_command_returns_2(home, identity, recipient):
    _setup(home, identity, recipient)
    result = _run(home, ["run", "-n", "test", "--"])
    assert result.returncode == 2


def test_run_unknown_command_returns_2(home, identity, recipient):
    _setup(home, identity, recipient)
    result = _run(home, ["run", "-n", "test", "--", "cubby-no-such-binary"])
    assert result.returncode == 2
    assert "not found" in result.stderr
    assert "Traceback" not in result.stderr
