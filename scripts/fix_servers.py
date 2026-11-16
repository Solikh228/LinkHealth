"""
Automated fix for low memory, swapfile configuration, Grafana responsiveness,
and port 80 routing on both subtracker-dev and subtracker-prod servers.
"""

import time
import boto3
import sys

sys.stdout.reconfigure(encoding="utf-8")
ssm = boto3.client("ssm", region_name="ap-southeast-2")

DEV_INSTANCE = "i-0ab9957b598dde50d"
PROD_INSTANCE = "i-0b8ca25bf547c7417"
ECR_REGISTRY = "981273599628.dkr.ecr.ap-southeast-2.amazonaws.com"


def run_ssm_script(instance_id: str, script: str, timeout: int = 400):
    print(f"\n--- Running script on {instance_id} ---")
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [script]},
        TimeoutSeconds=timeout,
    )
    cmd_id = resp["Command"]["CommandId"]

    for _ in range(timeout // 5):
        time.sleep(5)
        inv = ssm.get_command_invocation(CommandId=cmd_id, InstanceId=instance_id)
        status = inv.get("Status")
        if status in ["Success", "Cancelled", "TimedOut", "Failed"]:
            print(f"Command {cmd_id} finished with status: {status}")
            stdout = inv.get("StandardOutputContent", "")
            stderr = inv.get("StandardErrorContent", "")
            if stdout:
                print("STDOUT:\n" + stdout)
            if stderr:
                print("STDERR:\n" + stderr)
            return status == "Success"
    print(f"Command {cmd_id} timed out waiting.")
    return False


def main():
    print("=================================================================")
    print(" STEP 1: Fix subtracker-dev-server (Swap + App Stack + Grafana)")
    print("=================================================================")

    dev_fix_script = f"""#!/bin/bash
set -e

echo "=== 1. Creating and Enabling 2GB Swapfile ==="
if [ ! -f /swapfile ]; then
    dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress
    chmod 600 /swapfile
    mkswap /swapfile
fi
swapon /swapfile || true
if ! grep -q '/swapfile' /etc/fstab; then
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
sysctl vm.swappiness=10
echo 'vm.swappiness=10' > /etc/sysctl.d/99-swap.conf
free -h

echo "=== 2. Ensuring docker-buildx is installed ==="
mkdir -p /usr/libexec/docker/cli-plugins
if [ ! -f /usr/libexec/docker/cli-plugins/docker-buildx ] || [ "$(/usr/libexec/docker/cli-plugins/docker-buildx version 2>&1 | grep -o 'v0.21')" != "v0.21" ]; then
    curl -SL https://github.com/docker/buildx/releases/download/v0.21.2/buildx-v0.21.2.linux-amd64 -o /usr/libexec/docker/cli-plugins/docker-buildx
    chmod +x /usr/libexec/docker/cli-plugins/docker-buildx
fi
docker buildx version

echo "=== 3. Pulling latest codebase ==="
cd /opt/subtracker-dev
git fetch origin main
git reset --hard origin/main

echo "=== 4. Updating Caddyfile for Direct HTTP Port 80 Serving ==="
cat << 'EOF' > /opt/subtracker-dev/Caddyfile
{{
    admin off
    auto_https off
}}

:80 {{
    encode zstd gzip
    reverse_proxy web:8000 {{
        header_up Host {{host}}
        header_up X-Real-IP {{remote_host}}
        header_up X-Forwarded-For {{remote_host}}
        header_up X-Forwarded-Proto {{scheme}}
    }}
}}
EOF

echo "=== 5. Building and Pushing FullStack App Image to Amazon ECR ==="
docker build -t {ECR_REGISTRY}/subtracker:latest .
aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin {ECR_REGISTRY} || true
docker push {ECR_REGISTRY}/subtracker:latest || true

echo "=== 6. Starting Dev Application Stack ==="
cd /opt/subtracker-dev
docker compose -f docker-compose.prod.yml down || true
docker compose -f docker-compose.prod.yml up -d

echo "=== 7. Restarting Grafana in Observability Stack with Increased Memory Headroom ==="
cd /opt/subtracker-dev/observability
docker compose restart grafana

echo "=== 8. Verifying Running Containers and Ports ==="
sleep 5
docker ps
ss -tulpn | grep -E ':(80|443|3000|8000|8080)' || true

echo "=== 9. Testing Local Endpoints ==="
curl -s -o /dev/null -w "Port 80 (App SPA): HTTP %{{http_code}}\\n" http://localhost:80/ || true
curl -s -o /dev/null -w "Port 8000 (Backend Health): HTTP %{{http_code}}\\n" http://localhost:8000/api/health || true
curl -s -o /dev/null -w "Port 3000 (Grafana Health): HTTP %{{http_code}}\\n" http://localhost:3000/api/health || true
"""

    success_dev = run_ssm_script(DEV_INSTANCE, dev_fix_script, timeout=600)
    print(f"Dev fix completed with status: {success_dev}")

    print("\n=================================================================")
    print(" STEP 2: Fix subtracker-prod-server (Swap + App Stack on Port 80)")
    print("=================================================================")

    prod_fix_script = f"""#!/bin/bash
set -e

echo "=== 1. Creating and Enabling 2GB Swapfile on Prod ==="
if [ ! -f /swapfile ]; then
    dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress
    chmod 600 /swapfile
    mkswap /swapfile
fi
swapon /swapfile || true
if ! grep -q '/swapfile' /etc/fstab; then
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
sysctl vm.swappiness=10
echo 'vm.swappiness=10' > /etc/sysctl.d/99-swap.conf
free -h

echo "=== 2. Pulling latest codebase on Prod ==="
cd /opt/subtracker-prod
git fetch origin main
git reset --hard origin/main

echo "=== 3. Updating Caddyfile for Direct HTTP Port 80 Serving ==="
cat << 'EOF' > /opt/subtracker-prod/Caddyfile
{{
    admin off
    auto_https off
}}

:80 {{
    encode zstd gzip
    reverse_proxy web:8000 {{
        header_up Host {{host}}
        header_up X-Real-IP {{remote_host}}
        header_up X-Forwarded-For {{remote_host}}
        header_up X-Forwarded-Proto {{scheme}}
    }}
}}
EOF

echo "=== 4. Pulling Built Image from Amazon ECR ==="
aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin {ECR_REGISTRY} || true
docker pull {ECR_REGISTRY}/subtracker:latest

echo "=== 5. Starting Production Application Stack ==="
docker compose -f docker-compose.prod.yml down || true
docker compose -f docker-compose.prod.yml up -d

echo "=== 6. Verifying Running Containers and Ports on Prod ==="
sleep 5
docker ps
ss -tulpn | grep -E ':(80|443|8000)' || true

echo "=== 7. Testing Local Endpoints on Prod ==="
curl -s -o /dev/null -w "Port 80 (App SPA): HTTP %{{http_code}}\\n" http://localhost:80/ || true
curl -s -o /dev/null -w "Port 8000 (Backend Health): HTTP %{{http_code}}\\n" http://localhost:8000/api/health || true
"""

    success_prod = run_ssm_script(PROD_INSTANCE, prod_fix_script, timeout=400)
    print(f"Prod fix completed with status: {success_prod}")


if __name__ == "__main__":
    main()
