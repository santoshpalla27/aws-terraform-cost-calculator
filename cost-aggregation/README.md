# Cost Aggregation Engine

Pure computation engine that aggregates costs from enriched resources, pricing, and usage models.

## Overview

This engine performs cost calculations (`cost = usage × pricing`), aggregates by resource/service/region, supports Terraform plan diffs, tracks cost drivers, and assigns confidence scores.

**Key Principle**: Pure computation only. No pricing assumptions or Terraform parsing.

## Features

- **Pure Computation**: `cost = usage × pricing`
- **Aggregations**: Per-resource, per-service, per-region
- **Terraform Diff**: Before vs after comparison
- **Cost Drivers**: Top cost contributors by component
- **Confidence Scoring**: Based on metadata/pricing/usage quality

## API Endpoints

### Generate Cost Estimate

```http
POST /api/v1/estimate
Content-Type: application/json

{
  "resources": [
    {
      "resource_id": "aws_instance.web[0]",
      "resource_type": "aws_instance",
      "region": "us-east-1",
      "sku": "SKU123"
    }
  ],
  "pricing_data": [
    {
      "sku": "SKU123",
      "price_per_unit": 0.0416,
      "storage_rate": 0.10,
      "data_transfer_rate": 0.09
    }
  ],
  "usage_data": [
    {
      "resource_id": "aws_instance.web[0]",
      "compute_hours": 730,
      "network_out_gb": 100,
      "ebs_storage_gb_month": 30
    }
  ],
  "profile": "prod"
}
```

**Response:**
```json
{
  "total_monthly_cost": 123.45,
  "confidence_score": 0.85,
  "profile": "prod",
  "by_resource": [
    {
      "resource_id": "aws_instance.web[0]",
      "service": "EC2",
      "region": "us-east-1",
      "compute_cost": 30.37,
      "storage_cost": 3.00,
      "network_cost": 9.00,
      "total_monthly_cost": 42.37,
      "confidence_score": 0.9,
      "cost_drivers": [
        {
          "component": "compute",
          "cost": 30.37,
          "percentage": 71.7,
          "description": "Compute costs"
        }
      ]
    }
  ],
  "by_service": [
    {
      "service": "EC2",
      "total_cost": 100.00,
      "resource_count": 5
    }
  ],
  "by_region": [
    {
      "region": "us-east-1",
      "total_cost": 123.45,
      "resource_count": 10,
      "services": {
        "EC2": 100.00,
        "S3": 23.45
      }
    }
  ]
}
```

### Calculate Cost Diff

```http
POST /api/v1/diff
Content-Type: application/json

{
  "before": {
    "resources": [...],
    "pricing_data": [...],
    "usage_data": [...]
  },
  "after": {
    "resources": [...],
    "pricing_data": [...],
    "usage_data": [...]
  }
}
```

**Response:**
```json
{
  "total_delta": 50.00,
  "percentage_change": 25.5,
  "added_resources": [
    {
      "resource_id": "aws_instance.new",
      "total_monthly_cost": 30.00
    }
  ],
  "removed_resources": [
    {
      "resource_id": "aws_instance.old",
      "total_monthly_cost": 20.00
    }
  ],
  "changed_resources": [
    {
      "resource_id": "aws_instance.web",
      "before_cost": 30.00,
      "after_cost": 60.00,
      "delta": 30.00,
      "percentage_change": 100.0
    }
  ],
  "added_cost": 30.00,
  "removed_cost": 20.00
}
```

## Quick Start

```bash
cd cost-aggregation
pip install -r requirements.txt
python -m app.main
```

Service available at: http://localhost:8006

## Cost Calculation

### Formula

```
cost = usage × pricing
```

### Components

- **Compute**: `compute_hours × price_per_hour`
- **Storage**: `storage_gb_month × storage_rate`
- **Network**: `network_out_gb × data_transfer_rate`
- **Other**: `requests × request_rate`

### Example

```python
# EC2 Instance
compute_cost = 730 hours × $0.0416/hour = $30.37
storage_cost = 30 GB × $0.10/GB = $3.00
network_cost = 100 GB × $0.09/GB = $9.00
total_cost = $42.37
```

## Aggregations

### By Resource
Individual resource costs with breakdown.

### By Service
Group by AWS service (EC2, S3, RDS, etc.).

### By Region
Group by AWS region (us-east-1, eu-west-1, etc.).

## Cost Drivers

Identifies top cost contributors:
- Compute costs
- Storage costs
- Network costs
- Other costs

Sorted by cost descending with percentage of total.

## Confidence Scoring

Score: 0.0 (low) to 1.0 (high)

**Factors:**
- **Metadata**: Enriched (0.9), Degraded (0.5), Default (0.7)
- **Pricing**: SKU match (0.95), Estimated (0.6)
- **Usage**: Override (0.95), Profile (0.8), Estimated (0.6)

**Overall**: Weighted average by resource cost.

## Input Dependencies

1. **Enriched Resources**: From metadata resolver
2. **Pricing Data**: From pricing engine
3. **Usage Data**: From usage modeling engine

## License

[Your License]
