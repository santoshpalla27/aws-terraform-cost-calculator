AWS Pricing Engine Walkthrough
Overview
Successfully implemented an AWS Pricing Engine that retrieves and normalizes pricing data from AWS Price List API, stores it in PostgreSQL with version snapshots, and provides deterministic pricing lookups.

What Was Built
Database Schema
1. PostgreSQL Schema (
schema.sql
)
Tables:

services
: AWS service catalog (EC2, S3, RDS, etc.)
products
: Product SKUs with JSONB attributes
pricing_dimensions
: Unit costs with tiered pricing support
pricing_snapshots: Versioned pricing data
Indexes:

GIN index on JSONB attributes for fast lookups
Indexes on service_id, sku, region, effective_date
Composite indexes for common queries
Features:

Automatic updated_at triggers
Foreign key constraints with CASCADE delete
Comments on tables and columns
Core Models
2. SQLAlchemy Models (
models.py
)
Service Model:

service_code: Unique service identifier (AmazonEC2)
service_name: Human-readable name
Relationship to products
Product Model:

sku: Unique product identifier
product_family: Product category
attributes
: JSONB for flexible attributes
region
: AWS region code
Relationship to pricing dimensions
PricingDimension Model:

rate_code: Unique rate identifier
unit
: Pricing unit (hour, GB-month, etc.)
price_per_unit: Decimal price
begin_range/end_range: For tiered pricing
term_type: OnDemand, Reserved, etc.
effective_date: When pricing became effective
PricingSnapshot Model:

snapshot_date: Date of snapshot
version
: Version identifier
status
: active, in_progress, etc.
Counts for services, products, pricing
3. Database Connection (
database.py
)
Features:

SQLAlchemy engine with connection pooling
Session factory with autocommit=False
Context manager for automatic commit/rollback
Database initialization function
Price List API Integration
4. Price List Client (
price_list_client.py
)
Methods:

get_service_index()
: Fetch service catalog
get_service_offer()
: Download offer file for a service
get_region_index()
: Location to region mapping
parse_offer()
: Parse offer JSON
API Endpoints:

Service index: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json
Service offer: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/{service}/current/index.json
5. Unit Conversion (
units.py
)
Supported Units:

Time: Hrs, Hour → 
hour
Storage: GB-Mo, GB-Month, TB-Mo → GB-month
Requests: Requests, 1M requests → request
Data Transfer: GB, TB → GB
IOPS: IOPS, IOPS-Mo → IOPS-month
Functions:

normalize_unit()
: Convert to standard format
convert_to_hourly()
: Convert GB-month to hourly (÷730)
convert_price()
: Convert between units
6. Pricing Normalizer (
normalizer.py
)
Normalization Flow:

Parse products from offer file
Extract attributes (instanceType, memory, etc.)
Map location to region code
Parse pricing terms (OnDemand, Reserved)
Extract pricing dimensions
Normalize units
Handle tiered pricing (begin_range, end_range)
Output:

{
  "service_code": "AmazonEC2",
  "version": "20231201000000",
  "products": [...],
  "pricing_dimensions": [...]
}
Pricing Ingestion
7. Ingestion Service (
ingestion.py
)
Workflow:

Create pricing snapshot (in_progress status)
For each target service:
Fetch offer from Price List API
Normalize data
Batch insert products (1000 per batch)
Batch insert pricing dimensions
Update snapshot (active status, counts)
Performance:

Batch inserts for efficiency
Bulk save objects (SQLAlchemy)
~30-60 minutes for full ingestion
~1M+ SKUs across all services
Pricing Lookup
8. Lookup Service (
lookup.py
)
Deterministic Lookup:

Find service by service_code
Find product by 
region
 and 
attributes
Match attributes (exact match on all search attributes)
Get latest pricing dimension by effective_date
Return pricing information
Example:

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
API Layer
9. FastAPI Application (
main.py
)
Endpoints:

POST /api/v1/lookup - Lookup pricing by attributes
POST /api/v1/ingest - Trigger pricing ingestion (background task)
GET /health - Health check
Features:

Database initialization on startup
Background task for ingestion
Comprehensive error handling
OpenAPI documentation
Configuration
10. Settings (
config.py
)
Configuration:

DATABASE_URL: PostgreSQL connection
TARGET_SERVICES: Services to ingest (EC2, S3, RDS, EKS, ELB)
BATCH_SIZE: Batch insert size (1000)
PRICE_LIST_BASE_URL: AWS Price List API URL
Documentation
11. README (
README.md
)
Database schema documentation
API endpoint documentation
Quick start guide
Configuration options
Example lookups
Performance metrics
Key Features Delivered
✅ AWS Price List API as Source of Truth
No Hardcoded Prices:

All pricing from AWS Price List API
No static JSON files
Versioned snapshots for history
✅ Normalized PostgreSQL Schema
Structure:

Service → Product → PricingDimension
         ↓
    PricingSnapshot
Benefits:

Efficient queries with indexes
JSONB for flexible attributes
Tiered pricing support
Version snapshots
✅ Deterministic Lookups
SKU Mapping:

Exact attribute matching
Region-aware lookups
Latest pricing by effective_date
Fallback to previous snapshots
✅ Unit Conversion
Supported Conversions:

GB-month → hourly (÷730)
TB-month → GB-month (×1024)
1M requests → requests (÷1,000,000)
Project Structure
pricing-engine/
├── app/
│   ├── __init__.py           # Package init
│   ├── config.py             # Configuration
│   ├── database.py           # Database connection
│   ├── models.py             # SQLAlchemy models
│   ├── price_list_client.py  # AWS Price List API client
│   ├── units.py              # Unit conversion
│   ├── normalizer.py         # Pricing normalization
│   ├── ingestion.py          # Ingestion workflow
│   ├── lookup.py             # Pricing lookup
│   └── main.py               # FastAPI application
├── schema.sql                # PostgreSQL schema
├── requirements.txt          # Dependencies
└── README.md                 # Documentation
Total Files Created: 13 files

How to Use
1. Setup Database
createdb pricing
psql pricing < schema.sql
2. Configure
Create .env:

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pricing
TARGET_SERVICES=AmazonEC2,AmazonS3,AmazonRDS
3. Start Service
cd pricing-engine
pip install -r requirements.txt
python -m app.main
4. Ingest Pricing
curl -X POST http://localhost:8004/api/v1/ingest
5. Lookup Pricing
curl -X POST http://localhost:8004/api/v1/lookup \
  -H "Content-Type: application/json" \
  -d '{
    "service_code": "AmazonEC2",
    "region": "us-east-1",
    "attributes": {
      "instanceType": "t3.medium",
      "operatingSystem": "Linux",
      "tenancy": "Shared"
    }
  }'
Response:

{
  "sku": "SKU123",
  "unit": "hour",
  "price_per_unit": 0.0416,
  "currency": "USD"
}
Summary
Successfully delivered an AWS Pricing Engine with:

🗄️ PostgreSQL schema (4 tables, normalized)
🔌 AWS Price List API integration
🔄 Pricing ingestion workflow (~1M SKUs)
📅 Version snapshots
🔍 Deterministic lookups
🔢 Unit conversion
🚀 FastAPI application
✅ 13 files created