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


def test_restore_refuses_existing_store_without_force(inited_home, monkeypatch,
                                                      capsys, tmp_path):
    bundle = tmp_path / "b.age"
    bundle.write_bytes(b"x")
    monkeypatch.setattr(archive, "restore_bundle", lambda src, home: None)
    assert cli.main(["restore", str(bundle)]) == 4
    assert "already exists" in capsys.readouterr().err


def test_restore_force_overwrites(inited_home, monkeypatch, capsys, tmp_path):
    bundle = tmp_path / "b.age"
    bundle.write_bytes(b"x")
    called = {}
    monkeypatch.setattr(archive, "restore_bundle",
                        lambda src, home: called.setdefault("done", True))
    assert cli.main(["restore", str(bundle), "--force"]) == 0
    assert called["done"] is True


def test_restore_missing_file_returns_2(inited_home, capsys, tmp_path):
    assert cli.main(["restore", str(tmp_path / "nope.age")]) == 2
    assert "not found" in capsys.readouterr().err


def test_restore_reports_keychain_backup(inited_home, monkeypatch, capsys, tmp_path):
    bundle = tmp_path / "b.age"
    bundle.write_bytes(b"x")
    monkeypatch.setattr(archive, "restore_bundle", lambda src, home: "keychain")
    assert cli.main(["restore", str(bundle), "--force"]) == 0
    out = capsys.readouterr().out
    assert "keychain" in out and "file key-mode" in out


def test_restore_no_note_for_file_backup(inited_home, monkeypatch, capsys, tmp_path):
    bundle = tmp_path / "b.age"
    bundle.write_bytes(b"x")
    monkeypatch.setattr(archive, "restore_bundle", lambda src, home: "file")
    assert cli.main(["restore", str(bundle), "--force"]) == 0
    assert "keychain" not in capsys.readouterr().out
