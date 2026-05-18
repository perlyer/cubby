import getpass

from cubby_tool import cli, config, store, audit


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


def test_doctor_fails_when_config_is_missing(home, monkeypatch, capsys):
    monkeypatch.setenv("CUBBY_HOME", str(home))
    assert cli.main(["doctor"]) == 2
    out = capsys.readouterr().out
    assert "no config" in out


def test_doctor_fails_when_identity_is_gone(inited_home, capsys):
    from cubby_tool import keyring
    # delete the file-mode age identity so it can no longer be loaded
    keyring.identity_file(inited_home).unlink()
    assert cli.main(["doctor"]) == 2
    out = capsys.readouterr().out
    assert "identity" in out


def test_doctor_flags_expired_secret(inited_home, identity, recipient, capsys):
    store.set_secret(inited_home, "test", "stale", "v", identity, recipient,
                     meta={"ttl": "1d", "expires": "2000-01-01T00:00:00+00:00"})
    rc = cli.main(["doctor"])
    out = capsys.readouterr().out
    assert "stale" in out and "expired" in out
    assert rc == 0  # an expired secret is a warning, not a failure


def test_doctor_notes_audit_off(inited_home, capsys):
    cli.main(["doctor"])
    assert "audit logging is off" in capsys.readouterr().out


def test_doctor_silent_when_audit_on(inited_home, capsys):
    cli.main(["audit", "--enable"])
    capsys.readouterr()
    cli.main(["doctor"])
    assert "audit logging is off" not in capsys.readouterr().out
