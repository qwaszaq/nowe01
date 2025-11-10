#!/bin/bash
# API Testing Script
# Test all main.py endpoints with curl

API_URL="http://localhost:8000"

echo "=================================================="
echo "Testing Investigation Platform API"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Root endpoint
echo -e "${BLUE}[1] Testing Root Endpoint: GET /${NC}"
curl -s -X GET "$API_URL/" | jq '.'
echo ""
echo ""

# Test 2: Health check
echo -e "${BLUE}[2] Testing Health Check: GET /api/health${NC}"
curl -s -X GET "$API_URL/api/health" | jq '.'
echo ""
echo ""

# Test 3: OpenAPI schema
echo -e "${BLUE}[3] Testing OpenAPI Schema: GET /openapi.json${NC}"
curl -s -X GET "$API_URL/openapi.json" | jq '.info'
echo ""
echo ""

# Test 4: Check if server is running
echo -e "${BLUE}[4] Server Status Check${NC}"
if curl -s -f "$API_URL/" > /dev/null; then
    echo -e "${GREEN}✓ Server is running${NC}"
else
    echo -e "${RED}✗ Server is not responding${NC}"
fi
echo ""

echo "=================================================="
echo "Testing Complete"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Start the server: cd backend && uvicorn src.api.main:app --reload"
echo "2. View Swagger UI: http://localhost:8000/docs"
echo "3. View ReDoc: http://localhost:8000/redoc"
echo ""
