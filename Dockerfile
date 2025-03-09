# Build stage
FROM python:3.13-slim-bookworm AS builder

# Set working directory for the build
WORKDIR /app

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        libffi-dev \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.13-slim-bookworm AS runtime

# Set working directory
WORKDIR /app

# Create non-root user
RUN useradd -m -r -s /bin/bash appuser \
    && chown appuser:appuser /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=wsgi.py \
    FLASK_DEBUG=1 \
    FLASK_ENV=development

# Copy application files
COPY --chown=appuser:appuser . .

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/instance /app/logs \
    && chown -R appuser:appuser /app/data /app/instance /app/logs \
    && chmod 700 /app/data /app/instance /app/logs \
    && chmod -R 755 /app/static /app/templates

# Security hardening
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tini \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && chmod 755 /app \
    && chmod 644 /app/*.py \
    && chmod 644 /app/requirements.txt

# Switch to non-root user
USER appuser

# Expose port 5000
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Use tini as init
ENTRYPOINT ["/usr/bin/tini", "--"]

# Run the application with Flask development server
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"] 