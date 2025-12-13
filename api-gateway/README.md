# API Gateway - Terraform Cost Estimator

Production-grade FastAPI gateway for AWS Terraform Cost Estimation platform.

## Overview

This service provides a REST API for uploading Terraform configurations and managing cost estimation jobs. It acts as the entry point to the cost estimation platform, orchestrating downstream services without embedding business logic.

## Features

- ✅ **File Upload**: Upload Terraform files as ZIP or individual files
- ✅ **Job Management**: Create, track, and manage cost estimation jobs
- ✅ **Idempotency**: Prevent duplicate job creation with idempotency keys
- ✅ **Rate Limiting**: Token bucket algorithm with configurable limits
- ✅ **Authentication**: Optional JWT-based authentication (pluggable)
- ✅ **Structured Logging**: JSON-formatted logs with correlation IDs
- ✅ **Health Checks**: Kubernetes-ready health endpoints
- ✅ **OpenAPI**: Auto-generated API documentation
- ✅ **Containerized**: Production-ready Docker setup

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
┌──────▼──────────────┐
│  API Gateway        │
│  (This Service)     │
│                     │
│  - Upload Handler   │
│  - Job Manager      │
│  - Orchestrator     │
└──────┬──────────────┘
       │
┌──────▼──────────────┐
│ Terraform Executor  │
│ (Downstream)        │
└─────────────────────┘
```

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start the service
docker-compose up --build

# Service will be available at http://localhost:8000
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python -m app.main

# Or with uvicorn
uvicorn app.main:app --reload
```

## Configuration

Configuration is managed via environment variables. See `docker-compose.yml` for all available options.

### Key Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_UPLOAD_SIZE_MB` | 100 | Maximum upload size in MB |
| `ALLOWED_EXTENSIONS` | .tf,.tfvars,.zip | Allowed file extensions |
| `RATE_LIMIT_ENABLED` | true | Enable rate limiting |
| `RATE_LIMIT_REQUESTS` | 100 | Max requests per period |
| `RATE_LIMIT_PERIOD` | 60 | Rate limit period in seconds |
| `AUTH_ENABLED` | false | Enable JWT authentication |
| `LOG_LEVEL` | INFO | Logging level |
| `LOG_FORMAT` | json | Log format (json or text) |

## API Documentation

### Interactive Documentation

Once the service is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

### Example Workflow

1. **Upload Terraform Files**
   ```bash
   curl -X POST http://localhost:8000/api/v1/uploads \
     -F "file=@terraform.zip" \
     -F "project_name=my-project"
   ```
   
   Response:
   ```json
   {
     "upload_id": "upload_456def",
     "project_name": "my-project",
     "file_count": 5,
     "total_size_bytes": 12345,
     "message": "Files uploaded successfully"
   }
   ```

2. **Create Cost Estimation Job**
   ```bash
   curl -X POST http://localhost:8000/api/v1/jobs \
     -H "Content-Type: application/json" \
     -d '{
       "upload_id": "upload_456def",
       "region": "us-east-1"
     }'
   ```
   
   Response:
   ```json
   {
     "job_id": "job_123abc",
     "upload_id": "upload_456def",
     "status": "PENDING",
     "region": "us-east-1",
     "created_at": "2025-12-13T10:00:00Z",
     "updated_at": "2025-12-13T10:00:00Z"
   }
   ```

3. **Check Job Status**
   ```bash
   curl http://localhost:8000/api/v1/jobs/job_123abc
   ```
   
   Response:
   ```json
   {
     "job_id": "job_123abc",
     "status": "COMPLETED",
     "result_data": {
       "total_monthly_cost": 1234.56,
       "resources": [...]
     }
   }
   ```

## API Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe

### Uploads
- `POST /api/v1/uploads` - Upload Terraform files

### Jobs
- `POST /api/v1/jobs` - Create cost estimation job
- `GET /api/v1/jobs/{job_id}` - Get job status
- `GET /api/v1/jobs` - List jobs (paginated)
- `DELETE /api/v1/jobs/{job_id}` - Delete job

## Project Structure

```
api-gateway/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models/              # Pydantic models
│   │   ├── domain.py        # Domain models
│   │   ├── requests.py      # Request schemas
│   │   └── responses.py     # Response schemas
│   ├── routers/             # API endpoints
│   │   ├── health.py        # Health checks
│   │   ├── uploads.py       # Upload endpoints
│   │   └── jobs.py          # Job endpoints
│   ├── services/            # Business logic
│   │   ├── upload_service.py
│   │   ├── job_service.py
│   │   └── orchestrator.py
│   ├── repositories/        # Data access
│   │   └── job_repository.py
│   ├── middleware/          # Middleware
│   │   ├── auth.py          # JWT authentication
│   │   ├── rate_limit.py    # Rate limiting
│   │   └── logging.py       # Structured logging
│   └── utils/               # Utilities
│       ├── logger.py
│       └── validators.py
├── docs/
│   ├── openapi.yaml         # OpenAPI specification
│   └── examples/            # Example payloads
├── tests/                   # Test suite
├── Dockerfile               # Container definition
├── docker-compose.yml       # Local development
└── requirements.txt         # Python dependencies
```

## Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

## Deployment

### Docker

```bash
# Build image
docker build -t terraform-cost-api-gateway .

# Run container
docker run -p 8000:8000 \
  -e AUTH_ENABLED=false \
  -e LOG_LEVEL=INFO \
  terraform-cost-api-gateway
```

### Kubernetes

The service includes health check endpoints for Kubernetes:
- Liveness probe: `/health/live`
- Readiness probe: `/health/ready`

Example deployment:
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

## Security

- **Authentication**: JWT-based (optional, configurable)
- **Rate Limiting**: Token bucket algorithm
- **Input Validation**: Pydantic models with strict validation
- **File Validation**: Extension, size, and structure checks
- **Path Traversal Protection**: Filename sanitization
- **Non-root Container**: Runs as non-root user (UID 1000)

## Monitoring

### Structured Logs

All logs are JSON-formatted with correlation IDs:

```json
{
  "timestamp": "2025-12-13T10:00:00Z",
  "level": "info",
  "message": "Request completed",
  "correlation_id": "abc-123",
  "path": "/api/v1/jobs",
  "method": "POST",
  "status_code": 201,
  "duration_ms": 45.2
}
```

### Correlation IDs

Every request gets a unique correlation ID added to:
- Response headers: `X-Correlation-ID`
- All log entries
- Downstream service calls

## Troubleshooting

### Common Issues

1. **Upload fails with "File too large"**
   - Increase `MAX_UPLOAD_SIZE_MB` environment variable

2. **Rate limit exceeded**
   - Adjust `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_PERIOD`
   - Or disable with `RATE_LIMIT_ENABLED=false`

3. **Job submission fails**
   - Check `TERRAFORM_EXECUTOR_URL` is correct
   - Verify downstream service is healthy

### Debug Mode

Enable debug mode for detailed logs:
```bash
docker-compose up -e DEBUG=true -e LOG_FORMAT=text
```

## License

[Your License Here]

## Support

For issues and questions, please contact [support@example.com](mailto:support@example.com)
