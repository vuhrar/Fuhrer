#!/usr/bin/env bash
set -Eeuo pipefail
python -m pip install --user -r requirements-runtime.txt
mkdir -p "${FUHRER_DATA_DIR:-/workspaces/.fulaw-data}"
chmod 700 "${FUHRER_DATA_DIR:-/workspaces/.fulaw-data}"
if [ ! -f .env ]; then
  cp .env.example .env
  python - <<'PY'
from pathlib import Path
from secrets import token_urlsafe
from cryptography.fernet import Fernet
p = Path('.env')
s = p.read_text()
s = s.replace('APP_ACCESS_TOKEN=غيّر_هذا_إلى_رمز_طويل_وفريد', 'APP_ACCESS_TOKEN=' + token_urlsafe(48))
s = s.replace('FULAW_STORAGE_KEY=', 'FULAW_STORAGE_KEY=' + Fernet.generate_key().decode())
s = s.replace('FUHRER_DATA_DIR=~/fuhrer_data', 'FUHRER_DATA_DIR=/workspaces/.fulaw-data')
p.write_text(s)
PY
  chmod 600 .env
fi
