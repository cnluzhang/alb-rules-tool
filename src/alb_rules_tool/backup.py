"""ALB rule backup functionality."""

import json
import yaml
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

def describe_alb_rules(listener_arn: str) -> List[Dict[str, Any]]:
    """Get all rules associated with an ALB listener.
    
    Args:
        listener_arn: ARN of the ALB listener
        
    Returns:
        List of rules associated with the listener
        
    Raises:
        ClientError: If there is an issue with the AWS API call
    """
    try:
        client = boto3.client('elbv2')
        response = client.describe_rules(ListenerArn=listener_arn)
        return response['Rules']
    except ClientError as e:
        logger.error(f"Error describing rules for listener {listener_arn}: {e}")
        raise

def backup_rules_to_file(rules: List[Dict[str, Any]], 
                      file_path: Optional[str] = None,
                      format_type: str = "json") -> str:
    """Save ALB rules to a local file.
    
    Args:
        rules: List of ALB rules to backup
        file_path: Path where to save the backup file (optional)
        format_type: Format to save the rules (json or yaml)
        
    Returns:
        Path to the created backup file
        
    Raises:
        ValueError: If format_type is not supported
        IOError: If there's an issue writing the file
    """
    if not file_path:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        file_path = f"alb-rules-backup-{timestamp}.{format_type}"
    
    try:
        with open(file_path, 'w') as f:
            if format_type.lower() == "json":
                json.dump(rules, f, indent=2)
            elif format_type.lower() == "yaml":
                yaml.dump(rules, f)
            else:
                raise ValueError(f"Unsupported format type: {format_type}. Use 'json' or 'yaml'.")
                
        logger.info(f"Successfully backed up rules to {file_path}")
        return file_path
    except IOError as e:
        logger.error(f"Error writing backup to file {file_path}: {e}")
        raise

def upload_backup_to_s3(file_path: str, bucket_name: str, s3_key: Optional[str] = None) -> str:
    """Upload a backup file to an S3 bucket.
    
    Args:
        file_path: Path to the local backup file
        bucket_name: S3 bucket name
        s3_key: S3 object key (optional)
        
    Returns:
        S3 URI of the uploaded file
        
    Raises:
        ClientError: If there is an issue with the AWS API call
    """
    if not s3_key:
        s3_key = file_path.split("/")[-1]
    
    try:
        s3_client = boto3.client('s3')
        s3_client.upload_file(file_path, bucket_name, s3_key)
        s3_uri = f"s3://{bucket_name}/{s3_key}"
        logger.info(f"Successfully uploaded backup to {s3_uri}")
        return s3_uri
    except ClientError as e:
        logger.error(f"Error uploading backup to S3: {e}")
        raise

def backup_alb_rules(listener_arn: str, 
                   output_path: Optional[str] = None,
                   format_type: str = "json",
                   upload_to_s3: bool = False,
                   s3_bucket: Optional[str] = None) -> Dict[str, str]:
    """Backup ALB rules for a given listener ARN.
    
    Args:
        listener_arn: ARN of the ALB listener
        output_path: Path where to save the backup file (optional)
        format_type: Format to save the rules (json or yaml)
        upload_to_s3: Whether to upload the backup to S3
        s3_bucket: S3 bucket name
        
    Returns:
        Dictionary containing paths to local backup file and S3 URI if applicable
        
    Raises:
        ValueError: If upload_to_s3 is True but s3_bucket is not provided
    """
    result = {}
    
    # Validate parameters
    if upload_to_s3 and not s3_bucket:
        raise ValueError("S3 bucket name is required when upload_to_s3 is True")
    
    # Get rules from ALB
    rules = describe_alb_rules(listener_arn)
    
    # Save to file
    local_path = backup_rules_to_file(rules, output_path, format_type)
    result["local_path"] = local_path
    
    # Upload to S3 if requested
    if upload_to_s3:
        s3_uri = upload_backup_to_s3(local_path, s3_bucket)
        result["s3_uri"] = s3_uri
    
    return result
