"""
Deploy the Observability stack onto subtracker-dev-server and configure
OTEL_EXPORTER_OTLP_ENDPOINT on both dev and prod servers.
"""

import time
import boto3

ssm = boto3.client("ssm", region_name="ap-southeast-2")

DEV_INSTANCE = "i-0ab9957b598dde50d"
PROD_INSTANCE = "i-0b8ca25bf547c7417"
DEV_IP = "13.239.73.166"


def run_ssm_script(instance_id: str, script: str, timeout: int = 180):
    print(f"\n--- Running script on {instance_id} ---")
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [script]},
        TimeoutSeconds=timeout,
    )
    cmd_id = resp["Command"]["CommandId"]

    # Poll for completion
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
    print(f"Command {cmd_id} timed out waiting for invocation.")
    return False


def main():
    print("=== 1. Deploying Observability Stack on subtracker-dev-server ===")

    dev_script = f"""#!/bin/bash
set -e

echo "=== 1. Upgrading docker-buildx to latest v0.21.2 ==="
mkdir -p /usr/libexec/docker/cli-plugins
curl -SL https://github.com/docker/buildx/releases/download/v0.21.2/buildx-v0.21.2.linux-amd64 -o /usr/libexec/docker/cli-plugins/docker-buildx
chmod +x /usr/libexec/docker/cli-plugins/docker-buildx
docker buildx version

echo "=== 2. Pulling latest code into /opt/subtracker-dev ==="
cd /opt/subtracker-dev
git fetch origin main
git reset --hard origin/main

echo "=== 3. Deploying Observability Docker Compose Stack ==="
cd /opt/subtracker-dev/observability
docker compose down || true
docker compose up -d --build

echo "=== 4. Setting up subtracker-observability.service ==="
cat << 'EOF' > /etc/systemd/system/subtracker-observability.service
[Unit]
Description=SubTracker Observability Stack (OTel, Prometheus, Loki, Tempo, Grafana, On-Call Agent)
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/subtracker-dev/observability
ExecStart=/usr/libexec/docker/cli-plugins/docker-compose up -d
ExecStop=/usr/libexec/docker/cli-plugins/docker-compose down

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable subtracker-observability.service

echo "=== 5. Updating /opt/subtracker-dev/.env with OTEL_EXPORTER_OTLP_ENDPOINT ==="
if grep -q "^OTEL_EXPORTER_OTLP_ENDPOINT=" /opt/subtracker-dev/.env; then
    sed -i "s|^OTEL_EXPORTER_OTLP_ENDPOINT=.*|OTEL_EXPORTER_OTLP_ENDPOINT=http://{DEV_IP}:4317|" /opt/subtracker-dev/.env
else
    echo "OTEL_EXPORTER_OTLP_ENDPOINT=http://{DEV_IP}:4317" >> /opt/subtracker-dev/.env
fi

echo "=== 6. Verifying Running Observability Containers ==="
docker compose ps
"""

    success_dev = run_ssm_script(DEV_INSTANCE, dev_script, timeout=300)
    if not success_dev:
        print("Warning: Dev observability deployment encountered issues.")

    print("\n=== 2. Configuring OTEL_EXPORTER_OTLP_ENDPOINT on subtracker-prod-server ===")
    prod_script = f"""#!/bin/bash
set -e

echo "=== Updating /opt/subtracker-prod/.env with OTEL_EXPORTER_OTLP_ENDPOINT ==="
mkdir -p /opt/subtracker-prod
if [ -f /opt/subtracker-prod/.env ]; then
    if grep -q "^OTEL_EXPORTER_OTLP_ENDPOINT=" /opt/subtracker-prod/.env; then
        sed -i "s|^OTEL_EXPORTER_OTLP_ENDPOINT=.*|OTEL_EXPORTER_OTLP_ENDPOINT=http://{DEV_IP}:4317|" /opt/subtracker-prod/.env
    else
        echo "OTEL_EXPORTER_OTLP_ENDPOINT=http://{DEV_IP}:4317" >> /opt/subtracker-prod/.env
    fi
else
    echo "OTEL_EXPORTER_OTLP_ENDPOINT=http://{DEV_IP}:4317" > /opt/subtracker-prod/.env
fi

echo "Current prod .env OTEL configuration:"
grep "^OTEL_" /opt/subtracker-prod/.env || true
"""

    success_prod = run_ssm_script(PROD_INSTANCE, prod_script, timeout=120)
    if not success_prod:
        print("Warning: Prod configuration encountered issues.")


if __name__ == "__main__":
    main()
