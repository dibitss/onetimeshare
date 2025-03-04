"""Command-line interface for OneTimeShare."""
import os
import click
from flask.cli import FlaskGroup
from . import create_app

def create_cli_app():
    """Create the Flask application for CLI commands."""
    return create_app(os.getenv('FLASK_ENV', 'development'))

@click.group(cls=FlaskGroup, create_app=create_cli_app)
def main():
    """Management script for OneTimeShare."""

@main.command()
def init():
    """Initialize the application."""
    from . import db
    db.create_all()
    click.echo('Database initialized.')

@main.command()
def cleanup():
    """Clean up expired secrets."""
    from .models import Secret
    count = Secret.cleanup_expired()
    click.echo(f'Cleaned up {count} expired secrets.')

@main.command()
def generate_keys():
    """Generate secure keys for the application."""
    import secrets
    secret_key = secrets.token_hex(32)
    encryption_key = secrets.token_hex(32)
    click.echo('Generated secure keys. Add these to your environment:')
    click.echo(f'export SECRET_KEY="{secret_key}"')
    click.echo(f'export ENCRYPTION_KEY="{encryption_key}"')

if __name__ == '__main__':
    main() 