import getpass

from cubby_tool import cli, config


def test_ns_add_then_listed_bare(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    assert cli.main(["ns", "add", "acme", "--cwd-prefix", "/p/acme"]) == 0
    capsys.readouterr()
    assert cli.main(["ns"]) == 0
    out = capsys.readouterr().out
    assert "acme" in out
    assert "/p/acme" in out


def test_ns_list_is_alias_of_bare(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    cli.main(["ns", "add", "acme"])
    capsys.readouterr()
    assert cli.main(["ns", "list"]) == 0
    assert "acme" in capsys.readouterr().out


def test_ns_bare_marks_default(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    cfg = config.Config(default_namespace="acme", namespaces={"acme": config.Namespace()})
    config.save_config(home, cfg)
    capsys.readouterr()
    assert cli.main(["ns"]) == 0
    out = capsys.readouterr().out
    assert "acme" in out and "default" in out
    assert "active" in out


def test_ns_use_sets_default(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    cli.main(["ns", "add", "one"])
    cli.main(["ns", "add", "two"])
    assert cli.main(["ns", "use", "two"]) == 0
    assert config.load_config(home).default_namespace == "two"


def test_ns_use_unknown_returns_4(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    cli.main(["ns", "add", "one"])
    assert cli.main(["ns", "use", "ghost"]) == 4


def test_ns_rm(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    cli.main(["ns", "add", "acme"])
    assert cli.main(["ns", "rm", "acme"]) == 0
    assert config.load_config(home).namespaces == {}


def test_ns_bare_shows_namespaces_title(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    cli.main(["ns", "add", "acme"])
    capsys.readouterr()
    assert cli.main(["ns"]) == 0
    assert "namespaces" in capsys.readouterr().out


def test_ns_rename_moves_the_namespace(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    cli.main(["ns", "add", "old-ns"])
    assert cli.main(["ns", "rename", "old-ns", "new-ns"]) == 0
    cfg = config.load_config(home)
    assert "new-ns" in cfg.namespaces
    assert "old-ns" not in cfg.namespaces


def test_ns_rename_updates_the_default(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    cli.main(["ns", "add", "only-ns"])          # becomes the default
    assert cli.main(["ns", "rename", "only-ns", "renamed"]) == 0
    assert config.load_config(home).default_namespace == "renamed"


def test_ns_rename_missing_returns_4(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    cli.main(["ns", "add", "exists"])
    assert cli.main(["ns", "rename", "ghost", "whatever"]) == 4


def test_ns_rename_to_existing_returns_4(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    cli.main(["ns", "add", "one"])
    cli.main(["ns", "add", "two"])
    assert cli.main(["ns", "rename", "one", "two"]) == 4


def test_ns_rename_moves_the_encrypted_file(inited_home, monkeypatch, capsys):
    home = inited_home
    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: "s3cret")
    cli.main(["ns", "add", "src-ns"])
    cli.main(["set", "-n", "src-ns", "thekey"])
    assert (home / "secrets" / "src-ns.age").exists()
    assert cli.main(["ns", "rename", "src-ns", "dst-ns"]) == 0
    # the encrypted file moved with the namespace
    assert not (home / "secrets" / "src-ns.age").exists()
    assert (home / "secrets" / "dst-ns.age").exists()
    # and the secret is still readable under the new namespace
    capsys.readouterr()
    assert cli.main(["list", "-n", "dst-ns"]) == 0
    assert "thekey" in capsys.readouterr().out


def test_ns_rename_of_non_default_leaves_default_alone(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    cli.main(["ns", "add", "first"])          # becomes the default
    cli.main(["ns", "add", "second"])         # not the default
    assert cli.main(["ns", "rename", "second", "second-renamed"]) == 0
    assert config.load_config(home).default_namespace == "first"
