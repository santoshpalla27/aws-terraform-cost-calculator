# Results Storage & Reporting Service

Persistent storage for cost estimation results with PostgreSQL, immutable records, and read-only APIs.

## Overview

This service stores job metadata and cost results with versioning, provides read-only APIs for UI consumption, supports historical comparisons, and ensures immutability.

**Key Principle**: Immutable records (INSERT-only). No recalculation on read.

## Features

- **Immutable Records**: INSERT-only pattern, no updates/deletes
- **PostgreSQL Storage**: Jobs, cost results, service/region aggregations
- **Read-Only APIs**: Fast retrieval for dashboards
- **Historical Comparisons**: Compare jobs over time
- **Denormalized Aggregations**: Fast service/region queries
- **Schema Versioning**: Alembic migrations for evolution

## Database Schema

### Tables

- **jobs**: Cost estimation jobs with metadata
- **cost_results**: Immutable resource costs
- **service_costs**: Denormalized service aggregations
- **region_costs**: Denormalized region aggregations

### Indexes

- `idx_jobs_created`: Fast recent jobs query
- `idx_jobs_user`: User-specific jobs
- `idx_cost_results_job`: Resource lookup by job
- `idx_cost_results_cost`: Top expensive resources

## API Endpoints

### Store Estimate

```http
POST /api/v1/store
Content-Type: application/json

{
  "estimate": {
    "total_monthly_cost": 1234.56,
    "confidence_score": 0.85,
    "by_resource": [...],
    "by_service": [...],
    "by_region": [...]
  },
  "user_id": "user123",
  "terraform_plan_hash": "abc123"
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Get Job

```http
GET /api/v1/jobs/{job_id}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2023-12-13T10:30:00",
  "profile": "prod",
  "total_monthly_cost": 1234.56,
  "confidence_score": 0.85,
  "resource_count": 25,
  "status": "completed"
}
```

### List Jobs

```http
GET /api/v1/jobs?user_id=user123&limit=10
```

### Get Resources

```http
GET /api/v1/jobs/{job_id}/resources
```

### Get Services

```http
GET /api/v1/jobs/{job_id}/services
```

### Get Regions

```http
GET /api/v1/jobs/{job_id}/regions
```

### Compare Jobs

```http
GET /api/v1/compare?job_id_1={id1}&job_id_2={id2}
```

**Response:**
```json
{
  "job_1": {
    "job_id": "...",
    "total_cost": 1000.00,
    "created_at": "2023-12-01T10:00:00"
  },
  "job_2": {
    "job_id": "...",
    "total_cost": 1200.00,
    "created_at": "2023-12-13T10:00:00"
  },
  "delta": 200.00,
  "percentage_change": 20.0
}
```

## Quick Start

### Setup Database

```bash
createdb results
psql results < schema.sql
```

### Configure

Create `.env`:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/results
```

### Run Service

```bash
cd results-storage
pip install -r requirements.txt
python -m app.main
```

Service available at: http://localhost:8007

## Immutability Pattern

### INSERT-Only

```python
# ✅ Store new estimate
storage.store_estimate(estimate, user_id="user123")

# ❌ NEVER update existing records
# db.query(CostResult).filter_by(id=123).update({...})  # NOT ALLOWED
```

### Audit Trail

All records preserved for historical analysis.

## Query Patterns

### Recent Jobs

```sql
SELECT * FROM jobs
WHERE user_id = 'user123'
ORDER BY created_at DESC
LIMIT 10;
```

### Top Expensive Resources

```sql
SELECT * FROM cost_results
WHERE job_id = '...'
ORDER BY total_monthly_cost DESC
LIMIT 10;
```

### Service Breakdown

```sql
SELECT * FROM service_costs
WHERE job_id = '...'
ORDER BY total_cost DESC;
```

## Schema Evolution

### Alembic Migrations

```bash
# Create migration
alembic revision -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Backward Compatibility

- `schema_version` field in jobs table
- API versioning (/api/v1, /api/v2)
- Graceful handling of old schema

## Performance

- **Denormalized Tables**: service_costs, region_costs for fast aggregation
- **Indexes**: On job_id, created_at, user_id, total_monthly_cost
- **JSONB**: For flexible cost_drivers and assumptions

## License

[Your License]
