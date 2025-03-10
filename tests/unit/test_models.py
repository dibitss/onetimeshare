"""Unit tests for models."""
import pytest
from datetime import datetime, timedelta, timezone
from onetimeshare.models import Secret
import time
from sqlalchemy import text

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

def test_secret_save_and_load(app):
    """Test saving and loading a secret from the database."""
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    original_secret = Secret(secret="test secret", expiration=expiration)
    original_secret.save()
    
    # Load the secret from the database
    loaded_secret = Secret.get_by_sid(original_secret.sid)
    assert loaded_secret is not None
    assert loaded_secret.secret == original_secret.secret
    assert loaded_secret.expiration == original_secret.expiration
    assert loaded_secret.sid == original_secret.sid

def test_secret_get_nonexistent(app):
    """Test getting a non-existent secret."""
    secret = Secret.get_by_sid("nonexistent")
    assert secret is None

def test_secret_encryption(app):
    """Test that secrets are properly encrypted in the database."""
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    secret = Secret(secret="test secret", expiration=expiration)
    secret.save()

    # Get the raw secret from the database
    from onetimeshare import db
    result = db.session.execute(text("SELECT secret FROM secrets WHERE sid = :sid"), {"sid": secret.sid}).first()
    encrypted_secret = result[0]

    # Verify the secret is encrypted
    assert encrypted_secret != "test secret"
    assert encrypted_secret.startswith("gAAAAAB")  # Fernet encrypted strings start with this prefix

def test_secret_validation(app):
    """Test various validation scenarios."""
    # Test None expiration
    with pytest.raises(ValueError):
        Secret(secret="test secret", expiration=None)
    
    # Test None secret
    with pytest.raises(ValueError):
        Secret(secret=None, expiration=datetime.now(timezone.utc) + timedelta(hours=1))
    
    # Test whitespace-only secret
    with pytest.raises(ValueError):
        Secret(secret="   ", expiration=datetime.now(timezone.utc) + timedelta(hours=1))

def test_secret_properties(app):
    """Test secret properties and their behavior."""
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    secret = Secret(secret="test secret", expiration=expiration)
    
    # Test property getters
    assert secret.secret == "test secret"
    assert secret.expiration == expiration
    
    # Test property setters
    new_expiration = datetime.now(timezone.utc) + timedelta(hours=2)
    secret.expiration = new_expiration
    assert secret.expiration == new_expiration
    
    # Test invalid expiration setting
    with pytest.raises(ValueError):
        secret.expiration = datetime.now(timezone.utc) - timedelta(hours=1) 