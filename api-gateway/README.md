# API Gateway - AWS Cost Calculator

Production-grade API Gateway for the Terraform-based AWS Cost Calculator platform.

## Overview

This service is the **single public entry point** for:
- Frontend UI
- CI/CD pipelines
- External integrations

It acts as a **security and contract boundary** - a pure control plane, NOT a compute plane.

## What It Does

✅ **Authentication & Authorization**
- JWT token validation
- OIDC integration (pluggable)
- Configurable auth bypass for local dev

✅ **File Upload Service**
- Accept Terraform configs (.tf, .tfvars, .zip)
- Strict validation (size, extensions, path traversal)
- Zip bomb detection
- Isolated storage

✅ **Job Management**
- Create cost estimation jobs
- Track job status
- List jobs with pagination
- Idempotent operations

✅ **Security Hardening**
- Rate limiting (per-client)
- Request size limits
- CORS configuration
- Audit logging
- Non-root container

## What It Does NOT Do

❌ Execute Terraform
❌ Calculate costs or pricing
❌ Contain business logic
❌ Call AWS APIs directly
❌ Perform long-running tasks

## Tech Stack

- **Language**: Python 3.11
- **Framework**: FastAPI (async-first)
- **Validation**: Pydantic v2
- **Auth**: JWT + OIDC (pluggable)
- **Container**: Docker (multi-stage, non-root)

## Quick Start

### Local Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker

```bash
# Build
docker build -t api-gateway .

# Run
docker run -p 8000:8000 \
  -e AUTH_ENABLED=false \
  -e LOG_LEVEL=INFO \
  api-gateway
```

### Docker Compose

```bash
docker-compose up -d
```

## API Endpoints

### Health
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe

### Uploads
- `POST /api/v1/uploads` - Upload Terraform files
- `GET /api/v1/uploads/{upload_id}` - Get upload metadata

### Jobs
- `POST /api/v1/jobs` - Create cost estimation job
- `GET /api/v1/jobs/{job_id}` - Get job details
- `GET /api/v1/jobs` - List jobs (paginated)
- `DELETE /api/v1/jobs/{job_id}` - Delete job

## Configuration

All configuration via environment variables:

```env
# Authentication
AUTH_ENABLED=false
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256

# File Uploads
MAX_UPLOAD_SIZE=52428800  # 50MB
UPLOAD_DIR=/tmp/uploads
ALLOWED_EXTENSIONS=.tf,.tfvars,.zip

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60  # seconds

# CORS
CORS_ORIGINS=http://localhost:3000
```

See `.env.example` for all options.

## Security Features

### File Upload Security
- ✅ Extension whitelist (.tf, .tfvars, .zip only)
- ✅ Size limit enforcement
- ✅ Path traversal prevention
- ✅ Zip bomb detection
- ✅ Filename sanitization

### Authentication
- ✅ JWT token validation
- ✅ OIDC integration ready
- ✅ Configurable bypass for dev
- ✅ Protected endpoints

### Rate Limiting
- ✅ Per-client limits
- ✅ Configurable thresholds
- ✅ Graceful 429 responses
- ✅ Redis-ready architecture

### Container Security
- ✅ Non-root user (apigateway)
- ✅ Minimal base image
- ✅ No secrets in image
- ✅ Health checks

## Example Requests

### Upload Files

```bash
curl -X POST http://localhost:8000/api/v1/uploads \
  -F "files=@main.tf" \
  -F "files=@variables.tf"
```

### Create Job

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Production Infrastructure Cost Estimate"
  }'
```

### List Jobs

```bash
curl "http://localhost:8000/api/v1/jobs?page=1&page_size=10&status=PENDING"
```

## Project Structure

```
api-gateway/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── middleware/          # Auth, rate limiting, logging
│   ├── routers/             # API endpoints
│   ├── services/            # Business logic
│   ├── repositories/        # Data persistence
│   ├── models/              # Pydantic models
│   └── utils/               # Validators, security
├── tests/                   # Test suite
├── Dockerfile               # Production build
├── docker-compose.yml       # Local development
├── requirements.txt         # Python dependencies
└── .env.example             # Environment template
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type check
mypy app/
```

## Observability

### Structured Logging

All logs are in JSON format with:
- Timestamp
- Log level
- Correlation ID
- Request details
- Response time

### Correlation IDs

Every request gets a unique correlation ID for tracing:
- Auto-generated or from `X-Correlation-ID` header
- Propagated to all logs
- Returned in response headers

### Metrics

- Request duration (via `X-Response-Time` header)
- Status codes
- Rate limit hits

## Deployment

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api-gateway
        image: api-gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: AUTH_ENABLED
          value: "true"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
```

## Troubleshooting

### Upload Fails

- Check file size limits (`MAX_UPLOAD_SIZE`)
- Verify file extensions are allowed
- Check upload directory permissions

### Authentication Errors

- Verify `AUTH_ENABLED` setting
- Check JWT secret configuration
- Validate token expiration

### Rate Limiting

- Adjust `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW`
- Check client IP or user ID
- Review `Retry-After` header in 429 responses

## Production Checklist

- [ ] Set strong `JWT_SECRET`
- [ ] Enable authentication (`AUTH_ENABLED=true`)
- [ ] Configure CORS origins
- [ ] Set appropriate rate limits
- [ ] Configure log aggregation
- [ ] Set up monitoring/alerting
- [ ] Enable HTTPS
- [ ] Review security headers
- [ ] Test health checks
- [ ] Verify upload directory permissions

## License

Part of the AWS Cost Calculator platform.
