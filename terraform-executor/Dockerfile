# Multi-stage secure Dockerfile for Terraform execution
# Stage 1: Download and verify Terraform
FROM alpine:3.19 AS terraform-downloader

# Terraform version
ARG TERRAFORM_VERSION=1.6.6

# Install dependencies for download
RUN apk add --no-cache \
    curl \
    unzip \
    gnupg

# Download Terraform
WORKDIR /tmp
RUN curl -fsSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip" -o terraform.zip && \
    unzip terraform.zip && \
    chmod +x terraform && \
    ./terraform version

# Stage 2: Minimal runtime environment
FROM python:3.11-alpine

# Install runtime dependencies only
RUN apk add --no-cache \
    ca-certificates \
    git \
    && rm -rf /var/cache/apk/*

# Copy Terraform binary from downloader stage
COPY --from=terraform-downloader /tmp/terraform /usr/local/bin/terraform

# Create non-root user
RUN adduser -D -u 1000 -h /home/tfuser tfuser && \
    mkdir -p /tmp/workspace && \
    chown -R tfuser:tfuser /tmp/workspace

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=tfuser:tfuser ./app ./app

# Switch to non-root user
USER tfuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TF_IN_AUTOMATION=1
ENV TF_INPUT=0
ENV TF_CLI_ARGS="-no-color"

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
