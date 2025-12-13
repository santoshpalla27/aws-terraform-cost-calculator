Results Storage & Reporting Service Walkthrough
Overview
Successfully implemented a Results Storage & Reporting Service that provides persistent storage for cost estimation results with PostgreSQL, immutable records, read-only APIs, and historical comparisons.

What Was Built
Database Schema
1. PostgreSQL Schema (
schema.sql
)
Tables:

jobs:

job_id: UUID primary key
profile
: Usage profile (dev/staging/prod)
total_monthly_cost: Summary cost
confidence_score: Overall confidence
resource_count: Number of resources
schema_version: For evolution
cost_results:

Immutable resource costs
Cost breakdown (compute, storage, network, other)
JSONB for cost_drivers and assumptions
Foreign key to jobs
service_costs:

Denormalized service aggregations
Fast dashboard queries
Unique constraint on (job_id, service)
region_costs:

Denormalized region aggregations
JSONB for services breakdown
Unique constraint on (job_id, region)
Indexes:

idx_jobs_created: Recent jobs (DESC)
idx_jobs_user: User-specific jobs
idx_cost_results_job: Resource lookup
idx_cost_results_cost: Top expensive resources
SQLAlchemy Models
2. Models (
models.py
)
Job Model:

UUID job_id with auto-generation
Relationships to cost_results, service_costs, region_costs
Cascade delete for cleanup
CostResult Model:

Immutable cost record
DECIMAL for precise cost values
JSONB for flexible metadata
Indexed on job_id, service, region, cost
ServiceCost Model:

Denormalized aggregation
Fast service breakdown queries
RegionCost Model:

Denormalized aggregation
JSONB for service breakdown
Storage Service
3. Storage (
storage.py
)
Immutable INSERT-Only Pattern:

def store_estimate(estimate, user_id, terraform_plan_hash):
    # Create job
    job = Job(job_id=uuid.uuid4(), ...)
    db.add(job)
    
    # Store cost results (immutable)
    for resource in estimate["by_resource"]:
        cost_result = CostResult(...)
        db.add(cost_result)  # INSERT only
    
    # Store aggregations (denormalized)
    for service in estimate["by_service"]:
        service_cost = ServiceCost(...)
        db.add(service_cost)
    
    db.commit()
No Updates:

Never update existing records
Always create new records for changes
Preserves audit trail
API Layer
4. FastAPI Application (
main.py
)
Endpoints:

POST /api/v1/store:

Store cost estimate
Returns job_id
Immutable storage
GET /api/v1/jobs/{job_id}:

Get job summary
No recalculation
GET /api/v1/jobs:

List recent jobs
Filter by user_id
Pagination support
GET /api/v1/jobs/{job_id}/resources:

Get resource costs
Sorted by cost DESC
Fast query via index
GET /api/v1/jobs/{job_id}/services:

Service aggregation
Denormalized table
No JOIN required
GET /api/v1/jobs/{job_id}/regions:

Region aggregation
JSONB service breakdown
GET /api/v1/compare:

Compare two jobs
Calculate delta and percentage
Historical analysis
Key Features Delivered
✅ Immutable Records
INSERT-Only Pattern:

# ✅ Correct
storage.store_estimate(estimate)
# ❌ Never do this
db.query(CostResult).update({...})
Benefits:

Complete audit trail
Historical analysis
No data loss
✅ Read-Only APIs
No Recalculation:

Pre-computed results only
Fast retrieval
Consistent data
Example:

GET /api/v1/jobs/{job_id}/services
# Returns denormalized service_costs table
# No aggregation on read
✅ Historical Comparisons
Compare Jobs:

{
  "job_1": {"total_cost": 1000.00},
  "job_2": {"total_cost": 1200.00},
  "delta": 200.00,
  "percentage_change": 20.0
}
Trend Analysis:

Query jobs by date range
Track cost evolution
Identify anomalies
✅ Fast Dashboard Queries
Denormalized Tables:

service_costs: Pre-aggregated
region_costs: Pre-aggregated
No expensive JOINs
Indexes:

created_at DESC for recent jobs
total_monthly_cost DESC for top resources
job_id for fast lookups
✅ Schema Evolution
Alembic Migrations:

# alembic/versions/001_initial.py
def upgrade():
    op.create_table('jobs', ...)
def downgrade():
    op.drop_table('jobs')
Versioning:

schema_version field in jobs
API versioning (/api/v1)
Backward compatibility
Project Structure
results-storage/
├── app/
│   ├── __init__.py           # Package init
│   ├── config.py             # Configuration
│   ├── models.py             # SQLAlchemy models
│   ├── database.py           # Database connection
│   ├── storage.py            # Storage service
│   └── main.py               # FastAPI application
├── schema.sql                # PostgreSQL schema
├── requirements.txt          # Dependencies
└── README.md                 # Documentation
Total Files Created: 9 files

How to Use
1. Setup Database
createdb results
psql results < schema.sql
2. Start Service
cd results-storage
pip install -r requirements.txt
python -m app.main
3. Store Estimate
curl -X POST http://localhost:8007/api/v1/store \
  -H "Content-Type: application/json" \
  -d '{
    "estimate": {
      "total_monthly_cost": 1234.56,
      "by_resource": [...]
    },
    "user_id": "user123"
  }'
4. Retrieve Results
# Get job
curl http://localhost:8007/api/v1/jobs/{job_id}
# Get resources
curl http://localhost:8007/api/v1/jobs/{job_id}/resources
# Compare jobs
curl http://localhost:8007/api/v1/compare?job_id_1={id1}&job_id_2={id2}
Summary
Successfully delivered a Results Storage & Reporting Service with:

🗄️ PostgreSQL schema (4 tables, immutable)
🔒 INSERT-only pattern (audit trail)
📖 Read-only APIs (7 endpoints)
📊 Historical comparisons
⚡ Fast queries (denormalized, indexed)
🔄 Schema evolution (Alembic)
✅ 9 files created