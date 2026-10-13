#!/usr/bin/env bash
set -Eeuo pipefail
set -a
[ -f .env ] && . ./.env
set +a
exec uvicorn server:app --host 0.0.0.0 --port 8000
