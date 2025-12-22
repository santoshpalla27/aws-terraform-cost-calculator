# Job Orchestrator - Terraform Cost Calculator

Production-grade Job Orchestrator as the **system brain** for coordinating Terraform cost estimation execution stages.

## Overview

This service manages the job state machine, sequences execution stages, enforces timeouts, handles retries, and triggers downstream services.

**This is NOT**:
- An API gateway
- A compute engine
- A Terraform executor
- A cost calculator

## State Machine

### States (STRICT - 7 states only)

```
UPLOADED → PLANNING → PARSING → ENRICHING → COSTING → COMPLETED
                                                      ↓
                                                   FAILED
```

### Allowed Transitions

- `UPLOADED` → `PLANNING` or `FAILED`
- `PLANNING` → `PARSING` or `FAILED`
- `PARSING` → `ENRICHING` or `FAILED`
- `ENRICHING` → `COSTING` or `FAILED`
- `COSTING` → `COMPLETED` or `FAILED`
- `COMPLETED` → (terminal)
- `FAILED` → (terminal)

**Invalid transitions are REJECTED.**

## Architecture

```
job-orchestrator/
├── app/
│   ├── state_machine/      # State machine logic
│   ├── stages/             # Stage executors
│   ├── services/           # Lock manager, orchestrator
│   ├── repositories/       # PostgreSQL persistence
│   ├── routers/            # Internal APIs
│   ├── database/           # DB connection & migrations
│   ├── models/             # Domain models
│   └── utils/              # Logging, retry logic
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Quick Start

### Local Development

1. **Start dependencies**
   ```bash
   docker-compose up -d postgres redis
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker

```bash
docker-compose up -d
```

## Internal APIs

**Base URL**: `http://localhost:8001/internal`

### Start Job
```bash
POST /internal/jobs/{job_id}/start
```

### Fail Job
```bash
POST /internal/jobs/{job_id}/fail
Body: { "error_message": "..." }
```

### Get Job State
```bash
GET /internal/jobs/{job_id}/state
```

## Stage Configuration

| Stage | Timeout | Max Retries | Backoff |
|-------|---------|-------------|---------|
| PLANNING | 300s | 2 | Exponential |
| PARSING | 120s | 2 | Exponential |
| ENRICHING | 180s | 1 | Exponential |
| COSTING | 60s | 2 | Exponential |

## Distributed Locking

- **Redis-based** distributed locks
- **One orchestrator per job** (enforced)
- **TTL-based** auto-release (300s default)
- **Idempotent** stage execution

## Database Schema

### Jobs Table
- job_id (UUID, PK)
- current_state, previous_state
- created_at, updated_at, started_at, completed_at
- retry_count, error_message
- plan_reference, result_reference

### Stage Executions Table
- job_id, stage_name, attempt_number
- started_at, completed_at, duration_ms
- status (RUNNING, SUCCESS, FAILED)
- input_data, output_data (JSONB)

## Crash Recovery

1. **On startup**: Query non-terminal jobs
2. **Check locks**: Identify stale locks (expired TTL)
3. **Resume jobs**: Pick up jobs without active locks
4. **Idempotent execution**: Safe to re-execute stages

## Configuration

All via environment variables:

```env
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379/0

PLANNING_TIMEOUT=300
PLANNING_MAX_RETRIES=2
# ... (see .env.example)

TERRAFORM_EXECUTION_URL=http://...
PLAN_INTERPRETER_URL=http://...
# ... (downstream services)
```

## Observability

### Structured Logging
- JSON format
- Correlation ID propagation
- Job ID in all logs
- State transition events
- Stage duration metrics

### Example Log
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "job_id": "550e8400...",
  "event": "state_transition",
  "from_state": "PLANNING",
  "to_state": "PARSING"
}
```

## Security

- **Internal network only** (NO public exposure)
- **Service-to-service auth** (token-based)
- **Non-root container**
- **No secrets in code**

## Deployment

### Kubernetes Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: job-orchestrator
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: orchestrator
        image: job-orchestrator:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
```

## Troubleshooting

### Job Stuck in State
- Check Redis locks: `redis-cli GET job:lock:{job_id}`
- Check stage executions table
- Review logs for errors

### Lock Not Released
- Locks auto-expire after TTL (300s)
- Manually delete: `redis-cli DEL job:lock:{job_id}`

### Database Connection Issues
- Verify DATABASE_URL
- Check PostgreSQL is running
- Review connection pool settings

## Development

### Run Tests
```bash
pytest tests/
```

### Database Migrations
```bash
# Migrations are in app/database/migrations/
# Run 001_initial.sql on first setup
```

## Quality Guarantees

✅ Survives process crashes
✅ Resumes jobs safely
✅ Never skips states
✅ Debuggable from logs alone
✅ Replaceable without breaking services
✅ Enforces strict state transitions
✅ Handles distributed locking correctly
