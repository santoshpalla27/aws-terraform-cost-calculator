# Platform Tester Service

A comprehensive black-box testing service that validates the entire Terraform Cost Intelligence Platform end-to-end.

## Overview

The Platform Tester treats the entire system as a distributed black box and validates:
- **Contract compliance**: All API responses match JSON schemas
- **State machine correctness**: Job transitions are valid and monotonic
- **Immutability**: Results are write-once and never change
- **Resilience**: Platform survives service restarts
- **End-to-end flow**: Complete user journey works correctly

## Architecture

```
platform-tester (container)
├── Health Tests → Ensure all services reachable
├── Contract Tests → Validate API response schemas
├── API Gateway Tests → Auth, rate limiting, validation
├── Job Tests → Lifecycle, state transitions
├── Terraform Tests → Sandbox constraints
├── Cost Pipeline Tests → Metadata, pricing, usage, aggregation
├── Results Tests → Persistence, immutability
├── E2E Tests → Full user flow
└── Resilience Tests → Service restart recovery
```

## Quick Start

### Run All Tests

```bash
# Local
docker compose up --build platform-tester

# CI (blocks deployment on failure)
docker compose up --abort-on-container-exit --exit-code-from platform-tester
```

### Run Specific Test Category

```bash
# Health checks only
docker compose run platform-tester pytest tests/00_health/ -v

# Contract tests only
docker compose run platform-tester pytest tests/01_contracts/ -v

# E2E tests only
docker compose run platform-tester pytest tests/07_e2e/ -v
```

### Run with Markers

```bash
# Run all health tests
docker compose run platform-tester pytest -m health -v

# Run all contract tests
docker compose run platform-tester pytest -m contract -v

# Run all E2E tests
docker compose run platform-tester pytest -m e2e -v

# Skip slow tests
docker compose run platform-tester pytest -m "not slow" -v
```

## Test Categories

### 00_health - Health Checks
- Nginx responds
- API Gateway healthy
- All backend services reachable

**Purpose**: Fail fast if infrastructure is down

### 01_contracts - Contract Validation
- ApiResponse envelope structure
- correlation_id presence and format
- success/error semantics
- No forbidden fields

**Purpose**: Ensure API contract compliance

### 02_api_gateway - API Gateway
- Authentication (JWT validation)
- Rate limiting enforcement
- Input validation
- CORS headers

**Purpose**: Validate gateway functionality

### 03_jobs - Job Lifecycle
- Job creation
- State transitions
- Progress monotonicity
- Terminal states

**Purpose**: Validate job state machine

### 04_terraform_execution - Terraform Sandbox
- Prevent local-exec
- Prevent file writes
- Prevent network access

**Purpose**: Ensure sandbox security

### 05_cost_pipeline - Cost Pipeline
- Metadata enrichment
- Pricing resolution
- Usage modeling
- Cost aggregation

**Purpose**: Validate cost calculation correctness

### 06_results_governance - Results Governance
- Write-once enforcement
- Update/delete rejection
- Persistence across restarts

**Purpose**: Ensure immutability

### 07_e2e - End-to-End
- Full user flow
- Upload → Create → Poll → Results
- Browser refresh mid-job
- Result immutability

**Purpose**: Validate complete user journey

### 08_resilience - Resilience
- Service restart recovery
- Partial failure handling
- Job resume/fail cleanly

**Purpose**: Validate platform resilience

## Exit Codes

- **0**: All tests passed → Deploy
- **1**: Tests failed → Block deployment

## Configuration

### Environment Variables

```bash
BASE_URL=http://nginx          # Nginx base URL
API_BASE=http://nginx/api      # API Gateway base URL
PYTEST_ARGS="-v --tb=short"    # Pytest arguments
```

### Endpoints (config/endpoints.yaml)

```yaml
endpoints:
  health: /health
  api_health: /api/health
  usage_profiles: /api/usage-profiles
  jobs: /api/jobs
  job_status: /api/jobs/{job_id}/status
  job_results: /api/jobs/{job_id}/results
```

## JSON Schemas

All API responses are validated against JSON schemas in `config/contracts/`:

- **ApiResponse.json**: Standard response envelope
- **Job.json**: Job object structure
- **UsageProfile.json**: Usage profile structure
- **CostResult.json**: Cost result structure

## Utilities

### API Client (`utils/api_client.py`)

```python
from utils.api_client import PlatformClient

client = PlatformClient()
response = client.get('/usage-profiles', validate_schema='UsageProfile')
```

Features:
- Automatic schema validation
- correlation_id tracking
- Error handling

### Polling (`utils/polling.py`)

```python
from utils.polling import poll_until_sync

result = poll_until_sync(
    check_fn=lambda: client.get(f'/jobs/{job_id}/status'),
    condition_fn=lambda r: r['data']['status'] in ['COMPLETED', 'FAILED'],
    max_attempts=60,
    timeout=300
)
```

Features:
- Exponential backoff
- Timeout handling
- Condition checking

### Assertions (`utils/assertions.py`)

```python
from utils.assertions import (
    assert_valid_state_transition,
    assert_correlation_id,
    assert_terminal_state
)

assert_valid_state_transition('PLANNING', 'PARSING')  # OK
assert_valid_state_transition('COMPLETED', 'PARSING')  # AssertionError
```

### Correlation Tracking (`utils/correlation.py`)

```python
from utils.correlation import track_request, print_correlation_summary

track_request(correlation_id, '/jobs', 'POST', success=True)
print_correlation_summary()  # At end of tests
```

## Development

### Adding New Tests

1. Create test file in appropriate category directory
2. Use `@pytest.mark.<category>` decorator
3. Use `api_client` fixture for API calls
4. Use `track_correlation` fixture to track correlation IDs
5. Validate responses against schemas

Example:

```python
import pytest

@pytest.mark.jobs
def test_job_creation(api_client, track_correlation):
    """Test job creation."""
    response = api_client.post('/jobs', json={
        'name': 'Test Job',
        'upload_id': 'uuid',
        'usage_profile': 'prod'
    }, validate_schema='Job')
    
    track_correlation(response, '/jobs', 'POST')
    
    assert response['success']
    assert 'job_id' in response['data']
```

### Running Tests Locally

```bash
# Install dependencies
cd tester
pip install -r requirements.txt

# Run tests (requires platform running)
export BASE_URL=http://localhost
export API_BASE=http://localhost/api
pytest -v
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run Platform Tests
  run: |
    docker compose up -d
    docker compose up --abort-on-container-exit --exit-code-from platform-tester
    
- name: Cleanup
  if: always()
  run: docker compose down
```

### GitLab CI Example

```yaml
test:
  script:
    - docker compose up -d
    - docker compose up --abort-on-container-exit --exit-code-from platform-tester
  after_script:
    - docker compose down
```

## Troubleshooting

### Tests Fail with "Nginx not healthy"

**Cause**: Nginx not started or not accessible

**Solution**:
```bash
# Check nginx status
docker compose ps nginx

# Check nginx logs
docker compose logs nginx

# Restart nginx
docker compose restart nginx
```

### Tests Fail with "Schema validation failed"

**Cause**: API response doesn't match schema

**Solution**:
1. Check correlation_id in error message
2. Review API response structure
3. Update schema if API changed intentionally

### Tests Timeout

**Cause**: Job taking too long or stuck

**Solution**:
1. Check job-orchestrator logs
2. Increase timeout in test
3. Check for deadlocks in backend services

## Success Criteria

When platform-tester passes:
✅ Platform is production-ready
✅ All contracts enforced
✅ State machine correct
✅ Results immutable
✅ Platform resilient
✅ E2E flow works

## License

Same as parent project
