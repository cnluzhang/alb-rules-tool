# AWS Setup Guide for ALB Rules Tool

This guide covers the necessary AWS configurations to use the ALB Rules Tool effectively and securely.

## IAM Setup

### Option 1: IAM User for CLI Access

1. **Create IAM User**:
   - Navigate to the IAM console
   - Create a new user with programmatic access
   - Attach appropriate permissions (see [IAM Permissions Guide](iam_permissions.md))

2. **Generate Access Keys**:
   - Create access key and secret access key
   - Store these securely or use AWS CLI profiles

3. **Use with ALB Rules Tool**:
   ```bash
   # Via environment variables
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_REGION=us-east-1
   
   # Or via .env file in project root
   echo "AWS_ACCESS_KEY_ID=your_access_key" > .env
   echo "AWS_SECRET_ACCESS_KEY=your_secret_key" >> .env
   echo "AWS_REGION=us-east-1" >> .env
   ```

### Option 2: IAM Role for EC2/ECS (Recommended for Production)

1. **Create IAM Role**:
   - Navigate to the IAM console
   - Create a new role for EC2/ECS
   - Attach appropriate permissions (see [IAM Permissions Guide](iam_permissions.md))

2. **Assign Role**:
   - For EC2: Assign the role to the instance profile
   - For ECS: Reference the role in task definition
   - For EKS: Configure IRSA (IAM Roles for Service Accounts)

3. **Use with ALB Rules Tool**:
   ```bash
   # No credentials needed - instance metadata service provides them
   # Just specify the region if needed
   export AWS_REGION=us-east-1
   ```

## S3 Bucket for Backups

1. **Create S3 Bucket**:
   ```bash
   aws s3 mb s3://alb-rules-backups --region us-east-1
   ```

2. **Enable Versioning** (Recommended):
   ```bash
   aws s3api put-bucket-versioning \
     --bucket alb-rules-backups \
     --versioning-configuration Status=Enabled
   ```

3. **Enable Encryption** (Recommended):
   ```bash
   aws s3api put-bucket-encryption \
     --bucket alb-rules-backups \
     --server-side-encryption-configuration \
     '{
       "Rules": [
         {
           "ApplyServerSideEncryptionByDefault": {
             "SSEAlgorithm": "AES256"
           }
         }
       ]
     }'
   ```

4. **Configure Lifecycle Rules** (Optional):
   ```bash
   aws s3api put-bucket-lifecycle-configuration \
     --bucket alb-rules-backups \
     --lifecycle-configuration \
     '{
       "Rules": [
         {
           "ID": "Delete old backups",
           "Status": "Enabled",
           "Prefix": "",
           "Expiration": {
             "Days": 30
           }
         }
       ]
     }'
   ```

## AWS Secrets Manager (Optional)

If you prefer to store credentials in AWS Secrets Manager:

1. **Create Secret**:
   ```bash
   aws secretsmanager create-secret \
     --name alb-rules-tool/credentials \
     --description "ALB Rules Tool Credentials" \
     --secret-string '{"aws_access_key_id":"YOUR_ACCESS_KEY","aws_secret_access_key":"YOUR_SECRET_KEY"}'
   ```

2. **Use in Tool**:
   ```python
   # In config.py, the tool already has get_secret() function
   # Usage example:
   from alb_rules_tool.config import get_secret
   creds = get_secret("alb-rules-tool/credentials")
   ```

## Monitoring Setup

1. **CloudWatch Logs** (if running as Lambda or ECS task):
   - Ensure the execution role has permissions to write to CloudWatch Logs
   - Configure log retention period if needed

2. **CloudWatch Alarms** (for automated monitoring):
   ```bash
   aws cloudwatch put-metric-alarm \
     --alarm-name ALBRulesTool-RestoreFailure \
     --alarm-description "Alarm if restore operation fails" \
     --metric-name RestoreErrors \
     --namespace ALBRulesTool \
     --statistic Sum \
     --period 60 \
     --threshold 1 \
     --comparison-operator GreaterThanOrEqualToThreshold \
     --evaluation-periods 1 \
     --alarm-actions arn:aws:sns:us-east-1:account-id:topic-name
   ```

## Automation with AWS Lambda

For automated periodic backups:

1. **Create Lambda Function**:
   - Use Python 3.8+ runtime
   - Use the provided IAM policies for Lambda execution role
   - Package the ALB Rules Tool and dependencies
   
2. **Lambda Function Example**:
   ```python
   import os
   import boto3
   from alb_rules_tool.backup import backup_alb_rules
   from alb_rules_tool.logger import setup_logger
   
   logger = setup_logger()
   
   def lambda_handler(event, context):
       listener_arns = event.get('listener_arns', [])
       if not listener_arns:
           # Fetch all load balancers and listeners if not provided
           client = boto3.client('elbv2')
           lbs = client.describe_load_balancers()
           for lb in lbs['LoadBalancers']:
               listeners = client.describe_listeners(LoadBalancerArn=lb['LoadBalancerArn'])
               for listener in listeners['Listeners']:
                   listener_arns.append(listener['ListenerArn'])
       
       results = []
       for arn in listener_arns:
           try:
               result = backup_alb_rules(
                   listener_arn=arn,
                   format_type="json",
                   upload_to_s3=True,
                   s3_bucket=os.environ['BACKUP_BUCKET']
               )
               results.append({
                   "listener_arn": arn,
                   "status": "success",
                   "backup_location": result.get('s3_uri', '')
               })
           except Exception as e:
               logger.error(f"Error backing up {arn}: {e}")
               results.append({
                   "listener_arn": arn,
                   "status": "error",
                   "message": str(e)
               })
       
       return {
           "backup_results": results
       }
   ```

3. **Schedule with EventBridge**:
   ```bash
   aws events put-rule \
     --name DailyALBBackup \
     --schedule-expression "cron(0 1 * * ? *)" \
     --description "Daily backup of ALB rules at 1 AM UTC"
   
   aws events put-targets \
     --rule DailyALBBackup \
     --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:account-id:function:alb-backup-function"
   ```