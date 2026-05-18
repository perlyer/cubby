import io
import subprocess
import tarfile

import pytest

from cubby_tool import archive
from cubby_tool import config


def test_build_then_extract_round_trips():
    members = {"identity": b"KEY", "config.json": b"{}",
               "secrets/test.age": b"\x01\x02"}
    data = archive.build_tar(members)
    assert archive.extract_tar(data) == members


def test_build_tar_is_a_valid_tar():
    data = archive.build_tar({"a": b"x"})
    with tarfile.open(fileobj=io.BytesIO(data), mode="r") as tar:
        assert tar.getnames() == ["a"]


def test_extract_tar_rejects_path_traversal():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name="../escape")
        info.size = 3
        tar.addfile(info, io.BytesIO(b"bad"))
    with pytest.raises(ValueError):
        archive.extract_tar(buf.getvalue())


def test_extract_tar_rejects_absolute_path():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name="/etc/evil")
        info.size = 3
        tar.addfile(info, io.BytesIO(b"bad"))
    with pytest.raises(ValueError):
        archive.extract_tar(buf.getvalue())


def test_extract_tar_rejects_compressed_archive():
    import gzip
    plain = archive.build_tar({"a": b"x"})
    with pytest.raises(tarfile.ReadError):
        archive.extract_tar(gzip.compress(plain))


def test_store_members_collects_identity_config_and_secrets(inited_home, identity,
                                                            recipient):
    from cubby_tool import store
    store.set_secret(inited_home, "test", "tok", "v", identity, recipient)
    members = archive._store_members(inited_home)
    assert members["identity"]
    assert members["config.json"]
    assert "secrets/test.age" in members


def test_export_bundle_invokes_age_with_the_tar(inited_home, identity, recipient,
                                                monkeypatch, tmp_path):
    from cubby_tool import store
    store.set_secret(inited_home, "test", "tok", "v", identity, recipient)
    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        captured["input"] = kw.get("input")
        class R:
            returncode = 0
        return R()

    monkeypatch.setattr(archive.subprocess, "run", fake_run)
    dest = tmp_path / "backup.age"
    archive.export_bundle(inited_home, dest)
    assert captured["cmd"][0] == "age"
    assert "--passphrase" in captured["cmd"]
    members = archive.extract_tar(captured["input"])
    assert "identity" in members and "config.json" in members


def test_restore_bundle_unpacks_into_home(home, monkeypatch, tmp_path):
    members = {
        "identity": b"AGE-SECRET-KEY-FAKE",
        "config.json": b'{"default_namespace": "test", "key_mode": "file", '
                       b'"audit": false, "namespaces": {"test": {"cwd_prefix": '
                       b'null, "env_map": {}}}}',
        "secrets/test.age": b"\x01\x02\x03",
    }
    tar_bytes = archive.build_tar(members)

    def fake_run(cmd, **kw):
        assert cmd[0] == "age" and "--decrypt" in cmd
        class R:
            stdout = tar_bytes
            returncode = 0
        return R()

    monkeypatch.setattr(archive.subprocess, "run", fake_run)
    archive.restore_bundle(tmp_path / "bundle.age", home)
    assert (home / "identity").read_bytes() == b"AGE-SECRET-KEY-FAKE"
    assert (home / "secrets" / "test.age").read_bytes() == b"\x01\x02\x03"
    assert oct((home / "identity").stat().st_mode & 0o777) == "0o600"


def test_restore_bundle_forces_file_key_mode(home, monkeypatch, tmp_path):
    from cubby_tool import config
    members = {
        "identity": b"AGE-SECRET-KEY-FAKE",
        "config.json": b'{"default_namespace": "test", "key_mode": "keychain", '
                       b'"audit": false, "namespaces": {"test": {"cwd_prefix": '
                       b'null, "env_map": {}}}}',
    }
    tar_bytes = archive.build_tar(members)

    def fake_run(cmd, **kw):
        class R:
            stdout = tar_bytes
            returncode = 0
        return R()

    monkeypatch.setattr(archive.subprocess, "run", fake_run)
    archive.restore_bundle(tmp_path / "bundle.age", home)
    assert config.load_config(home).key_mode == "file"


def test_restore_bundle_clears_stale_namespace_files(home, monkeypatch, tmp_path):
    (home / "secrets").mkdir(parents=True)
    (home / "secrets" / "stale.age").write_bytes(b"OLD")
    members = {
        "identity": b"AGE-SECRET-KEY-FAKE",
        "config.json": b'{"default_namespace": "test", "key_mode": "file", '
                       b'"audit": false, "namespaces": {}}',
        "secrets/test.age": b"\x01\x02\x03",
    }
    tar_bytes = archive.build_tar(members)

    def fake_run(cmd, **kw):
        class R:
            stdout = tar_bytes
            returncode = 0
        return R()

    monkeypatch.setattr(archive.subprocess, "run", fake_run)
    archive.restore_bundle(tmp_path / "bundle.age", home)
    assert not (home / "secrets" / "stale.age").exists()
    assert (home / "secrets" / "test.age").read_bytes() == b"\x01\x02\x03"


def test_restore_bundle_returns_original_key_mode(home, monkeypatch, tmp_path):
    members = {
        "identity": b"AGE-SECRET-KEY-FAKE",
        "config.json": b'{"default_namespace": "test", "key_mode": "keychain", '
                       b'"audit": false, "namespaces": {}}',
    }
    tar_bytes = archive.build_tar(members)

    def fake_run(cmd, **kw):
        class R:
            stdout = tar_bytes
            returncode = 0
        return R()

    monkeypatch.setattr(archive.subprocess, "run", fake_run)
    original = archive.restore_bundle(tmp_path / "bundle.age", home)
    assert original == "keychain"
    assert config.load_config(home).key_mode == "file"


def test_restore_bundle_decrypt_failure_leaves_store_intact(home, monkeypatch, tmp_path):
    (home / "secrets").mkdir(parents=True)
    (home / "secrets" / "keep.age").write_bytes(b"PRECIOUS")

    def failing_run(cmd, **kw):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(archive.subprocess, "run", failing_run)
    with pytest.raises(subprocess.CalledProcessError):
        archive.restore_bundle(tmp_path / "bundle.age", home)
    # the decrypt failed before any deletion — the existing secret survives
    assert (home / "secrets" / "keep.age").read_bytes() == b"PRECIOUS"
