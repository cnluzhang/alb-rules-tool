"""Configuration management for the ALB Rules Tool."""

import os
from typing import Dict, Optional, Any
import boto3
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

def load_aws_config() -> Dict[str, str]:
    """Load AWS configuration from environment variables.
    
    Returns:
        Dictionary with AWS configuration
    """
    config = {}
    
    # AWS credentials and region
    config["region"] = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION"))
    
    # Check if AWS credentials are set in environment
    if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get("AWS_SECRET_ACCESS_KEY"):
        logger.info("AWS credentials not found in environment variables. Using boto3 credential discovery.")
    
    return config

def get_secret(secret_name: str, region_name: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve a secret from AWS Secrets Manager.
    
    Args:
        secret_name: Name of the secret
        region_name: AWS region name (optional)
        
    Returns:
        Dictionary containing the secret values
        
    Raises:
        Exception: If the secret cannot be retrieved
    """
    if not region_name:
        region_name = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION"))
    
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        logger.error(f"Error retrieving secret {secret_name}: {e}")
        raise
    
    # Parse the secret string
    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
        return json.loads(secret)
    else:
        logger.error(f"Secret {secret_name} does not contain SecretString")
        raise ValueError(f"Secret {secret_name} does not contain SecretString")
