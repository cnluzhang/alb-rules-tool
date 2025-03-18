"""Pytest configuration file."""

import os
import pytest
import boto3
from moto import mock_elbv2, mock_s3

@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for boto3."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture(scope="function")
def elbv2_client(aws_credentials):
    """Mocked ELBv2 client."""
    with mock_elbv2():
        client = boto3.client("elbv2", region_name="us-east-1")
        yield client

@pytest.fixture(scope="function")
def s3_client(aws_credentials):
    """Mocked S3 client."""
    with mock_s3():
        client = boto3.client("s3", region_name="us-east-1")
        yield client

@pytest.fixture(scope="function")
def mock_alb_listener(elbv2_client):
    """Create a mock ALB and listener."""
    # Create a mock VPC
    ec2 = boto3.client("ec2", region_name="us-east-1")
    vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
    vpc_id = vpc["Vpc"]["VpcId"]
    
    # Create subnets
    subnet_1 = ec2.create_subnet(VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone="us-east-1a")
    subnet_2 = ec2.create_subnet(VpcId=vpc_id, CidrBlock="10.0.2.0/24", AvailabilityZone="us-east-1b")
    subnet_ids = [subnet_1["Subnet"]["SubnetId"], subnet_2["Subnet"]["SubnetId"]]
    
    # Create security group
    sg = ec2.create_security_group(GroupName="test-sg", Description="Test SG", VpcId=vpc_id)
    sg_id = sg["GroupId"]
    
    # Create target group
    target_group = elbv2_client.create_target_group(
        Name="test-target-group",
        Protocol="HTTP",
        Port=80,
        VpcId=vpc_id,
        TargetType="instance"
    )
    target_group_arn = target_group["TargetGroups"][0]["TargetGroupArn"]
    
    # Create ALB
    lb = elbv2_client.create_load_balancer(
        Name="test-alb",
        Subnets=subnet_ids,
        SecurityGroups=[sg_id],
        Type="application"
    )
    lb_arn = lb["LoadBalancers"][0]["LoadBalancerArn"]
    
    # Create listener
    listener = elbv2_client.create_listener(
        LoadBalancerArn=lb_arn,
        Protocol="HTTP",
        Port=80,
        DefaultActions=[
            {
                "Type": "forward",
                "TargetGroupArn": target_group_arn
            }
        ]
    )
    listener_arn = listener["Listeners"][0]["ListenerArn"]
    
    # Create some rules
    rule1 = elbv2_client.create_rule(
        ListenerArn=listener_arn,
        Priority="1",
        Conditions=[
            {
                "Field": "path-pattern",
                "Values": ["/api/*"]
            }
        ],
        Actions=[
            {
                "Type": "forward",
                "TargetGroupArn": target_group_arn
            }
        ]
    )
    
    rule2 = elbv2_client.create_rule(
        ListenerArn=listener_arn,
        Priority="2",
        Conditions=[
            {
                "Field": "host-header",
                "Values": ["api.example.com"]
            }
        ],
        Actions=[
            {
                "Type": "forward",
                "TargetGroupArn": target_group_arn
            }
        ]
    )
    
    return {
        "listener_arn": listener_arn,
        "rule_arns": [rule1["Rules"][0]["RuleArn"], rule2["Rules"][0]["RuleArn"]],
        "target_group_arn": target_group_arn
    }

@pytest.fixture
def mock_s3_bucket(s3_client):
    """Create a mock S3 bucket."""
    bucket_name = "test-alb-rules-backup"
    s3_client.create_bucket(Bucket=bucket_name)
    return bucket_name
