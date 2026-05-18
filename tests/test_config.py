import pytest

from cubby_tool import config


def test_load_missing_config_returns_defaults(tmp_path):
    cfg = config.load_config(tmp_path)
    assert cfg.default_namespace == ""
    assert cfg.key_mode == "file"
    assert cfg.namespaces == {}


def test_save_then_load_roundtrip(tmp_path):
    cfg = config.Config(
        default_namespace="acme",
        key_mode="keychain",
        namespaces={"acme": config.Namespace(cwd_prefix="/p/acme", env_map={"db": "PGPASSWORD"})},
    )
    config.save_config(tmp_path, cfg)
    loaded = config.load_config(tmp_path)
    assert loaded.default_namespace == "acme"
    assert loaded.key_mode == "keychain"
    assert loaded.namespaces["acme"].cwd_prefix == "/p/acme"
    assert loaded.namespaces["acme"].env_map == {"db": "PGPASSWORD"}


def test_get_home_honors_env(tmp_path, monkeypatch):
    monkeypatch.setenv("CUBBY_HOME", str(tmp_path))
    assert config.get_home() == tmp_path


def _cfg():
    return config.Config(
        default_namespace="acme",
        namespaces={
            "acme": config.Namespace(cwd_prefix="/p/acme"),
            "deep": config.Namespace(cwd_prefix="/p/acme/sub"),
        },
    )


def test_resolve_prefers_flag():
    assert config.resolve_namespace(_cfg(), flag="x", env="y", cwd="/p/acme") == ("x", "flag")


def test_resolve_uses_env_when_no_flag():
    assert config.resolve_namespace(_cfg(), flag=None, env="y", cwd="/p/acme") == ("y", "env")


def test_resolve_uses_longest_cwd_prefix():
    assert config.resolve_namespace(_cfg(), cwd="/p/acme/sub/x") == ("deep", "cwd")


def test_resolve_falls_back_to_default():
    assert config.resolve_namespace(_cfg(), cwd="/elsewhere") == ("acme", "default")


def test_resolve_does_not_match_sibling_prefix():
    assert config.resolve_namespace(_cfg(), cwd="/p/acme-corp/project") == ("acme", "default")


def test_resolve_raises_when_nothing_matches():
    empty = config.Config()
    with pytest.raises(LookupError):
        config.resolve_namespace(empty, cwd="/elsewhere")


def test_config_audit_round_trips(tmp_path):
    cfg = config.Config(default_namespace="x", audit=True)
    config.save_config(tmp_path, cfg)
    loaded = config.load_config(tmp_path)
    assert loaded.audit is True


def test_config_audit_defaults_false(tmp_path):
    cfg = config.Config(default_namespace="x")
    config.save_config(tmp_path, cfg)
    assert config.load_config(tmp_path).audit is False
