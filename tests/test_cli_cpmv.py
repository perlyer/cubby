from cubby_tool import cli, config, store


def _add_ns(home, name):
    cfg = config.load_config(home)
    cfg.namespaces[name] = config.Namespace()
    config.save_config(home, cfg)


def test_cp_copies_secret(inited_home, identity, recipient, capsys):
    _add_ns(inited_home, "other")
    store.set_secret(inited_home, "test", "tok", "v", identity, recipient)
    assert cli.main(["cp", "tok", "other"]) == 0
    assert store.read_entries(inited_home, "test", identity)["tok"]["value"] == "v"
    assert store.read_entries(inited_home, "other", identity)["tok"]["value"] == "v"


def test_cp_carries_env_map(inited_home, identity, recipient, capsys):
    _add_ns(inited_home, "other")
    store.set_secret(inited_home, "test", "tok", "v", identity, recipient)
    cfg = config.load_config(inited_home)
    cfg.namespaces["test"].env_map["tok"] = "MY_TOKEN"
    config.save_config(inited_home, cfg)
    assert cli.main(["cp", "tok", "other"]) == 0
    assert config.load_config(inited_home).namespaces["other"].env_map["tok"] == "MY_TOKEN"
    assert config.load_config(inited_home).namespaces["test"].env_map.get("tok") == "MY_TOKEN"


def test_cp_missing_secret_returns_4(inited_home, capsys):
    _add_ns(inited_home, "other")
    assert cli.main(["cp", "absent", "other"]) == 4
    assert "not found" in capsys.readouterr().err


def test_cp_missing_dest_namespace_returns_4(inited_home, identity, recipient, capsys):
    store.set_secret(inited_home, "test", "tok", "v", identity, recipient)
    assert cli.main(["cp", "tok", "ghost"]) == 4
    assert "ghost" in capsys.readouterr().err


def test_cp_name_exists_in_dest_returns_4(inited_home, identity, recipient, capsys):
    _add_ns(inited_home, "other")
    store.set_secret(inited_home, "test", "tok", "v1", identity, recipient)
    store.set_secret(inited_home, "other", "tok", "v2", identity, recipient)
    assert cli.main(["cp", "tok", "other"]) == 4
    assert "already exists" in capsys.readouterr().err


def test_cp_dest_equals_source_returns_4(inited_home, identity, recipient, capsys):
    store.set_secret(inited_home, "test", "tok", "v", identity, recipient)
    assert cli.main(["cp", "tok", "test"]) == 4
    assert "rename" in capsys.readouterr().err


def test_mv_moves_secret(inited_home, identity, recipient, capsys):
    _add_ns(inited_home, "other")
    store.set_secret(inited_home, "test", "tok", "v", identity, recipient)
    assert cli.main(["mv", "tok", "other"]) == 0
    assert "tok" not in store.read_entries(inited_home, "test", identity)
    assert store.read_entries(inited_home, "other", identity)["tok"]["value"] == "v"


def test_mv_moves_env_map(inited_home, identity, recipient, capsys):
    _add_ns(inited_home, "other")
    store.set_secret(inited_home, "test", "tok", "v", identity, recipient)
    cfg = config.load_config(inited_home)
    cfg.namespaces["test"].env_map["tok"] = "MY_TOKEN"
    config.save_config(inited_home, cfg)
    assert cli.main(["mv", "tok", "other"]) == 0
    after = config.load_config(inited_home)
    assert "tok" not in after.namespaces["test"].env_map
    assert after.namespaces["other"].env_map["tok"] == "MY_TOKEN"


def test_mv_missing_secret_returns_4(inited_home, capsys):
    _add_ns(inited_home, "other")
    assert cli.main(["mv", "absent", "other"]) == 4


def test_mv_name_exists_in_dest_keeps_source(inited_home, identity, recipient, capsys):
    _add_ns(inited_home, "other")
    store.set_secret(inited_home, "test", "tok", "v1", identity, recipient)
    store.set_secret(inited_home, "other", "tok", "v2", identity, recipient)
    assert cli.main(["mv", "tok", "other"]) == 4
    # the move was refused — the source secret is still there
    assert store.read_entries(inited_home, "test", identity)["tok"]["value"] == "v1"
