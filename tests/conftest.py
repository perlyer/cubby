import pytest

from cubby_tool import config, keyring


@pytest.fixture
def home(tmp_path):
    return tmp_path / "cubby"


@pytest.fixture
def identity():
    text, _pub = keyring.generate_identity()
    return text


@pytest.fixture
def recipient(identity):
    return keyring.public_key(identity)


@pytest.fixture
def inited_home(home, identity, monkeypatch):
    keyring.store_identity(home, identity, "file")
    cfg = config.Config(
        default_namespace="test",
        key_mode="file",
        namespaces={"test": config.Namespace()},
    )
    config.save_config(home, cfg)
    monkeypatch.setenv("CUBBY_HOME", str(home))
    return home
