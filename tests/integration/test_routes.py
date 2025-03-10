"""Integration tests for routes."""
import pytest
from datetime import datetime, timedelta, timezone
from flask import session
from onetimeshare.models import Secret
from onetimeshare.routes import db
from sqlalchemy import text
from unittest.mock import patch

def test_home_page(client):
    """Test home page renders correctly."""
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
    """Test creating a secret with empty content."""
    response = client.post('/create', data={
        'secret': '',
        'expiration': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    })
    assert response.status_code == 302
    assert b'Redirecting' in response.data

def test_get_secret(client, sample_secret):
    """Test retrieving a secret."""
    response = client.get(f'/secret/{sample_secret.sid}')
    assert response.status_code == 200
    assert b'test secret' in response.data

def test_get_nonexistent_secret(client):
    """Test retrieving a non-existent secret."""
    response = client.get('/secret/nonexistent')
    assert response.status_code == 302
    assert b'Redirecting' in response.data

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'

def test_create_secret_invalid_csrf(client):
    """Test creating a secret with invalid CSRF token."""
    response = client.post('/create', data={
        'secret': 'test secret',
        'expiration': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    }, headers={'X-CSRFToken': 'invalid'})
    assert response.status_code == 302
    assert b'Redirecting' in response.data

def test_create_secret_invalid_expiration(client):
    """Test creating a secret with past expiration time."""
    response = client.post('/create', data={
        'secret': 'test secret',
        'expiration': (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    })
    assert response.status_code == 302
    assert b'Redirecting' in response.data

def test_get_secret_expired(client, app):
    """Test retrieving an expired secret."""
    with app.app_context():
        # Create a valid secret first
        secret = Secret(
            secret="expired secret",
            expiration=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        secret.save()
        
        # Update the secret to be expired in the database
        db.session.execute(
            text("UPDATE secrets SET expiration = :expiration WHERE id = :id"),
            {
                "expiration": datetime.now(timezone.utc) - timedelta(hours=1),
                "id": secret.id
            }
        )
        db.session.commit()
        
        response = client.get(f'/secret/{secret.sid}')
        assert response.status_code == 302
        assert b'Redirecting' in response.data

def test_get_secret_database_error(client, app):
    """Test handling of database errors when retrieving a secret."""
    with app.app_context():
        # Create a proper mock that mimics SQLAlchemy's query interface
        class MockQuery:
            def filter_by(self, *args, **kwargs):
                raise Exception("Database error")
            def first(self):
                raise Exception("Database error")
        
        with pytest.MonkeyPatch.context() as m:
            m.setattr(Secret, 'query', MockQuery())
            response = client.get('/secret/test')
            assert response.status_code == 302
            assert b'Redirecting' in response.data

def test_create_secret_missing_expiration(client):
    """Test creating a secret without expiration time."""
    response = client.post('/create', data={
        'secret': 'test secret'
    })
    assert response.status_code == 302
    assert b'Redirecting' in response.data

def test_get_secret_ajax_request(client, sample_secret):
    """Test retrieving a secret via AJAX."""
    response = client.get(f'/secret/{sample_secret.sid}', headers={'X-Requested-With': 'XMLHttpRequest'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'secret' in data
    assert 'expiration' in data 