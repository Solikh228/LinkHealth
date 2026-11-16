"""
Deploy and monitor SubTracker Dev and Prod CloudFormation stacks in AWS.
"""

import sys
import time
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

REGION = "ap-southeast-2"
DEV_STACK = "subtracker-dev"
PROD_STACK = "subtracker-prod"

cf = boto3.client("cloudformation", region_name=REGION)
root_dir = Path(__file__).resolve().parent.parent

with open(root_dir / "cloudformation.yaml", "r", encoding="utf-8") as f:
    dev_template = f.read()

with open(root_dir / "cloudformation-prod.yaml", "r", encoding="utf-8") as f:
    prod_template = f.read()


def get_stack_status(stack_name: str):
    try:
        resp = cf.describe_stacks(StackName=stack_name)
        return resp["Stacks"][0]
    except ClientError as e:
        if "does not exist" in str(e):
            return None
        raise


def create_or_check_stack(stack_name: str, template: str, params: list):
    stack = get_stack_status(stack_name)
    if stack:
        status = stack["StackStatus"]
        print(f"Stack '{stack_name}' already exists with status: {status}")
        return status

    print(f"Initiating stack creation for '{stack_name}'...")
    cf.create_stack(
        StackName=stack_name,
        TemplateBody=template,
        Parameters=params,
        Capabilities=["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
        Tags=[
            {"Key": "Project", "Value": "SubTracker"},
            {"Key": "Environment", "Value": "dev" if "dev" in stack_name else "prod"},
        ],
    )
    print(f"Stack '{stack_name}' creation request accepted.")
    return "CREATE_IN_PROGRESS"


def monitor_stacks(stack_names: list):
    active = set(stack_names)
    seen_events = set()

    print(f"\nMonitoring CloudFormation deployment for: {active}...\n")
    start_time = time.time()

    while active:
        for name in list(active):
            # Print latest events
            try:
                events = cf.describe_stack_events(StackName=name)["StackEvents"]
                for ev in reversed(events[:10]):
                    ev_id = ev["EventId"]
                    if ev_id not in seen_events:
                        seen_events.add(ev_id)
                        res_name = ev.get("LogicalResourceId", "")
                        status = ev.get("ResourceStatus", "")
                        reason = ev.get("ResourceStatusReason", "")
                        print(f"[{name}] {res_name} -> {status} {reason}")
            except Exception:
                pass

            stack = get_stack_status(name)
            if not stack:
                continue

            status = stack["StackStatus"]
            if status in ["CREATE_COMPLETE", "UPDATE_COMPLETE"]:
                print(f"\n SUCCESS: Stack '{name}' reached {status} in {int(time.time() - start_time)}s!\n")
                active.remove(name)
            elif "FAILED" in status or "ROLLBACK" in status:
                print(f"\n FAILED: Stack '{name}' entered {status}!")
                active.remove(name)

        if active:
            time.sleep(10)


def print_stack_outputs(stack_name: str):
    stack = get_stack_status(stack_name)
    if not stack:
        print(f"Stack '{stack_name}' not found.")
        return

    print(f"\n=======================================================")
    print(f" STACK OUTPUTS: {stack_name} ({stack['StackStatus']})")
    print(f"=======================================================")
    outputs = stack.get("Outputs", [])
    for out in outputs:
        key = out.get("OutputKey")
        val = out.get("OutputValue")
        desc = out.get("Description", "")
        print(f"- {key}: {val}  ({desc})")
    print(f"=======================================================\n")


def main():
    print("=== SubTracker Infrastructure Deployment ===")
    sts = boto3.client("sts", region_name=REGION)
    identity = sts.get_caller_identity()
    print(f"AWS Account: {identity['Account']}")
    print(f"IAM Caller ARN: {identity['Arn']}")
    print(f"AWS Region: {REGION}\n")

    # 1. Create Dev Stack
    create_or_check_stack(
        DEV_STACK,
        dev_template,
        [{"ParameterKey": "Environment", "ParameterValue": "dev"}],
    )

    # 2. Create Prod Stack
    create_or_check_stack(
        PROD_STACK,
        prod_template,
        [
            {"ParameterKey": "Environment", "ParameterValue": "prod"},
            {"ParameterKey": "CreateEcrRepository", "ParameterValue": "false"},
        ],
    )

    # 3. Monitor both
    monitor_stacks([DEV_STACK, PROD_STACK])

    # 4. Print Outputs
    print_stack_outputs(DEV_STACK)
    print_stack_outputs(PROD_STACK)


if __name__ == "__main__":
    main()
