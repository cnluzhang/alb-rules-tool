"""Tests for the restore module."""

import os
import json
import tempfile
from unittest.mock import patch, mock_open, MagicMock
import pytest
from alb_rules_tool.restore import (
    load_backup_file,
    download_backup_from_s3,
    create_rule,
    delete_rule,
    compare_rules,
    restore_alb_rules
)

def test_load_backup_file():
    """Test load_backup_file function."""
    test_rules = [
        {"Priority": "1", "Conditions": [], "Actions": []},
        {"Priority": "2", "Conditions": [], "Actions": []}
    ]
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as json_file:
        json.dump(test_rules, json_file)
        json_path = json_file.name
    
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as yaml_file:
        yaml_file.write(b"- Priority: '1'\n  Conditions: []\n  Actions: []\n- Priority: '2'\n  Conditions: []\n  Actions: []\n")
        yaml_path = yaml_file.name
    
    try:
        # Test loading JSON
        json_rules = load_backup_file(json_path)
        assert json_rules == test_rules
        
        # Test loading YAML
        yaml_rules = load_backup_file(yaml_path)
        assert len(yaml_rules) == 2
        assert yaml_rules[0]["Priority"] == "1"
        assert yaml_rules[1]["Priority"] == "2"
        
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            load_backup_file("non_existent_file.json")
        
        # Test with unsupported file format
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as bad_file:
            bad_file.write(b"This is not a valid backup file")
            bad_path = bad_file.name
        
        with pytest.raises(ValueError):
            load_backup_file(bad_path)
    
    finally:
        # Clean up temp files
        for path in [json_path, yaml_path, bad_path]:
            if os.path.exists(path):
                os.remove(path)

def test_download_backup_from_s3(s3_client, mock_s3_bucket):
    """Test download_backup_from_s3 function."""
    bucket_name = mock_s3_bucket
    s3_key = "test_backup.json"
    
    # Upload a test file to S3
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=json.dumps({"test": "data"})
    )
    
    # Test download
    try:
        local_path = download_backup_from_s3(bucket_name, s3_key)
        
        # Check file was downloaded
        assert os.path.exists(local_path)
        assert local_path == s3_key
        
        # Check content
        with open(local_path, "r") as f:
            content = json.load(f)
            assert content == {"test": "data"}
    
    finally:
        # Clean up local file
        if os.path.exists(s3_key):
            os.remove(s3_key)

def test_create_rule(elbv2_client, mock_alb_listener):
    """Test create_rule function."""
    listener_arn = mock_alb_listener["listener_arn"]
    target_group_arn = mock_alb_listener["target_group_arn"]
    
    # Test data
    rule = {
        "Priority": "5",
        "Conditions": [
            {
                "Field": "path-pattern",
                "Values": ["/test/*"]
            }
        ],
        "Actions": [
            {
                "Type": "forward",
                "TargetGroupArn": target_group_arn
            }
        ],
        # These shouldn't be included in create_rule
        "RuleArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:listener-rule/app/my-load-balancer/1234567890/1234567890/1234567890",
        "IsDefault": False
    }
    
    # Create rule
    response = create_rule(listener_arn, rule)
    
    # Check response
    assert "Rules" in response
    assert len(response["Rules"]) == 1
    assert response["Rules"][0]["Priority"] == "5"
    
    # Check rule was created properly
    client = boto3.client("elbv2", region_name="us-east-1")
    rules_response = client.describe_rules(ListenerArn=listener_arn)
    
    # Should now have default rule + 3 custom rules
    assert len(rules_response["Rules"]) == 4
    
    # Find the new rule
    new_rule = None
    for rule in rules_response["Rules"]:
        if rule["Priority"] == "5":
            new_rule = rule
            break
    
    assert new_rule is not None
    assert len(new_rule["Conditions"]) == 1
    assert new_rule["Conditions"][0]["Field"] == "path-pattern"
    assert "/test/*" in new_rule["Conditions"][0]["Values"]

def test_delete_rule(elbv2_client, mock_alb_listener):
    """Test delete_rule function."""
    rule_arn = mock_alb_listener["rule_arns"][0]
    listener_arn = mock_alb_listener["listener_arn"]
    
    # Check rule exists
    client = boto3.client("elbv2", region_name="us-east-1")
    rules_before = client.describe_rules(ListenerArn=listener_arn)
    assert len(rules_before["Rules"]) == 3  # default + 2 custom
    
    # Delete rule
    response = delete_rule(rule_arn)
    
    # Check response
    assert response == {}
    
    # Check rule was deleted
    rules_after = client.describe_rules(ListenerArn=listener_arn)
    assert len(rules_after["Rules"]) == 2  # default + 1 custom

def test_compare_rules():
    """Test compare_rules function."""
    # Test data
    existing_rules = [
        {"Priority": "default", "IsDefault": True},
        {"Priority": "1", "Conditions": [{"Field": "path-pattern", "Values": ["/api/*"]}], "Actions": [{"Type": "forward"}]},
        {"Priority": "2", "Conditions": [{"Field": "host-header", "Values": ["api.example.com"]}], "Actions": [{"Type": "forward"}]},
        {"Priority": "3", "Conditions": [{"Field": "path-pattern", "Values": ["/old/*"]}], "Actions": [{"Type": "forward"}]}
    ]
    
    backup_rules = [
        {"Priority": "default", "IsDefault": True},
        {"Priority": "1", "Conditions": [{"Field": "path-pattern", "Values": ["/api/*"]}], "Actions": [{"Type": "forward"}]},
        {"Priority": "2", "Conditions": [{"Field": "host-header", "Values": ["api.example.com"]}], "Actions": [{"Type": "redirect"}]},  # Changed action
        {"Priority": "4", "Conditions": [{"Field": "path-pattern", "Values": ["/new/*"]}], "Actions": [{"Type": "forward"}]}  # New rule
    ]
    
    # Compare rules
    to_create, to_delete, to_update = compare_rules(existing_rules, backup_rules)
    
    # Check results
    assert len(to_create) == 1
    assert to_create[0]["Priority"] == "4"
    
    assert len(to_delete) == 1
    assert to_delete[0]["Priority"] == "3"
    
    assert len(to_update) == 1
    assert to_update[0][0]["Priority"] == "2"  # Existing rule
    assert to_update[0][1]["Priority"] == "2"  # Backup rule
    assert to_update[0][1]["Actions"][0]["Type"] == "redirect"  # Changed action

def test_restore_alb_rules(elbv2_client, mock_alb_listener):
    """Test restore_alb_rules function."""
    listener_arn = mock_alb_listener["listener_arn"]
    target_group_arn = mock_alb_listener["target_group_arn"]
    
    # Create a backup file
    backup_rules = [
        {"Priority": "default", "IsDefault": True, "Actions": [{"Type": "forward", "TargetGroupArn": target_group_arn}]},
        {"Priority": "5", "Conditions": [{"Field": "path-pattern", "Values": ["/new/*"]}], 
         "Actions": [{"Type": "forward", "TargetGroupArn": target_group_arn}]}
    ]
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        json.dump(backup_rules, f)
        backup_file = f.name
    
    try:
        # Mock the load_backup_file function to return our test data
        with patch("alb_rules_tool.restore.load_backup_file", return_value=backup_rules):
            # Test incremental restore
            result = restore_alb_rules(listener_arn, backup_file, "incremental")
            
            # Check result
            assert result["created"] == 1  # One new rule
            assert result["errors"] == 0
            
            # Check rule was created
            client = boto3.client("elbv2", region_name="us-east-1")
            rules = client.describe_rules(ListenerArn=listener_arn)
            
            # Should have default rule + 3 custom rules (2 original + 1 new)
            assert len(rules["Rules"]) == 4
            
            # Should have the new rule with priority 5
            priorities = [rule["Priority"] for rule in rules["Rules"]]
            assert "5" in priorities
            
            # Test full restore
            result = restore_alb_rules(listener_arn, backup_file, "full")
            
            # Check result
            assert result["deleted"] > 0  # Should have deleted the original rules
            assert result["created"] == 1  # Should have created our backup rule
            
            # Check rules after full restore
            rules = client.describe_rules(ListenerArn=listener_arn)
            
            # Should have default rule + 1 custom rule from backup
            assert len(rules["Rules"]) == 2
            
            # Priorities should be 'default' and '5'
            priorities = [rule["Priority"] for rule in rules["Rules"]]
            assert "default" in priorities
            assert "5" in priorities
    
    finally:
        # Clean up
        if os.path.exists(backup_file):
            os.remove(backup_file)