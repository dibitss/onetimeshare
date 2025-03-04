"""Setup script for OneTimeShare."""
from setuptools import setup, find_packages

setup(
    name="onetimeshare",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.13",
    install_requires=[
        'Flask>=2.3.0',
        'SQLAlchemy>=2.0.0',
        'Flask-SQLAlchemy>=3.0.0',
        'sqlalchemy-utils>=0.41.0',
        'cryptography>=42.0.0',
        'Flask-Limiter>=3.5.0',
        'Flask-Talisman>=1.1.0',
        'Flask-WTF>=1.2.1',
        'APScheduler>=3.10.4',
        'python-dotenv>=1.0.0',
        'gunicorn>=21.2.0',
        'psycopg2-binary>=2.9.0',  # PostgreSQL support
    ],
    extras_require={
        'dev': [
            'pytest>=8.0.0',
            'pytest-cov>=4.1.0',
            'black>=24.0.0',
            'flake8>=7.0.0',
            'mypy>=1.8.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'onetimeshare=onetimeshare.cli:main',
        ],
    },
) 