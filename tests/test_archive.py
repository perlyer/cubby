import io
import tarfile

import pytest

from cubby_tool import archive


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
