# Terraform Execution Service

**Sandboxed Terraform executor** for safely running untrusted Terraform configurations.

## ⚠️ Security Notice

This service executes **UNTRUSTED** Terraform code and is designed as a **hostile workload sandbox**.

## Overview

**Pure Execution Plane** - NOT an orchestrator, NOT a cost calculator:
- ✅ Runs Terraform CLI
- ✅ Produces plan JSON
- ✅ Returns execution artifacts
- ❌ NO orchestration logic
- ❌ NO pricing/cost logic
- ❌ NO state persistence

## Threat Model

Assumes uploaded Terraform configurations may attempt:
- Data exfiltration via external data sources
- Privilege escalation via local-exec provisioners
- DoS attacks via resource exhaustion
- Network scanning
- Credential theft

## Security Controls

### Filesystem
- ✅ Read-only root filesystem
- ✅ Writable /tmp only (1GB limit)
- ✅ No host mounts
- ✅ No Docker socket access

### Terraform Restrictions
- ✅ Blocks local-exec provisioners
- ✅ Blocks external data sources
- ✅ Provider allowlist (aws, random, null)
- ✅ No auto-install of unknown providers

### Process
- ✅ No shell execution (direct subprocess only)
- ✅ Seccomp profile applied
- ✅ AppArmor profile (optional)
- ✅ Non-root user (terraform)
- ✅ No capabilities

### Resource Limits
- ✅ CPU: 2 cores max
- ✅ Memory: 2GB max
- ✅ Execution timeout: 300s
- ✅ Workspace size: 100MB max

### Credentials
- ✅ Short-lived (15min) credentials
- ✅ Read-only IAM role
- ✅ Runtime injection only
- ✅ Never persisted

## Quick Start

### Docker

```bash
docker-compose up -d
```

### Local Development

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Execution Flow

```
1. Receive execution request (job_id, workspace_reference)
2. Create isolated workspace: /tmp/terraform-workspaces/{job_id}/
3. Copy Terraform files
4. Validate configuration (security checks)
5. Execute:
   - terraform init -backend=false
   - terraform validate
   - terraform plan -out=tfplan
   - terraform show -json tfplan > plan.json
6. Upload plan.json to storage
7. Destroy workspace immediately
8. Return plan.json reference
```

## Internal API

**Base URL**: `http://localhost:8002/internal`

### Execute Terraform Plan

```bash
POST /internal/execute
Content-Type: application/json

{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "workspace_reference": "s3://bucket/uploads/550e8400.zip",
  "credentials": {
    "aws_access_key_id": "AKIA...",
    "aws_secret_access_key": "...",
    "aws_session_token": "..."
  }
}
```

**Response** (202 Accepted):
```json
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "plan_reference": "s3://bucket/plans/550e8400.json",
  "metadata": {
    "duration_ms": 12345,
    "cpu_usage": 1.5,
    "memory_mb": 512
  }
}
```

## Error Classification

| Error Type | Description |
|------------|-------------|
| `validation_error` | terraform validate failed |
| `provider_error` | Provider initialization failed |
| `execution_timeout` | Exceeded 300s timeout |
| `security_violation` | Blocked provisioner/data source |
| `resource_limit` | OOM or CPU limit exceeded |
| `unknown_error` | Unexpected error |

## Configuration

All via environment variables:

```env
TERRAFORM_VERSION=1.6.0
MAX_EXECUTION_TIME=300
CPU_LIMIT=2
MEMORY_LIMIT=2048
MAX_WORKSPACE_SIZE=100
ALLOWED_PROVIDERS=aws,random,null
BLOCK_LOCAL_EXEC=true
BLOCK_EXTERNAL_DATA=true
```

## Security Profiles

### Seccomp

Located at `security/seccomp.json` - restricts syscalls to safe subset.

### AppArmor

Located at `security/apparmor.profile` - additional process isolation.

## Observability

### Structured Logging

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "job_id": "550e8400...",
  "event": "terraform_execution",
  "stage": "plan",
  "duration_ms": 12345
}
```

## Deployment

### Kubernetes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: terraform-executor
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
    seccompProfile:
      type: Localhost
      localhostProfile: terraform-executor.json
  containers:
  - name: executor
    image: terraform-executor:latest
    securityContext:
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
    resources:
      limits:
        cpu: "2"
        memory: "2Gi"
      requests:
        cpu: "500m"
        memory: "512Mi"
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir:
      sizeLimit: 1Gi
```

## Quality Guarantees

✅ Killable instantly without side effects
✅ Survives malicious Terraform inputs
✅ Never leaks credentials
✅ Never writes outside sandbox
✅ Never blocks orchestrator
✅ Enforces strict resource limits
✅ Cleans up workspaces immediately

## Troubleshooting

### Execution Timeout
- Check `MAX_EXECUTION_TIME` setting
- Review Terraform plan complexity
- Check resource limits

### Security Violation
- Review Terraform files for local-exec
- Check for external data sources
- Verify provider allowlist

### Resource Limit Exceeded
- Increase `MEMORY_LIMIT` if needed
- Check workspace size
- Review Terraform resource count
