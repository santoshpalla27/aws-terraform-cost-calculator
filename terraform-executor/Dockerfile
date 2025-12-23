# ============================================================================
# Simplified Dockerfile for Terraform Executor
# ============================================================================

# Stage 1: Python Builder
FROM python:3.11-slim AS python-builder

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

ARG TERRAFORM_VERSION=1.6.0

# Install Terraform and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
    && unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
    && mv terraform /usr/local/bin/ \
    && chmod +x /usr/local/bin/terraform \
    && rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip

# Create non-root user
RUN groupadd -r terraform && useradd -r -g terraform terraform

# Copy Python dependencies
COPY --from=python-builder /root/.local /home/terraform/.local

# Copy application code
COPY app/ ./app/
COPY worker.py ./

# Set environment variables
ENV PATH=/home/terraform/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV WORKSPACE_BASE_DIR=/tmp/terraform-workspaces

# Create writable /tmp directory
RUN mkdir -p /tmp/terraform-workspaces && \
    chown -R terraform:terraform /tmp && \
    chown -R terraform:terraform /app

# Switch to non-root user
USER terraform

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health').read()"

# Default: Run API (worker runs separately)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
