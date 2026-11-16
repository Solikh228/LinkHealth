import time
import boto3
import sys

sys.stdout.reconfigure(encoding="utf-8")
ssm = boto3.client("ssm", region_name="ap-southeast-2")

PROD_INSTANCE = "i-0b8ca25bf547c7417"

prod_script = """#!/bin/bash
set -e

echo "=== 1. Ensuring docker-buildx on Prod ==="
mkdir -p /usr/libexec/docker/cli-plugins
curl -SL https://github.com/docker/buildx/releases/download/v0.21.2/buildx-v0.21.2.linux-amd64 -o /usr/libexec/docker/cli-plugins/docker-buildx
chmod +x /usr/libexec/docker/cli-plugins/docker-buildx
docker buildx version

echo "=== 2. Updating Caddyfile for Direct HTTP Port 80 Serving ==="
cat << 'EOF' > /opt/subtracker-prod/Caddyfile
{
    admin off
    auto_https off
}

:80 {
    encode zstd gzip
    reverse_proxy web:8000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}
EOF

echo "=== 3. Building and Starting Application Stack on Prod ==="
cd /opt/subtracker-prod
docker compose -f docker-compose.prod.yml down || true
docker compose -f docker-compose.prod.yml up -d --build

echo "=== 4. Verifying Running Containers and Ports on Prod ==="
sleep 6
docker ps
ss -tulpn | grep -E ':(80|443|8000)' || true

echo "=== 5. Testing Local Endpoint ==="
curl -s -o /dev/null -w "Port 80 (App SPA): HTTP %{http_code}\n" http://localhost:80/ || true
"""

resp = ssm.send_command(
    InstanceIds=[PROD_INSTANCE],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": [prod_script]},
    TimeoutSeconds=500,
)
cmd_id = resp["Command"]["CommandId"]
print(f"Sent command to prod: {cmd_id}")
