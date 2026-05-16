from cubby_tool import cli, commands, store


def test_parse_env_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text('# comment\nDB_HOST=localhost\nTOKEN="abc 123"\n\nEMPTY=\n')
    parsed = commands._parse_env_file(env)
    assert parsed == {"DB_HOST": "localhost", "TOKEN": "abc 123", "EMPTY": ""}


def test_import_from_env_file(inited_home, tmp_path, identity, capsys):
    env = tmp_path / ".env"
    env.write_text("DB_HOST=localhost\nDB_PASW=secret\n")
    assert cli.main(["import", "--from-env", str(env)]) == 0
    values = store.read_values(inited_home, "test", identity)
    assert values == {"DB_HOST": "localhost", "DB_PASW": "secret"}


def test_import_without_source_returns_2(inited_home):
    assert cli.main(["import"]) == 2


def test_import_missing_env_file_returns_2(inited_home, tmp_path, capsys):
    missing = tmp_path / "nope.env"
    assert cli.main(["import", "--from-env", str(missing)]) == 2
    assert "not found" in capsys.readouterr().err
