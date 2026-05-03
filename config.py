import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-change-me'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Explicitly configure Flask-Limiter storage to avoid the in-memory warning.
    # For production, set the environment variable RATELIMIT_STORAGE_URI to e.g. 'redis://localhost:6379'
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI') or 'memory://'


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
