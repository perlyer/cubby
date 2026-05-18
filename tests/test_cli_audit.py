from cubby_tool import cli, config, audit, store


def test_audit_no_config_exits_4(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    assert cli.main(["audit", "--enable"]) == 4
    assert "not initialized" in capsys.readouterr().err
    assert not (home / "config.json").exists()


def test_audit_enable_disable(inited_home, capsys):
    assert cli.main(["audit", "--enable"]) == 0
    assert config.load_config(inited_home).audit is True
    assert cli.main(["audit", "--disable"]) == 0
    assert config.load_config(inited_home).audit is False


def test_audit_mutually_exclusive_flags(inited_home, capsys):
    assert cli.main(["audit", "--enable", "--clear"]) == 2
    assert "mutually exclusive" in capsys.readouterr().err


def test_audit_clear(inited_home, capsys):
    audit.log_event(inited_home, True, "run", "test", "echo")
    assert cli.main(["audit", "--clear"]) == 0
    assert audit.read_log(inited_home) == []


def test_audit_bare_shows_log(inited_home, capsys):
    audit.log_event(inited_home, True, "run", "test", "psql -h db")
    assert cli.main(["audit"]) == 0
    assert "psql -h db" in capsys.readouterr().out


def test_audit_bare_empty(inited_home, capsys):
    assert cli.main(["audit"]) == 0
    assert "no audit entries" in capsys.readouterr().out


def test_reveal_is_logged_when_audit_on(inited_home, identity, recipient, capsys):
    store.set_secret(inited_home, "test", "tok", "v", identity, recipient)
    cli.main(["audit", "--enable"])
    capsys.readouterr()
    assert cli.main(["get", "tok", "--reveal"]) == 0
    lines = audit.read_log(inited_home)
    assert any("reveal" in ln and "tok" in ln for ln in lines)


def test_reveal_not_logged_when_audit_off(inited_home, identity, recipient, capsys):
    store.set_secret(inited_home, "test", "tok", "v", identity, recipient)
    assert cli.main(["get", "tok", "--reveal"]) == 0
    assert audit.read_log(inited_home) == []
