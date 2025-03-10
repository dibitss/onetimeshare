"""Unit tests for models."""
import pytest
from datetime import datetime, timedelta, timezone
from onetimeshare.models import Secret
import time

def test_secret_creation(app):
    """Test secret creation with valid data."""
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    secret = Secret(secret="test secret", expiration=expiration)
    assert secret.secret == "test secret"
    assert secret.expiration == expiration
    assert secret.sid is not None
    assert len(secret.sid) > 0

def test_secret_empty_secret(app):
    """Test secret creation with empty secret."""
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    with pytest.raises(ValueError):
        Secret(secret="", expiration=expiration)

def test_secret_past_expiration(app):
    """Test secret creation with past expiration."""
    expiration = datetime.now(timezone.utc) - timedelta(hours=1)
    with pytest.raises(ValueError):
        Secret(secret="test secret", expiration=expiration)

def test_secret_is_expired(app):
    """Test secret expiration check."""
    # Create a secret with a very short expiration time (1 second)
    expiration = datetime.now(timezone.utc) + timedelta(seconds=1)
    secret = Secret(secret="test secret", expiration=expiration)
    
    # Wait for the secret to expire
    time.sleep(2)
    
    # Check if the secret is expired
    assert secret.is_expired()

def test_secret_not_expired(app):
    """Test secret not expired check."""
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    secret = Secret(secret="test secret", expiration=expiration)
    assert not secret.is_expired() 