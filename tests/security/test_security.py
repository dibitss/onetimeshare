"""Security tests for OneTimeShare."""
from datetime import datetime, timedelta
import pytest
from onetimeshare import create_app, db
from onetimeshare.models import Secret

def test_csrf_protection(client):
    """Test CSRF protection."""
    # Enable CSRF for this test
    client.application.config['WTF_CSRF_ENABLED'] = True
    
    # Attempt to create a secret without CSRF token
    response = client.post('/', data={
        'secret': 'test secret',
        'expiration': (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    })
    assert response.status_code == 400
    assert b'CSRF token is missing' in response.data

def test_xss_protection(client, sample_secret):
    """Test XSS protection."""
    # Try to create a secret with malicious content
    xss_payload = '<script>alert("xss")</script>'
    response = client.post('/', data={
        'secret': xss_payload,
        'expiration': (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    })
    assert response.status_code == 200
    
    # Verify the content is escaped in the response
    assert b'<script>' not in response.data
    assert b'&lt;script&gt;' in response.data

def test_sql_injection_protection(client):
    """Test SQL injection protection."""
    # Try SQL injection in the secret ID
    response = client.get("/'; DROP TABLE secrets; --")
    assert response.status_code == 404
    
    # Verify the secrets table still exists
    with client.application.app_context():
        result = db.session.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='secrets'")
        assert result.fetchone() is not None

def test_secure_headers(client):
    """Test security headers are set correctly."""
    response = client.get('/')
    headers = response.headers
    
    # Check security headers
    assert headers.get('X-Content-Type-Options') == 'nosniff'
    assert headers.get('X-Frame-Options') == 'DENY'
    assert headers.get('X-XSS-Protection') == '1; mode=block'
    assert 'Content-Security-Policy' in headers

def test_secret_encryption_at_rest(client):
    """Test that secrets are encrypted in the database."""
    test_secret = "sensitive data 123"
    expiration = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    
    # Create a secret
    response = client.post('/', data={
        'secret': test_secret,
        'expiration': expiration
    })
    assert response.status_code == 200
    
    # Get the secret from the database
    with client.application.app_context():
        secret = Secret.query.first()
        # Check that the raw database value is not the plain text
        assert secret._secret != test_secret
        # But the decrypted value matches
        assert secret.secret == test_secret

def test_secret_deletion(client):
    """Test that secrets are properly deleted."""
    # Create a secret
    expiration = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    response = client.post('/', data={
        'secret': 'delete me',
        'expiration': expiration
    })
    assert response.status_code == 200
    
    # Get the secret URL and ID
    secret_url = response.data.decode().split('secret_url=')[1].split('"')[0]
    sid = secret_url.split('/')[-1]
    
    # Verify secret exists
    with client.application.app_context():
        assert Secret.query.filter_by(sid=sid).first() is not None
    
    # Retrieve the secret
    response = client.get(f'/{sid}')
    assert response.status_code == 200
    
    # Verify secret is deleted
    with client.application.app_context():
        assert Secret.query.filter_by(sid=sid).first() is None

def test_max_secret_size(client):
    """Test maximum secret size limit."""
    large_secret = 'x' * (16 * 1024 + 1)  # Exceed 16KB limit
    response = client.post('/', data={
        'secret': large_secret,
        'expiration': (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    })
    assert response.status_code == 413
    assert b'Secret is too large' in response.data

def test_session_security(client):
    """Test session security settings."""
    response = client.get('/')
    assert response.status_code == 200
    
    # Check session cookie settings
    cookie = next((c for c in client.cookie_jar if c.name == 'session'), None)
    assert cookie is not None
    assert cookie.secure  # Ensure secure flag is set
    assert cookie.has_nonstandard_attr('HttpOnly')  # Ensure HttpOnly flag is set 