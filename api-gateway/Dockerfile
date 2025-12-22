# ============================================================================
# Multi-stage Dockerfile for API Gateway
# ============================================================================

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================================
# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r apigateway && useradd -r -g apigateway apigateway

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/apigateway/.local

# Copy application code
COPY app/ ./app/

# Create upload directory
RUN mkdir -p /tmp/uploads && chown -R apigateway:apigateway /tmp/uploads

# Set environment variables
ENV PATH=/home/apigateway/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV UPLOAD_DIR=/tmp/uploads

# Switch to non-root user
USER apigateway

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
