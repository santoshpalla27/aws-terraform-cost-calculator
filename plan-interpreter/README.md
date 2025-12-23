# Terraform Plan Interpreter Service

## Overview

The **Terraform Plan Interpreter** is the "semantic brain" of the AWS Terraform Cost Calculator platform. It parses `terraform show -json` output and produces a **Normalized Resource Graph (NRG)** — a deterministic, cloud-agnostic representation of infrastructure resources.

## Service Role (Non-Negotiable)

### MUST DO
- Parse `terraform show -json` output
- Resolve Terraform semantics (count, for_each, modules, conditionals)
- Produce deterministic Normalized Resource Graph (NRG)
- Handle unknown/computed values explicitly
- Maintain 100% determinism (same input → same output)

### MUST NOT
- Execute Terraform CLI
- Call AWS APIs
- Fetch pricing data
- Apply usage assumptions
- Perform orchestration
- Persist results long-term
- Accept public internet traffic

## Why This Service Exists

Terraform's plan JSON is complex and contains:
- **Resource multiplicity** (`count`, `for_each`)
- **Module nesting** (deeply nested module paths)
- **Conditional resources** (resources that may not be created)
- **Unknown values** (computed attributes)
- **Provider-specific syntax**

This service **eliminates Terraform complexity** and produces a clean, stable graph that downstream services (enrichment, costing) can consume without understanding Terraform semantics.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Terraform Plan Interpreter                  │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Parser     │───▶│ Multiplicity │───▶│ NRG Builder  │  │
│  │              │    │  Resolver    │    │              │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                    │          │
│         ▼                    ▼                    ▼          │
│  Extract Resources    Resolve count/       Build NRG Nodes  │
│  from plan JSON       for_each instances   with metadata    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                   Normalized Resource Graph (NRG)
```

## Normalized Resource Graph (NRG)

### NRG Schema

Each **NRG Node** represents a single, real resource instance:

```json
{
  "resource_id": "a1b2c3d4e5f6g7h8",
  "terraform_address": "module.vpc.aws_subnet.private[0]",
  "resource_type": "aws_subnet",
  "provider": "aws",
  "region": "us-east-1",
  "attributes": {
    "cidr_block": "10.0.1.0/24",
    "availability_zone": "us-east-1a"
  },
  "unknown_attributes": ["id", "arn"],
  "quantity": 1,
  "module_path": ["module.vpc"],
  "dependencies": ["module.vpc.aws_vpc.main"],
  "confidence_level": "HIGH"
}
```

### Confidence Levels

- **HIGH**: ≥90% of attributes are known
- **MEDIUM**: 50-89% of attributes are known
- **LOW**: <50% of attributes are known

## Terraform Semantics Resolution

### 1. Dependency Extraction

**Source**: `resource_changes[].change.after_depends_on` (or `before_depends_on`)

**Process**:
1. Parse `resource_changes` section from plan JSON
2. Extract `depends_on` lists for each resource
3. Map Terraform addresses to NRG resource IDs
4. Populate `dependencies` field in each NRG node

**Rules**:
- Dependencies reference NRG resource IDs, not Terraform addresses
- Missing dependencies are logged and skipped (non-fatal)
- Circular dependencies are preserved
- Dependency order is deterministic

**Example**:
```json
{
  "resource_id": "a1b2c3d4e5f6g7h8",
  "terraform_address": "aws_instance.web",
  "dependencies": ["b2c3d4e5f6g7h8i9", "c3d4e5f6g7h8i9j0"]
}
```

### 2. Resource Multiplicity

**count example:**
```hcl
resource "aws_instance" "web" {
  count = 3
  instance_type = "t3.micro"
}
```

**NRG Output:** 3 separate nodes
- `aws_instance.web[0]`
- `aws_instance.web[1]`
- `aws_instance.web[2]`

**for_each example:**
```hcl
resource "aws_instance" "web" {
  for_each = {
    prod = "t3.large"
    dev  = "t3.micro"
  }
  instance_type = each.value
}
```

**NRG Output:** 2 separate nodes
- `aws_instance.web["prod"]`
- `aws_instance.web["dev"]`

### 3. Module Flattening

**Terraform:**
```
module.vpc.module.subnets.aws_subnet.private[0]
```

**NRG:**
- `terraform_address`: `module.vpc.module.subnets.aws_subnet.private[0]`
- `module_path`: `["module.vpc", "module.subnets"]`
- `module_depth`: `2`

### 4. Unknown/Computed Values

Attributes that are `null` in the plan JSON are marked as **unknown**:

```json
{
  "attributes": {
    "instance_type": "t3.micro"
  },
  "unknown_attributes": ["id", "public_ip", "arn"]
}
```

**Never guess or default unknown values.**

### 5. Conditionals

Resources not planned for creation (due to `count = 0` or conditional logic) **do not appear in NRG**.

We use the plan's evaluation results only — no re-evaluation.

## API Specification

### POST /internal/interpret

**Request:**
```json
{
  "plan_json_reference": "file:///path/to/plan.json"
}
```

**Note**: Plan JSON is loaded from reference, not sent inline. Supports `file://` protocol.

**Response:**
```json
{
  "normalized_resource_graph": [
    {
      "resource_id": "...",
      "terraform_address": "...",
      "resource_type": "...",
      "provider": "...",
      "region": "...",
      "attributes": {},
      "unknown_attributes": [],
      "quantity": 1,
      "module_path": [],
      "dependencies": [],
      "confidence_level": "HIGH"
    }
  ],
  "interpretation_metadata": {
    "plan_hash": "a1b2c3d4e5f6g7h8",
    "total_resources": 10,
    "resources_by_type": {
      "aws_instance": 3,
      "aws_s3_bucket": 2
    },
    "unknown_value_count": 15,
    "module_depth": 2,
    "interpretation_timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### GET /internal/health

**Response:**
```json
{
  "status": "healthy",
  "service": "plan-interpreter"
}
```

## Tech Stack

- **Python 3.11**
- **FastAPI** (internal APIs only)
- **Pydantic v2** (schema validation)
- **Pure CPU-bound** (no network calls)
- **Deterministic** (same input → same output)
- **Containerized** (non-root user)

## Project Structure

```
plan-interpreter/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Configuration
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── nrg.py                 # NRG schema
│   │   └── api.py                 # API request/response models
│   ├── interpreter/
│   │   ├── __init__.py
│   │   ├── nrg_builder.py         # Main NRG builder
│   │   ├── multiplicity.py        # count/for_each resolution
│   │   └── utils.py               # Utilities
│   ├── routers/
│   │   ├── __init__.py
│   │   └── internal.py            # Internal API routes
│   └── utils/
│       ├── __init__.py
│       └── logger.py              # Structured logging
├── tests/
│   ├── __init__.py
│   ├── test_multiplicity.py       # Multiplicity tests
│   ├── test_nrg_builder.py        # NRG builder tests
│   └── test_api.py                # API tests
├── examples/
│   ├── simple_plan.json           # Example plan
│   └── simple_nrg.json            # Example NRG output
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── .env.example
├── .dockerignore
├── .gitignore
└── README.md
```

## Running Locally

### Prerequisites
- Python 3.11+
- Docker (optional)

### Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env if needed
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
http://localhost:8003
```

## Testing

### Run all tests:
```bash
pytest
```

### Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file:
```bash
pytest tests/test_nrg_builder.py -v
```

## Determinism Guarantees

1. **Resource IDs**: Generated via SHA256 hash of Terraform address
2. **Plan Hash**: Canonical JSON serialization (sorted keys)
3. **No randomness**: No UUIDs, timestamps in IDs, or random values
4. **Same input → Same output**: Always

## Error Handling

### Invalid Plan JSON
```json
{
  "detail": "Invalid plan JSON structure: missing key 'planned_values'"
}
```
**HTTP 400 Bad Request**

### Interpretation Failure
```json
{
  "detail": "Interpretation failed: <error message>"
}
```
**HTTP 500 Internal Server Error**

## Performance

- **Pure CPU-bound**: No I/O blocking
- **Async-ready**: FastAPI async handlers
- **Memory-efficient**: Streaming JSON parsing (future enhancement)
- **Fast**: Typical plan (100 resources) < 100ms

## Observability

### Structured Logging (JSON)
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "app.interpreter.nrg_builder",
  "message": "NRG build complete: 42 nodes",
  "total_resources": 42,
  "resources_by_type": {"aws_instance": 10},
  "unknown_count": 15
}
```

### Metrics (Future)
- Interpretation duration
- Plan size (bytes)
- Resource count
- Unknown value ratio

## Security

- **No external network calls**
- **No file system writes** (except logs)
- **Non-root container user**
- **Read-only root filesystem** (future)
- **No shell execution**
- **Input validation** (Pydantic)

## Integration

### Called By
- **Job Orchestrator** (after Terraform execution)

### Calls
- None (pure function)

### Data Flow
```
Job Orchestrator
    │
    ├─▶ POST /internal/interpret
    │   (plan_json_reference)
    │
    ◀─── NRG + metadata
```

## Future Enhancements

1. **Dependency Graph Extraction**: Parse `resource_changes` for explicit dependencies
2. **Streaming JSON Parsing**: Handle very large plans (>100MB)
3. **Provider-Specific Parsers**: Custom logic for complex providers
4. **Validation Rules**: Detect invalid resource configurations
5. **Cost Hints**: Extract attributes relevant for pricing

## Contributing

### Code Style
- **Black** for formatting
- **isort** for imports
- **mypy** for type checking
- **pylint** for linting

### Testing Requirements
- **100% coverage** for core logic
- **Determinism tests** mandatory
- **Golden test cases** for regression

## License

Proprietary - Internal Use Only

## Support

For issues or questions, contact the platform team.

---

**Last Updated**: 2024-01-15  
**Version**: 1.0.0  
**Maintainer**: Platform Engineering Team
