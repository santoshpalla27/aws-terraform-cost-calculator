# CloudCost ☁️💰

**CloudCost** is a modular, self-hosted alternative to Infracost. It parses Terraform code (HCL) without needing AWS credentials, resolves dependencies, and provides accurate cost estimations using offline pricing data.

## 🏗️ Architecture

- **Backend**: Python (FastAPI)
  - **Parser**: Hybrid `python-hcl2` + JSON for parsing Terraform.
  - **Graph Engine**: `networkx` for dependency resolution.
  - **Pricing Engine**: PostgreSQL with JSONB containment queries for sub-millisecond price lookups.
- **Frontend**: React (TypeScript + Vite) + Chart.js
- **Database**: PostgreSQL (Stores AWS Price List data)
- **Cache**: Redis (For parsing job queues - *Future Feature*)
- **Infrastructure**: Docker Compose

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for scripts)
- Node.js 18+ (for local frontend dev)

### 1. Start Infrastructure
```bash
docker-compose up -d --build
```
This spins up Postgres, Redis, Backend (port 8000), and Frontend (port 3000).

### 2. Sync Pricing Data (ETL)
Wait for Postgres to be healthy, then run the ETL script to fetch AWS pricing (defaults to **us-east-1** for EC2, RDS, S3, and Lambda).

```bash
# Install script deps (if running locally)
pip install requests psycopg2-binary
# Or run inside backend container
docker-compose exec backend python scripts/sync_aws_pricing.py
```
*Note: This downloads ~100MB+ of data and inserts it into the DB. It may take a few minutes.*

### 3. Access the Dashboard
Open [http://localhost:3000](http://localhost:3000)

1.  **Drag & Drop** your Terraform project (zip file) into the upload zone.
2.  Wait for the parsing and estimation.
3.  View the **Monthly Cost** breakdown and Charts.

## 🛠️ Development

### Backend
Currently runs at `http://localhost:8000`. API Docs at `/docs`.

### Frontend
To run locally with hot-reload:
```bash
cd frontend
npm install
npm run dev
```

### Adding New Services
To add support for a new AWS resource (e.g., RDS):
1.  Create `backend/app/services/rds.py` inheriting `BaseService`.
2.  Implement `get_cost_components`.
3.  Register it in `backend/app/main.py`.

## 🧪 Testing

Run the integration test to verify the full pipeline (Zip -> Upload -> Estimate):
```bash
# Requires backend running on localhost:8000
python tests/integration_test.py
```
