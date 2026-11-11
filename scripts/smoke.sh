#!/usr/bin/env bash
# PyroScope Deployment Smoke Test
# Usage: ./scripts/smoke.sh [API_BASE_URL]
set -euo pipefail

API_URL="${1:-http://localhost:8000}"
echo "==> PyroScope Smoke Verification: Testing API at ${API_URL}"

FAILED=0

check_endpoint() {
  local name="$1"
  local url="$2"
  local expected_keyword="$3"
  local post_data="${4:-}"

  echo -n "  Testing ${name}... "
  local response
  local http_code

  if [ -n "$post_data" ]; then
    response=$(curl -s -w "\n%{http_code}" -X POST "${url}" \
      -H "Content-Type: application/json" \
      -d "${post_data}")
  else
    response=$(curl -s -w "\n%{http_code}" "${url}")
  fi

  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | sed '$d')

  if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
    if echo "$body" | grep -q "$expected_keyword"; then
      echo "[OK] HTTP ${http_code}"
    else
      echo "[FAILED] HTTP ${http_code} but missing '${expected_keyword}'"
      echo "  Response: ${body}"
      FAILED=1
    fi
  else
    echo "[FAILED] HTTP ${http_code}"
    echo "  Response: ${body}"
    FAILED=1
  fi
}

# 1. Health check
check_endpoint "1. Health Endpoint (/api/health)" \
  "${API_URL}/api/health" \
  "healthy"

# 2. Meta parameters & attribution
check_endpoint "2. Meta & Manifest (/api/meta)" \
  "${API_URL}/api/meta" \
  "dataVersion"

# 3. Heatmap hex aggregation
check_endpoint "3. Heatmap Grid (/api/heatmap)" \
  "${API_URL}/api/heatmap?bbox=88.0,20.5,92.8,26.7&from=2020-05&to=2020-05&metric=harmonized&res=7" \
  "cells"

# 4. FireCalendar & seasonal stats
check_endpoint "4. FireCalendar Grid (/api/calendar)" \
  "${API_URL}/api/calendar?area_id=BGD-ADM2-alpha" \
  "grid"

# 5. Ask PyroScope (offline replay mode)
check_endpoint "5. Ask Assistant (/api/ask in replay mode)" \
  "${API_URL}/api/ask" \
  "replay" \
  '{"question": "When does fire season start in alpha and was 2020 unusual?", "area_id": "BGD-ADM2-alpha"}'

echo "--------------------------------------------------------"
if [ "$FAILED" -eq 0 ]; then
  echo "==> All deployment smoke tests PASSED successfully."
  exit 0
else
  echo "==> Deployment smoke tests FAILED."
  exit 1
fi
