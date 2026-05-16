from cubby_tool import cli, config, keyring


def test_init_creates_config_and_identity(home, monkeypatch):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    assert cli.main(["init", "--key-mode", "file", "--namespace", "acme"]) == 0
    cfg = config.load_config(home)
    assert cfg.default_namespace == "acme"
    assert cfg.key_mode == "file"
    assert "acme" in cfg.namespaces
    assert "AGE-SECRET-KEY-1" in keyring.load_identity(home, "file")


def test_init_refuses_when_already_initialized(home, monkeypatch):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    cli.main(["init", "--key-mode", "file"])
    assert cli.main(["init", "--key-mode", "file"]) == 4
