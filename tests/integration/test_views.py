"""Integration tests for views."""
from datetime import datetime, timedelta
from onetimeshare import create_app, db
from onetimeshare.models import Secret

def test_home_page(client):
    """Test the home page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Create New Secret' in response.data

def test_create_secret(client):
    """Test creating a new secret."""
    expiration = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    response = client.post('/', data={
        'secret': 'test secret',
        'expiration': expiration
    })
    assert response.status_code == 200
    assert b'Secret created successfully!' in response.data
    assert b'Click the link below to copy it' in response.data

def test_retrieve_secret(client, sample_secret):
    """Test retrieving a secret."""
    # First retrieval should succeed
    response = client.get(f'/{sample_secret.sid}')
    assert response.status_code == 200
    assert b'test secret' in response.data
    assert b'This secret has been deleted' in response.data

    # Second retrieval should fail
    response = client.get(f'/{sample_secret.sid}')
    assert response.status_code == 404
    assert b'Secret not found or already viewed' in response.data

def test_retrieve_expired_secret(client, expired_secret):
    """Test retrieving an expired secret."""
    response = client.get(f'/{expired_secret.sid}')
    assert response.status_code == 404
    assert b'This secret has expired' in response.data

def test_invalid_secret_id(client):
    """Test retrieving a non-existent secret."""
    response = client.get('/invalid-sid')
    assert response.status_code == 404
    assert b'Secret not found or already viewed' in response.data

def test_create_secret_validation(client):
    """Test secret creation validation."""
    # Test empty secret
    response = client.post('/', data={
        'secret': '',
        'expiration': (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    })
    assert response.status_code == 400
    assert b'Secret cannot be empty' in response.data

    # Test invalid expiration
    response = client.post('/', data={
        'secret': 'test secret',
        'expiration': datetime.utcnow().strftime('%Y-%m-%dT%H:%M')  # Current time (invalid)
    })
    assert response.status_code == 400
    assert b'Expiration time must be in the future' in response.data

def test_secret_masking(client):
    """Test that secrets are properly masked when viewed."""
    expiration = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    # Create a secret
    response = client.post('/', data={
        'secret': 'sensitive data',
        'expiration': expiration
    })
    assert response.status_code == 200
    
    # Get the secret URL from the response
    secret_url = response.data.decode().split('secret_url=')[1].split('"')[0]
    sid = secret_url.split('/')[-1]
    
    # Retrieve the secret
    response = client.get(f'/{sid}')
    assert response.status_code == 200
    assert b'class="secret-text"' in response.data  # Should be in a masked container
    assert b'Show Secret' in response.data  # Should have show/hide button
    assert b'Copy to Clipboard' in response.data  # Should have copy button

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy' 