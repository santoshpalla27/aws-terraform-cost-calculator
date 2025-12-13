# AWS Pricing Engine

Retrieves and normalizes AWS pricing data from AWS Price List API with PostgreSQL caching.

## Overview

This engine ingests pricing data from AWS Price List API, normalizes it into PostgreSQL tables, versions snapshots, and provides deterministic pricing lookups for cost estimation.

**Source of Truth**: AWS Price List API (no hardcoded prices or static JSON files)

## Features

- **AWS Price List API Integration**: Fetches pricing from official AWS API
- **PostgreSQL Storage**: Normalized schema (services, products, dimensions, snapshots)
- **Version Snapshots**: Historical pricing data with versioning
- **Deterministic Lookups**: SKU-based pricing resolution with attribute matching
- **Unit Conversion**: Hourly, GB-month, requests, IOPS
- **Batch Ingestion**: Efficient bulk inserts for large datasets (~1M+ SKUs)

## Database Schema

```sql
services
├── id
├── service_code (AmazonEC2)
└── service_name

products
├── id
├── service_id → services.id
├── sku (unique)
├── product_family
├── attributes (JSONB)
├── region
└── location

pricing_dimensions
├── id
├── product_id → products.id
├── rate_code
├── unit
├── price_per_unit
├── begin_range (tiered pricing)
├── end_range (tiered pricing)
├── term_type (OnDemand, Reserved)
└── effective_date

pricing_snapshots
├── id
├── snapshot_date
├── version
├── services_count
├── products_count
└── status
```

## API Endpoints

### Lookup Pricing

```http
POST /api/v1/lookup
Content-Type: application/json

{
  "service_code": "AmazonEC2",
  "region": "us-east-1",
  "attributes": {
    "instanceType": "t3.medium",
    "operatingSystem": "Linux",
    "tenancy": "Shared"
  },
  "term_type": "OnDemand"
}
```

**Response:**
```json
{
  "sku": "SKU123",
  "product_family": "Compute Instance",
  "region": "us-east-1",
  "unit": "hour",
  "price_per_unit": 0.0416,
  "currency": "USD",
  "term_type": "OnDemand",
  "description": "$0.0416 per On Demand Linux t3.medium Instance Hour",
  "effective_date": "2023-12-01T00:00:00"
}
```

### Trigger Ingestion

```http
POST /api/v1/ingest
```

Starts background ingestion of pricing data for all configured services.

### Health Check

```http
GET /health
```

## Quick Start

### Setup Database

```bash
# Create PostgreSQL database
createdb pricing

# Run schema
psql pricing < schema.sql
```

### Configure

Create `.env` file:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pricing
TARGET_SERVICES=AmazonEC2,AmazonS3,AmazonRDS,AmazonEKS,AWSELB
```

### Run Service

```bash
cd pricing-engine
pip install -r requirements.txt
python -m app.main
```

Service available at: http://localhost:8004

### Ingest Pricing

```bash
curl -X POST http://localhost:8004/api/v1/ingest
```

## Pricing Ingestion Workflow

1. **Fetch Service Index** from AWS Price List API
2. **For each service**:
   - Download offer file (JSON, ~100MB-1GB per service)
   - Parse products and SKUs
   - Extract pricing dimensions
   - Normalize units
   - Batch insert into PostgreSQL
3. **Create pricing snapshot** with version
4. **Mark snapshot as active**

**Duration**: ~30-60 minutes for full ingestion

## Unit Conversion

Supported units:
- **Time**: Hrs, Hour → normalized to `hour`
- **Storage**: GB-Mo, GB-Month, TB-Mo → normalized to `GB-month`
- **Requests**: Requests, 1M requests → normalized to `request`
- **Data Transfer**: GB, TB → normalized to `GB`
- **IOPS**: IOPS, IOPS-Mo → normalized to `IOPS`

## Example Lookups

### EC2 Instance

```python
lookup_price(
    service_code="AmazonEC2",
    region="us-east-1",
    attributes={
        "instanceType": "t3.medium",
        "operatingSystem": "Linux",
        "tenancy": "Shared"
    }
)
# Returns: $0.0416/hour
```

### S3 Storage

```python
lookup_price(
    service_code="AmazonS3",
    region="us-east-1",
    attributes={
        "storageClass": "Standard",
        "volumeType": "Standard"
    }
)
# Returns: $0.023/GB-month
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgresql://... | PostgreSQL connection |
| `TARGET_SERVICES` | EC2, S3, RDS, EKS, ELB | Services to ingest |
| `BATCH_SIZE` | 1000 | Batch insert size |
| `PRICE_LIST_BASE_URL` | https://pricing... | AWS Price List API URL |

## Performance

- **Data Volume**: ~1M+ SKUs across all services
- **Ingestion Time**: 30-60 minutes (full), 5-10 minutes (incremental)
- **Lookup Time**: <10ms (indexed queries)
- **Storage**: ~5-10GB for full pricing data

## License

[Your License]
