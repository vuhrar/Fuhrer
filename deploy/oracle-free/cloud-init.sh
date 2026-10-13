#!/usr/bin/env bash
set -Eeuo pipefail

# شغّل هذا النص كـ cloud-init على Ubuntu 24.04 في Oracle Always Free.
# لا تضع APP_ACCESS_TOKEN أو FULAW_STORAGE_KEY داخل هذا الملف.
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl git ufw openssl
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
curl -fsSL https://tailscale.com/install.sh | sh
systemctl enable --now tailscaled

install -d -m 700 /opt/fulaw
chown ubuntu:ubuntu /opt/fulaw
cat >/opt/fulaw/README_DEPLOY.txt <<'EOF'
1) انسخ المستودع إلى /opt/fulaw أو نفّذ git clone باستخدام SSH خاص بك.
2) انسخ .env.example إلى .env ولا ترفع .env إلى Git.
3) أنشئ APP_ACCESS_TOKEN طويلًا وFULAW_STORAGE_KEY Fernet داخل .env.
4) نفّذ docker compose up -d --build.
5) سجّل الجهاز في Tailscale ثم نفّذ: sudo tailscale serve --bg http://127.0.0.1:8000
6) افتح عنوان Tailscale فقط. لا تفتح 8000 على الإنترنت العام.
EOF
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw enable
systemctl restart ssh || true
printf 'VM bootstrap complete. Follow /opt/fulaw/README_DEPLOY.txt\n'
