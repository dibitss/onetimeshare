"""OneTimeShare - A secure, one-time secret sharing service."""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import timedelta, datetime, timezone
import secrets
from cryptography.fernet import Fernet
import base64

from flask import Flask, session, render_template, request, abort, flash, url_for, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect, CSRFError
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text
import sqlalchemy.exc

from config import config

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=["200 per day", "50 per hour"]
)
scheduler = BackgroundScheduler()
talisman = Talisman()

def create_app(test_config=None):
    """Create and configure the application."""
    app = Flask(__name__, 
                static_folder='../static',
                static_url_path='/static',
                template_folder='../templates')
    
    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', os.urandom(32).hex()),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'DATABASE_URL',
            'sqlite:///data/onetimeshare.db'
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ECHO=True,
        MAX_CONTENT_LENGTH=16 * 1024,  # 16KB
        ENCRYPTION_KEY=os.environ.get('ENCRYPTION_KEY', Fernet.generate_key().decode()),
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=5),
        WTF_CSRF_ENABLED=True,  # Enable CSRF protection by default
        WTF_CSRF_TIME_LIMIT=3600  # 1 hour CSRF token expiry
    )

    # Generate a Fernet key if not provided
    if not app.config.get('ENCRYPTION_KEY'):
        key = Fernet.generate_key()
        app.config['ENCRYPTION_KEY'] = key.decode()
    else:
        # Ensure the provided key is properly formatted
        try:
            key = base64.urlsafe_b64decode(app.config['ENCRYPTION_KEY'])
            if len(key) != 32:
                key = Fernet.generate_key()
                app.config['ENCRYPTION_KEY'] = key.decode()
        except:
            key = Fernet.generate_key()
            app.config['ENCRYPTION_KEY'] = key.decode()

    # Load test config if passed in
    if test_config is not None:
        app.config.update(test_config)
    
    # Configure logging
    app.logger.setLevel(logging.DEBUG)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)  # Initialize CSRF protection
    limiter.init_app(app)
    talisman.init_app(app)
    
    # Register error handlers
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """Handle CSRF errors."""
        return jsonify({'error': 'CSRF token missing or invalid'}), 400
    
    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            'logs/onetimeshare.log',
            maxBytes=10240,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('OneTimeShare startup')

    # Initialize database
    with app.app_context():
        try:
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            logger.debug(f"Initializing database with URI: {db_uri}")
            
            if db_uri != 'sqlite:///:memory:' and db_uri.startswith('sqlite:///'):
                db_path = db_uri.replace('sqlite:///', '')
                if not os.path.isabs(db_path):
                    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_path)
                    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
                    logger.debug(f'Using database at: {db_path}')
                
                db_dir = os.path.dirname(db_path)
                logger.debug(f"Ensuring database directory exists: {db_dir}")
                if not os.path.exists(db_dir):
                    logger.debug(f"Creating database directory: {db_dir}")
                    os.makedirs(db_dir, mode=0o777)
                
                if not os.path.exists(db_path):
                    logger.debug(f"Creating empty database file: {db_path}")
                    open(db_path, 'a').close()
                    os.chmod(db_path, 0o666)
                
                # Verify file permissions
                st = os.stat(db_path)
                logger.debug(f"Database file permissions: {oct(st.st_mode)}")
                logger.debug(f"Database file owner: {st.st_uid}:{st.st_gid}")
            
            # Import models to ensure they are registered with SQLAlchemy
            from .models import Secret
            logger.debug("Imported models")
            
            # Drop all tables and recreate them
            logger.debug("Dropping all tables...")
            db.drop_all()
            logger.debug("Creating database tables...")
            db.create_all()
            logger.info("Database initialization completed successfully")
            
            # Test database connection and verify table exists
            result = db.session.execute(text('SELECT name FROM sqlite_master WHERE type="table" AND name="secrets"')).fetchone()
            if result:
                logger.info("Secrets table created successfully")
            else:
                logger.error("Secrets table was not created")
                raise Exception("Failed to create secrets table")
            
            # Test basic database operations
            test_secret = Secret(secret="test", expiration=datetime.now(timezone.utc) + timedelta(minutes=5))
            db.session.add(test_secret)
            db.session.commit()
            logger.debug("Test secret created successfully")
            db.session.delete(test_secret)
            db.session.commit()
            logger.debug("Test secret deleted successfully")
            
        except sqlalchemy.exc.OperationalError as e:
            logger.error(f"Database operational error: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error during database initialization: {str(e)}", exc_info=True)
            raise

    # Register blueprints and routes
    from . import routes
    app.register_blueprint(routes.bp)
    
    # Configure session
    @app.before_request
    def before_request():
        """Set up session before each request."""
        if 'initialized' not in session:
            session['initialized'] = True
            session.permanent = True

    @app.after_request
    def after_request(response):
        """Log after each request."""
        app.logger.debug(f'Response headers: {dict(response.headers)}')
        return response
    
    # Configure security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to response."""
        if not app.debug:  # Only add security headers in production
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response

    # Start scheduler only in production
    if not app.debug and not app.testing:
        from .models import Secret
        scheduler.add_job(
            func=Secret.cleanup_expired,
            trigger="interval",
            minutes=60
        )
        scheduler.start()
    
    # Register teardown
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        """Shut down the scheduler when the app context tears down."""
        if scheduler.running:
            scheduler.shutdown()

    @app.errorhandler(Exception)
    def handle_error(error):
        """Log all errors."""
        app.logger.error(f'Unhandled error: {error}', exc_info=True)
        return 'An error occurred', 500

    @app.errorhandler(413)
    def handle_request_entity_too_large(e):
        """Handle request entity too large errors."""
        return jsonify({'error': 'Secret too large'}), 413

    return app
