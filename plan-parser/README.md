# Terraform Plan Parser

Converts Terraform plan JSON into a Normalized Resource Graph (NRG) for cloud-agnostic cost estimation.

## Overview

This service parses Terraform plan JSON output and produces a deterministic, normalized resource graph that:
- Fully resolves `count` and `for_each` meta-arguments
- Flattens module hierarchy while preserving relationships
- Calculates confidence scores based on known vs. computed attributes
- Works with any cloud provider (AWS, Azure, GCP, etc.)
- Contains NO pricing logic

## NRG Schema

### Resource Structure

```json
{
  "resource_id": "aws_instance.web[0]",
  "resource_type": "aws_instance",
  "provider": "aws",
  "region": "us-east-1",
  "quantity": 1,
  "module_path": ["root", "web_servers"],
  "attributes": {
    "ami": "ami-0c55b159cbfafe1f0",
    "instance_type": "t3.medium"
  },
  "computed_attributes": ["id", "public_ip"],
  "confidence": 0.85,
  "parent_id": null,
  "children": [],
  "metadata": {
    "action": "create"
  }
}
```

### Complete NRG

```json
{
  "resources": [ /* array of resources */ ],
  "metadata": {
    "total_resources": 10,
    "providers": ["aws", "azurerm"],
    "regions": ["us-east-1", "eastus"],
    "modules": ["root", "web_servers"],
    "resource_types": {
      "aws_instance": 5,
      "aws_s3_bucket": 3
    }
  },
  "terraform_version": "1.6.6",
  "format_version": "1.2"
}
```

## Features

### Count Resolution

**Input:**
```json
{
  "address": "aws_instance.servers",
  "change": {
    "after": {
      "count": 3,
      "instance_type": "t3.medium"
    }
  }
}
```

**Output:** 3 separate resources
```
aws_instance.servers[0]
aws_instance.servers[1]
aws_instance.servers[2]
```

### For_each Resolution

**Input:**
```json
{
  "address": "aws_instance.servers",
  "change": {
    "after": {
      "for_each": {"web": {}, "api": {}, "worker": {}},
      "instance_type": "t3.medium"
    }
  }
}
```

**Output:** 3 separate resources
```
aws_instance.servers["web"]
aws_instance.servers["api"]
aws_instance.servers["worker"]
```

### Module Flattening

**Input:**
```
module.web_servers.module.load_balancer.aws_lb.main
```

**Output:**
```json
{
  "resource_id": "module.web_servers.module.load_balancer.aws_lb.main",
  "module_path": ["root", "web_servers", "load_balancer"]
}
```

### Confidence Calculation

Confidence score (0.0-1.0) based on:
- **70%**: Known attributes / Total attributes
- **30%**: Critical attributes known / Critical attributes total

**Critical Attributes:**
- `aws_instance`: `instance_type`, `ami`
- `aws_db_instance`: `instance_class`, `engine`, `allocated_storage`
- `aws_s3_bucket`: `bucket`
- `azurerm_virtual_machine`: `vm_size`
- `google_compute_instance`: `machine_type`

## API Endpoints

### Parse Plan

```http
POST /api/v1/parse
Content-Type: application/json

{
  "plan_json": {
    "format_version": "1.2",
    "terraform_version": "1.6.6",
    "resource_changes": [...]
  }
}
```

**Response:**
```json
{
  "resources": [...],
  "metadata": {...},
  "terraform_version": "1.6.6",
  "format_version": "1.2"
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
  "version": "1.0.0"
}
```

## Quick Start

### Local Development

```bash
cd plan-parser
pip install -r requirements.txt
python -m app.main
```

Service available at: http://localhost:8002

### API Documentation

- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

## Examples

See `examples/` directory for:
- `input/simple.json` - Simple resources
- `input/count.json` - Count example
- `input/for_each.json` - For_each example
- `input/module.json` - Module example
- `output/` - Corresponding NRG outputs

## Testing

```bash
pytest tests/ -v
```

**Test Coverage:**
- Simple resource parsing
- Count resolution
- For_each resolution
- Module flattening
- Metadata generation
- Confidence calculation

## Architecture

```
┌─────────────────────────┐
│ Terraform Plan JSON     │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│ TerraformPlanParser     │
│                         │
│  ┌──────────────────┐   │
│  │ CountResolver    │   │
│  │ ForEachResolver  │   │
│  │ ModuleResolver   │   │
│  └──────────────────┘   │
│                         │
│  ┌──────────────────┐   │
│  │ AttributeExtractor│  │
│  └──────────────────┘   │
│                         │
│  ┌──────────────────┐   │
│  │ ConfidenceCalc   │   │
│  └──────────────────┘   │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│ Normalized Resource     │
│ Graph (NRG)             │
└─────────────────────────┘
```

## Design Principles

### Cloud-Agnostic

- No AWS-specific logic
- Provider extracted from `provider_name`
- Region extraction is provider-aware:
  - AWS: `region` or `availability_zone`
  - Azure: `location`
  - GCP: `zone` or `region`

### Deterministic

- Same input always produces same output
- No external dependencies
- No state or side effects

### Extensible

- Easy to add new providers
- Pluggable confidence calculation
- Modular resolver architecture

## Integration

This parser integrates with:
1. **Terraform Executor** - Receives plan JSON
2. **Metadata Resolver** - Consumes NRG for enrichment
3. **Pricing Engine** - Uses NRG for cost calculation

## License

[Your License]
