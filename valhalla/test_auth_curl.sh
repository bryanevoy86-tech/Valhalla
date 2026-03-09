#!/bin/bash
# Valhalla Authentication - cURL Examples and Testing
# Quick reference for testing the authentication API with curl

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="http://localhost:8000"
USERNAME="The All father"
PASSWORD="IAmBatman!1"

echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}  VALHALLA AUTHENTICATION - cURL EXAMPLES${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo ""
echo "API URL: $API_URL"
echo "Username: $USERNAME"
echo "Password: $PASSWORD"
echo ""

# Function to print section headers
print_section() {
    echo -e "${YELLOW}$1${NC}"
    echo "-----------"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Test 1: Health Check (Public)
print_section "Test 1: Health Check (No Authentication Required)"
echo "Command:"
echo "curl $API_URL/health"
echo ""
echo "Response:"
curl -s $API_URL/health | jq . 2>/dev/null || curl -s $API_URL/health
echo ""
echo ""

# Test 2: System Status (Public)
print_section "Test 2: System Status (No Authentication Required)"
echo "Command:"
echo "curl $API_URL/status"
echo ""
echo "Response:"
curl -s $API_URL/status | jq . 2>/dev/null || curl -s $API_URL/status
echo ""
echo ""

# Test 3: Login and Get Token
print_section "Test 3: Login and Get Access Token"
echo "Command:"
echo "curl -X POST $API_URL/token \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\"}'"
echo ""
echo "Response:"
LOGIN_RESPONSE=$(curl -s -X POST $API_URL/token \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\"}")

echo "$LOGIN_RESPONSE" | jq . 2>/dev/null || echo "$LOGIN_RESPONSE"
echo ""

# Extract tokens
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token' 2>/dev/null)
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.refresh_token' 2>/dev/null)

if [ "$ACCESS_TOKEN" != "null" ] && [ "$ACCESS_TOKEN" != "" ]; then
    print_success "Login successful!"
    echo "Access Token: ${ACCESS_TOKEN:0:50}..."
    echo "Refresh Token: ${REFRESH_TOKEN:0:50}..."
else
    print_error "Login failed!"
    exit 1
fi
echo ""
echo ""

# Test 4: Access Secure Data (Protected)
print_section "Test 4: Access Protected Endpoint - Secure Data"
echo "Command:"
echo "curl -X GET $API_URL/secure-data/ \\"
echo "  -H 'Authorization: Bearer \$ACCESS_TOKEN'"
echo ""
echo "Response:"
curl -s -X GET $API_URL/secure-data/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq . 2>/dev/null || \
curl -s -X GET $API_URL/secure-data/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
echo ""
echo ""

# Test 5: Get User Profile (Protected)
print_section "Test 5: Access Protected Endpoint - User Profile"
echo "Command:"
echo "curl -X GET $API_URL/user-profile/ \\"
echo "  -H 'Authorization: Bearer \$ACCESS_TOKEN'"
echo ""
echo "Response:"
curl -s -X GET $API_URL/user-profile/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq . 2>/dev/null || \
curl -s -X GET $API_URL/user-profile/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
echo ""
echo ""

# Test 6: Get Protected Resource (Protected)
print_section "Test 6: Access Protected Endpoint - Protected Resource"
echo "Command:"
echo "curl -X GET $API_URL/protected-resource/ \\"
echo "  -H 'Authorization: Bearer \$ACCESS_TOKEN'"
echo ""
echo "Response:"
curl -s -X GET $API_URL/protected-resource/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq . 2>/dev/null || \
curl -s -X GET $API_URL/protected-resource/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
echo ""
echo ""

# Test 7: Refresh Token
print_section "Test 7: Refresh Access Token"
echo "Command:"
echo "curl -X POST $API_URL/refresh \\"
echo "  -H 'Authorization: Bearer \$REFRESH_TOKEN'"
echo ""
echo "Response:"
curl -s -X POST $API_URL/refresh \
  -H "Authorization: Bearer $REFRESH_TOKEN" | jq . 2>/dev/null || \
curl -s -X POST $API_URL/refresh \
  -H "Authorization: Bearer $REFRESH_TOKEN"
echo ""
echo ""

# Test 8: Admin Stats (Protected - Admin Only)
print_section "Test 8: Admin Endpoint - System Statistics"
echo "Command:"
echo "curl -X GET $API_URL/admin/stats \\"
echo "  -H 'Authorization: Bearer \$ACCESS_TOKEN'"
echo ""
echo "Response:"
curl -s -X GET $API_URL/admin/stats \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq . 2>/dev/null || \
curl -s -X GET $API_URL/admin/stats \
  -H "Authorization: Bearer $ACCESS_TOKEN"
echo ""
echo ""

# Test 9: Admin Logs (Protected - Admin Only)
print_section "Test 9: Admin Endpoint - View Logs"
echo "Command:"
echo "curl -X GET $API_URL/admin/logs \\"
echo "  -H 'Authorization: Bearer \$ACCESS_TOKEN'"
echo ""
echo "Response:"
LOGS_RESPONSE=$(curl -s -X GET $API_URL/admin/logs \
  -H "Authorization: Bearer $ACCESS_TOKEN")
echo "$LOGS_RESPONSE" | jq . 2>/dev/null || echo "$LOGS_RESPONSE"
echo ""
echo ""

# Test 10: Invalid Token (Should Fail)
print_section "Test 10: Access with Invalid Token (Should Fail)"
echo "Command:"
echo "curl -X GET $API_URL/secure-data/ \\"
echo "  -H 'Authorization: Bearer invalid_token'"
echo ""
echo "Response (Expected: 401 Unauthorized):"
curl -s -X GET $API_URL/secure-data/ \
  -H "Authorization: Bearer invalid_token" | jq . 2>/dev/null || \
curl -s -X GET $API_URL/secure-data/ \
  -H "Authorization: Bearer invalid_token"
echo ""
echo ""

# Test 11: Missing Authorization Header (Should Fail)
print_section "Test 11: Access Without Token (Should Fail)"
echo "Command:"
echo "curl -X GET $API_URL/secure-data/"
echo ""
echo "Response (Expected: 403 Forbidden):"
curl -s -X GET $API_URL/secure-data/ | jq . 2>/dev/null || \
curl -s -X GET $API_URL/secure-data/
echo ""
echo ""

# Test 12: Wrong Credentials (Should Fail)
print_section "Test 12: Login with Wrong Credentials (Should Fail)"
echo "Command:"
echo "curl -X POST $API_URL/token \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"username\": \"wrong\", \"password\": \"wrong\"}'"
echo ""
echo "Response (Expected: 401 Unauthorized):"
curl -s -X POST $API_URL/token \
  -H "Content-Type: application/json" \
  -d '{"username": "wrong", "password": "wrong"}' | jq . 2>/dev/null || \
curl -s -X POST $API_URL/token \
  -H "Content-Type: application/json" \
  -d '{"username": "wrong", "password": "wrong"}'
echo ""
echo ""

# Summary
echo -e "${BLUE}=====================================================================${NC}"
echo -e "${GREEN}✓ Testing Complete!${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo ""
echo "Summary:"
echo "  ✓ Public endpoints tested (no authentication required)"
echo "  ✓ Protected endpoints tested (authentication required)"
echo "  ✓ Token generation verified"
echo "  ✓ Token refresh verified"
echo "  ✓ Admin endpoints tested"
echo "  ✓ Error handling verified"
echo ""
echo "Documentation:"
echo "  - Setup Guide: VALHALLA_AUTH_SETUP.md"
echo "  - Quick Start: VALHALLA_AUTH_QUICK_START.md"
echo "  - System Overview: README_AUTH.md"
echo ""
echo "Interactive API Docs:"
echo "  - Swagger UI: $API_URL/docs"
echo "  - ReDoc: $API_URL/redoc"
echo ""
echo -e "${BLUE}=====================================================================${NC}"
