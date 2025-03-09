"""Routes for OneTimeShare application."""
from datetime import datetime, timedelta, timezone
import html
from flask import (
    Blueprint, flash, g, redirect, render_template,
    request, url_for, abort, jsonify, current_app, make_response
)
from werkzeug.exceptions import RequestEntityTooLarge
from sqlalchemy import text
from . import db, limiter
from .models import Secret

bp = Blueprint('onetimeshare', __name__, url_prefix='')

@bp.route('/')
def home():
    """Render the home page."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M')
    suggested = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    return render_template('index.html', now=now, suggested=suggested)

@bp.route('/create', methods=['POST'])
@limiter.limit("10 per minute")
def add_secret():
    """Create a new secret."""
    try:
        if not request.form.get('secret'):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Secret is required'}), 400
            flash('Secret is required', 'error')
            return redirect(url_for('onetimeshare.home'))

        expiration = request.form.get('expiration')
        if not expiration:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Expiration time is required'}), 400
            flash('Expiration time is required', 'error')
            return redirect(url_for('onetimeshare.home'))

        try:
            # Parse the datetime and make it timezone-aware
            expiration = datetime.fromisoformat(expiration).replace(tzinfo=timezone.utc)
        except ValueError:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Invalid expiration time format'}), 400
            flash('Invalid expiration time format', 'error')
            return redirect(url_for('onetimeshare.home'))

        if expiration <= datetime.now(timezone.utc):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Expiration time must be in the future'}), 400
            flash('Expiration time must be in the future', 'error')
            return redirect(url_for('onetimeshare.home'))

        secret = Secret(secret=request.form['secret'], expiration=expiration)
        db.session.add(secret)
        db.session.commit()

        secret_url = url_for('onetimeshare.get_secret', sid=secret.sid, _external=True)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'url': secret_url})
        
        return render_template('index.html', 
                            url=secret_url,
                            now=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M'),
                            suggested=(datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'))

    except RequestEntityTooLarge:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Secret too large'}), 413
        flash('Secret too large', 'error')
        return redirect(url_for('onetimeshare.home'))
    except Exception as e:
        current_app.logger.error(f"Error creating secret: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Internal server error'}), 500
        flash('An error occurred while creating the secret', 'error')
        return redirect(url_for('onetimeshare.home'))

@bp.route('/secret/<sid>')
def get_secret(sid):
    """Retrieve and delete a secret."""
    secret = Secret.query.filter_by(sid=sid).first()
    
    if not secret:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Secret not found'}), 404
        flash('Secret not found', 'error')
        return redirect(url_for('onetimeshare.home'))

    if secret.is_expired():
        db.session.delete(secret)
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Secret has expired'}), 410
        flash('Secret has expired', 'error')
        return redirect(url_for('onetimeshare.home'))

    # Get the secret before deleting and escape HTML
    secret_text = html.escape(secret.secret)
    
    # Delete the secret
    db.session.delete(secret)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'secret': secret_text})
    
    return render_template('secret.html', secret=secret_text)

@bp.route('/health')
def health_check():
    """Check the health of the application."""
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500 