import getpass

from cubby_tool import cli, config


def _seed(monkeypatch, *names):
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    for n in names:
        cli.main(["set", n])


def test_map_lists_secrets_and_their_env_vars(inited_home, monkeypatch, capsys):
    _seed(monkeypatch, "db-pass", "token")
    capsys.readouterr()
    assert cli.main(["map"]) == 0
    out = capsys.readouterr().out
    assert "db-pass" in out and "DB_PASS" in out
    assert "token" in out and "TOKEN" in out
    assert "default" in out


def test_map_sets_an_override(inited_home, monkeypatch, capsys):
    _seed(monkeypatch, "db-pass")
    capsys.readouterr()
    assert cli.main(["map", "db-pass", "PGPASSWORD"]) == 0
    assert config.load_config(inited_home).namespaces["test"].env_map["db-pass"] == "PGPASSWORD"


def test_map_reset_drops_the_override(inited_home, monkeypatch, capsys):
    _seed(monkeypatch, "db-pass")
    cli.main(["map", "db-pass", "PGPASSWORD"])
    capsys.readouterr()
    assert cli.main(["map", "db-pass", "--reset"]) == 0
    assert "db-pass" not in config.load_config(inited_home).namespaces["test"].env_map


def test_map_show_one_secret(inited_home, monkeypatch, capsys):
    _seed(monkeypatch, "token")
    capsys.readouterr()
    assert cli.main(["map", "token"]) == 0
    assert "TOKEN" in capsys.readouterr().out


def test_map_unknown_secret_returns_4(inited_home, capsys):
    assert cli.main(["map", "ghost", "GHOST"]) == 4
    assert "not found" in capsys.readouterr().err


def test_map_clashing_var_returns_4(inited_home, monkeypatch, capsys):
    _seed(monkeypatch, "alpha", "beta")
    capsys.readouterr()
    assert cli.main(["map", "beta", "ALPHA"]) == 4
    assert "already used by secret 'alpha'" in capsys.readouterr().err
