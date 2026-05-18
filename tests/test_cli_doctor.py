import getpass

from cubby_tool import cli, config


def test_doctor_passes_on_a_healthy_store(inited_home, capsys):
    assert cli.main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "cubby doctor" in out
    assert "all checks passed" in out


def test_doctor_fails_on_a_duplicate_env_var(inited_home, monkeypatch, capsys):
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    cli.main(["set", "alpha"])
    cli.main(["set", "beta"])
    # force a duplicate: point beta's override at alpha's default env var
    cfg = config.load_config(inited_home)
    cfg.namespaces["test"].env_map["beta"] = "ALPHA"
    config.save_config(inited_home, cfg)
    capsys.readouterr()
    assert cli.main(["doctor"]) == 2
    assert "ALPHA" in capsys.readouterr().out


def test_doctor_warns_on_a_dangling_env_map_entry(inited_home, capsys):
    cfg = config.load_config(inited_home)
    cfg.namespaces["test"].env_map["ghost"] = "GHOST_VAR"
    config.save_config(inited_home, cfg)
    capsys.readouterr()
    # a dangling entry is a warning, not a failure — still exit 0
    assert cli.main(["doctor"]) == 0
    assert "ghost" in capsys.readouterr().out
