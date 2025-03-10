"""Unit tests for CLI commands."""
import pytest
from flask import Flask
from onetimeshare import db
from datetime import datetime, timedelta, timezone
from onetimeshare.models import Secret
from sqlalchemy import text
from onetimeshare.cli import init_db, cleanup_db, generate_app_keys

def test_init_db(app):
    """Test database initialization command."""
    with app.app_context():
        # Run init command
        init_db()
        
        # Verify database was initialized
        inspector = db.inspect(db.engine)
        assert 'secrets' in inspector.get_table_names()

def test_cleanup_db(app):
    """Test database cleanup command."""
    with app.app_context():
        # Create a secret with future expiration
        future_secret = Secret(
            secret="expired secret",
            expiration=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        future_secret.save()

        # Update the secret to be expired in the database using raw SQL
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        db.session.execute(
            text("UPDATE secrets SET expiration = :expiration WHERE id = :id"),
            {"expiration": expired_time, "id": future_secret.id}
        )
        db.session.commit()

        # Create a valid secret
        valid_secret = Secret(
            secret="valid secret",
            expiration=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        valid_secret.save()

        # Run cleanup command
        cleanup_db()
        
        # Verify expired secret was cleaned up
        expired_secret = db.session.get(Secret, future_secret.id)
        assert expired_secret is None
        
        # Verify valid secret still exists
        valid_secret = db.session.get(Secret, valid_secret.id)
        assert valid_secret is not None

def test_cleanup_db_no_expired(app):
    """Test cleanup command when no expired secrets exist."""
    with app.app_context():
        # Create only valid secrets
        valid_secret = Secret(
            secret="valid secret",
            expiration=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        valid_secret.save()

        # Run cleanup command
        cleanup_db()
        
        # Verify valid secret still exists
        valid_secret = db.session.get(Secret, valid_secret.id)
        assert valid_secret is not None

def test_generate_keys(app):
    """Test key generation command."""
    with app.app_context():
        # Run generate-keys command
        generate_app_keys()
        
        # Verify keys were generated
        assert app.config['SECRET_KEY'] is not None
        assert app.config['ENCRYPTION_KEY'] is not None 