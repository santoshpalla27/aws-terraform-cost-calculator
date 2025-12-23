#!/bin/bash
# ============================================================================
# API Contract Verification Script
# Tests all API endpoints to ensure canonical ApiResponse format
# ============================================================================

set -e

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
CORRELATION_ID="test-$(date +%s)"

echo "============================================================================"
echo "API Contract Verification Test Suite"
echo "============================================================================"
echo "API Base URL: $API_BASE_URL"
echo "Correlation ID: $CORRELATION_ID"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# ============================================================================
# Helper Functions
# ============================================================================

test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_status="$4"
    local data="$5"
    
    echo -n "Testing: $name ... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" \
            -H "X-Correlation-ID: $CORRELATION_ID" \
            -H "Content-Type: application/json" \
            "$API_BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" \
            -X "$method" \
            -H "X-Correlation-ID: $CORRELATION_ID" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_BASE_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    # Check HTTP status code
    if [ "$http_code" != "$expected_status" ]; then
        echo -e "${RED}FAIL${NC} (HTTP $http_code, expected $expected_status)"
        echo "Response: $body"
        ((TESTS_FAILED++))
        return 1
    fi
    
    # Check ApiResponse structure
    has_success=$(echo "$body" | jq -r 'has("success")')
    has_data=$(echo "$body" | jq -r 'has("data")')
    has_error=$(echo "$body" | jq -r 'has("error")')
    has_correlation=$(echo "$body" | jq -r 'has("correlation_id")')
    
    if [ "$has_success" != "true" ] || [ "$has_data" != "true" ] || \
       [ "$has_error" != "true" ] || [ "$has_correlation" != "true" ]; then
        echo -e "${RED}FAIL${NC} (Missing required fields)"
        echo "Response: $body"
        echo "has_success=$has_success, has_data=$has_data, has_error=$has_error, has_correlation=$has_correlation"
        ((TESTS_FAILED++))
        return 1
    fi
    
    # Check success/error consistency
    success=$(echo "$body" | jq -r '.success')
    data=$(echo "$body" | jq -r '.data')
    error=$(echo "$body" | jq -r '.error')
    
    if [ "$success" = "true" ]; then
        if [ "$data" = "null" ]; then
            echo -e "${YELLOW}WARN${NC} (success=true but data=null)"
        fi
        if [ "$error" != "null" ]; then
            echo -e "${RED}FAIL${NC} (success=true but error is not null)"
            echo "Response: $body"
            ((TESTS_FAILED++))
            return 1
        fi
    else
        if [ "$error" = "null" ]; then
            echo -e "${RED}FAIL${NC} (success=false but error=null)"
            echo "Response: $body"
            ((TESTS_FAILED++))
            return 1
        fi
        if [ "$data" != "null" ]; then
            echo -e "${YELLOW}WARN${NC} (success=false but data is not null)"
        fi
    fi
    
    echo -e "${GREEN}PASS${NC}"
    ((TESTS_PASSED++))
    return 0
}

# ============================================================================
# Health Check
# ============================================================================

echo "============================================================================"
echo "1. Health Check"
echo "============================================================================"

test_endpoint "Health endpoint" "GET" "/health" "200"

echo ""

# ============================================================================
# Usage Profiles
# ============================================================================

echo "============================================================================"
echo "2. Usage Profiles API"
echo "============================================================================"

test_endpoint "Get usage profiles" "GET" "/api/usage-profiles" "200"

echo ""

# ============================================================================
# Jobs API
# ============================================================================

echo "============================================================================"
echo "3. Jobs API"
echo "============================================================================"

test_endpoint "List jobs (empty)" "GET" "/api/jobs?page=1&page_size=10" "200"

# Test job creation (will fail without upload, but should return proper error format)
test_endpoint "Create job (invalid data)" "POST" "/api/jobs" "422" \
    '{"name": "test-job"}'

# Test get non-existent job
test_endpoint "Get non-existent job" "GET" "/api/jobs/non-existent-id" "404"

echo ""

# ============================================================================
# Error Handling Tests
# ============================================================================

echo "============================================================================"
echo "4. Error Handling"
echo "============================================================================"

# Test 404
test_endpoint "404 Not Found" "GET" "/api/non-existent-endpoint" "404"

# Test validation error
test_endpoint "Validation error" "POST" "/api/jobs" "422" \
    '{"invalid": "data"}'

echo ""

# ============================================================================
# Correlation ID Propagation
# ============================================================================

echo "============================================================================"
echo "5. Correlation ID Propagation"
echo "============================================================================"

echo -n "Testing correlation ID propagation ... "

response=$(curl -s \
    -H "X-Correlation-ID: custom-correlation-123" \
    -H "Content-Type: application/json" \
    "$API_BASE_URL/health")

correlation_id=$(echo "$response" | jq -r '.correlation_id // empty')

if [ "$correlation_id" = "custom-correlation-123" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}FAIL${NC} (Expected: custom-correlation-123, Got: $correlation_id)"
    ((TESTS_FAILED++))
fi

echo ""

# ============================================================================
# Data Structure Consistency
# ============================================================================

echo "============================================================================"
echo "6. Data Structure Consistency"
echo "============================================================================"

echo -n "Testing jobs list returns flat array ... "

response=$(curl -s \
    -H "X-Correlation-ID: $CORRELATION_ID" \
    "$API_BASE_URL/api/jobs?page=1&page_size=10")

# Check that data is an array, not nested object
data_type=$(echo "$response" | jq -r '.data | type')

if [ "$data_type" = "array" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}FAIL${NC} (Expected array, got: $data_type)"
    echo "Response: $response"
    ((TESTS_FAILED++))
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "============================================================================"
echo "Test Summary"
echo "============================================================================"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "API Contract Quality Score: 10/10"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "API Contract Quality Score: $((TESTS_PASSED * 10 / (TESTS_PASSED + TESTS_FAILED)))/10"
    exit 1
fi
