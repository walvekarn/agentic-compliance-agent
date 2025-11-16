#!/bin/bash
# Test script for all 4 agentic API endpoints
# Usage: ./scripts/test_agentic_endpoints.sh

set -e

BASE_URL="${API_BASE_URL:-http://localhost:8000}"
ENDPOINTS_BASE="/api/v1/agentic"

echo "🧪 Testing Agentic API Endpoints"
echo "=================================="
echo "Base URL: $BASE_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -e "${YELLOW}Testing: $name${NC}"
    echo "  Method: $method"
    echo "  Endpoint: $endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -H "Accept: application/json" \
            --max-time 125)
    else
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -H "Accept: application/json" \
            -d "$data" \
            --max-time 125)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "  ${GREEN}✓ Status: $http_code${NC}"
        
        # Parse response
        status=$(echo "$body" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
        has_results=$(echo "$body" | grep -c '"results"' || echo "0")
        has_timestamp=$(echo "$body" | grep -c '"timestamp"' || echo "0")
        
        echo "  Response status: $status"
        
        if [ "$has_results" -gt 0 ]; then
            echo -e "  ${GREEN}✓ Has 'results' field${NC}"
        else
            echo -e "  ${RED}✗ Missing 'results' field${NC}"
        fi
        
        if [ "$has_timestamp" -gt 0 ]; then
            echo -e "  ${GREEN}✓ Has 'timestamp' field${NC}"
        else
            echo -e "  ${RED}✗ Missing 'timestamp' field${NC}"
        fi
        
        echo "  Response preview:"
        echo "$body" | head -c 200
        echo "..."
        echo ""
    else
        echo -e "  ${RED}✗ Status: $http_code${NC}"
        echo "  Error:"
        echo "$body" | head -c 200
        echo ""
        echo ""
        return 1
    fi
}

# Test 1: Status endpoint
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "Status" "GET" "$ENDPOINTS_BASE/status" ""

# Test 2: Test Suite endpoint
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TEST_SUITE_DATA='{"num_random": 2, "max_iterations": 3, "complexity_distribution": {"low": 1, "medium": 1}}'
test_endpoint "Test Suite" "POST" "$ENDPOINTS_BASE/testSuite" "$TEST_SUITE_DATA"

# Test 3: Benchmarks endpoint
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
BENCHMARK_DATA='{"levels": ["light"], "max_cases_per_level": 2, "max_iterations": 3}'
test_endpoint "Benchmarks" "POST" "$ENDPOINTS_BASE/benchmarks" "$BENCHMARK_DATA"

# Test 4: Recovery endpoint
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
RECOVERY_DATA='{"task": "Test recovery simulation", "failure_type": "tool_timeout", "failure_rate": 0.5, "max_iterations": 3}'
test_endpoint "Recovery" "POST" "$ENDPOINTS_BASE/recovery" "$RECOVERY_DATA"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✅ All endpoint tests completed!${NC}"
echo ""
echo "Note: Some endpoints may take up to 120 seconds to complete."
echo "For detailed JSON output, use curl directly:"
echo ""
echo "  curl -X GET $BASE_URL$ENDPOINTS_BASE/status | jq"
echo "  curl -X POST $BASE_URL$ENDPOINTS_BASE/testSuite -H 'Content-Type: application/json' -d '$TEST_SUITE_DATA' | jq"
echo "  curl -X POST $BASE_URL$ENDPOINTS_BASE/benchmarks -H 'Content-Type: application/json' -d '$BENCHMARK_DATA' | jq"
echo "  curl -X POST $BASE_URL$ENDPOINTS_BASE/recovery -H 'Content-Type: application/json' -d '$RECOVERY_DATA' | jq"

