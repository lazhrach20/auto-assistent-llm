# ==============================================
# Stage 1: Builder - Install dependencies
# ==============================================
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==============================================
# Stage 2: Final - Runtime image
# ==============================================
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security (but we need to run entrypoint as root first)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Copy and make entrypoint executable (must be done as root)
COPY entrypoint.sh /entrypoint.sh

# Change ownership to non-root user
RUN chown -R appuser:appuser /app && \
    chmod +x /entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import socket; sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); sock.settimeout(5); result = sock.connect_ex(('localhost', 8000)); sock.close(); exit(0 if result == 0 else 1)"

# Use entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
