#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  echo "الملف .env غير موجود. انسخ .env.example إلى .env واضبط APP_ACCESS_TOKEN أولًا." >&2
  exit 1
fi

if [[ -z "${APP_ACCESS_TOKEN:-}" ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [[ -z "${APP_ACCESS_TOKEN:-}" || "${APP_ACCESS_TOKEN}" == *"غيّر_هذا"* || "${APP_ACCESS_TOKEN}" == *"ضع_رمزًا"* ]]; then
  echo "يجب ضبط APP_ACCESS_TOKEN برمز طويل وفريد قبل التشغيل." >&2
  exit 1
fi

exec streamlit run app.py --server.address "${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}" --server.port "${STREAMLIT_SERVER_PORT:-8501}"
