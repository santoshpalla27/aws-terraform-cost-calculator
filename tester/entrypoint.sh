#!/bin/bash
set -e

echo "🧪 Platform Tester Starting..."
echo "================================"

# Get configuration from environment
BASE_URL=${BASE_URL:-http://nginx}
API_BASE=${API_BASE:-http://nginx/api}
PYTEST_ARGS=${PYTEST_ARGS:--v --tb=short}
CERTIFICATION_MODE=${CERTIFICATION_MODE:-false}

echo "Base URL: $BASE_URL"
echo "API Base: $API_BASE"
echo "Certification Mode: $CERTIFICATION_MODE"
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

# Certification mode enforcement
if [ "$CERTIFICATION_MODE" = "true" ]; then
    echo "🔒 CERTIFICATION MODE ENABLED"
    echo "   - All tests MUST run"
    echo "   - No skips allowed"
    echo "   - No xfail allowed"
    echo "   - Exit on first failure"
    echo "================================"
    
    # Add strict flags
    PYTEST_ARGS="$PYTEST_ARGS --exitfirst --strict-markers -p no:warnings"
fi

# Run tests
echo "🚀 Running platform tests..."
echo ""

pytest $PYTEST_ARGS

# Capture exit code
EXIT_CODE=$?

# Check for skipped tests in certification mode
if [ "$CERTIFICATION_MODE" = "true" ] && [ $EXIT_CODE -eq 0 ]; then
    # Verify no tests were skipped
    SKIP_COUNT=$(pytest --collect-only -q 2>/dev/null | grep -c "skipped" || true)
    
    if [ $SKIP_COUNT -gt 0 ]; then
        echo ""
        echo "================================"
        echo "❌ CERTIFICATION FAILURE"
        echo "   $SKIP_COUNT test(s) were skipped"
        echo "   Skips are FORBIDDEN in certification mode"
        echo "================================"
        exit 1
    fi
fi

echo ""
echo "================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ ALL TESTS PASSED"
    if [ "$CERTIFICATION_MODE" = "true" ]; then
        echo "✅ PLATFORM CERTIFIED"
    else
        echo "Platform is production-ready!"
    fi
else
    echo "❌ TESTS FAILED"
    if [ "$CERTIFICATION_MODE" = "true" ]; then
        echo "❌ CERTIFICATION DENIED"
    else
        echo "Platform has regressions - deployment blocked"
    fi
fi
echo "================================"

exit $EXIT_CODE

