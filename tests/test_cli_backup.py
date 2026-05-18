from cubby_tool import cli, archive


def test_export_writes_a_bundle(inited_home, monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(archive, "export_bundle",
                        lambda home, dest: dest.write_bytes(b"x"))
    dest = tmp_path / "backup.age"
    assert cli.main(["export", str(dest)]) == 0
    assert "backup" in capsys.readouterr().out


def test_export_without_a_store_returns_4(home, monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    assert cli.main(["export", str(tmp_path / "b.age")]) == 4
    assert "not initialized" in capsys.readouterr().err
