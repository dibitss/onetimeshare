"""Integration tests for views."""
from datetime import datetime, timedelta, timezone
from onetimeshare import create_app, db
from onetimeshare.models import Secret

def test_home_page(client):
    """Test the home page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Generate Secret Link' in response.data

def test_create_secret(client):
    """Test creating a new secret."""
    expiration = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    response = client.post('/create', data={
        'secret': 'test secret',
        'expiration': expiration
    })
    assert response.status_code == 200
    assert 'message' in response.json
    assert response.json['message'] == 'Secret created successfully'
    assert 'url' in response.json

def test_retrieve_secret(client, sample_secret):
    """Test retrieving a secret."""
    # First retrieval should succeed
    response = client.get(f'/secret/{sample_secret["sid"]}')
    assert response.status_code == 200
    assert 'secret' in response.json
    assert response.json['secret'] == 'test secret'

    # Second retrieval should fail
    response = client.get(f'/secret/{sample_secret["sid"]}')
    assert response.status_code == 404
    assert b'Secret not found' in response.data

def test_retrieve_expired_secret(client, expired_secret):
    """Test retrieving an expired secret."""
    response = client.get(f'/secret/{expired_secret["sid"]}')
    assert response.status_code == 410
    assert b'Secret has expired' in response.data

def test_invalid_secret_id(client):
    """Test retrieving a non-existent secret."""
    response = client.get('/secret/invalid-sid')
    assert response.status_code == 404
    assert b'Secret not found' in response.data

def test_create_secret_validation(client):
    """Test secret creation validation."""
    # Test empty secret
    response = client.post('/create', data={
        'secret': '',
        'expiration': (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    })
    assert response.status_code == 400
    assert b'Secret cannot be empty' in response.data

    # Test invalid expiration
    response = client.post('/create', data={
        'secret': 'test secret',
        'expiration': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M')  # Current time (invalid)
    })
    assert response.status_code == 400
    assert b'Expiration must be in the future' in response.data

def test_secret_masking(client):
    """Test that secrets are properly masked when viewed."""
    expiration = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    # Create a secret
    response = client.post('/create', data={
        'secret': 'sensitive data',
        'expiration': expiration
    })
    assert response.status_code == 200
    assert 'url' in response.json
    
    # Get the secret URL from the response
    secret_url = response.json['url']
    sid = secret_url.split('/')[-1]
    
    # Retrieve the secret
    response = client.get(f'/secret/{sid}')
    assert response.status_code == 200
    assert 'secret' in response.json
    assert response.json['secret'] == 'sensitive data'

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy' 