"""Command-line interface for the ALB Rules Tool."""

import click
import logging
import os
from typing import Optional

from alb_rules_tool.backup import backup_alb_rules
from alb_rules_tool.restore import restore_alb_rules, download_backup_from_s3
from alb_rules_tool.logger import setup_logger
from alb_rules_tool.config import load_aws_config

# Set up logger
logger = setup_logger()

@click.group()
@click.option('--debug/--no-debug', default=False, help='Enable debug logging')
@click.option('--log-file', help='Path to log file')
def cli(debug: bool, log_file: Optional[str]) -> None:
    """ALB Rules backup and restore tool.
    
    This tool helps you backup and restore AWS Application Load Balancer (ALB)
    rules to prevent accidental loss and improve disaster recovery capabilities.
    """
    # Configure logging based on CLI options
    log_level = "DEBUG" if debug else "INFO"
    global logger
    logger = setup_logger(log_level=log_level, log_file=log_file)
    
    # Load AWS configuration
    load_aws_config()

@cli.command()
@click.argument('listener-arn', required=True)
@click.option('--output', '-o', help='Output path for the backup file')
@click.option('--format', '-f', type=click.Choice(['json', 'yaml'], case_sensitive=False), 
              default='json', help='Output format (json or yaml)')
@click.option('--s3-bucket', help='S3 bucket name for uploading the backup')
def backup(listener_arn: str, output: Optional[str], format: str, s3_bucket: Optional[str]) -> None:
    """Backup ALB rules for a given listener ARN.
    
    LISTENER-ARN is the ARN of the ALB listener to backup rules from.
    """
    try:
        upload_to_s3 = s3_bucket is not None
        result = backup_alb_rules(
            listener_arn=listener_arn,
            output_path=output,
            format_type=format,
            upload_to_s3=upload_to_s3,
            s3_bucket=s3_bucket
        )
        
        click.echo(f"Backup completed successfully!")
        click.echo(f"Local backup file: {result['local_path']}")
        
        if upload_to_s3 and 's3_uri' in result:
            click.echo(f"S3 URI: {result['s3_uri']}")
    
    except Exception as e:
        logger.error(f"Failed to backup ALB rules: {e}")
        click.echo(f"Error: {e}")
        raise click.Abort()

@cli.command()
@click.argument('listener-arn', required=True)
@click.argument('backup-file', required=True)
@click.option('--mode', type=click.Choice(['incremental', 'full'], case_sensitive=False),
              default='incremental', help='Restore mode (incremental or full)')
@click.option('--s3-bucket', help='S3 bucket name if backup file is in S3')
@click.option('--s3-key', help='S3 key if backup file is in S3')
def restore(listener_arn: str, backup_file: str, mode: str, 
           s3_bucket: Optional[str], s3_key: Optional[str]) -> None:
    """Restore ALB rules for a given listener ARN from a backup file.
    
    LISTENER-ARN is the ARN of the ALB listener to restore rules to.
    
    BACKUP-FILE is the path to the backup file. If the file is in S3,
    provide --s3-bucket and --s3-key options.
    """
    try:
        # If S3 parameters are provided, download the backup file first
        if s3_bucket and s3_key:
            click.echo(f"Downloading backup file from S3...")
            backup_file = download_backup_from_s3(
                bucket_name=s3_bucket,
                s3_key=s3_key,
                local_path=backup_file
            )
        
        click.echo(f"Restoring ALB rules in {mode} mode...")
        result = restore_alb_rules(
            listener_arn=listener_arn,
            backup_file=backup_file,
            restore_mode=mode
        )
        
        click.echo("Restore completed successfully!")
        click.echo(f"Rules created: {result['created']}")
        click.echo(f"Rules updated: {result['updated']}")
        click.echo(f"Rules deleted: {result['deleted']}")
        
        if result['errors'] > 0:
            click.echo(f"Errors encountered: {result['errors']} (check logs for details)")
    
    except Exception as e:
        logger.error(f"Failed to restore ALB rules: {e}")
        click.echo(f"Error: {e}")
        raise click.Abort()

if __name__ == '__main__':
    cli()