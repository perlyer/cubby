import getpass

from cubby_tool import cli


def test_set_via_getpass_then_list(inited_home, monkeypatch, capsys):
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    assert cli.main(["set", "db"]) == 0
    capsys.readouterr()
    assert cli.main(["list"]) == 0
    assert "db" in capsys.readouterr().out


def test_get_without_reveal_hides_value(inited_home, monkeypatch, capsys):
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    cli.main(["set", "db"])
    capsys.readouterr()
    assert cli.main(["get", "db"]) == 0
    out = capsys.readouterr().out
    assert "s3cret" not in out
    assert "length: 6" in out


def test_get_with_reveal_prints_value(inited_home, monkeypatch, capsys):
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    cli.main(["set", "db"])
    capsys.readouterr()
    assert cli.main(["get", "db", "--reveal"]) == 0
    captured = capsys.readouterr()
    assert "s3cret" in captured.out
    assert "WARNING" in captured.err


def test_get_missing_secret_returns_4(inited_home, capsys):
    assert cli.main(["get", "nope"]) == 4


def test_rm_secret(inited_home, monkeypatch):
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    cli.main(["set", "db"])
    assert cli.main(["rm", "db"]) == 0
    assert cli.main(["get", "db"]) == 4


def test_get_metadata_shows_secret_title(inited_home, monkeypatch, capsys):
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    cli.main(["set", "db"])
    capsys.readouterr()
    assert cli.main(["get", "db"]) == 0
    assert "secret 'db'" in capsys.readouterr().out


def test_set_with_env_records_the_override(inited_home, monkeypatch, capsys):
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    assert cli.main(["set", "db", "--env", "PGPASSWORD"]) == 0
    from cubby_tool import config
    cfg = config.load_config(inited_home)
    assert cfg.namespaces["test"].env_map["db"] == "PGPASSWORD"


def test_set_with_clashing_env_returns_4(inited_home, monkeypatch, capsys):
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    cli.main(["set", "alpha"])               # default env var ALPHA
    capsys.readouterr()
    assert cli.main(["set", "beta", "--env", "ALPHA"]) == 4
    err = capsys.readouterr().err
    assert "already used by secret 'alpha'" in err
