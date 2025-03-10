"""Integration tests for routes."""
import pytest
from datetime import datetime, timedelta, timezone
from onetimeshare.models import Secret

def test_home_page(client):
    """Test home page route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'OneTimeShare' in response.data

def test_create_secret(client):
    """Test secret creation route."""
    # Get the CSRF token from the home page
    response = client.get('/')
    assert response.status_code == 200
    csrf_token = response.data.decode('utf-8').split('name="csrf_token" value="')[1].split('"')[0]
    
    expiration = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    response = client.post('/create', data={
        'secret': 'test secret',
        'expiration': expiration,
        'csrf_token': csrf_token
    })
    assert response.status_code == 200
    assert b'url' in response.data

def test_create_secret_empty(client):
    """Test secret creation with empty secret."""
    expiration = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    response = client.post('/create', data={
        'secret': '',
        'expiration': expiration
    })
    assert response.status_code == 302  # Redirect to home with error

def test_get_secret(client, sample_secret):
    """Test retrieving a secret."""
    response = client.get(f'/secret/{sample_secret.sid}')
    assert response.status_code == 200
    assert b'test secret' in response.data

def test_get_nonexistent_secret(client):
    """Test retrieving a non-existent secret."""
    response = client.get('/secret/nonexistent')
    assert response.status_code == 302  # Redirect to home with error

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert b'healthy' in response.data 