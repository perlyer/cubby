from cubby_tool import cli, store


def test_rotate_increments_counter(inited_home, identity, recipient, monkeypatch, capsys):
    store.set_secret(inited_home, "test", "tok", "old", identity, recipient)
    monkeypatch.setattr("sys.stdin.read", lambda: "new\n")
    assert cli.main(["rotate", "tok", "--stdin"]) == 0
    entry = store.read_entries(inited_home, "test", identity)["tok"]
    assert entry["value"] == "new"
    assert entry["rotated"] == 1


def test_rotate_missing_secret_returns_4(inited_home, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin.read", lambda: "new\n")
    assert cli.main(["rotate", "absent", "--stdin"]) == 4
    assert "not found" in capsys.readouterr().err


def test_rotate_refreshes_existing_ttl(inited_home, identity, recipient, monkeypatch, capsys):
    store.set_secret(inited_home, "test", "tok", "old", identity, recipient,
                     meta={"ttl": "7d", "expires": "2000-01-01T00:00:00+00:00"})
    monkeypatch.setattr("sys.stdin.read", lambda: "new\n")
    assert cli.main(["rotate", "tok", "--stdin"]) == 0
    entry = store.read_entries(inited_home, "test", identity)["tok"]
    assert entry["ttl"] == "7d"
    assert entry["expires"] > "2025-01-01"  # recomputed into the future


def test_rotate_ttl_none_clears_expiry(inited_home, identity, recipient, monkeypatch, capsys):
    store.set_secret(inited_home, "test", "tok", "old", identity, recipient,
                     meta={"ttl": "7d", "expires": "2099-01-01T00:00:00+00:00"})
    monkeypatch.setattr("sys.stdin.read", lambda: "new\n")
    assert cli.main(["rotate", "tok", "--stdin", "--ttl", "none"]) == 0
    entry = store.read_entries(inited_home, "test", identity)["tok"]
    assert "ttl" not in entry and "expires" not in entry
