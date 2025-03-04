"""Test configuration and fixtures."""
import os
import tempfile
import pytest
from datetime import datetime, timedelta, timezone
from cryptography.fernet import Fernet

from onetimeshare import create_app, db
from onetimeshare.models import Secret

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Generate a test encryption key
    test_key = Fernet.generate_key()
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SECRET_KEY': 'test_secret_key',
        'ENCRYPTION_KEY': test_key.decode(),
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'MAX_CONTENT_LENGTH': 16 * 1024,  # 16KB max-limit
        'RATELIMIT_ENABLED': False,  # Disable rate limiting for testing
        'SERVER_NAME': 'localhost',  # Required for url generation
        'SESSION_COOKIE_SECURE': True,  # Enable secure cookies
        'SESSION_COOKIE_HTTPONLY': True,  # Enable HttpOnly
        'SESSION_COOKIE_SAMESITE': 'Lax',  # Set SameSite policy
        'PREFERRED_URL_SCHEME': 'https'  # Force HTTPS
    })

    # Create the database and the tables
    with app.app_context():
        db.create_all()

    yield app

    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()

@pytest.fixture
def sample_secret(app):
    """Create a sample secret for testing."""
    with app.app_context():
        secret = Secret(
            secret="test secret",
            expiration=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        secret.save()
        return secret

@pytest.fixture
def expired_secret(app):
    """Create an expired secret for testing."""
    with app.app_context():
        secret = Secret(
            secret="expired secret",
            expiration=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        secret.save()
        return secret