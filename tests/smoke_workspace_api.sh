#!/usr/bin/env bash
set -euo pipefail
BASE="http://127.0.0.1:8010"
TOKEN="workspace-test-token"
rm -rf /tmp/fuhrer_workspace_test
FUHRER_DATA_DIR=/tmp/fuhrer_workspace_test APP_ACCESS_TOKEN="$TOKEN" uvicorn server:app --host 127.0.0.1 --port 8010 >/tmp/fuhrer_workspace_api.log 2>&1 &
PID=$!
trap 'kill "$PID" 2>/dev/null || true' EXIT
sleep 2
MATTER=$(curl -fsS -H "X-App-Token: $TOKEN" -H 'Content-Type: application/json' -d '{"title":"اختبار ملف قانوني","matter_type":"عقد","client_name":"عميل اختبار"}' "$BASE/api/matters")
MATTER_ID=$(printf '%s' "$MATTER" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p' | head -1)
test -n "$MATTER_ID"
curl -fsS -H "X-App-Token: $TOKEN" -H 'Content-Type: application/json' -d '{"title":"مراجعة بند الإنهاء","due_date":"2026-09-10"}' "$BASE/api/matters/$MATTER_ID/tasks" >/dev/null
printf 'hello legal document' >/tmp/fuhrer_workspace_test.txt
curl -fsS -H "X-App-Token: $TOKEN" -F "matter_id=$MATTER_ID" -F 'files=@/tmp/fuhrer_workspace_test.txt' "$BASE/api/upload" >/dev/null
curl -fsS -H "X-App-Token: $TOKEN" "$BASE/api/dashboard" | grep -q 'open_matters'
printf 'workspace api smoke: ok\n'
