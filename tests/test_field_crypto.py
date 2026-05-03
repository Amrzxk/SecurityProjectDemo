import pytest

from app.field_crypto import decrypt_field, encrypt_field, normalize_encryption_key


@pytest.fixture
def sample_key_bytes():
    return bytes.fromhex('11' * 32)


def test_encrypt_decrypt_round_trip(sample_key_bytes):
    ct = encrypt_field('hello world', key=sample_key_bytes)
    assert ct
    assert decrypt_field(ct, key=sample_key_bytes) == 'hello world'


def test_empty_plaintext_returns_empty_string(sample_key_bytes):
    assert encrypt_field('', key=sample_key_bytes) == ''
    assert encrypt_field(None, key=sample_key_bytes) == ''
    assert decrypt_field('', key=sample_key_bytes) == ''


def test_wrong_key_rejects_decrypt(sample_key_bytes):
    other = bytes.fromhex('aa' * 32)
    blob = encrypt_field('classified', key=sample_key_bytes)
    with pytest.raises(Exception):
        decrypt_field(blob, key=other)


def test_normalize_encryption_key_accepts_hex_64_chars():
    h = '0f' * 32
    k = normalize_encryption_key(h)
    assert len(k) == 32
    assert k == bytes.fromhex(h)


def test_normalize_encryption_key_accepts_ascii_32_byte_string():
    s = 'x' * 32
    k = normalize_encryption_key(s)
    assert k == b'x' * 32


def test_invalid_ciphertext_raises():
    k = bytes.fromhex('22' * 32)
    with pytest.raises(Exception):
        decrypt_field('zzz', key=k)


def test_unique_iv_per_encryption(sample_key_bytes):
    a = encrypt_field('same', key=sample_key_bytes)
    b = encrypt_field('same', key=sample_key_bytes)
    assert a != b
