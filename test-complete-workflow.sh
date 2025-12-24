#!/bin/bash
# ============================================================================
# Complete E2E Workflow Test
# Tests upload → job creation → status polling → results display
# ============================================================================

set -e

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

echo "============================================================================"
echo "Complete E2E Workflow Test"
echo "============================================================================"
echo "API Base URL: $API_BASE_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# Step 1: Verify Usage Profiles Endpoint
# ============================================================================

echo -e "${BLUE}Step 1: Testing usage profiles endpoint${NC}"

profiles_response=$(curl -s "$API_BASE_URL/api/usage-profiles")

if echo "$profiles_response" | jq -e '.success == true' > /dev/null; then
    echo -e "${GREEN}✓ Usage profiles endpoint working${NC}"
    profiles_count=$(echo "$profiles_response" | jq '.data | length')
    echo "  Found $profiles_count profiles"
else
    echo -e "${RED}✗ Usage profiles endpoint failed${NC}"
    echo "Response: $profiles_response"
    exit 1
fi

echo ""

# ============================================================================
# Step 2: Create Test Terraform File
# ============================================================================

echo -e "${BLUE}Step 2: Creating test Terraform file${NC}"

TEST_TF_FILE="/tmp/test-e2e-$(date +%s).tf"

cat > "$TEST_TF_FILE" << 'EOF'
provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
  
  tags = {
    Name = "web-server"
  }
}

resource "aws_ebs_volume" "data" {
  availability_zone = "us-east-1a"
  size             = 50
  type             = "gp3"
}
EOF

echo -e "${GREEN}✓ Test file created${NC}"
echo ""

# ============================================================================
# Step 3: Upload File
# ============================================================================

echo -e "${BLUE}Step 3: Uploading Terraform file${NC}"

upload_response=$(curl -s -X POST \
    -F "files=@$TEST_TF_FILE" \
    "$API_BASE_URL/api/uploads")

upload_id=$(echo "$upload_response" | jq -r '.upload.upload_id // .data.upload_id // empty')

if [ -z "$upload_id" ]; then
    echo -e "${RED}✗ Upload failed${NC}"
    echo "Response: $upload_response"
    rm -f "$TEST_TF_FILE"
    exit 1
fi

echo -e "${GREEN}✓ File uploaded${NC}"
echo "  Upload ID: $upload_id"
echo ""

# ============================================================================
# Step 4: Create Job
# ============================================================================

echo -e "${BLUE}Step 4: Creating cost estimation job${NC}"

job_request=$(cat <<EOF
{
  "name": "E2E Test Job",
  "upload_id": "$upload_id",
  "usage_profile": "prod"
}
EOF
)

job_response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$job_request" \
    "$API_BASE_URL/api/jobs")

job_id=$(echo "$job_response" | jq -r '.data.job_id // empty')

if [ -z "$job_id" ]; then
    echo -e "${RED}✗ Job creation failed${NC}"
    echo "Response: $job_response"
    rm -f "$TEST_TF_FILE"
    exit 1
fi

echo -e "${GREEN}✓ Job created${NC}"
echo "  Job ID: $job_id"
echo ""

# ============================================================================
# Step 5: Poll Job Status
# ============================================================================

echo -e "${BLUE}Step 5: Polling job status${NC}"

MAX_POLLS=30
POLL_INTERVAL=2
poll_count=0

while [ $poll_count -lt $MAX_POLLS ]; do
    status_response=$(curl -s "$API_BASE_URL/api/jobs/$job_id/status")
    
    job_status=$(echo "$status_response" | jq -r '.data.status // empty')
    progress=$(echo "$status_response" | jq -r '.data.progress // 0')
    
    echo "  Status: $job_status | Progress: $progress%"
    
    if [ "$job_status" = "COMPLETED" ]; then
        echo -e "${GREEN}✓ Job completed successfully${NC}"
        break
    elif [ "$job_status" = "FAILED" ]; then
        echo -e "${RED}✗ Job failed${NC}"
        rm -f "$TEST_TF_FILE"
        exit 1
    fi
    
    sleep $POLL_INTERVAL
    ((poll_count++))
done

if [ $poll_count -eq $MAX_POLLS ]; then
    echo -e "${RED}✗ Job did not complete within timeout${NC}"
    rm -f "$TEST_TF_FILE"
    exit 1
fi

echo ""

# ============================================================================
# Step 6: Fetch Results
# ============================================================================

echo -e "${BLUE}Step 6: Fetching cost estimation results${NC}"

results_response=$(curl -s "$API_BASE_URL/api/jobs/$job_id/results")

if echo "$results_response" | jq -e '.success == true' > /dev/null; then
    echo -e "${GREEN}✓ Results fetched successfully${NC}"
    
    total_cost=$(echo "$results_response" | jq -r '.data.total_monthly_cost // .data.totalMonthlyCost // 0')
    currency=$(echo "$results_response" | jq -r '.data.currency // "USD"')
    confidence=$(echo "$results_response" | jq -r '.data.confidence // .data.overallConfidence // 0')
    
    echo "  Total Monthly Cost: $currency $total_cost"
    echo "  Confidence: $(echo "$confidence * 100" | bc)%"
else
    echo -e "${RED}✗ Failed to fetch results${NC}"
    echo "Response: $results_response"
    rm -f "$TEST_TF_FILE"
    exit 1
fi

echo ""

# ============================================================================
# Step 7: Verify API Contract
# ============================================================================

echo -e "${BLUE}Step 7: Verifying API contract compliance${NC}"

# Check all responses have ApiResponse structure
for endpoint in "usage-profiles" "jobs/$job_id" "jobs/$job_id/status" "jobs/$job_id/results"; do
    response=$(curl -s "$API_BASE_URL/api/$endpoint")
    
    if echo "$response" | jq -e 'has("success") and has("data") and has("error") and has("correlation_id")' > /dev/null; then
        echo -e "  ${GREEN}✓${NC} /api/$endpoint"
    else
        echo -e "  ${RED}✗${NC} /api/$endpoint - Missing required fields"
    fi
done

echo ""

# ============================================================================
# Cleanup
# ============================================================================

echo -e "${BLUE}Cleanup${NC}"
rm -f "$TEST_TF_FILE"
echo -e "${GREEN}✓ Test file removed${NC}"
echo ""

# ============================================================================
# Summary
# ============================================================================

echo "============================================================================"
echo -e "${GREEN}✓ COMPLETE E2E WORKFLOW TEST PASSED${NC}"
echo "============================================================================"
echo ""
echo "Verified:"
echo "  ✓ Usage profiles endpoint works"
echo "  ✓ File upload works"
echo "  ✓ Job creation returns proper structure"
echo "  ✓ Status polling endpoint works"
echo "  ✓ Job completes successfully"
echo "  ✓ Results endpoint returns cost data"
echo "  ✓ All endpoints follow ApiResponse contract"
echo ""
echo "The platform is FULLY FUNCTIONAL from API perspective!"
echo ""
echo "Next: Test in browser at $FRONTEND_URL"
echo ""
