#!/bin/bash
set -e

HEALTH_STATUS="stable"
VERSION=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

# Checks local health endpoint; if it is unavailable, mark app as failed.
if ! curl -fsS http://localhost:8000/healthz/ > /dev/null 2>&1; then
    HEALTH_STATUS="failed"
fi

cat > /app/health.json <<EOF
{
  "status": "$HEALTH_STATUS",
  "version": "$VERSION"
}
EOF
