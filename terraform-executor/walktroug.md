Terraform Execution Service Walkthrough
Overview
Successfully implemented a secure, sandboxed Terraform execution service that executes untrusted Terraform code in an isolated container environment and returns deterministic plan JSON.

What Was Built
Secure Container Infrastructure
1. Dockerfile (
Dockerfile
)
Multi-stage build: Separate stages for Terraform download and runtime
Minimal base: Alpine Linux 3.19 for small attack surface
Terraform 1.6.6: Official HashiCorp binary
Non-root user: UID 1000 (tfuser)
Security: No shell, minimal dependencies
Health check: Built-in container health monitoring
2. Docker Compose (
docker-compose.yml
)
Read-only filesystem: Root filesystem mounted read-only
Tmpfs mounts: Writable /tmp (256MB) and .terraform.d (128MB)
Resource limits: 512MB RAM, 1 CPU core
Security options: no-new-privileges, dropped capabilities
Volume mounts: Shared uploads directory with API gateway
Core Application
3. Configuration (
config.py
)
Pydantic Settings for environment-based config
Execution timeout (default: 300s)
Workspace directory configuration
Security settings (blocked providers, network access)
Upload directory configuration
4. Data Models (
models.py
)
ExecutionStatus enum (SUCCESS, FAILED, TIMEOUT)
ExecutionRequest: Job ID and upload ID
ExecutionResponse: Plan JSON, status, errors, timing
HealthCheckResponse: Service health and Terraform version
Execution Engine
5. Terraform Executor (
executor.py
)
4-Step Execution Flow:

terraform init -backend=false: Initialize without backend
terraform validate: Validate configuration
terraform plan -out=tfplan: Generate plan file
terraform show -json tfplan: Export plan as JSON
Features:

Workspace isolation via context manager
Security validation before execution
Timeout enforcement (subprocess timeout)
Comprehensive error handling
Structured logging of all steps
Output capture and parsing
6. Security Validator (
security.py
)
Security Checks:

Provider filtering: Blocks local-exec, external, null (with provisioners)
Backend detection: Scans for backend "..." blocks
Provisioner detection: Blocks local-exec and remote-exec
Path sanitization: Removes .. and null bytes
Detection Method:

Regex pattern matching in all .tf files
Pre-execution validation
Fails fast before Terraform init
7. Plan Parser (
parser.py
)
Parses Terraform JSON plan output
Validates JSON structure
Extracts resource changes
Generates change summary (create/update/delete counts)
Error handling for malformed JSON
Utilities
8. Workspace Manager (
workspace.py
)
Creates isolated workspaces in tmpfs
Unique workspace IDs
File copying from upload directory
Automatic cleanup via context manager
Structured logging
9. Structured Logging (
logger.py
)
JSON formatted logs
Configurable log levels
Correlation tracking
Performance metrics
API Layer
10. FastAPI Application (
main.py
)
Endpoints:

POST /api/v1/execute - Execute Terraform and return plan JSON
GET /health - Health check with Terraform version
GET / - Service information
Features:

Lifespan events for startup/shutdown
Global executor instance
Comprehensive error handling
OpenAPI documentation
Request validation
Documentation
11. README (
README.md
)
Security model overview
Execution flow diagram
API documentation with examples
Configuration options
Deployment guide (Docker, Kubernetes)
Troubleshooting section
12. Security Documentation (
SECURITY.md
)
Comprehensive threat model
Attack surface analysis
Security controls documentation
Residual risks
Best practices
Incident response procedures
Compliance information
Testing
13. Test Configuration (
conftest.py
)
Pytest fixtures
Test client setup
Sample Terraform configurations:
Valid configuration
Dangerous configuration (local-exec)
Backend configuration
14. Security Tests (
test_security.py
)
Valid configuration validation
Blocked provider detection
Backend detection
Path sanitization
15. Executor Tests (
test_executor.py
)
Executor initialization
Terraform version check
Security validation enforcement
Backend blocking enforcement
16. API Tests (
test_api.py
)
Health check endpoint
Root endpoint
Execute endpoint validation
Test Fixtures
17. Valid Configuration (
valid/main.tf
)
AWS provider with skip credentials
EC2 instance
S3 bucket
RDS database
Proper tags
18. Dangerous Configuration (
dangerous/local-exec.tf
)
Null resource with local-exec provisioner
Should be blocked by security validator
19. Backend Configuration (
backend/main.tf
)
S3 backend configuration
Should be blocked by security validator
Security Model Verification
Container Isolation ✅
# Read-only filesystem
read_only: true
# Writable tmpfs only
tmpfs:
  - /tmp:size=256m
  - /home/tfuser/.terraform.d:size=128m
# Resource limits
mem_limit: 512m
cpus: 1.0
# Security options
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
Provider Filtering ✅
Blocked Providers:

❌ local-exec (provisioner)
❌ remote-exec (provisioner)
❌ external (provider)
❌ null (with provisioners)
Allowed Providers:

✅ aws
✅ azure
✅ google
✅ Other standard providers
Backend Blocking ✅
All backend configurations are detected and blocked:

terraform {
  backend "s3" { ... }  # ❌ BLOCKED
}
Timeout Enforcement ✅
Default: 300 seconds (5 minutes)
Enforced via subprocess timeout
Returns TIMEOUT status
Kills subprocess on timeout
Execution Flow Diagram
┌─────────────────────────────────────────────────┐
│ 1. API Gateway sends execution request         │
│    {job_id, upload_id}                          │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ 2. Create isolated workspace in /tmp           │
│    workspace_id: ws_abc123                      │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ 3. Copy Terraform files to workspace           │
│    Source: /uploads/{upload_id}                 │
│    Dest: /tmp/workspace/ws_abc123               │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ 4. Security Validation                          │
│    ✓ Check for dangerous providers              │
│    ✓ Check for backend config                   │
│    ✓ Check for provisioners                     │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────▼────────┐
        │  Valid?         │
        └─┬──────────────┬┘
          │ No           │ Yes
          │              │
┌─────────▼──────┐      ┌▼────────────────────────┐
│ Return ERROR   │      │ 5. terraform init       │
│ Status: FAILED │      │    -backend=false       │
└────────────────┘      └┬────────────────────────┘
                         │
                ┌────────▼────────────────────────┐
                │ 6. terraform validate           │
                └┬────────────────────────────────┘
                 │
                ┌▼────────────────────────────────┐
                │ 7. terraform plan -out=tfplan   │
                └┬────────────────────────────────┘
                 │
                ┌▼────────────────────────────────┐
                │ 8. terraform show -json tfplan  │
                └┬────────────────────────────────┘
                 │
                ┌▼────────────────────────────────┐
                │ 9. Parse JSON                   │
                │    Validate structure           │
                └┬────────────────────────────────┘
                 │
                ┌▼────────────────────────────────┐
                │ 10. Cleanup workspace           │
                │     Remove all files            │
                └┬────────────────────────────────┘
                 │
                ┌▼────────────────────────────────┐
                │ 11. Return plan JSON            │
                │     Status: SUCCESS             │
                └─────────────────────────────────┘
Project Structure
terraform-executor/
├── app/
│   ├── __init__.py           # Package init
│   ├── main.py               # FastAPI application
│   ├── config.py             # Configuration
│   ├── models.py             # Data models
│   ├── executor.py           # Terraform executor
│   ├── security.py           # Security validator
│   ├── parser.py             # Plan JSON parser
│   └── utils/
│       ├── __init__.py
│       ├── logger.py         # Structured logging
│       └── workspace.py      # Workspace manager
├── tests/
│   ├── conftest.py           # Pytest config
│   ├── test_api.py           # API tests
│   ├── test_executor.py      # Executor tests
│   ├── test_security.py      # Security tests
│   └── fixtures/
│       ├── valid/            # Valid configs
│       ├── dangerous/        # Blocked configs
│       └── backend/          # Backend configs
├── Dockerfile                # Secure container
├── docker-compose.yml        # Local development
├── requirements.txt          # Python dependencies
├── README.md                 # Documentation
└── SECURITY.md               # Security documentation
Total Files Created: 22 files

How to Use
1. Start the Service
cd terraform-executor
docker-compose up --build
Service available at: http://localhost:8001

2. View API Documentation
Swagger UI: http://localhost:8001/docs
Health check: http://localhost:8001/health
3. Execute Terraform
curl -X POST http://localhost:8001/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "job_123abc",
    "upload_id": "upload_456def"
  }'
4. Response
Success:

{
  "job_id": "job_123abc",
  "status": "SUCCESS",
  "plan_json": {
    "format_version": "1.2",
    "terraform_version": "1.6.6",
    "resource_changes": [...]
  },
  "execution_time_seconds": 12.5
}
Blocked (Security):

{
  "job_id": "job_123abc",
  "status": "FAILED",
  "error_type": "ExecutionError",
  "error_message": "Security validation failed: Dangerous provisioner detected: local-exec"
}
Key Features Delivered
✅ Secure Execution

Read-only filesystem
Non-root user
Resource limits (512MB RAM, 1 CPU)
Timeout enforcement (5 min)
✅ Security Controls

Provider filtering (blocks dangerous providers)
Backend blocking (no state persistence)
Provisioner detection
Path sanitization
✅ Deterministic Output

4-step Terraform workflow
JSON plan output
Consistent results
No side effects
✅ Production-Ready

Containerized with Docker
Health checks
Structured logging
Comprehensive error handling
✅ Well-Documented

README with usage guide
SECURITY.md with threat model
OpenAPI documentation
Test suite
Integration with API Gateway
The Terraform Executor integrates with the API Gateway:

API Gateway receives Terraform upload
API Gateway creates job and calls executor
Executor processes Terraform in isolated container
Executor returns plan JSON to API Gateway
API Gateway stores results and updates job status
Shared Volume:

volumes:
  - ../api-gateway/uploads:/uploads:ro
Summary
Successfully delivered a secure, sandboxed Terraform execution service with:

🔒 Multi-layered security (container, provider filtering, backend blocking)
⚡ Deterministic execution (4-step workflow)
📊 Structured output (plan JSON)
🧪 Comprehensive test suite
📖 Detailed documentation
🐳 Production-ready containerization
🚀 Ready for deployment