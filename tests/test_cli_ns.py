from cubby_tool import cli, config


def test_ns_add_and_list(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    assert cli.main(["ns", "add", "nord", "--cwd-prefix", "/p/Nord"]) == 0
    capsys.readouterr()
    assert cli.main(["ns", "list"]) == 0
    assert "nord" in capsys.readouterr().out


def test_ns_status_shows_active_namespace_and_reason(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    cfg = config.Config(default_namespace="nord", namespaces={"nord": config.Namespace()})
    config.save_config(home, cfg)
    capsys.readouterr()
    assert cli.main(["ns"]) == 0
    out = capsys.readouterr().out
    assert "nord" in out and "default" in out


def test_ns_rm(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    cli.main(["ns", "add", "nord"])
    assert cli.main(["ns", "rm", "nord"]) == 0
    assert config.load_config(home).namespaces == {}
