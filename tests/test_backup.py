"""Tests for the backup module."""

import os
import json
import yaml
from unittest.mock import patch, mock_open
import pytest
from alb_rules_tool.backup import describe_alb_rules, backup_rules_to_file, upload_backup_to_s3, backup_alb_rules

def test_describe_alb_rules(elbv2_client, mock_alb_listener):
    """Test describe_alb_rules function."""
    listener_arn = mock_alb_listener["listener_arn"]
    rules = describe_alb_rules(listener_arn)
    
    # Should have default rule + 2 custom rules
    assert len(rules) == 3
    
    # Check that rules have the expected structure
    rule_priorities = [rule["Priority"] for rule in rules]
    assert "default" in rule_priorities
    assert "1" in rule_priorities
    assert "2" in rule_priorities

def test_backup_rules_to_file():
    """Test backup_rules_to_file function."""
    test_rules = [
        {"Priority": "1", "Conditions": [], "Actions": []},
        {"Priority": "2", "Conditions": [], "Actions": []}
    ]
    
    # Test with JSON format
    with patch("builtins.open", mock_open()) as mocked_file:
        result = backup_rules_to_file(test_rules, "backup.json", "json")
        assert result == "backup.json"
        mocked_file.assert_called_once_with("backup.json", "w")
    
    # Test with YAML format
    with patch("builtins.open", mock_open()) as mocked_file:
        result = backup_rules_to_file(test_rules, "backup.yaml", "yaml")
        assert result == "backup.yaml"
        mocked_file.assert_called_once_with("backup.yaml", "w")

def test_upload_backup_to_s3(s3_client, mock_s3_bucket):
    """Test upload_backup_to_s3 function."""
    bucket_name = mock_s3_bucket
    
    # Create a temp file
    with open("temp_backup.json", "w") as f:
        json.dump({"test": "data"}, f)
    
    try:
        # Test upload
        result = upload_backup_to_s3("temp_backup.json", bucket_name)
        
        # Check result
        assert result == f"s3://{bucket_name}/temp_backup.json"
        
        # Verify file exists in S3
        objects = s3_client.list_objects_v2(Bucket=bucket_name)
        assert "Contents" in objects
        assert len(objects["Contents"]) == 1
        assert objects["Contents"][0]["Key"] == "temp_backup.json"
    finally:
        # Clean up temp file
        if os.path.exists("temp_backup.json"):
            os.remove("temp_backup.json")

def test_backup_alb_rules(elbv2_client, mock_alb_listener, s3_client, mock_s3_bucket):
    """Test backup_alb_rules function."""
    listener_arn = mock_alb_listener["listener_arn"]
    
    # Test basic backup
    with patch("alb_rules_tool.backup.backup_rules_to_file",
             return_value="test_output.json") as mock_backup_to_file:
        result = backup_alb_rules(listener_arn, "test_output.json")
        assert mock_backup_to_file.called
        assert result["local_path"] == "test_output.json"
    
    # Test with S3 upload
    with patch("alb_rules_tool.backup.backup_rules_to_file",
             return_value="test_output.json") as mock_backup_to_file, \
         patch("alb_rules_tool.backup.upload_backup_to_s3",
                return_value=f"s3://{mock_s3_bucket}/test_output.json") as mock_upload_to_s3:
        result = backup_alb_rules(
            listener_arn=listener_arn,
            output_path="test_output.json",
            upload_to_s3=True,
            s3_bucket=mock_s3_bucket
        )
        
        assert mock_backup_to_file.called
        assert mock_upload_to_s3.called
        assert result["local_path"] == "test_output.json"
        assert result["s3_uri"] == f"s3://{mock_s3_bucket}/test_output.json"
