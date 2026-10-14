#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
if ss -ltn 2>/dev/null | grep -q ':8000 '; then
  exit 0
fi
nohup bash .devcontainer/start.sh > /tmp/fulaw.log 2>&1 &
echo "FüLaw is starting on port 8000"
