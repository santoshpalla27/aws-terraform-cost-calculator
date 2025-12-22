# ============================================================================
# Multi-stage Dockerfile for Job Orchestrator
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
RUN groupadd -r orchestrator && useradd -r -g orchestrator orchestrator

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/orchestrator/.local

# Copy application code
COPY app/ ./app/

# Set environment variables
ENV PATH=/home/orchestrator/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER orchestrator

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health').read()"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
