import json

import pytest

from cubby_tool import cli, commands, store


def test_parse_env_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text('# comment\nDB_HOST=localhost\nTOKEN="abc 123"\n\nEMPTY=\n')
    parsed = commands._parse_env_file(env)
    assert parsed == {"DB_HOST": "localhost", "TOKEN": "abc 123", "EMPTY": ""}


def test_parse_json_file_flat(tmp_path):
    f = tmp_path / "s.json"
    f.write_text('{"A": "1", "B": 2}')
    assert commands._parse_json_file(f) == {"A": "1", "B": "2"}


def test_parse_json_file_rejects_non_object(tmp_path):
    f = tmp_path / "s.json"
    f.write_text('["a", "b"]')
    with pytest.raises(ValueError):
        commands._parse_json_file(f)


def test_parse_json_file_rejects_nested_value(tmp_path):
    f = tmp_path / "s.json"
    f.write_text('{"A": {"nested": 1}}')
    with pytest.raises(ValueError):
        commands._parse_json_file(f)


def test_import_dotenv(inited_home, tmp_path, identity, capsys):
    env = tmp_path / ".env"
    env.write_text("DB_HOST=localhost\nDB_PASW=secret\n")
    assert cli.main(["import", "dotenv", str(env)]) == 0
    values = store.read_values(inited_home, "test", identity)
    assert values == {"DB_HOST": "localhost", "DB_PASW": "secret"}


def test_import_json(inited_home, tmp_path, identity, capsys):
    f = tmp_path / "s.json"
    f.write_text('{"K1": "v1", "K2": "v2"}')
    assert cli.main(["import", "json", str(f)]) == 0
    assert store.read_values(inited_home, "test", identity) == {"K1": "v1", "K2": "v2"}


def test_import_json_bad_document_returns_2(inited_home, tmp_path, capsys):
    f = tmp_path / "s.json"
    f.write_text('["not", "an", "object"]')
    assert cli.main(["import", "json", str(f)]) == 2


def test_import_missing_file_returns_2(inited_home, tmp_path, capsys):
    assert cli.main(["import", "dotenv", str(tmp_path / "nope.env")]) == 2
    assert "not found" in capsys.readouterr().err


def test_import_ns_copies_values(inited_home, identity, recipient, capsys):
    from cubby_tool import config
    cfg = config.load_config(inited_home)
    cfg.namespaces["src"] = config.Namespace()
    config.save_config(inited_home, cfg)
    store.set_secret(inited_home, "src", "shared", "val", identity, recipient)
    assert cli.main(["import", "ns", "src"]) == 0
    assert store.read_values(inited_home, "test", identity)["shared"] == "val"


def test_import_ns_onto_itself_returns_4(inited_home, capsys):
    assert cli.main(["import", "ns", "test"]) == 4
    assert "itself" in capsys.readouterr().err


def test_import_ns_unknown_returns_4(inited_home, capsys):
    assert cli.main(["import", "ns", "ghost"]) == 4


def test_import_unknown_type_errors(inited_home, capsys):
    with pytest.raises(SystemExit):
        cli.main(["import", "bogus", "x"])


def test_fetch_1password_picks_password_field(monkeypatch):
    import subprocess as sp

    def fake_run(cmd, **kwargs):
        class R:
            pass
        r = R()
        if cmd[:3] == ["op", "item", "list"]:
            r.stdout = json.dumps([{"id": "i1", "title": "GitHub"}])
        else:
            r.stdout = json.dumps({"fields": [
                {"type": "STRING", "value": "ignore"},
                {"type": "CONCEALED", "purpose": "PASSWORD", "value": "pw"},
            ]})
        return r

    monkeypatch.setattr(sp, "run", fake_run)
    assert commands._fetch_1password("Personal") == {"GitHub": "pw"}
