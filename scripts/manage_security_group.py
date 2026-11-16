import boto3
from botocore.exceptions import ClientError

ec2 = boto3.client("ec2", region_name="ap-southeast-2")
cf = boto3.client("cloudformation", region_name="ap-southeast-2")

res = cf.describe_stack_resource(StackName="subtracker-dev", LogicalResourceId="InstanceSecurityGroup")
sg_name = res["StackResourceDetail"]["PhysicalResourceId"]

sgs = ec2.describe_security_groups(Filters=[{"Name": "group-name", "Values": [sg_name]}])["SecurityGroups"]
if not sgs:
    raise RuntimeError(f"Could not find security group with name {sg_name}")
sg_id = sgs[0]["GroupId"]
print(f"Dev Security Group Name: {sg_name}")
print(f"Dev Security Group ID: {sg_id}")

ports_to_open = [
    (3000, 3000, "Grafana UI"),
    (4317, 4317, "OpenTelemetry Collector OTLP gRPC"),
    (4318, 4318, "OpenTelemetry Collector OTLP HTTP"),
    (8080, 8080, "AI On-Call Responder Webhook / API"),
]

for from_port, to_port, desc in ports_to_open:
    try:
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": from_port,
                    "ToPort": to_port,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": desc}],
                }
            ],
        )
        print(f"[OK] Opened port {from_port} ({desc})")
    except ClientError as e:
        if "InvalidPermission.Duplicate" in str(e):
            print(f"- Port {from_port} already authorized ({desc})")
        else:
            print(f"Error opening port {from_port}: {e}")

print("\nUpdated Security Group Rules:")
sg = ec2.describe_security_groups(GroupIds=[sg_id])["SecurityGroups"][0]
for rule in sg["IpPermissions"]:
    print(f" - Port {rule.get('FromPort')}-{rule.get('ToPort')} ({rule.get('IpProtocol')}): {[r.get('CidrIp') for r in rule.get('IpRanges', [])]}")
