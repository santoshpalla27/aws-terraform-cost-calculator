# Terraform Executor Service

Secure, sandboxed service for executing Terraform and producing plan JSON output.

## Overview

This service accepts Terraform configuration bundles, executes them in an isolated container environment with strict security controls, and returns deterministic plan JSON without persisting state.

## Security Model

### Container Isolation

- **Read-Only Filesystem**: Root filesystem is read-only, only `/tmp` writable (tmpfs)
- **Non-Root User**: Runs as UID 1000 with no privileges
- **Resource Limits**: 512MB RAM, 1 CPU core, 5-minute timeout
- **No Network** (configurable): Can disable network access during execution
- **Isolated Workspaces**: Each execution gets a unique tmpfs workspace

### Security Controls

**Blocked Providers:**
- `local-exec` provisioner
- `external` provider
- `null` provider (with provisioners)

**Blocked Features:**
- Backend configuration (forced `-backend=false`)
- `remote-exec` provisioner
- `connection` blocks

**Enforced:**
- Timeout limits
- Resource limits
- Path sanitization
- Configuration validation

## Execution Flow

```
1. Receive execution request
2. Create isolated workspace in /tmp
3. Copy Terraform files to workspace
4. Validate configuration (security checks)
5. Execute: terraform init -backend=false
6. Execute: terraform validate
7. Execute: terraform plan -out=tfplan
8. Execute: terraform show -json tfplan
9. Parse and return JSON
10. Cleanup workspace
```

## API Endpoints

### Execute Terraform

```http
POST /api/v1/execute
Content-Type: application/json

{
  "job_id": "job_123abc",
  "upload_id": "upload_456def"
}
```

**Response (Success):**
```json
{
  "job_id": "job_123abc",
  "status": "SUCCESS",
  "plan_json": {
    "format_version": "1.2",
    "terraform_version": "1.6.6",
    "planned_values": {...},
    "resource_changes": [...]
  },
  "execution_time_seconds": 12.5
}
```

**Response (Failed):**
```json
{
  "job_id": "job_123abc",
  "status": "FAILED",
  "error_type": "ExecutionError",
  "error_message": "Blocked provider detected: local-exec",
  "execution_time_seconds": 0.5
}
```

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "terraform_version": "1.6.6"
}
```

## Quick Start

### Using Docker Compose

```bash
cd terraform-executor
docker-compose up --build
```

Service available at: http://localhost:8001

### Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `EXECUTION_TIMEOUT` | 300 | Execution timeout in seconds |
| `WORKSPACE_DIR` | /tmp/workspace | Workspace directory |
| `MAX_PLAN_SIZE_MB` | 50 | Maximum plan size |
| `ALLOW_NETWORK` | true | Allow network access |
| `BLOCKED_PROVIDERS` | local-exec,external,null | Blocked providers |
| `UPLOAD_BASE_DIR` | /uploads | Upload directory |

## Testing

### Valid Terraform

```bash
curl -X POST http://localhost:8001/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "test_job",
    "upload_id": "upload_456def"
  }'
```

### Test Security Controls

Create a Terraform file with blocked provider:

```hcl
resource "null_resource" "test" {
  provisioner "local-exec" {
    command = "echo dangerous"
  }
}
```

Expected: Error response blocking execution

## Architecture

```
┌─────────────────────┐
│   API Gateway       │
└──────────┬──────────┘
           │
           │ POST /api/v1/execute
           │
┌──────────▼──────────┐
│ Terraform Executor  │
│                     │
│  ┌──────────────┐   │
│  │  Security    │   │
│  │  Validator   │   │
│  └──────┬───────┘   │
│         │           │
│  ┌──────▼───────┐   │
│  │  Workspace   │   │
│  │  Manager     │   │
│  └──────┬───────┘   │
│         │           │
│  ┌──────▼───────┐   │
│  │  Terraform   │   │
│  │  Executor    │   │
│  └──────┬───────┘   │
│         │           │
│  ┌──────▼───────┐   │
│  │  Plan        │   │
│  │  Parser      │   │
│  └──────────────┘   │
└─────────────────────┘
```

## Security Considerations

### Threat Model

**Threats Mitigated:**
- ✅ Arbitrary code execution (via provisioners)
- ✅ Data exfiltration (via external provider)
- ✅ Resource exhaustion (via limits)
- ✅ State persistence (via backend blocking)
- ✅ Path traversal (via sanitization)

**Residual Risks:**
- ⚠️ Complex Terraform configurations may consume resources
- ⚠️ Provider downloads require network access (can be disabled)
- ⚠️ Terraform bugs/vulnerabilities

### Best Practices

1. **Network Isolation**: Disable network after provider downloads
2. **Provider Mirror**: Use local provider mirror in production
3. **Resource Monitoring**: Monitor container resource usage
4. **Log Analysis**: Review execution logs for anomalies
5. **Version Pinning**: Pin Terraform version for consistency

## Deployment

### Docker

```bash
docker build -t terraform-executor .
docker run -p 8001:8001 \
  --read-only \
  --tmpfs /tmp:size=256m \
  --memory=512m \
  --cpus=1.0 \
  terraform-executor
```

### Kubernetes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: terraform-executor
spec:
  containers:
  - name: executor
    image: terraform-executor:latest
    resources:
      limits:
        memory: "512Mi"
        cpu: "1"
    securityContext:
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 1000
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir:
      sizeLimit: 256Mi
```

## Troubleshooting

### Execution Timeout

Increase `EXECUTION_TIMEOUT` environment variable:
```bash
docker-compose up -e EXECUTION_TIMEOUT=600
```

### Provider Download Fails

Ensure `ALLOW_NETWORK=true` or use provider mirror.

### Memory Limit Exceeded

Increase memory limit in docker-compose.yml:
```yaml
mem_limit: 1g
```

## License

[Your License]

## Support

For issues and questions, contact [support@example.com](mailto:support@example.com)
