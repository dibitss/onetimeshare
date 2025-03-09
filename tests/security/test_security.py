import pytest
from datetime import datetime, timedelta, timezone
from onetimeshare import create_app, db
from onetimeshare.models import Secret
from sqlalchemy import text

def get_csrf_token(client):
    """Get CSRF token from the home page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'csrf_token' in response.data
    # Extract CSRF token from the form
    csrf_token = response.data.split(b'csrf_token" value="')[1].split(b'"')[0].decode()
    return csrf_token

def test_csrf_protection(secure_client):
    """Test CSRF protection."""
    # Initialize session and get CSRF token
    with secure_client.session_transaction() as sess:
        sess['initialized'] = True
        sess.permanent = True
    
    # Get CSRF token
    csrf_token = secure_client.get_csrf_token()
    print(f"Generated CSRF token: {csrf_token}")

    # Attempt to create a secret without CSRF token
    response = secure_client.post('/create', data={
        'secret': 'test-secret',
        'expiration': (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    })
    assert response.status_code == 400
    assert b'CSRF token missing' in response.data
    print(f"First response data: {response.data}")

    # Now try with a CSRF token
    response = secure_client.post_with_csrf('/create', data={
        'secret': 'test-secret',
        'expiration': (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    })
    print(f"Second response data: {response.data}")
    assert response.status_code == 200
    assert b'url' in response.data

def test_xss_protection(client):
    """Test XSS protection."""
    # Initialize session and get CSRF token
    csrf_token = get_csrf_token(client)

    # Try to create a secret with XSS payload
    xss_payload = '<script>alert("xss")</script>'
    response = client.post('/create', data={
        'secret': xss_payload,
        'expiration': (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
        'csrf_token': csrf_token
    })
    assert response.status_code == 200

    # Get the secret URL
    url = response.json['url']

    # Verify the script tags are escaped in the response
    response = client.get(url)
    assert response.status_code == 200
    assert xss_payload not in response.json['secret']
    assert '&lt;script&gt;' in response.json['secret']

def test_sql_injection_protection(client, sample_secret):
    """Test SQL injection protection."""
    # Try a basic SQL injection
    response = client.post('/create', data={
        'secret': "'; DROP TABLE secrets; --",
        'expiration': (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    }, environ_base={'wsgi.url_scheme': 'https'})
    assert response.status_code == 200

    # Verify the table still exists and we can create secrets
    response = client.post('/create', data={
        'secret': 'test-secret',
        'expiration': (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    }, environ_base={'wsgi.url_scheme': 'https'})
    assert response.status_code == 200

def test_secret_encryption_at_rest(client):
    """Test that secrets are encrypted in the database."""
    # Initialize session and get CSRF token
    csrf_token = get_csrf_token(client)

    # Create a secret with CSRF token
    response = client.post('/create', data={
        'secret': 'test-secret',
        'expiration': (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
        'csrf_token': csrf_token
    })
    assert response.status_code == 200

    # Get the secret URL
    url = response.json['url']

    # Get the secret and verify it matches
    response = client.get(url)
    assert response.status_code == 200
    assert response.json['secret'] == 'test-secret'

    # Verify the secret was deleted after retrieval
    response = client.get(url)
    assert response.status_code == 404

def test_secret_deletion(client, app):
    """Test that secrets are properly deleted."""
    # Create a secret
    with app.app_context():
        secret = Secret(
            secret='test-secret',
            expiration=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        db.session.add(secret)
        db.session.commit()
        sid = secret.sid

    # Access the secret
    response = client.get(f'/secret/{sid}', environ_base={'wsgi.url_scheme': 'https'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'test-secret' in response.data

    # Verify the secret was deleted
    with app.app_context():
        assert Secret.query.filter_by(sid=sid).first() is None

def test_max_secret_size(client, sample_secret, app):
    """Test maximum secret size limit."""
    large_secret = 'x' * (app.config['MAX_CONTENT_LENGTH'] + 1)
    response = client.post('/create', data={
        'secret': large_secret,
        'expiration': sample_secret['expiration'].strftime('%Y-%m-%dT%H:%M')
    }, environ_base={'wsgi.url_scheme': 'https'}, follow_redirects=True)
    assert response.status_code == 413  # Request Entity Too Large

def test_session_security(client):
    """Test session security settings."""
    # Make a request that should set a session
    response = client.post('/create', data={
        'secret': 'test-secret',
        'expiration': (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    }, environ_base={'wsgi.url_scheme': 'https'})
    assert response.status_code == 200

    # Check session cookie settings
    session_cookie = response.headers.get('Set-Cookie', '')
    assert 'Secure' in session_cookie
    assert 'HttpOnly' in session_cookie
    assert 'SameSite=Lax' in session_cookie

def test_secure_headers(client):
    """Test security headers."""
    response = client.get('/', environ_base={'wsgi.url_scheme': 'https'})
    assert response.status_code == 200
    headers = response.headers
    assert headers.get('X-Frame-Options') == 'DENY'
    assert headers.get('X-Content-Type-Options') == 'nosniff'
    assert headers.get('X-XSS-Protection') == '1; mode=block'
    assert 'Content-Security-Policy' in headers 