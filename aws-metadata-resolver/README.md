# AWS Metadata Resolver Service

## Overview

The **AWS Metadata Resolver** enriches Normalized Resource Graphs (NRG) with AWS-specific metadata that Terraform plans do NOT expose but which is REQUIRED for accurate cost estimation.

## Service Role (Non-Negotiable)

### DOES
- Call AWS Describe/List APIs (read-only)
- Resolve implicit billable AWS resources
- Fill missing attributes Terraform doesn't expose
- Produce Enriched Resource Graph (ERG)
- Cache AWS metadata aggressively

### DOES NOT
- Modify AWS resources
- Perform pricing calculations
- Execute Terraform
- Apply usage assumptions
- Perform orchestration
- Accept public traffic

## Why This Service Exists

Terraform plans describe **INTENT**, not **REAL AWS BEHAVIOR**.

AWS billing depends on:
- Defaults (EBS gp3 vs gp2, instance tenancy)
- Implicit resources (root EBS volumes, ENIs)
- Service-specific behavior
- Regional and account-level settings

This service bridges that gap.

## Architecture

```
NRG (from Plan Interpreter)
    ↓
AWS Metadata Resolver
    ├─→ Service Adapters (EC2, EBS, ELB)
    ├─→ AWS API Calls (with caching)
    ├─→ Implicit Resource Detection
    └─→ Dependency Graph Enrichment
    ↓
ERG (Enriched Resource Graph)
```

## Enrichment Logic

### 1. Resource Defaults

Resolves AWS defaults Terraform omits:

**EC2:**
- Default tenancy: `default`
- EBS optimization: Based on instance family
- Monitoring: `false` (unless enabled)

**EBS:**
- Volume type: `gp3` (current AWS default)
- IOPS: `3000` (gp3 default)
- Throughput: `125 MB/s` (gp3 default)
- Encryption: `false`

**ELB:**
- Load balancer type: `application` (if not specified)
- Cross-zone load balancing: `true` for ALB, `false` for NLB
- Deletion protection: `false`

### 2. Implicit Billable Resources

Identifies resources NOT explicitly declared but ARE billable:

**EC2 Instance creates:**
- **Root EBS Volume**: 8GB gp3 by default
- **Primary ENI**: One per instance

**Future:**
- NAT Gateway data processing
- CloudWatch baseline logs/metrics
- ALB/NLB LCUs

### 3. Provenance Tracking

Each resource is tagged with its source:
- `TERRAFORM`: Explicitly declared in Terraform
- `IMPLICIT`: Implicitly created by AWS
- `DERIVED`: Derived from AWS API calls

## API Specification

### POST /internal/enrich

**Request:**
```json
{
  "normalized_resource_graph": [
    {
      "resource_id": "a1b2c3d4",
      "terraform_address": "aws_instance.web",
      "resource_type": "aws_instance",
      "provider": "aws",
      "region": "us-east-1",
      "attributes": {"instance_type": "t3.micro"},
      "unknown_attributes": [],
      "quantity": 1,
      "module_path": [],
      "dependencies": [],
      "confidence_level": "HIGH"
    }
  ],
  "aws_account_id": "123456789012"
}
```

**Response:**
```json
{
  "enriched_resource_graph": [
    {
      "resource_id": "a1b2c3d4",
      "terraform_address": "aws_instance.web",
      "resource_type": "aws_instance",
      "enriched_attributes": {
        "tenancy": "default",
        "ebs_optimized": true,
        "monitoring": false
      },
      "provenance": "terraform",
      "confidence_level": "HIGH"
    },
    {
      "resource_id": "implicit_001",
      "terraform_address": null,
      "resource_type": "aws_ebs_volume",
      "provenance": "implicit",
      "parent_resource_id": "a1b2c3d4"
    }
  ],
  "enrichment_metadata": {
    "total_resources": 3,
    "terraform_resources": 1,
    "implicit_resources": 2,
    "cache_hit_rate": 0.75,
    "enrichment_duration_ms": 150
  }
}
```

### GET /internal/health

**Response:**
```json
{
  "status": "healthy",
  "service": "aws-metadata-resolver",
  "cache_enabled": true
}
```

## Configuration

All configuration via environment variables:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ROLE_ARN=arn:aws:iam::123456789012:role/TerraformCostCalculatorReadOnly

# Cache Configuration
REDIS_URL=redis://localhost:6379/0
METADATA_CACHE_TTL=3600
ENABLE_CACHE=true

# API Configuration
MAX_API_RETRIES=3
API_RETRY_BACKOFF=2

# Service Adapters (comma-separated)
ENABLE_SERVICE_ADAPTERS=ec2,ebs,elb

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## IAM Policy (Read-Only)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "elasticloadbalancing:Describe*",
        "rds:Describe*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Deny",
      "Action": [
        "*:Create*",
        "*:Delete*",
        "*:Update*"
      ],
      "Resource": "*"
    }
  ]
}
```

See `iam-policy.json` for complete policy.

## Running Locally

### Prerequisites
- Python 3.11+
- Redis (optional, falls back to in-memory cache)
- AWS credentials with read-only access

### Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your AWS configuration
```

3. **Run the service:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

4. **Access API docs:**
```
http://localhost:8000/docs
```

## Running with Docker

### Build and run:
```bash
docker-compose up --build
```

### Access service:
```
http://localhost:8004
```

## Cache Strategy

### Why Caching?
- AWS APIs are slow (100-500ms per call)
- Rate limits are strict (varies by service)
- Metadata changes infrequently

### Cache Key Format
```
{account_id}:{region}:{service}:{resource_type}:{resource_id}
```

Example: `123456789012:us-east-1:ec2:instance:i-1234567890abcdef0`

### TTL
- Default: 1 hour (3600s)
- Configurable via `METADATA_CACHE_TTL`

### Backends
1. **Redis** (preferred): Distributed cache, survives restarts
2. **In-Memory**: Fallback, LRU eviction

## Service Adapters

### EC2 Adapter
- Resolves instance tenancy defaults
- Detects implicit root EBS volumes
- Detects implicit ENIs
- Determines EBS optimization by instance family

### EBS Adapter
- Resolves volume type defaults (gp3)
- Resolves default IOPS/throughput
- Resolves encryption defaults

### ELB Adapter
- Detects ALB vs NLB
- Resolves cross-zone load balancing defaults
- Resolves deletion protection defaults

## Error Handling

### Missing Permissions
```json
{
  "detail": "AccessDenied: User is not authorized to perform ec2:DescribeInstances"
}
```
**HTTP 500**

### Throttling
- Automatic retry with exponential backoff
- Max retries: 3 (configurable)
- Backoff: 2^attempt seconds

### Partial Enrichment
- Service continues on individual resource failures
- Failed resources returned without enrichment
- Metadata includes `failed_count`

## Observability

### Structured Logging (JSON)
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "app.enrichment.orchestrator",
  "message": "Enrichment complete: 15 total resources",
  "terraform_resources": 10,
  "implicit_resources": 5,
  "cache_hit_rate": 0.75,
  "duration_ms": 150
}
```

### Metrics
- Cache hit/miss rate
- AWS API call count
- Enrichment duration per resource type
- Implicit resource detection rate

## Security

- **Read-Only**: Explicit deny for all write operations
- **Short-Lived Credentials**: STS AssumeRole (15 min)
- **No Persistence**: Credentials never written to disk
- **No Secrets in Logs**: Credentials scrubbed from logs
- **Non-Root Container**: Runs as user `resolver` (UID 1000)

## Integration

### Called By
- **Job Orchestrator** (after Plan Interpreter)

### Calls
- AWS APIs (read-only)

### Data Flow
```
Job Orchestrator
    │
    ├─▶ POST /internal/enrich
    │   (NRG from Plan Interpreter)
    │
    ◀─── ERG + metadata
```

## Extending

### Adding a New Service Adapter

1. Create `app/adapters/{service}.py`
2. Extend `BaseServiceAdapter`
3. Implement `enrich()` and `detect_implicit_resources()`
4. Register in `EnrichmentOrchestrator._initialize_adapters()`
5. Add to `ENABLE_SERVICE_ADAPTERS` config

Example:
```python
class RDSAdapter(BaseServiceAdapter):
    def _get_service_name(self) -> str:
        return "rds"
    
    async def enrich(self, node: ERGNode, account_id: str) -> ERGNode:
        # Add RDS-specific enrichment
        return node
    
    async def detect_implicit_resources(self, node: ERGNode, account_id: str) -> List[ERGNode]:
        # Detect implicit RDS resources
        return []
```

## Project Structure

```
aws-metadata-resolver/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Configuration
│   ├── schemas/
│   │   ├── erg.py                 # ERG schema
│   │   └── api.py                 # API models
│   ├── adapters/
│   │   ├── base.py                # Base adapter
│   │   ├── ec2.py                 # EC2 adapter
│   │   ├── ebs.py                 # EBS adapter
│   │   └── elb.py                 # ELB adapter
│   ├── cache/
│   │   ├── interface.py           # Cache interface
│   │   ├── redis_cache.py         # Redis implementation
│   │   └── memory_cache.py        # In-memory fallback
│   ├── aws/
│   │   ├── client_manager.py      # AWS client manager
│   │   └── retry_handler.py       # Retry logic
│   ├── enrichment/
│   │   └── orchestrator.py        # Main orchestrator
│   ├── routers/
│   │   └── internal.py            # API routes
│   └── utils/
│       └── logger.py              # Logging
├── Dockerfile
├── docker-compose.yml
├── iam-policy.json
├── requirements.txt
├── .env.example
└── README.md
```

## License

Proprietary - Internal Use Only

## Support

For issues or questions, contact the platform team.

---

**Last Updated**: 2024-12-23  
**Version**: 1.0.0  
**Maintainer**: Platform Engineering Team
