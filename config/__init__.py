"""Configuration module for OneTimeShare."""
import os
from datetime import timedelta

class BaseConfig:
    """Base configuration."""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    MAX_CONTENT_LENGTH = 10 * 1024  # 10KB

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'dev-key-please-change-in-production')
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SSL_STRICT = True
    WTF_CSRF_TIME_LIMIT = 3600
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)

    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = ["200 per day", "50 per hour"]
    RATELIMIT_HEADERS_ENABLED = True

class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///data/onetimeshare.db'
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development

class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'
    SESSION_COOKIE_SECURE = True

class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://user:pass@localhost/onetimeshare')
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 