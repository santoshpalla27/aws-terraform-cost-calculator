# API Contract Enforcement - Test Suite

This directory contains comprehensive test scripts to verify API contract enforcement across the platform.

## Test Scripts

### 1. `test-api-contract.sh` (Linux/Mac)
**Purpose**: Verify canonical ApiResponse format across all endpoints

**Usage**:
```bash
# Make executable
chmod +x test-api-contract.sh

# Run with default URL (localhost:8000)
./test-api-contract.sh

# Run with custom API URL
API_BASE_URL=http://your-server:8000 ./test-api-contract.sh
```

**Tests**:
- ✓ Health endpoint returns proper ApiResponse
- ✓ Usage profiles endpoint returns proper ApiResponse
- ✓ Jobs list endpoint returns flat array
- ✓ Error responses follow ApiResponse format
- ✓ Correlation IDs present in all responses
- ✓ success/error field consistency

---

### 2. `test-api-contract.ps1` (Windows)
**Purpose**: Same as above, but for Windows PowerShell

**Usage**:
```powershell
# Run with default URL
.\test-api-contract.ps1

# Run with custom API URL
.\test-api-contract.ps1 -ApiBaseUrl "http://your-server:8000"
```

---

### 3. `test-e2e-integration.sh`
**Purpose**: End-to-end integration test of complete job workflow

**Usage**:
```bash
chmod +x test-e2e-integration.sh
./test-e2e-integration.sh
```

**Workflow**:
1. Creates test Terraform file
2. Uploads file to API
3. Creates cost estimation job
4. Verifies job data structure is FLAT (not nested)
5. Retrieves job details
6. Lists all jobs
7. Validates ApiResponse format at each step

**Critical Validation**:
- Ensures `POST /api/jobs` returns `{data: {job_id: "..."}}` not `{data: {job: {job_id: "..."}}}`
- Verifies frontend can parse responses without defensive fallbacks

---

### 4. `test-frontend-build.sh`
**Purpose**: Verify frontend TypeScript compilation after API type changes

**Usage**:
```bash
chmod +x test-frontend-build.sh
./test-frontend-build.sh
```

**Checks**:
- ✓ TypeScript type checking passes
- ✓ ESLint validation
- ✓ Production build succeeds
- ✓ ApiResponse<T> interface changes are compatible

---

## Running All Tests

### On Linux/Mac:
```bash
# 1. Start the platform
docker-compose up -d

# 2. Wait for services to be ready (30 seconds)
sleep 30

# 3. Run API contract tests
./test-api-contract.sh

# 4. Run E2E integration test
./test-e2e-integration.sh

# 5. Run frontend build test
./test-frontend-build.sh
```

### On Windows:
```powershell
# 1. Start the platform
docker-compose up -d

# 2. Wait for services
Start-Sleep -Seconds 30

# 3. Run API contract tests
.\test-api-contract.ps1

# 4. For E2E and frontend tests, use Git Bash or WSL
```

---

## Expected Results

### ✅ Success Criteria

**API Contract Tests**:
- All endpoints return `{success, data, error, correlation_id}`
- `success=true` → `error=null`
- `success=false` → `error != null`
- Correlation IDs propagate correctly

**E2E Integration**:
- Job creation returns flat data: `response.data.job_id`
- NOT nested: `response.data.job.job_id`
- Complete workflow succeeds without errors

**Frontend Build**:
- No TypeScript errors
- Production build completes
- All services handle nullable types correctly

---

## Troubleshooting

### Test Fails: "Backend still returning nested structure"
**Problem**: `jobs.py` not updated correctly

**Fix**:
```bash
# Verify changes in jobs.py
grep -A 5 "return {" api-gateway/app/routers/jobs.py

# Should see:
# "data": job,
# NOT: "data": {"job": job, "message": "..."}
```

### Test Fails: "Missing correlation_id"
**Problem**: Middleware not setting correlation_id

**Fix**:
```bash
# Check correlation middleware
cat api-gateway/app/middleware/correlation.py | grep "request.state.correlation_id"

# Should see:
# request.state.correlation_id = correlation_id
```

### Frontend Build Fails: Type errors
**Problem**: Services not handling nullable types

**Fix**:
```typescript
// WRONG
if (response.data) { ... }

// CORRECT
if (response.success && response.data !== null) { ... }
```

---

## Quality Metrics

After running all tests, you should achieve:

- **API Contract Consistency**: 10/10
- **Frontend Integration**: 9/10
- **Error Visibility**: 9/10
- **Overall Platform Stability**: 9.5/10

---

## Manual Browser Testing

After automated tests pass, perform manual verification:

1. **Open** `http://localhost:3000`
2. **Upload** a Terraform file
3. **Create** a job
4. **Verify**:
   - No console errors
   - Job appears in list
   - Job details page loads
   - No infinite spinners
5. **Refresh** the page → should still work
6. **Stop API Gateway** → should show error message with correlation_id

---

## CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: API Contract Tests
  run: |
    docker-compose up -d
    sleep 30
    ./test-api-contract.sh
    
- name: E2E Integration Tests
  run: ./test-e2e-integration.sh
  
- name: Frontend Build
  run: ./test-frontend-build.sh
```
