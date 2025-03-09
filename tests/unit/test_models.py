"""Unit tests for the Secret model."""
from datetime import datetime, timedelta, timezone
import pytest
from onetimeshare.models import Secret

def test_secret_creation(app):
    """Test creating a new secret."""
    with app.app_context():
        secret = Secret(
            secret="test secret",
            expiration=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        assert len(secret.sid) > 16
        assert secret.secret == "test secret"
        assert not secret.is_expired()

def test_secret_representation(app):
    """Test string representation of secrets."""
    with app.app_context():
        secret = Secret(
            secret="test secret",
            expiration=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        assert str(secret) == f'<Secret {secret.sid}>'

def test_secret_encryption(app):
    """Test that secrets are properly encrypted."""
    with app.app_context():
        original_secret = "test secret"
        secret = Secret(
            secret=original_secret,
            expiration=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        # The stored secret should be encrypted
        assert secret._secret != original_secret
        # But the property should decrypt it
        assert secret.secret == original_secret

def test_secret_unique_sid(app):
    """Test that each secret gets a unique SID."""
    with app.app_context():
        secret1 = Secret(
            secret="first secret",
            expiration=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        secret2 = Secret(
            secret="second secret",
            expiration=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        assert secret1.sid != secret2.sid

def test_secret_required_fields(app):
    """Test that secrets require both content and expiration."""
    with app.app_context():
        with pytest.raises(ValueError, match="Secret cannot be empty"):
            Secret(secret="", expiration=datetime.now(timezone.utc) + timedelta(hours=1))
        
        with pytest.raises(ValueError, match="Expiration time is required"):
            Secret(secret="test secret", expiration=None)

def test_secret_expiration(app):
    """Test secret expiration logic."""
    with app.app_context():
        # Test that we can't create an expired secret
        with pytest.raises(ValueError, match="Expiration time must be in the future"):
            Secret(
                secret="expired",
                expiration=datetime.now(timezone.utc) - timedelta(minutes=1)
            )
        
        # Create a valid secret
        secret = Secret(
            secret="valid",
            expiration=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        assert not secret.is_expired()

def test_secret_cleanup(app):
    """Test cleanup of expired secrets."""
    with app.app_context():
        # Create some expired and valid secrets
        with pytest.raises(ValueError, match="Expiration time must be in the future"):
            Secret(
                secret="expired1",
                expiration=datetime.now(timezone.utc) - timedelta(hours=2)
            ).save()
        
        # Create a valid secret
        valid = Secret(
            secret="valid",
            expiration=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        valid.save()
        
        # Run cleanup
        removed = Secret.cleanup_expired()
        assert removed == 0  # No expired secrets should be found
        
        # Verify the valid secret still exists
        assert Secret.query.count() == 1 