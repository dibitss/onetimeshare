"""Test configuration and fixtures."""
import os
import pytest
from datetime import datetime, timedelta, timezone
from flask import Flask
from onetimeshare import create_app, db
from onetimeshare.models import Secret
from cryptography.fernet import Fernet

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Generate a proper Fernet key for testing
    test_key = Fernet.generate_key()
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'ENCRYPTION_KEY': test_key.decode()
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

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
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    secret = Secret(secret="test secret", expiration=expiration)
    secret.save()
    return secret 