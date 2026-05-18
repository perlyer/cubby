from cubby_tool import store


def test_read_entries_missing_namespace_returns_empty(home, identity):
    assert store.read_entries(home, "acme", identity) == {}


def test_set_get_roundtrip(home, identity, recipient):
    store.set_secret(home, "acme", "db", "s3cret", identity, recipient)
    values = store.read_values(home, "acme", identity)
    assert values == {"db": "s3cret"}


def test_set_records_updated_timestamp(home, identity, recipient):
    store.set_secret(home, "acme", "db", "s3cret", identity, recipient)
    entry = store.read_entries(home, "acme", identity)["db"]
    assert entry["value"] == "s3cret"
    assert "updated" in entry


def test_namespace_file_is_0600(home, identity, recipient):
    store.set_secret(home, "acme", "db", "s3cret", identity, recipient)
    mode = store.secrets_path(home, "acme").stat().st_mode & 0o777
    assert mode == 0o600


def test_delete_secret(home, identity, recipient):
    store.set_secret(home, "acme", "db", "s3cret", identity, recipient)
    assert store.delete_secret(home, "acme", "db", identity, recipient) is True
    assert store.read_values(home, "acme", identity) == {}
    assert store.delete_secret(home, "acme", "db", identity, recipient) is False


def test_list_names_sorted(home, identity, recipient):
    store.set_secret(home, "acme", "z", "1", identity, recipient)
    store.set_secret(home, "acme", "a", "2", identity, recipient)
    assert store.list_names(home, "acme", identity) == ["a", "z"]


def test_set_secret_writes_meta(home, identity, recipient):
    store.set_secret(home, "ns", "k", "v", identity, recipient,
                     meta={"ttl": "30d", "expires": "2099-01-01T00:00:00+00:00"})
    entry = store.read_entries(home, "ns", identity)["k"]
    assert entry["value"] == "v"
    assert entry["ttl"] == "30d"
    assert entry["expires"] == "2099-01-01T00:00:00+00:00"


def test_set_secret_without_meta_has_no_extra_fields(home, identity, recipient):
    store.set_secret(home, "ns", "k", "v", identity, recipient)
    entry = store.read_entries(home, "ns", identity)["k"]
    assert set(entry) == {"value", "updated"}


def test_rotate_secret_increments_counter(home, identity, recipient):
    store.set_secret(home, "ns", "k", "old", identity, recipient)
    assert store.rotate_secret(home, "ns", "k", "new", identity, recipient) == "ok"
    entry = store.read_entries(home, "ns", identity)["k"]
    assert entry["value"] == "new"
    assert entry["rotated"] == 1
    assert store.rotate_secret(home, "ns", "k", "newer", identity, recipient) == "ok"
    assert store.read_entries(home, "ns", identity)["k"]["rotated"] == 2


def test_rotate_secret_missing(home, identity, recipient):
    assert store.rotate_secret(home, "ns", "absent", "v", identity, recipient) == "missing"


def test_rotate_secret_applies_meta(home, identity, recipient):
    store.set_secret(home, "ns", "k", "old", identity, recipient)
    store.rotate_secret(home, "ns", "k", "new", identity, recipient,
                        meta={"ttl": "7d", "expires": "2099-01-01T00:00:00+00:00"})
    entry = store.read_entries(home, "ns", identity)["k"]
    assert entry["ttl"] == "7d"
    assert entry["expires"] == "2099-01-01T00:00:00+00:00"


def test_copy_secret_copies_entry(home, identity, recipient):
    store.set_secret(home, "src", "k", "v", identity, recipient,
                     meta={"ttl": "30d", "expires": "2099-01-01T00:00:00+00:00"})
    assert store.copy_secret(home, "src", "dst", "k", identity, recipient) == "ok"
    src = store.read_entries(home, "src", identity)
    dst = store.read_entries(home, "dst", identity)
    assert "k" in src                       # source untouched
    assert dst["k"]["value"] == "v"
    assert dst["k"]["ttl"] == "30d"          # metadata carried
    assert dst["k"]["expires"] == "2099-01-01T00:00:00+00:00"


def test_copy_secret_missing_source(home, identity, recipient):
    assert store.copy_secret(home, "src", "dst", "absent", identity,
                             recipient) == "missing"


def test_copy_secret_exists_in_destination(home, identity, recipient):
    store.set_secret(home, "src", "k", "v1", identity, recipient)
    store.set_secret(home, "dst", "k", "v2", identity, recipient)
    assert store.copy_secret(home, "src", "dst", "k", identity,
                             recipient) == "exists"
    assert store.read_entries(home, "dst", identity)["k"]["value"] == "v2"


def test_copy_secret_preserves_other_destination_secrets(home, identity, recipient):
    store.set_secret(home, "src", "k", "v", identity, recipient)
    store.set_secret(home, "dst", "existing", "keep-me", identity, recipient)
    assert store.copy_secret(home, "src", "dst", "k", identity, recipient) == "ok"
    dst = store.read_entries(home, "dst", identity)
    assert dst["k"]["value"] == "v"
    assert dst["existing"]["value"] == "keep-me"   # the prior secret survives
