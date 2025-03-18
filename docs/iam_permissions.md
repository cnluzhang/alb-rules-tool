# IAM Permissions for ALB Rules Tool

This document outlines the recommended IAM permissions for using the ALB Rules Tool in both read-only (backup) and read-write (backup and restore) modes.

## Read-Only Permissions (Backup Only)

For environments where you only need to backup ALB rules without the ability to restore them, use these minimal permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ALBRulesToolReadOnly",
            "Effect": "Allow",
            "Action": [
                "elasticloadbalancing:DescribeRules",
                "elasticloadbalancing:DescribeListeners",
                "elasticloadbalancing:DescribeLoadBalancers"
            ],
            "Resource": "*"
        },
        {
            "Sid": "S3BackupStorage",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR_BACKUP_BUCKET_NAME",
                "arn:aws:s3:::YOUR_BACKUP_BUCKET_NAME/*"
            ]
        }
    ]
}
```

### Read-Only IAM Role Example

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

## Read-Write Permissions (Backup and Restore)

For environments where you need to both backup and restore ALB rules:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ALBRulesToolReadWrite",
            "Effect": "Allow",
            "Action": [
                "elasticloadbalancing:DescribeRules",
                "elasticloadbalancing:DescribeListeners",
                "elasticloadbalancing:DescribeLoadBalancers",
                "elasticloadbalancing:CreateRule",
                "elasticloadbalancing:DeleteRule",
                "elasticloadbalancing:ModifyRule"
            ],
            "Resource": "*"
        },
        {
            "Sid": "S3BackupStorage",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR_BACKUP_BUCKET_NAME",
                "arn:aws:s3:::YOUR_BACKUP_BUCKET_NAME/*"
            ]
        }
    ]
}
```

### Read-Write IAM Role Example

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

## Recommended Best Practices

1. **Least Privilege**: Always restrict permissions to only the specific ALB listeners you need to manage, by replacing the wildcard (`*`) with specific ARNs where possible.

2. **Resource Constraints**: Limit S3 permissions to only the specific bucket and directory path you use for backups.

3. **Using KMS for Encryption**: If using KMS encryption for S3 backups, add these permissions:

```json
{
    "Sid": "KMSForEncryption",
    "Effect": "Allow",
    "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:GenerateDataKey"
    ],
    "Resource": "arn:aws:kms:region:account-id:key/key-id"
}
```

4. **Cross-Account Access**: For backing up and restoring across AWS accounts, use IAM roles with cross-account assume role permissions.

5. **Secrets Management**: For credentials, use AWS Secrets Manager instead of hardcoding them:

```json
{
    "Sid": "SecretsManagerAccess",
    "Effect": "Allow",
    "Action": [
        "secretsmanager:GetSecretValue"
    ],
    "Resource": "arn:aws:secretsmanager:region:account-id:secret:secret-name-*"
}
```

## Sample IAM Policy for EC2 Instance Profile

If running the tool on an EC2 instance:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ALBRulesToolFullAccess",
            "Effect": "Allow",
            "Action": [
                "elasticloadbalancing:DescribeRules",
                "elasticloadbalancing:DescribeListeners",
                "elasticloadbalancing:CreateRule",
                "elasticloadbalancing:DeleteRule",
                "elasticloadbalancing:ModifyRule"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:ResourceTag/Environment": [
                        "Development",
                        "Staging"
                    ]
                }
            }
        },
        {
            "Sid": "S3BackupAccess",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::alb-rules-backups",
                "arn:aws:s3:::alb-rules-backups/*"
            ]
        }
    ]
}
```

## Sample IAM Policy for Lambda Execution Role

If running the tool as a scheduled Lambda function:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ALBRulesBackupOnly",
            "Effect": "Allow",
            "Action": [
                "elasticloadbalancing:DescribeRules",
                "elasticloadbalancing:DescribeListeners"
            ],
            "Resource": "*"
        },
        {
            "Sid": "S3BackupWriteAccess",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::alb-rules-backups",
                "arn:aws:s3:::alb-rules-backups/*"
            ]
        },
        {
            "Sid": "CloudWatchLogsAccess",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```