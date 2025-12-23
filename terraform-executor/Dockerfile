# ============================================================================
# Hardened Dockerfile for Terraform Executor
# PRE-BAKES PROVIDERS - NO RUNTIME DOWNLOADS
# ============================================================================

# Stage 1: Terraform Builder
FROM alpine:3.19 AS terraform-builder

ARG TERRAFORM_VERSION=1.6.0

RUN apk add --no-cache wget unzip ca-certificates && \
    wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    mv terraform /usr/local/bin/ && \
    chmod +x /usr/local/bin/terraform

# Stage 2: Provider Builder (PRE-BAKE PROVIDERS)
FROM hashicorp/terraform:1.6.0 AS provider-builder

# Create plugin directory
RUN mkdir -p /opt/terraform/plugins

# Pre-download allowed providers
# This prevents runtime downloads and ensures deterministic versions
WORKDIR /tmp/provider-init

# Create minimal terraform config to download providers
RUN cat > main.tf <<'EOF'
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}
EOF

# Download providers to plugin directory
RUN terraform init -plugin-dir=/opt/terraform/plugins

# ============================================================================
# Stage 3: Python Builder
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
# Stage 4: Runtime
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r terraform && useradd -r -g terraform terraform

# Copy Terraform binary
COPY --from=terraform-builder /usr/local/bin/terraform /usr/local/bin/terraform

# Copy PRE-BAKED providers
COPY --from=provider-builder /opt/terraform/plugins /opt/terraform/plugins

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
    chown -R terraform:terraform /opt/terraform/plugins

# Switch to non-root user
USER terraform

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health').read()"

# Default: Run API (worker runs separately)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
