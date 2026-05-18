import getpass

from cubby_tool import cli, commands, store


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


def test_set_with_env_records_the_override(inited_home, monkeypatch):
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
    # the clash must be atomic — beta was not stored
    capsys.readouterr()
    assert cli.main(["list"]) == 0
    assert "beta" not in capsys.readouterr().out


def test_get_shows_the_default_env_var(inited_home, monkeypatch, capsys):
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    cli.main(["set", "db-pass"])
    capsys.readouterr()
    assert cli.main(["get", "db-pass"]) == 0
    out = capsys.readouterr().out
    assert "DB_PASS" in out
    assert "default" in out


def test_get_shows_an_override_env_var(inited_home, monkeypatch, capsys):
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    cli.main(["set", "db-pass", "--env", "PGPASSWORD"])
    capsys.readouterr()
    assert cli.main(["get", "db-pass"]) == 0
    out = capsys.readouterr().out
    assert "PGPASSWORD" in out
    assert "override" in out


def test_set_with_ttl_stores_expiry(inited_home, identity, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin.read", lambda: "v\n")
    assert cli.main(["set", "tok", "--stdin", "--ttl", "30d"]) == 0
    from cubby_tool import store
    entry = store.read_entries(inited_home, "test", identity)["tok"]
    assert entry["ttl"] == "30d"
    assert "expires" in entry


def test_set_without_ttl_has_no_expiry(inited_home, identity, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin.read", lambda: "v\n")
    assert cli.main(["set", "tok", "--stdin"]) == 0
    from cubby_tool import store
    entry = store.read_entries(inited_home, "test", identity)["tok"]
    assert "expires" not in entry and "ttl" not in entry


def test_set_with_bad_ttl_returns_2(inited_home, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin.read", lambda: "v\n")
    assert cli.main(["set", "tok", "--stdin", "--ttl", "bogus"]) == 2
    assert "invalid duration" in capsys.readouterr().err


def test_get_shows_expires_and_rotated(inited_home, identity, recipient, capsys):
    from cubby_tool import store
    store.set_secret(inited_home, "test", "tok", "v", identity, recipient,
                     meta={"ttl": "30d", "expires": "2099-01-01T00:00:00+00:00"})
    assert cli.main(["get", "tok"]) == 0
    out = capsys.readouterr().out
    assert "expires:" in out and "2099-01-01" in out
    assert "rotated:" in out and "never" in out


def test_get_shows_never_when_no_ttl(inited_home, identity, recipient, capsys):
    from cubby_tool import store
    store.set_secret(inited_home, "test", "tok", "v", identity, recipient)
    assert cli.main(["get", "tok"]) == 0
    out = capsys.readouterr().out
    assert "expires:" in out and "never" in out


def test_get_copy_copies_without_printing(inited_home, identity, recipient,
                                          monkeypatch, capsys):
    store.set_secret(inited_home, "test", "tok", "s3cret", identity, recipient)
    copied = {}

    def fake_copy(text):
        copied["v"] = text
        return "pbcopy"

    monkeypatch.setattr(commands, "_copy_to_clipboard", fake_copy)
    assert cli.main(["get", "tok", "--copy"]) == 0
    out = capsys.readouterr().out
    assert copied["v"] == "s3cret"
    assert "s3cret" not in out
    assert "copied" in out


def test_get_copy_no_tool_returns_2(inited_home, identity, recipient,
                                    monkeypatch, capsys):
    store.set_secret(inited_home, "test", "tok", "s3cret", identity, recipient)

    def boom(text):
        raise RuntimeError("no clipboard tool found")

    monkeypatch.setattr(commands, "_copy_to_clipboard", boom)
    assert cli.main(["get", "tok", "--copy"]) == 2


def test_get_copy_and_reveal_together_is_an_error(inited_home, identity,
                                                  recipient, capsys):
    store.set_secret(inited_home, "test", "tok", "s3cret", identity, recipient)
    import pytest
    with pytest.raises(SystemExit):
        cli.main(["get", "tok", "--copy", "--reveal"])


def test_copy_to_clipboard_uses_first_available_tool(monkeypatch):
    calls = {}
    monkeypatch.setattr(commands.shutil, "which",
                        lambda name: "/usr/bin/" + name if name == "pbcopy" else None)
    monkeypatch.setattr(commands.subprocess, "run",
                        lambda cmd, **kw: calls.update(cmd=cmd, text=kw.get("input")))
    tool = commands._copy_to_clipboard("hello")
    assert tool == "pbcopy"
    assert calls["cmd"][0] == "pbcopy"
    assert calls["text"] == "hello"
