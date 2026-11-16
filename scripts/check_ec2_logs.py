import boto3
import time

ssm = boto3.client("ssm", region_name="ap-southeast-2")

for name, instance_id in [("dev", "i-0ab9957b598dde50d"), ("prod", "i-0b8ca25bf547c7417")]:
    print(f"\n==================== Checking {name} ({instance_id}) ====================")
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["cat /var/lib/cloud/instance/scripts/part-001"]},
    )
    cmd_id = resp["Command"]["CommandId"]
    time.sleep(3)
    inv = ssm.get_command_invocation(CommandId=cmd_id, InstanceId=instance_id)
    print(inv.get("StandardOutputContent", "No standard output"))
    err = inv.get("StandardErrorContent", "")
    if err:
        print("STDERR:", err)
