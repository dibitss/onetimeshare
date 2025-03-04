# 🔐 OneTimeShare

```
 ▒█████   ███▄    █ ▓█████▄▄▄█████▓ ██▓ ███▄ ▄███▓▓█████   ██████  ██░ ██  ▄▄▄       ██▀███  ▓█████ 
▒██▒  ██▒ ██ ▀█   █ ▓█   ▀▓  ██▒ ▓▒▓██▒▓██▒▀█▀ ██▒▓█   ▀ ▒██    ▒ ▓██░ ██▒▒████▄    ▓██ ▒ ██▒▓█   ▀ 
▒██░  ██▒▓██  ▀█ ██▒▒███  ▒ ▓██░ ▒░▒██▒▓██    ▓██░▒███   ░ ▓██▄   ▒██▀▀██░▒██  ▀█▄  ▓██ ░▄█ ▒▒███   
▒██   ██░▓██▒  ▐▌██▒▒▓█  ▄░ ▓██▓ ░ ░██░▒██    ▒██ ▒▓█  ▄   ▒   ██▒░▓█ ░██ ░██▄▄▄▄██ ▒██▀▀█▄  ▒▓█  ▄ 
░ ████▓▒░▒██░   ▓██░░▒████▒ ▒██▒ ░ ░██░▒██▒   ░██▒░▒████▒▒██████▒▒░▓█▒░██▓ ▓█   ▓██▒░██▓ ▒██▒░▒████▒
░ ▒░▒░▒░ ░ ▒░   ▒ ▒ ░░ ▒░ ░ ▒ ░░   ░▓  ░ ▒░   ░  ░░░ ▒░ ░▒ ▒▓▒ ▒ ░ ▒ ░░▒░▒ ▒▒   ▓▒█░░ ▒▓ ░▒▓░░░ ▒░ ░
  ░ ▒ ▒░ ░ ░░   ░ ▒░ ░ ░  ░   ░     ▒ ░░  ░      ░ ░ ░  ░░ ░▒  ░ ░ ▒ ░▒░ ░  ▒   ▒▒ ░  ░▒ ░ ▒░ ░ ░  ░
░ ░ ░ ▒     ░   ░ ░    ░    ░       ▒ ░░      ░      ░   ░  ░  ░   ░  ░░ ░  ░   ▒     ░░   ░    ░   
    ░ ░           ░    ░  ░         ░         ░      ░  ░      ░   ░  ░  ░      ░  ░   ░        ░  ░
```

[![Tests](https://github.com/yourusername/onetimeshare/actions/workflows/tests.yml/badge.svg)](https://github.com/yourusername/onetimeshare/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/yourusername/onetimeshare/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/onetimeshare)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

A secure, cyberpunk-themed secret sharing service that allows you to share sensitive information through one-time-use links. Once a secret is viewed, it's permanently deleted from the system.

![Cyberpunk Theme](https://your-screenshot-url-here.png)

## 🌟 Features

- 🔒 End-to-end encryption of secrets
- ⏰ Time-based expiration
- 🔥 One-time access (secrets are deleted after viewing)
- 🎨 Cyberpunk-themed UI with dark mode
- 🛡️ Rate limiting and CSRF protection
- 🔍 Health monitoring
- 🧹 Automatic cleanup of expired secrets
- 💾 Support for SQLite and PostgreSQL databases
- 📋 One-click secret copying
- 👀 Masked secrets with show/hide functionality

## 🔒 Security Model

OneTimeShare is built with security as the top priority:

1. **Data Protection**:
   - Secrets are encrypted at rest using AES encryption
   - Secrets are stored in a database with encrypted fields
   - Secrets are automatically deleted after viewing or expiration
   - Support for both SQLite and PostgreSQL with SSL/TLS
   - Secrets are masked by default and require explicit user action to view

2. **Application Security**:
   - CSRF protection against cross-site request forgery
   - Rate limiting to prevent brute force attempts
   - Input validation and size limits (16KB max)
   - Secure headers (HSTS, XSS protection, etc.)
   - Session security with secure cookies
   - Content security policy enforcement

3. **Infrastructure Security**:
   - Non-root container execution
   - Read-only root filesystem
   - Minimal base image
   - Regular security updates
   - Kubernetes security context
   - Database connection pooling and health checks

## 🚀 Quick Start

### Local Development

1. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export FLASK_APP=wsgi.py
export FLASK_DEBUG=1
export SECRET_KEY="your-secure-secret-key"
export ENCRYPTION_KEY="your-secure-encryption-key"
```

3. Run the application:
```bash
flask run
```

Visit http://localhost:5000 to access the application.

### 🐳 Docker Compose Deployment

The easiest way to run OneTimeShare is using Docker Compose, which sets up both the application and PostgreSQL database:

1. Clone the repository:
```bash
git clone https://github.com/yourusername/onetimeshare.git
cd onetimeshare
```

2. Start the services:
```bash
docker-compose up --build
```

The application will be available at http://localhost:5001

This setup includes:
- PostgreSQL database with persistent storage
- Automatic database initialization
- Health checks for both app and database
- Development mode with debug logging
- Volume mounts for logs and instance data

### 🐳 Manual Docker Deployment

If you prefer to run without Docker Compose:

1. Build the Docker image:
```bash
docker build -t onetimeshare .
```

2. Run the container:
```bash
docker run -d \
  --name onetimeshare \
  -p 5001:5000 \
  -e FLASK_APP=wsgi.py \
  -e FLASK_DEBUG=1 \
  -e SECRET_KEY=your-secure-secret-key \
  -e ENCRYPTION_KEY=your-secure-encryption-key \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/instance:/app/instance \
  onetimeshare
```

### ⚓ Kubernetes Deployment with Helm

1. Add the required secret values to a `secrets.yaml` file:
```yaml
secrets:
  secretKey: "your-secure-secret-key"
  encryptionKey: "your-secure-encryption-key"

# Optional: Configure PostgreSQL
config:
  database:
    type: postgresql
    postgresql:
      password: "your-database-password"

postgresql:
  enabled: true  # Enable built-in PostgreSQL
  auth:
    password: "your-database-password"
```

2. Install the Helm chart:
```bash
# Add the Bitnami repository for PostgreSQL
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install the chart
helm install onetimeshare ./helm/onetimeshare \
  --values ./helm/onetimeshare/values.yaml \
  --values ./secrets.yaml
```

#### Helm Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Image repository | `onetimeshare` |
| `image.tag` | Image tag | `latest` |
| `persistence.enabled` | Enable persistent storage | `true` |
| `persistence.size` | Storage size | `1Gi` |
| `resources.limits` | Resource limits | `{cpu: 500m, memory: 512Mi}` |
| `config.database.type` | Database type (sqlite/postgresql) | `sqlite` |
| `postgresql.enabled` | Enable built-in PostgreSQL | `false` |
| `postgresql.auth.password` | PostgreSQL password | `""` |

#### Database Configuration

OneTimeShare supports two database backends:

1. **SQLite** (default for local development):
   - Simple setup, suitable for development
   - Data stored in `data/onetimeshare.db`
   - Configured by default in development mode

2. **PostgreSQL** (recommended for production):
   - Scalable and robust
   - Connection pooling with automatic recycling
   - Health checks and automatic reconnection
   - Configure via environment:
     ```bash
     export SQLALCHEMY_DATABASE_URI="postgresql://user:password@localhost:5432/onetimeshare"
     ```
   - Or use Docker Compose for automatic setup

## 🛠️ Development

### Prerequisites

- Python 3.13+
- Docker & Docker Compose (for containerized deployment)
- PostgreSQL (optional, can use Docker Compose)

### Running Tests

```bash
python -m pytest tests/
```

### Development Server

```bash
# With SQLite (default)
flask run

# With PostgreSQL (using Docker Compose)
docker-compose up --build
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🔍 Monitoring

The application provides:
- `/health` endpoint for monitoring
- Detailed logging in `logs/` directory
- Database connection health checks
- Docker health checks for both app and database

## 🌟 Acknowledgments

- Inspired by various secret sharing services
- Built with Flask and SQLAlchemy
- Cyberpunk theme inspiration from the cyberpunk genre
