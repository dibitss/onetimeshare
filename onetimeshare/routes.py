"""Routes for OneTimeShare application."""
from datetime import datetime, timedelta, timezone
import html
from flask import (
    Blueprint, flash, g, redirect, render_template,
    request, url_for, abort, jsonify, current_app
)
from werkzeug.exceptions import RequestEntityTooLarge
from sqlalchemy import text
from . import db, limiter
from .models import Secret

bp = Blueprint('onetimeshare', __name__)

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
        secret = request.form.get('secret', '').strip()
        if not secret:
            return jsonify({'error': 'Secret cannot be empty'}), 400

        try:
            expiration_str = request.form.get('expiration')
            expiration = datetime.strptime(expiration_str, '%Y-%m-%dT%H:%M')
            expiration = expiration.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid expiration format'}), 400

        if expiration <= datetime.now(timezone.utc):
            return jsonify({'error': 'Expiration must be in the future'}), 400

        secret_obj = Secret(secret=secret, expiration=expiration)
        secret_obj.save()

        return jsonify({
            'message': 'Secret created successfully',
            'url': url_for('onetimeshare.get_secret', sid=secret_obj.sid, _external=True)
        }), 200

    except RequestEntityTooLarge:
        return jsonify({'error': 'Secret too large'}), 413
    except Exception as e:
        current_app.logger.error(f"Error creating secret: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/secret/<sid>')
def get_secret(sid):
    """Retrieve and delete a secret."""
    secret = Secret.query.filter_by(sid=sid).first()
    
    if not secret:
        return jsonify({'error': 'Secret not found'}), 404

    if secret.is_expired():
        db.session.delete(secret)
        db.session.commit()
        return jsonify({'error': 'Secret has expired'}), 410

    # Get the secret before deleting and escape HTML
    secret_text = html.escape(secret.secret)
    
    # Delete the secret
    db.session.delete(secret)
    db.session.commit()

    return jsonify({'secret': secret_text}), 200

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