#!/bin/bash
# Contract Verification Test Script
# Tests all API Gateway endpoints for canonical response format

set -e

API_URL="${API_URL:-http://localhost:8080}"
PASSED=0
FAILED=0

echo "================================================================================"
echo "API CONTRACT VERIFICATION TEST"
echo "================================================================================"
echo "Testing API Gateway at: $API_URL"
echo ""

# Helper function to test endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_status="$4"
    
    echo "Testing: $name"
    echo "  $method $endpoint"
    
    response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_URL$endpoint")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    # Check HTTP status
    if [ "$http_code" != "$expected_status" ]; then
        echo "  ❌ FAIL: Expected HTTP $expected_status, got $http_code"
        ((FAILED++))
        return 1
    fi
    
    # Check response has required fields
    if ! echo "$body" | jq -e '.success' > /dev/null 2>&1; then
        echo "  ❌ FAIL: Missing 'success' field"
        ((FAILED++))
        return 1
    fi
    
    if ! echo "$body" | jq -e '.correlation_id' > /dev/null 2>&1; then
        echo "  ❌ FAIL: Missing 'correlation_id' field"
        ((FAILED++))
        return 1
    fi
    
    # Check success field matches HTTP status
    success=$(echo "$body" | jq -r '.success')
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        if [ "$success" != "true" ]; then
            echo "  ❌ FAIL: success should be true for 2xx status"
            ((FAILED++))
            return 1
        fi
    else
        if [ "$success" != "false" ]; then
            echo "  ❌ FAIL: success should be false for error status"
            ((FAILED++))
            return 1
        fi
    fi
    
    # Check data/error fields
    if [ "$success" = "true" ]; then
        if echo "$body" | jq -e '.error != null' > /dev/null 2>&1; then
            echo "  ❌ FAIL: error should be null when success=true"
            ((FAILED++))
            return 1
        fi
    else
        if ! echo "$body" | jq -e '.error' > /dev/null 2>&1; then
            echo "  ❌ FAIL: error field missing when success=false"
            ((FAILED++))
            return 1
        fi
        if ! echo "$body" | jq -e '.error.code' > /dev/null 2>&1; then
            echo "  ❌ FAIL: error.code missing"
            ((FAILED++))
            return 1
        fi
        if ! echo "$body" | jq -e '.error.message' > /dev/null 2>&1; then
            echo "  ❌ FAIL: error.message missing"
            ((FAILED++))
            return 1
        fi
    fi
    
    echo "  ✅ PASS"
    ((PASSED++))
    return 0
}

echo "================================================================================"
echo "TESTING ENDPOINTS"
echo "================================================================================"
echo ""

# Test health endpoint
test_endpoint "Health Check" "GET" "/health" "200"

# Test usage profiles
test_endpoint "Usage Profiles" "GET" "/api/usage-profiles" "200"

# Test jobs list
test_endpoint "Jobs List" "GET" "/api/jobs" "200"

# Test 404 error
test_endpoint "404 Not Found" "GET" "/api/jobs/nonexistent-id" "404"

echo ""
echo "================================================================================"
echo "TEST RESULTS"
echo "================================================================================"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ ALL TESTS PASSED"
    exit 0
else
    echo "❌ SOME TESTS FAILED"
    exit 1
fi
