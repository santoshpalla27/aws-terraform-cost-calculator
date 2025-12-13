Usage Modeling Engine Walkthrough
Overview
Successfully implemented a Usage Modeling Engine that generates cost scenarios with explicit usage assumptions, environment-aware profiles, and override mechanisms.

What Was Built
Usage Profiles
1. Dev Profile (
dev.yaml
)
Assumptions:

Resources run 8 hours/day, 5 days/week (40 hours/week)
Low traffic and data transfer
Minimal storage retention (1-day backups)
Cost optimization prioritized
Parameters:

Uptime: 160 hours/month (22% of 730 hours)
EC2: 20% CPU, 10GB network out
S3: 50GB storage, 10K GET, 1K PUT
RDS: 20GB storage, 1-day retention
ELB: 10GB processed, 10 conn/sec
2. Staging Profile (
staging.yaml
)
Assumptions:

Resources run 12 hours/day, 7 days/week
Moderate traffic for testing
Weekly backup retention
Balance cost and performance
Parameters:

Uptime: 360 hours/month (49%)
EC2: 40% CPU, 50GB network out
S3: 200GB storage, 100K GET, 10K PUT
RDS: 100GB storage, 7-day retention
ELB: 50GB processed, 50 conn/sec
3. Prod Profile (
prod.yaml
)
Assumptions:

Resources run 24/7 with high availability
Production-level traffic
30-day backup retention
Performance prioritized
Parameters:

Uptime: 730 hours/month (100%)
EC2: 60% CPU, 500GB network out
S3: 1TB storage, 1M GET, 100K PUT
RDS: 500GB storage, 30-day retention
ELB: 500GB processed, 200 conn/sec
Core Components
4. Profile Loader (
profiles.py
)
Features:

Loads YAML profiles from directory
Pydantic model validation
Profile scaling support (0.5x, 1.5x)
List available profiles
UsageProfile Model:

profile_name: Profile identifier
description: Human-readable description
environment: dev/staging/production
assumptions: List of explicit assumptions
defaults: Dictionary of default parameters
scaling: Min/max scaling factors
Scaling:

min_profile = profile.scale(0.5)  # 50% of defaults
max_profile = profile.scale(1.5)  # 150% of defaults
Resource Usage Models
5. EC2 Usage Model (
ec2_model.py
)
Parameters:

uptime_hours_per_month: Instance uptime
cpu_utilization_percent: Average CPU utilization
network_out_gb: Data transfer out
ebs_volume_gb: Root EBS volume size
Assumption Tracking:

{
  "parameter": "uptime_hours_per_month",
  "value": 730,
  "source": "profile:prod",
  "description": "Instance uptime based on production environment"
}
6. S3 Usage Model (
s3_model.py
)
Parameters:

storage_gb: Average storage size
requests_get: GET requests/month
requests_put: PUT requests/month
7. RDS Usage Model (
rds_model.py
)
Parameters:

uptime_hours_per_month: Database uptime
storage_gb: Database storage
backup_retention_days: Backup retention period
Calculated:

backup_storage_gb_month: storage × retention days
8. ELB Usage Model (
elb_model.py
)
Parameters:

uptime_hours: Load balancer uptime
processed_gb: Data processed
connections_per_second: Average connections
Scenario Generation
9. Scenario Generator (
scenarios.py
)
Workflow:

Load profile by name
Get resource-specific model
Generate expected scenario (100%)
Generate min scenario (50%)
Generate max scenario (150%)
Return all scenarios with assumptions
Output Structure:

{
  "resource_id": "aws_instance.web[0]",
  "scenarios": {
    "min": {
      "usage": {...},
      "assumptions": [...],
      "scaling_factor": 0.5
    },
    "expected": {
      "usage": {...},
      "assumptions": [...],
      "scaling_factor": 1.0
    },
    "max": {
      "usage": {...},
      "assumptions": [...],
      "scaling_factor": 1.5
    }
  }
}
API Layer
10. FastAPI Application (
main.py
)
Endpoints:

POST /api/v1/scenarios - Generate usage scenarios
GET /api/v1/profiles - List available profiles
GET /health - Health check
Request:

{
  "resource": {
    "resource_id": "aws_instance.web[0]",
    "resource_type": "aws_instance"
  },
  "profile": "prod",
  "overrides": {
    "uptime_hours_per_month": 500
  }
}
Documentation
11. README (
README.md
)
Profile descriptions
API endpoint documentation
Override mechanism
Assumption documentation
Quick start guide
Key Features Delivered
✅ Explicit Assumptions
No Hidden Assumptions:

All parameters documented
Source tracking (profile, override, metadata)
Description for every value
Example:

{
  "parameter": "uptime_hours_per_month",
  "value": 730,
  "source": "profile:prod",
  "description": "Resources run 24/7 with high availability"
}
✅ Environment-Aware Profiles
Three Profiles:

Dev: 22% uptime (160h/month)
Staging: 49% uptime (360h/month)
Prod: 100% uptime (730h/month)
Automatic Adjustments:

Uptime hours
Traffic levels
Storage retention
Backup policies
✅ Override Mechanism
Priority:

API overrides (highest)
Config file overrides
Profile defaults (lowest)
Example:

{
  "profile": "prod",
  "overrides": {
    "ec2_uptime_hours": 500,
    "s3_storage_gb": 2000
  }
}
✅ Cost Scenarios
Three Scenarios:

Min: 50% of expected (conservative)
Expected: 100% (profile defaults)
Max: 150% of expected (aggressive)
Scaling:

All numeric parameters scaled
Assumptions updated
Scaling factor tracked
Project Structure
usage-modeling/
├── app/
│   ├── __init__.py           # Package init
│   ├── config.py             # Configuration
│   ├── profiles.py           # Profile loader
│   ├── scenarios.py          # Scenario generator
│   ├── main.py               # FastAPI application
│   └── models/
│       ├── __init__.py
│       ├── ec2_model.py      # EC2 usage model
│       ├── s3_model.py       # S3 usage model
│       ├── rds_model.py      # RDS usage model
│       └── elb_model.py      # ELB usage model
├── profiles/
│   ├── dev.yaml              # Dev profile
│   ├── staging.yaml          # Staging profile
│   └── prod.yaml             # Prod profile
├── requirements.txt          # Dependencies
└── README.md                 # Documentation
Total Files Created: 14 files

How to Use
1. Start Service
cd usage-modeling
pip install -r requirements.txt
python -m app.main
2. Generate Scenarios
curl -X POST http://localhost:8005/api/v1/scenarios \
  -H "Content-Type: application/json" \
  -d '{
    "resource": {
      "resource_id": "aws_instance.web[0]",
      "resource_type": "aws_instance"
    },
    "profile": "prod"
  }'
3. Response
{
  "scenarios": {
    "min": {
      "usage": {"compute_hours": 365},
      "scaling_factor": 0.5
    },
    "expected": {
      "usage": {"compute_hours": 730},
      "scaling_factor": 1.0
    },
    "max": {
      "usage": {"compute_hours": 1095},
      "scaling_factor": 1.5
    }
  }
}
Summary
Successfully delivered a Usage Modeling Engine with:

📊 Three default profiles (dev/staging/prod)
🔧 Resource-specific models (EC2, S3, RDS, ELB)
📈 Cost scenarios (min/expected/max)
🎛️ Override mechanism (API + config)
📝 Assumption documentation (every parameter)
🚀 FastAPI application
✅ 14 files created