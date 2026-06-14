#!/usr/bin/env bash
# verify_demo.sh — end-to-end smoke test for the sportsml v0 demo loop.
# Run after `make install` and `make ingest`.

set -euo pipefail

cd "$(dirname "$0")/.."

# Activate venv so the .pth-installed namespace packages resolve.
if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  . .venv/bin/activate
fi

API_URL="${API_URL:-http://localhost:8000}"
WORKBENCH_URL="${WORKBENCH_URL:-http://localhost:3000}"

green() { printf "\033[32m%s\033[0m\n" "$1"; }
red() { printf "\033[31m%s\033[0m\n" "$1"; }
yellow() { printf "\033[33m%s\033[0m\n" "$1"; }

check() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    green "✓ $name"
  else
    red "✗ $name"
    return 1
  fi
}

echo "=== sportsml v0 demo verification ==="
echo

yellow "1. Python package imports"
check "sportsml.core importable" \
  python -c "import sportsml.core"
check "sportsml.sports.basketball.nba importable" \
  python -c "import sportsml.sports.basketball.nba"
check "sportsml_dagster importable" \
  python -c "import sportsml_dagster"
check "sportsml_api importable" \
  python -c "import sportsml_api"

echo
yellow "2. Data layer"
if [ -f data/sportsml.duckdb ]; then
  green "✓ DuckDB file present"
else
  yellow "○ DuckDB file missing — run 'make ingest' first"
fi

echo
yellow "3. API liveness (skipping if backend not running)"
if curl -sf -o /dev/null "$API_URL/health"; then
  green "✓ API responding at $API_URL"
  check "GET /models" curl -sf -o /dev/null "$API_URL/models"
  check "GET /models/lineup_net_rating/schema" curl -sf -o /dev/null "$API_URL/models/lineup_net_rating/schema"
  check "GET /ontology/types" curl -sf -o /dev/null "$API_URL/ontology/types"
  check "GET /datasets" curl -sf -o /dev/null "$API_URL/datasets"
else
  yellow "○ API not running — start with 'make api'"
fi

echo
yellow "4. Workbench liveness (skipping if frontend not running)"
if curl -sf -o /dev/null "$WORKBENCH_URL"; then
  green "✓ Workbench responding at $WORKBENCH_URL"
else
  yellow "○ Workbench not running — start with 'make workbench'"
fi

echo
green "Verification complete. To test the demo loop:"
echo "  1. Open $WORKBENCH_URL"
echo "  2. Navigate to Apps → Lineup Analysis"
echo "  3. Drag the 'rapm_lambda' slider, click Run Model"
echo "  4. Confirm the top-lineups table updates"
