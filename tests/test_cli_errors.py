from cubby_tool import cli, config


def test_main_handles_corrupt_config(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    config.config_path(home).parent.mkdir(parents=True, exist_ok=True)
    config.config_path(home).write_text("{ not json")
    rc = cli.main(["ns", "list"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "✗" in err
    assert "Traceback" not in err


def test_main_handles_unresolvable_namespace(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    config.save_config(home, config.Config())
    rc = cli.main(["list"])
    assert rc == 4
    err = capsys.readouterr().err
    assert "✗" in err
    assert "Traceback" not in err
