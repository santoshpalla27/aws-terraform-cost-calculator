#!/bin/bash
set -e

echo "🧪 Platform Tester Starting..."
echo "================================"

# Get configuration from environment
BASE_URL=${BASE_URL:-http://nginx}
API_BASE=${API_BASE:-http://nginx/api}
PYTEST_ARGS=${PYTEST_ARGS:--v --tb=short}

echo "Base URL: $BASE_URL"
echo "API Base: $API_BASE"
echo "================================"

# Wait for nginx to be healthy
echo "⏳ Waiting for nginx..."
MAX_RETRIES=30
RETRY_COUNT=0

until curl -sf $BASE_URL/health > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Nginx failed to become healthy after $MAX_RETRIES attempts"
        exit 1
    fi
    echo "  Attempt $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

echo "✅ Nginx is healthy"
echo "================================"

# Run tests
echo "🚀 Running platform tests..."
echo ""

pytest $PYTEST_ARGS

# Capture exit code
EXIT_CODE=$?

echo ""
echo "================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ ALL TESTS PASSED"
    echo "Platform is production-ready!"
else
    echo "❌ TESTS FAILED"
    echo "Platform has regressions - deployment blocked"
fi
echo "================================"

exit $EXIT_CODE
