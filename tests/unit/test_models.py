"""Unit tests for the Secret model."""
from datetime import datetime, timedelta
import pytest
from onetimeshare.models import Secret

def test_secret_creation(app):
    """Test creating a new secret."""
    with app.app_context():
        secret = Secret(
            secret="test secret",
            expiration=datetime.utcnow() + timedelta(hours=1)
        )
        assert secret.secret == "test secret"
        assert secret.sid is not None
        assert len(secret.sid) > 16  # Ensure reasonable length for security
        assert not secret.is_expired

def test_secret_representation(app):
    """Test the string representation of a secret."""
    with app.app_context():
        secret = Secret(
            secret="test secret",
            expiration=datetime.utcnow() + timedelta(hours=1)
        )
        assert str(secret) == f'<Secret {secret.sid}>'

def test_secret_encryption(app):
    """Test that secrets are properly encrypted."""
    with app.app_context():
        original_secret = "sensitive data"
        secret = Secret(
            secret=original_secret,
            expiration=datetime.utcnow() + timedelta(hours=1)
        )
        # The secret should be encrypted in memory
        assert secret.secret == original_secret
        # The raw attribute should contain encrypted data
        assert hasattr(secret, '_secret')
        assert secret._secret != original_secret

def test_secret_unique_sid(app):
    """Test that each secret gets a unique SID."""
    with app.app_context():
        secret1 = Secret(
            secret="first secret",
            expiration=datetime.utcnow() + timedelta(hours=1)
        )
        secret2 = Secret(
            secret="second secret",
            expiration=datetime.utcnow() + timedelta(hours=1)
        )
        assert secret1.sid != secret2.sid

def test_secret_required_fields(app):
    """Test that secrets require both content and expiration."""
    with app.app_context():
        with pytest.raises(ValueError):
            Secret(secret="", expiration=datetime.utcnow() + timedelta(hours=1))
        
        with pytest.raises(ValueError):
            Secret(secret="test secret", expiration=None)

def test_secret_expiration(app):
    """Test secret expiration logic."""
    with app.app_context():
        # Create an expired secret
        expired = Secret(
            secret="expired",
            expiration=datetime.utcnow() - timedelta(minutes=1)
        )
        assert expired.is_expired

        # Create a future secret
        future = Secret(
            secret="future",
            expiration=datetime.utcnow() + timedelta(hours=1)
        )
        assert not future.is_expired

def test_secret_cleanup(app):
    """Test cleanup of expired secrets."""
    with app.app_context():
        # Create some expired and valid secrets
        Secret(
            secret="expired1",
            expiration=datetime.utcnow() - timedelta(hours=2)
        ).save()
        Secret(
            secret="expired2",
            expiration=datetime.utcnow() - timedelta(hours=1)
        ).save()
        Secret(
            secret="valid",
            expiration=datetime.utcnow() + timedelta(hours=1)
        ).save()

        # Run cleanup
        count = Secret.cleanup_expired()
        assert count == 2  # Should have removed 2 expired secrets
        
        # Check that only valid secrets remain
        remaining = Secret.query.all()
        assert len(remaining) == 1
        assert not remaining[0].is_expired 