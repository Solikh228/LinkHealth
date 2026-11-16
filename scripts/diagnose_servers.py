import boto3
import time
import sys

sys.stdout.reconfigure(encoding="utf-8")
ssm = boto3.client("ssm", region_name="ap-southeast-2")

DEV_INSTANCE = "i-0ab9957b598dde50d"
PROD_INSTANCE = "i-0b8ca25bf547c7417"

diag_cmd = """
echo "=== 1. Memory and Swap ==="
free -h
swapon --show || true

echo "=== 2. Docker Containers ==="
docker ps -a

echo "=== 3. Listening Ports ==="
ss -tulpn | grep -E ':(80|443|3000|8000|8080)' || true

echo "=== 4. Systemd Service Status ==="
systemctl status subtracker-*.service --no-pager || true
"""

for name, instance_id in [("DEV", DEV_INSTANCE), ("PROD", PROD_INSTANCE)]:
    print(f"\n==================== DIAGNOSTICS: {name} ({instance_id}) ====================")
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [diag_cmd]},
    )
    cmd_id = resp["Command"]["CommandId"]
    time.sleep(5)
    inv = ssm.get_command_invocation(CommandId=cmd_id, InstanceId=instance_id)
    print(inv.get("StandardOutputContent", "No output"))
    err = inv.get("StandardErrorContent", "")
    if err:
        print("STDERR:\n", err)
