"""AES-CBC + PKCS7 for optional plaintext fields stored in SQLite (IV prepended per value)."""

from __future__ import annotations

import base64
import os
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


_BLOCK = algorithms.AES.block_size // 8  # 16 bytes


def normalize_encryption_key(config_value: str | None) -> bytes:
    if not config_value:
        raise ValueError('Encryption key missing from configuration')
    s = str(config_value).strip()
    if len(s) == 64:
        try:
            k = bytes.fromhex(s)
        except ValueError as e:
            raise ValueError('FIELD_ENCRYPTION_KEY must be valid 64-character hex') from e
        if len(k) != 32:
            raise ValueError('FIELD_ENCRYPTION_KEY hex must represent 32 bytes')
        return k
    kb = s.encode('utf-8')
    if len(kb) == 32:
        return kb
    raise ValueError('FIELD_ENCRYPTION_KEY must be 64 hex chars or a 32-byte UTF-8 string')


def encrypt_field(plaintext: str, *, key: bytes) -> str:
    if plaintext is None or plaintext == '':
        return ''
    raw = plaintext.encode('utf-8')
    iv = os.urandom(_BLOCK)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    padder = sym_padding.PKCS7(algorithms.AES.block_size).padder()
    padded = padder.update(raw) + padder.finalize()
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return base64.urlsafe_b64encode(iv + ciphertext).decode('ascii')


def decrypt_field(stored_b64: str | None, *, key: bytes) -> str:
    if not stored_b64:
        return ''
    blob = base64.urlsafe_b64decode(stored_b64.encode('ascii'))
    if len(blob) <= _BLOCK or len(blob) % _BLOCK:
        raise ValueError('Invalid ciphertext length')
    iv, ciphertext = blob[:_BLOCK], blob[_BLOCK:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = sym_padding.PKCS7(algorithms.AES.block_size).unpadder()
    raw = unpadder.update(padded) + unpadder.finalize()
    return raw.decode('utf-8')
