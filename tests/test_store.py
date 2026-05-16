from cubby_tool import store


def test_read_entries_missing_namespace_returns_empty(home, identity):
    assert store.read_entries(home, "nord", identity) == {}


def test_set_get_roundtrip(home, identity, recipient):
    store.set_secret(home, "nord", "db", "s3cret", identity, recipient)
    values = store.read_values(home, "nord", identity)
    assert values == {"db": "s3cret"}


def test_set_records_updated_timestamp(home, identity, recipient):
    store.set_secret(home, "nord", "db", "s3cret", identity, recipient)
    entry = store.read_entries(home, "nord", identity)["db"]
    assert entry["value"] == "s3cret"
    assert "updated" in entry


def test_namespace_file_is_0600(home, identity, recipient):
    store.set_secret(home, "nord", "db", "s3cret", identity, recipient)
    mode = store.secrets_path(home, "nord").stat().st_mode & 0o777
    assert mode == 0o600


def test_delete_secret(home, identity, recipient):
    store.set_secret(home, "nord", "db", "s3cret", identity, recipient)
    assert store.delete_secret(home, "nord", "db", identity, recipient) is True
    assert store.read_values(home, "nord", identity) == {}
    assert store.delete_secret(home, "nord", "db", identity, recipient) is False


def test_list_names_sorted(home, identity, recipient):
    store.set_secret(home, "nord", "z", "1", identity, recipient)
    store.set_secret(home, "nord", "a", "2", identity, recipient)
    assert store.list_names(home, "nord", identity) == ["a", "z"]
