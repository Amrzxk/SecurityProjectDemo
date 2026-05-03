import hashlib
import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-change-me'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Explicitly configure Flask-Limiter storage to avoid the in-memory warning.
    # For production, set the environment variable RATELIMIT_STORAGE_URI to e.g. 'redis://localhost:6379'
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI') or 'memory://'

    # AES field encryption key: 64 hex chars (32 bytes) or UTF-8 string with exactly 32 bytes.
    # Prefer setting FIELD_ENCRYPTION_KEY in env for production instead of derivation from SECRET_KEY.
    FIELD_ENCRYPTION_KEY = os.environ.get('FIELD_ENCRYPTION_KEY') or hashlib.sha256(
        ((os.environ.get('SECRET_KEY') or 'dev-secret-change-me') + ':field_encryption').encode('utf-8')
    ).hexdigest()


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    FIELD_ENCRYPTION_KEY = '0' * 64
