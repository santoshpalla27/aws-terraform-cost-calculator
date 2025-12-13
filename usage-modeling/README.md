# Usage Modeling Engine

Generates cost scenarios for cloud resources with explicit usage assumptions and environment-aware profiles.

## Overview

This engine models resource usage patterns, applies environment-specific profiles (dev/staging/prod), and generates min/expected/max cost scenarios with fully documented assumptions.

**Key Principle**: Every modeled cost must be explainable. No hidden assumptions.

## Features

- **Default Profiles**: Dev (22% uptime), Staging (49% uptime), Prod (100% uptime)
- **Resource Models**: EC2, S3, RDS, ELB with specific usage parameters
- **Scenarios**: Min (50%), Expected (100%), Max (150%) scaling
- **Overrides**: API and config file support with priority
- **Assumption Tracking**: Every parameter documented with source

## Usage Profiles

### Dev Profile
- **Uptime**: 160 hours/month (8h/day, 5 days/week)
- **Use Case**: Development and testing
- **Cost Optimization**: Prioritized over performance
- **Assumptions**:
  - Low traffic and data transfer
  - Minimal storage retention (1-day backups)
  - Non-production workloads

### Staging Profile
- **Uptime**: 360 hours/month (12h/day, 7 days/week)
- **Use Case**: Pre-production testing
- **Balance**: Cost and performance
- **Assumptions**:
  - Moderate traffic simulating production
  - Weekly backup retention
  - Higher availability than dev

### Prod Profile
- **Uptime**: 730 hours/month (24/7)
- **Use Case**: Production workloads
- **Availability**: 99.9% (three nines)
- **Assumptions**:
  - Production-level traffic
  - 30-day backup retention
  - Multi-AZ deployment

## API Endpoints

### Generate Scenarios

```http
POST /api/v1/scenarios
Content-Type: application/json

{
  "resource": {
    "resource_id": "aws_instance.web[0]",
    "resource_type": "aws_instance",
    "attributes": {
      "instance_type": "t3.medium"
    }
  },
  "profile": "prod",
  "overrides": {
    "uptime_hours_per_month": 500,
    "network_out_gb": 1000
  }
}
```

**Response:**
```json
{
  "resource_id": "aws_instance.web[0]",
  "profile": "prod",
  "scenarios": {
    "min": {
      "usage": {
        "compute_hours": 365,
        "network_out_gb": 250
      },
      "assumptions": [...],
      "scaling_factor": 0.5
    },
    "expected": {
      "usage": {
        "compute_hours": 730,
        "network_out_gb": 500
      },
      "assumptions": [
        {
          "parameter": "uptime_hours_per_month",
          "value": 730,
          "source": "profile:prod",
          "description": "Resources run 24/7 with high availability"
        }
      ],
      "scaling_factor": 1.0
    },
    "max": {
      "usage": {
        "compute_hours": 1095,
        "network_out_gb": 750
      },
      "assumptions": [...],
      "scaling_factor": 1.5
    }
  }
}
```

### List Profiles

```http
GET /api/v1/profiles
```

Returns: `["dev", "staging", "prod"]`

## Quick Start

```bash
cd usage-modeling
pip install -r requirements.txt
python -m app.main
```

Service available at: http://localhost:8005

## Resource Models

### EC2
- `uptime_hours_per_month`: Instance uptime
- `cpu_utilization`: Average CPU %
- `network_out_gb`: Data transfer out
- `ebs_volume_gb`: Root volume size

### S3
- `storage_gb`: Average storage size
- `requests_get`: GET requests/month
- `requests_put`: PUT requests/month
- `data_transfer_out_gb`: Data transfer

### RDS
- `uptime_hours_per_month`: Database uptime
- `storage_gb`: Database storage
- `backup_retention_days`: Backup retention
- `iops`: Provisioned IOPS

### ELB
- `uptime_hours`: Load balancer uptime
- `processed_gb`: Data processed
- `connections_per_second`: Avg connections/sec
- `lcu_hours`: LCU hours

## Override Mechanism

### Priority Order
1. **API Overrides** (highest priority)
2. **Config File Overrides**
3. **Profile Defaults** (lowest priority)

### Example with Overrides

```json
{
  "resource": {...},
  "profile": "prod",
  "overrides": {
    "ec2_uptime_hours": 500,
    "s3_storage_gb": 2000
  }
}
```

## Assumption Documentation

Every cost estimate includes:
- **Parameter**: What is being modeled
- **Value**: The value used
- **Source**: Where it came from (profile, override, metadata)
- **Description**: Why this value

Example:
```json
{
  "parameter": "uptime_hours_per_month",
  "value": 730,
  "source": "profile:prod",
  "description": "Resources run 24/7 with high availability"
}
```

## Separation of Concerns

- **Usage Modeling** (this engine): Usage patterns and assumptions
- **Pricing Engine**: Unit costs from AWS Price List API
- **Cost Calculation**: Usage × Pricing

## License

[Your License]
