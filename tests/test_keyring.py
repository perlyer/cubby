from cubby_tool import keyring


def test_generate_identity_returns_text_and_public_key():
    text, pub = keyring.generate_identity()
    assert "AGE-SECRET-KEY-1" in text
    assert pub.startswith("age1")


def test_public_key_parses_comment_line():
    text = "# created: now\n# public key: age1abc\nAGE-SECRET-KEY-1XYZ\n"
    assert keyring.public_key(text) == "age1abc"


def test_store_and_load_identity_file_mode(home):
    text, _ = keyring.generate_identity()
    keyring.store_identity(home, text, "file")
    assert keyring.identity_file(home).stat().st_mode & 0o777 == 0o600
    assert keyring.load_identity(home, "file") == text
