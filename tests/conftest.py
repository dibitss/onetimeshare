"""Test configuration and fixtures."""
import os
import tempfile
import pytest
from datetime import datetime, timedelta, timezone
from cryptography.fernet import Fernet
from sqlalchemy import text
from flask.testing import FlaskClient
from flask_wtf.csrf import generate_csrf
import flask
from flask import Flask, current_app, session
from werkzeug.http import parse_cookie
from http.cookiejar import CookieJar
import re
from bs4 import BeautifulSoup

from onetimeshare import create_app, db
from onetimeshare.models import Secret

class RequestShim:
    """Request shim that provides cookie support for the test client."""
    def __init__(self, client):
        self.client = client
        self.environ_base = {}
        self._cookies = None

    @property
    def cookies(self):
        if self._cookies is None:
            cookies = {}
            for cookie in self.client.cookie_jar:
                cookies[cookie.name] = cookie.value
            self._cookies = cookies
        return self._cookies

class CustomTestClient(FlaskClient):
    """Custom test client that handles CSRF tokens."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._csrf_token = None

    def get_csrf_token(self):
        """Get a CSRF token."""
        if not self._csrf_token:
            with self.session_transaction() as sess:
                sess['initialized'] = True
                sess.permanent = True
                self._csrf_token = generate_csrf()
                sess['csrf_token'] = self._csrf_token
        return self._csrf_token

    def post_with_csrf(self, *args, **kwargs):
        """Make a POST request with CSRF token."""
        if 'data' not in kwargs:
            kwargs['data'] = {}
        if not isinstance(kwargs['data'], dict):
            raise ValueError("Data must be a dictionary")
        
        # Get a fresh CSRF token
        token = self.get_csrf_token()
        
        # Add CSRF token to form data
        kwargs['data']['csrf_token'] = token
        
        # Add CSRF token to headers
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['X-CSRFToken'] = token
        
        # Ensure we're using the same session
        with self.session_transaction() as sess:
            sess['initialized'] = True
            sess.permanent = True
            sess['csrf_token'] = token
        
        # Make the request with the CSRF token
        return self.post(*args, **kwargs)

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test_secret_key',
        'WTF_CSRF_ENABLED': True,  # Enable CSRF for testing
        'MAX_CONTENT_LENGTH': 16 * 1024,  # 16KB max-limit
        'RATELIMIT_ENABLED': False,  # Disable rate limiting for testing
        'SERVER_NAME': 'localhost',  # Required for url generation
        'SESSION_COOKIE_SECURE': True,  # Enable secure cookies
        'SESSION_COOKIE_HTTPONLY': True,  # Enable HttpOnly
        'SESSION_COOKIE_SAMESITE': 'Lax',  # Set SameSite policy
        'PREFERRED_URL_SCHEME': 'https'  # Force HTTPS
    }
    app = create_app(test_config)
    app.test_client_class = CustomTestClient
    
    # Create the database and load test data
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def secure_app():
    """Create and configure a test app with security features enabled."""
    from onetimeshare import create_app
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test_secret_key',
        'WTF_CSRF_ENABLED': True,  # Enable CSRF for security tests
        'MAX_CONTENT_LENGTH': 16 * 1024,
        'RATELIMIT_ENABLED': False,
        'SERVER_NAME': 'localhost',
        'SESSION_COOKIE_SECURE': True,
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'PREFERRED_URL_SCHEME': 'https'
    }
    app = create_app(test_config)
    app.test_client_class = CustomTestClient
    return app

@pytest.fixture
def secure_client(app):
    """Create a test client with CSRF protection enabled."""
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    app.config['WTF_CSRF_SSL_STRICT'] = True
    app.test_client_class = CustomTestClient
    client = app.test_client()
    client.preserve_context = True  # Preserve the context for CSRF
    return client