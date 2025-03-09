"""Configuration for OneTimeShare."""
import os
from datetime import timedelta

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32).hex())
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', None)  # Will be generated if None
    MAX_CONTENT_LENGTH = 16 * 1024  # 16KB
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SEND_FILE_MAX_AGE_DEFAULT = 0

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///data/onetimeshare.db'
    )

class DockerConfig(Config):
    """Docker configuration."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SQLALCHEMY_DATABASE_URI',
        'postgresql://onetimeshare:secret@db:5432/onetimeshare'
    )

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'docker': DockerConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}