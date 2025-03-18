"""ALB rule restore functionality."""

import json
import yaml
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

def load_backup_file(file_path: str) -> List[Dict[str, Any]]:
    """Load backup rules from a file.
    
    Args:
        file_path: Path to the backup file
        
    Returns:
        List of ALB rules
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is not supported
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Backup file not found: {file_path}")
    
    try:
        _, ext = os.path.splitext(file_path)
        with open(file_path, 'r') as f:
            if ext.lower() == '.json':
                rules = json.load(f)
            elif ext.lower() in ['.yaml', '.yml']:
                rules = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported file format: {ext}")
        
        logger.info(f"Successfully loaded rules from {file_path}")
        return rules
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        logger.error(f"Error parsing backup file {file_path}: {e}")
        raise ValueError(f"Invalid file format: {e}")
    except Exception as e:
        logger.error(f"Error loading backup file {file_path}: {e}")
        raise

def download_backup_from_s3(bucket_name: str, s3_key: str, local_path: Optional[str] = None) -> str:
    """Download a backup file from S3.
    
    Args:
        bucket_name: S3 bucket name
        s3_key: S3 object key
        local_path: Local path to download the file to (optional)
        
    Returns:
        Path to the downloaded file
        
    Raises:
        ClientError: If there is an issue with the AWS API call
    """
    if not local_path:
        local_path = s3_key.split("/")[-1]
    
    try:
        s3_client = boto3.client('s3')
        s3_client.download_file(bucket_name, s3_key, local_path)
        logger.info(f"Successfully downloaded backup from s3://{bucket_name}/{s3_key} to {local_path}")
        return local_path
    except ClientError as e:
        logger.error(f"Error downloading backup from S3: {e}")
        raise

def _cleanup_rule_for_create(rule: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up rule data for creation.
    
    Removes fields that cannot be included when creating a rule.
    
    Args:
        rule: Rule data to clean up
        
    Returns:
        Cleaned up rule data ready for create_rule API
    """
    # Create a new dict with only allowed fields
    create_rule = {}
    
    # These fields are supported for create_rule API
    allowed_fields = [
        'Actions', 
        'Conditions', 
        'Priority'
    ]
    
    for field in allowed_fields:
        if field in rule:
            create_rule[field] = rule[field]
    
    return create_rule

def create_rule(listener_arn: str, rule: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new rule in the ALB listener.
    
    Args:
        listener_arn: ARN of the ALB listener
        rule: Rule data to create
        
    Returns:
        Response from AWS API
        
    Raises:
        ClientError: If there is an issue with the AWS API call
    """
    try:
        cleaned_rule = _cleanup_rule_for_create(rule)
        
        client = boto3.client('elbv2')
        response = client.create_rule(
            ListenerArn=listener_arn,
            **cleaned_rule
        )
        
        logger.info(f"Successfully created rule with priority {rule.get('Priority')}")
        return response
    except ClientError as e:
        logger.error(f"Error creating rule: {e}")
        raise

def delete_rule(rule_arn: str) -> Dict[str, Any]:
    """Delete an ALB rule.
    
    Args:
        rule_arn: ARN of the rule to delete
        
    Returns:
        Response from AWS API
        
    Raises:
        ClientError: If there is an issue with the AWS API call
    """
    try:
        client = boto3.client('elbv2')
        response = client.delete_rule(
            RuleArn=rule_arn
        )
        
        logger.info(f"Successfully deleted rule {rule_arn}")
        return response
    except ClientError as e:
        logger.error(f"Error deleting rule {rule_arn}: {e}")
        raise

def compare_rules(existing_rules: List[Dict[str, Any]], 
                backup_rules: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Compare existing rules with backup rules.
    
    Args:
        existing_rules: List of existing ALB rules
        backup_rules: List of backup ALB rules
        
    Returns:
        Tuple containing:
            - Rules to create (in backup but not in existing)
            - Rules to delete (in existing but not in backup)
            - Rules to update (in both but with differences)
    """
    # Extract rules by priority for easier comparison (skip default rule, priority '0')
    existing_by_priority = {rule['Priority']: rule for rule in existing_rules if rule['Priority'] != 'default'}
    backup_by_priority = {rule['Priority']: rule for rule in backup_rules if rule['Priority'] != 'default'}
    
    # Find rules to create (in backup but not in existing)
    create_priorities = set(backup_by_priority.keys()) - set(existing_by_priority.keys())
    rules_to_create = [backup_by_priority[p] for p in create_priorities]
    
    # Find rules to delete (in existing but not in backup)
    delete_priorities = set(existing_by_priority.keys()) - set(backup_by_priority.keys())
    rules_to_delete = [existing_by_priority[p] for p in delete_priorities]
    
    # Find rules to update (in both but with differences)
    # Note: This is a simple comparison and may need more sophisticated logic
    rules_to_update = []
    common_priorities = set(backup_by_priority.keys()) & set(existing_by_priority.keys())
    
    for priority in common_priorities:
        backup_rule = backup_by_priority[priority]
        existing_rule = existing_by_priority[priority]
        
        # Compare the rule content (excluding system fields like ARN, etc.)
        if (backup_rule.get('Actions') != existing_rule.get('Actions') or
            backup_rule.get('Conditions') != existing_rule.get('Conditions')):
            rules_to_update.append((existing_rule, backup_rule))
    
    return rules_to_create, rules_to_delete, rules_to_update

def restore_alb_rules(listener_arn: str, 
                     backup_file: str,
                     restore_mode: str = 'incremental') -> Dict[str, Any]:
    """Restore ALB rules from a backup file.
    
    Args:
        listener_arn: ARN of the ALB listener
        backup_file: Path to the backup file
        restore_mode: Mode of restore ('incremental' or 'full')
        
    Returns:
        Summary of restore operation
        
    Raises:
        ValueError: If restore_mode is not supported
        ClientError: If there is an issue with the AWS API call
    """
    if restore_mode not in ['incremental', 'full']:
        raise ValueError(f"Unsupported restore mode: {restore_mode}. Use 'incremental' or 'full'")
    
    # Load backup rules
    backup_rules = load_backup_file(backup_file)
    
    # Get existing rules
    client = boto3.client('elbv2')
    response = client.describe_rules(ListenerArn=listener_arn)
    existing_rules = response['Rules']
    
    result = {
        'created': 0,
        'deleted': 0,
        'updated': 0,
        'errors': 0
    }
    
    if restore_mode == 'full':
        # In full mode, delete all non-default existing rules first
        for rule in existing_rules:
            if rule['Priority'] != 'default':
                try:
                    delete_rule(rule['RuleArn'])
                    result['deleted'] += 1
                except Exception as e:
                    logger.error(f"Error deleting rule {rule['RuleArn']}: {e}")
                    result['errors'] += 1
        
        # Then create all backup rules
        for rule in backup_rules:
            if rule['Priority'] != 'default':
                try:
                    create_rule(listener_arn, rule)
                    result['created'] += 1
                except Exception as e:
                    logger.error(f"Error creating rule from backup: {e}")
                    result['errors'] += 1
    else:
        # In incremental mode, compare rules and apply changes
        rules_to_create, rules_to_delete, rules_to_update = compare_rules(
            existing_rules, backup_rules
        )
        
        # Create new rules
        for rule in rules_to_create:
            try:
                create_rule(listener_arn, rule)
                result['created'] += 1
            except Exception as e:
                logger.error(f"Error creating rule from backup: {e}")
                result['errors'] += 1
        
        # Update existing rules (delete and recreate)
        for existing_rule, backup_rule in rules_to_update:
            try:
                delete_rule(existing_rule['RuleArn'])
                create_rule(listener_arn, backup_rule)
                result['updated'] += 1
            except Exception as e:
                logger.error(f"Error updating rule {existing_rule['RuleArn']}: {e}")
                result['errors'] += 1
        
        # Delete rules not in backup
        for rule in rules_to_delete:
            try:
                delete_rule(rule['RuleArn'])
                result['deleted'] += 1
            except Exception as e:
                logger.error(f"Error deleting rule {rule['RuleArn']}: {e}")
                result['errors'] += 1
    
    logger.info(f"Restore summary: {result}")
    return result