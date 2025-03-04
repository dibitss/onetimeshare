"""Database models for OneTimeShare."""
import secrets
from datetime import datetime, timezone
from typing import Optional
import logging

from flask import current_app
from sqlalchemy import Unicode
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
from sqlalchemy.orm import validates

from . import db

logger = logging.getLogger(__name__)

class Secret(db.Model):
    """Model for storing secrets."""
    __tablename__ = 'secrets'
    
    id = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.String(32), unique=True, nullable=False)
    secret = db.Column(db.Text, nullable=False)
    expiration = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, secret, expiration):
        """Initialize a new secret."""
        self.sid = secrets.token_urlsafe(24)
        self.secret = secret  # This will trigger the setter
        self.expiration = expiration
        self.created_at = datetime.now(timezone.UTC)

    def __repr__(self):
        """Return string representation of the secret."""
        return f'<Secret {self.sid}>'

    @property
    def secret(self):
        """Get decrypted secret."""
        from cryptography.fernet import Fernet
        f = Fernet(current_app.config['ENCRYPTION_KEY'].encode())
        return f.decrypt(self.secret.encode()).decode()

    @secret.setter
    def secret(self, value):
        """Set and encrypt secret."""
        if not value:
            raise ValueError("Secret cannot be empty")
        from cryptography.fernet import Fernet
        f = Fernet(current_app.config['ENCRYPTION_KEY'].encode())
        self.secret = f.encrypt(value.encode()).decode()

    @property
    def expiration(self):
        """Get expiration datetime."""
        return self._expiration

    @expiration.setter
    def expiration(self, value):
        """Set expiration datetime with validation."""
        if value <= datetime.now(timezone.UTC):
            raise ValueError("Expiration must be in the future")
        self._expiration = value

    def is_expired(self):
        """Check if the secret has expired."""
        return datetime.now(timezone.UTC) >= self.expiration

    @classmethod
    def cleanup_expired(cls):
        """Remove all expired secrets."""
        expired = cls.query.filter(
            cls.expiration <= datetime.now(timezone.UTC)
        ).all()
        for secret in expired:
            db.session.delete(secret)
        db.session.commit()
        return len(expired)

    def save(self):
        """Save the secret to the database."""
        db.session.add(self)
        db.session.commit()
        return self

    @validates('secret')
    def validate_secret(self, key, value):
        """Validate the secret value."""
        if not value or not value.strip():
            raise ValueError("Secret cannot be empty")
        return value

    @validates('expiration')
    def validate_expiration(self, key, value):
        """Validate the expiration time."""
        if value <= datetime.now(timezone.UTC):
            raise ValueError("Expiration time must be in the future")
        return value 