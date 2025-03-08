# Multi-stage build for optimization
FROM python:3.10-slim AS builder

# Set working directory
WORKDIR /app

# Set environment variables for build optimization
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies and cleanup in the same layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements for better layer caching
COPY requirements.txt .

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies with pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir wheel && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    # Default AWS region (can be overridden at runtime)
    AWS_REGION=us-east-1 \
    # Set restricted file permissions for security
    UMASK=0027

# Install runtime dependencies and perform security hardening in one layer
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create directory for storing extracted terminology and AWS credentials
RUN mkdir -p /app/glossary_files && \
    mkdir -p /app/.aws && \
    chmod 750 /app/glossary_files && \
    chmod 700 /app/.aws

# Copy virtual environment and wheels from builder stage
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/wheels /app/wheels

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Install wheels and cleanup
RUN pip install --no-cache-dir --no-index --find-links=/app/wheels/ /app/wheels/* \
    && rm -rf /app/wheels \
    && find /opt/venv -type d -name "__pycache__" -exec rm -r {} +

# Copy application files (staged for better caching)
COPY src/ /app/src/
COPY .env.example /app/
COPY gradio_app.py /app/

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

# Create mount points for secrets and data persistence
VOLUME ["/app/.aws", "/app/glossary_files"]

# Expose port for Gradio
EXPOSE 7860

# Set entrypoint with script that can process AWS credentials from mounted volume
COPY docker-entrypoint.sh /app/
USER root
RUN chmod +x /app/docker-entrypoint.sh && \
    chown appuser:appuser /app/docker-entrypoint.sh
USER appuser

# Use tini as init system
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/docker-entrypoint.sh", "python", "gradio_app.py"]

# More specific health check for Gradio interface
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/api/health || exit 1
