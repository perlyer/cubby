from cubby_tool import cli, store


def test_ttl_set_on_existing_secret_keeps_value(inited_home, identity, recipient, capsys):
    store.set_secret(inited_home, "test", "tok", "v", identity, recipient)
    assert cli.main(["ttl", "tok", "30d"]) == 0
    entry = store.read_entries(inited_home, "test", identity)["tok"]
    assert entry["value"] == "v"
    assert entry["ttl"] == "30d"
    assert "expires" in entry


def test_ttl_none_clears(inited_home, identity, recipient, capsys):
    store.set_secret(inited_home, "test", "tok", "v", identity, recipient,
                     meta={"ttl": "30d", "expires": "2099-01-01T00:00:00+00:00"})
    assert cli.main(["ttl", "tok", "none"]) == 0
    entry = store.read_entries(inited_home, "test", identity)["tok"]
    assert "ttl" not in entry and "expires" not in entry


def test_ttl_unknown_secret_returns_4(inited_home, capsys):
    assert cli.main(["ttl", "absent", "30d"]) == 4
    assert "not found" in capsys.readouterr().err


def test_ttl_list_shows_secrets(inited_home, identity, recipient, capsys):
    store.set_secret(inited_home, "test", "a", "v", identity, recipient,
                     meta={"ttl": "30d", "expires": "2099-01-01T00:00:00+00:00"})
    store.set_secret(inited_home, "test", "b", "v", identity, recipient)
    assert cli.main(["ttl"]) == 0
    out = capsys.readouterr().out
    assert "a" in out and "b" in out
    assert "no expiry" in out


def test_ttl_clear_when_absent_is_a_noop(inited_home, identity, recipient, capsys):
    store.set_secret(inited_home, "test", "tok", "v", identity, recipient)
    assert cli.main(["ttl", "tok", "none"]) == 0
    assert "no expiry" in capsys.readouterr().out
