#!/usr/bin/env python3
"""
Example usage of the ALB Rules Tool library.

This example shows how to use the library functions directly
without going through the CLI interface.
"""

import os
import logging
from alb_rules_tool.backup import backup_alb_rules
from alb_rules_tool.restore import restore_alb_rules
from alb_rules_tool.logger import setup_logger

# Set up logger
logger = setup_logger(log_level="INFO")

def main():
    """Run the example."""
    # Replace this with your actual listener ARN
    listener_arn = "arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-load-balancer/1234567890/1234567890"
    
    # Backup the rules
    print("Creating backup of ALB rules...")
    backup_result = backup_alb_rules(
        listener_arn=listener_arn,
        output_path="alb-rules-backup.json",
        format_type="json"
    )
    print(f"Backup created: {backup_result['local_path']}")
    
    # Wait for user confirmation to restore
    input("Press Enter to restore the rules...")
    
    # Restore the rules
    print("Restoring ALB rules...")
    restore_result = restore_alb_rules(
        listener_arn=listener_arn,
        backup_file=backup_result['local_path'],
        restore_mode="incremental"
    )
    
    print("Restore completed:")
    print(f"  Rules created: {restore_result['created']}")
    print(f"  Rules updated: {restore_result['updated']}")
    print(f"  Rules deleted: {restore_result['deleted']}")
    print(f"  Errors encountered: {restore_result['errors']}")

if __name__ == "__main__":
    main()