import pytest

from cubby_tool import keyring


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
