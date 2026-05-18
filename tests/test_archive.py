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
