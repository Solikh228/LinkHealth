import boto3

cf = boto3.client("cloudformation", region_name="ap-southeast-2")

for stack_name in ["subtracker-dev", "subtracker-prod"]:
    print(f"\n==================== {stack_name} ====================")
    try:
        stack = cf.describe_stacks(StackName=stack_name)["Stacks"][0]
        print(f"Status: {stack['StackStatus']}")
        
        resources = cf.list_stack_resources(StackName=stack_name)["StackResourceSummaries"]
        for r in resources:
            print(f"- {r['LogicalResourceId']} ({r['ResourceType']}): {r['ResourceStatus']}")
            
        print("\nLatest 5 events:")
        events = cf.describe_stack_events(StackName=stack_name)["StackEvents"]
        for e in events[:5]:
            ts = e["Timestamp"].strftime("%H:%M:%S")
            print(f"  [{ts}] {e.get('LogicalResourceId')}: {e.get('ResourceStatus')} ({e.get('ResourceStatusReason', '')})")
    except Exception as e:
        print("Error:", e)
