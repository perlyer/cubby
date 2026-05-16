from cubby_tool import backend


def test_encrypt_decrypt_roundtrip(identity, recipient):
    plaintext = b'{"db": "s3cret"}'
    ciphertext = backend.encrypt(plaintext, recipient)
    assert ciphertext != plaintext
    assert backend.decrypt(ciphertext, identity) == plaintext
