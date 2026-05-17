import getpass

from cubby_tool import cli, config


def test_rename_moves_the_secret(inited_home, monkeypatch, capsys):
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    cli.main(["set", "old-name"])
    capsys.readouterr()
    assert cli.main(["rename", "old-name", "new-name"]) == 0
    capsys.readouterr()
    assert cli.main(["list"]) == 0
    out = capsys.readouterr().out
    assert "new-name" in out
    assert "old-name" not in out


def test_rename_moves_the_env_map_override(inited_home, monkeypatch, capsys):
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    cli.main(["set", "old-name", "--env", "MY_VAR"])
    capsys.readouterr()
    assert cli.main(["rename", "old-name", "new-name"]) == 0
    env_map = config.load_config(inited_home).namespaces["test"].env_map
    assert env_map.get("new-name") == "MY_VAR"
    assert "old-name" not in env_map


def test_rename_missing_secret_returns_4(inited_home, capsys):
    assert cli.main(["rename", "ghost", "other"]) == 4


def test_rename_to_existing_name_returns_4(inited_home, monkeypatch, capsys):
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    cli.main(["set", "alpha"])
    cli.main(["set", "beta"])
    capsys.readouterr()
    assert cli.main(["rename", "alpha", "beta"]) == 4


def test_rename_to_self_is_rejected(inited_home, monkeypatch, capsys):
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    cli.main(["set", "samename"])
    capsys.readouterr()
    assert cli.main(["rename", "samename", "samename"]) == 4
    capsys.readouterr()
    # the secret must still be there — the rejected rename must not destroy it
    assert cli.main(["list"]) == 0
    assert "samename" in capsys.readouterr().out
