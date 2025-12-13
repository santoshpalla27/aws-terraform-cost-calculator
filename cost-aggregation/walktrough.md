Cost Aggregation Engine Walkthrough
Overview
Successfully implemented a Cost Aggregation Engine that performs pure cost computation (cost = usage × pricing), aggregates by resource/service/region, supports Terraform plan diffs, and tracks cost drivers with confidence scoring.

What Was Built
Output Schema
1. Schema Models (
schema.py
)
CostDriver:

component: Cost component (compute, storage, network, other)
cost
: Cost amount
percentage: Percentage of total
description: Description
ResourceCost:

resource_id: Resource identifier
resource_type: Type (aws_instance, etc.)
service
: AWS service (EC2, S3, etc.)
region
: AWS region
Cost breakdown: compute, storage, network, other
total_monthly_cost: Total cost
confidence_score: 0.0-1.0
cost_drivers
: Top contributors
assumptions: Cost assumptions
ServiceCost:

service
: Service name
total_cost: Aggregated cost
resource_count: Number of resources
resources: List of resources
RegionCost:

region
: Region name
total_cost: Aggregated cost
resource_count: Number of resources
services
: Cost by service
CostEstimate:

total_monthly_cost: Total estimate
confidence_score: Overall confidence
by_resource: Per-resource costs
by_service
: Service aggregation
by_region
: Region aggregation
profile
: Usage profile
timestamp: Estimate time
CostDiff:

total_delta: Cost difference
percentage_change: % change
added_resources: New resources
removed_resources: Deleted resources
changed_resources: Modified resources
added_cost: Cost of additions
removed_cost: Cost of removals
Cost Calculator
2. Calculator (
calculator.py
)
Pure Computation Formula:

cost = usage × pricing
Cost Components:

Compute Cost:

compute_hours × price_per_hour
Storage Cost:

(storage_gb + ebs_gb + backup_gb) × storage_rate
Network Cost:

network_out_gb × data_transfer_rate
Other Cost:

(requests_get × rate_get) + (requests_put × rate_put)
Confidence Calculation:

Metadata: Enriched (0.9), Degraded (0.5), Default (0.7)
Pricing: SKU match (0.95), Estimated (0.6)
Usage: Has assumptions (0.8), No assumptions (0.6)
Average of all factors
Cost Driver Identification:

Sort components by cost descending
Calculate percentage of total
Return top contributors
Service Mapping:

aws_instance → EC2
aws_s3_bucket → S3
aws_db_instance → RDS
aws_lb → ELB
Aggregation Logic
3. Aggregator (
aggregator.py
)
Aggregate by Service:

Group resources by service
Sum costs per service
Count resources
Sort by cost descending
Aggregate by Region:

Group resources by region
Sum costs per region
Break down by service within region
Sort by cost descending
Overall Confidence:

Weighted average by resource cost
Formula: Σ(confidence × cost) / Σ(cost)
Diff Engine
4. Diff Engine (
diff.py
)
Diff Calculation:

Added Resources:

Resources in after but not in before
Sum of added costs
Removed Resources:

Resources in before but not in after
Sum of removed costs
Changed Resources:

Resources in both with different costs
Calculate delta and % change
Total Delta:

after.total - before.total
Percentage change
Use Case:

Terraform plan cost analysis
Before/after infrastructure changes
Cost impact assessment
API Layer
5. FastAPI Application (
main.py
)
Endpoints:

POST /api/v1/estimate:

Input: resources, pricing_data, usage_data, profile
Process:
Create pricing/usage maps
Calculate cost for each resource
Aggregate by service/region
Output: Complete cost estimate
POST /api/v1/diff:

Input: before and after estimates
Process:
Generate before estimate
Generate after estimate
Calculate diff
Output: Cost difference
GET /health:

Health check
Key Features Delivered
✅ Pure Computation
Formula:

cost = usage × pricing
No Assumptions:

No hardcoded prices
No Terraform parsing
Only computation
Example:

# EC2 Instance
compute_cost = 730 hours × $0.0416/hour = $30.37
storage_cost = 30 GB × $0.10/GB = $3.00
network_cost = 100 GB × $0.09/GB = $9.00
total = $42.37
✅ Hierarchical Aggregations
Three Levels:

Per-Resource: Individual breakdown
Per-Service: EC2, S3, RDS, etc.
Per-Region: us-east-1, eu-west-1, etc.
Sorted by Cost:

Highest cost first
Easy to identify expensive resources
✅ Terraform Diff Support
Before vs After:

{
  "total_delta": 50.00,
  "percentage_change": 25.5,
  "added_resources": [...],
  "removed_resources": [...],
  "changed_resources": [
    {
      "resource_id": "aws_instance.web",
      "before_cost": 30.00,
      "after_cost": 60.00,
      "delta": 30.00
    }
  ]
}
✅ Cost Driver Tracking
Top Contributors:

{
  "cost_drivers": [
    {
      "component": "compute",
      "cost": 30.37,
      "percentage": 71.7,
      "description": "Compute costs"
    },
    {
      "component": "network",
      "cost": 9.00,
      "percentage": 21.2
    }
  ]
}
✅ Confidence Scoring
Factors:

Metadata quality (enriched/degraded)
Pricing certainty (SKU match/estimated)
Usage assumptions (override/profile)
Weighted Average:

By resource cost
Overall estimate confidence
Project Structure
cost-aggregation/
├── app/
│   ├── __init__.py           # Package init
│   ├── config.py             # Configuration
│   ├── schema.py             # Output models
│   ├── calculator.py         # Cost calculator
│   ├── aggregator.py         # Aggregation logic
│   ├── diff.py               # Diff engine
│   └── main.py               # FastAPI application
├── requirements.txt          # Dependencies
└── README.md                 # Documentation
Total Files Created: 9 files

How to Use
1. Start Service
cd cost-aggregation
pip install -r requirements.txt
python -m app.main
2. Generate Estimate
curl -X POST http://localhost:8006/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "resources": [{
      "resource_id": "aws_instance.web[0]",
      "resource_type": "aws_instance",
      "region": "us-east-1",
      "sku": "SKU123"
    }],
    "pricing_data": [{
      "sku": "SKU123",
      "price_per_unit": 0.0416
    }],
    "usage_data": [{
      "resource_id": "aws_instance.web[0]",
      "compute_hours": 730
    }],
    "profile": "prod"
  }'
3. Calculate Diff
curl -X POST http://localhost:8006/api/v1/diff \
  -H "Content-Type: application/json" \
  -d '{
    "before": {...},
    "after": {...}
  }'
Summary
Successfully delivered a Cost Aggregation Engine with:

🧮 Pure computation (cost = usage × pricing)
📊 Hierarchical aggregations (resource/service/region)
🔄 Terraform diff support
📈 Cost driver tracking
🎯 Confidence scoring
🚀 FastAPI application
✅ 9 files created