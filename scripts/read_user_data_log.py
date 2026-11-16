import boto3
import time

ssm = boto3.client("ssm", region_name="ap-southeast-2")

resp = ssm.send_command(
    InstanceIds=["i-0ab9957b598dde50d"],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": ["tail -n 40 /var/log/user-data.log"]},
)
cmd_id = resp["Command"]["CommandId"]
time.sleep(3)
inv = ssm.get_command_invocation(CommandId=cmd_id, InstanceId="i-0ab9957b598dde50d")
print("=== user-data.log ===")
print(inv.get("StandardOutputContent", "No stdout"))
print(inv.get("StandardErrorContent", "No stderr"))
