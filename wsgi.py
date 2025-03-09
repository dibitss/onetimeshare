"""WSGI entry point for OneTimeShare."""
import os
from onetimeshare import create_app

# Determine configuration based on environment
config_name = os.environ.get('FLASK_CONFIG', 'default')
if os.environ.get('SQLALCHEMY_DATABASE_URI'):
    config_name = 'docker'

# Create the application instance
app = create_app({
    'SQLALCHEMY_DATABASE_URI': os.environ.get(
        'SQLALCHEMY_DATABASE_URI',
        'sqlite:///data/onetimeshare.db'
    ),
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev'),
    'WTF_CSRF_ENABLED': True,
    'MAX_CONTENT_LENGTH': 16 * 1024,  # 16KB
    'SERVER_NAME': None,  # Allow any server name
    'SESSION_COOKIE_SECURE': False,  # Allow non-HTTPS in development
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PREFERRED_URL_SCHEME': 'http',  # Use HTTP in development
    'TESTING': False,
    'DEBUG': True,
    'JSON_AS_ASCII': False,
    'JSONIFY_MIMETYPE': 'application/json',
    'TEMPLATES_AUTO_RELOAD': True,
    'EXPLAIN_TEMPLATE_LOADING': True,
    'APPLICATION_ROOT': '/',
    'TRAP_HTTP_EXCEPTIONS': True,
    'TRAP_BAD_REQUEST_ERRORS': True
})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True, ssl_context=None) 