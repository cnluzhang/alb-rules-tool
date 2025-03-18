# AWS ALB Rules Backup and Restore Tool

A command-line tool to backup and restore AWS Application Load Balancer (ALB) listener rules, helping prevent accidental rule deletion and improve disaster recovery capabilities.

## Features

- **Backup Rules**: Save ALB rules from a listener to a local file or S3 bucket
- **Restore Rules**: Restore ALB rules from a backup file (local or S3)
- **Multiple Formats**: Support for both JSON and YAML backup formats
- **Restore Modes**: Support for incremental and full restore modes
- **Logging**: Comprehensive logging with customizable verbosity
- **AWS Integration**: Secure authentication using standard AWS credentials

## Development Environment

### Using Docker (Recommended)

The project includes a Docker development environment that ensures consistent setups across different machines.

```bash
# Start dev environment and get a shell
./scripts/dev.sh

# Run a specific command in dev environment
./scripts/dev.sh pip install -e .
./scripts/dev.sh pytest
./scripts/dev.sh alb-rules --help
```

### Local Setup (Alternative)

```bash
# Clone the repository
git clone https://github.com/yourusername/alb-rules-tool.git
cd alb-rules-tool

# Install the package
pip install -e .
```

## Requirements

- Python 3.8+
- AWS credentials with appropriate permissions
- Required Python packages (installed automatically):
  - boto3
  - click
  - pyyaml
  - python-dotenv

## Usage

### Backup ALB Rules

```bash
# Basic backup to JSON file
./scripts/dev.sh alb-rules backup arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-load-balancer/1234567890/1234567890

# Specify output file and format
./scripts/dev.sh alb-rules backup arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-load-balancer/1234567890/1234567890 \
  --output rules-backup.yaml --format yaml

# Backup to S3
./scripts/dev.sh alb-rules backup arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-load-balancer/1234567890/1234567890 \
  --s3-bucket my-backup-bucket
```

### Restore ALB Rules

```bash
# Incremental restore (only changes rules that differ)
./scripts/dev.sh alb-rules restore arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-load-balancer/1234567890/1234567890 \
  rules-backup.json

# Full restore (deletes all existing rules and creates new ones from backup)
./scripts/dev.sh alb-rules restore arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-load-balancer/1234567890/1234567890 \
  rules-backup.json --mode full

# Restore from S3
./scripts/dev.sh alb-rules restore arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-load-balancer/1234567890/1234567890 \
  rules-backup.json --s3-bucket my-backup-bucket --s3-key backups/rules-backup.json
```

## AWS Credentials

The tool uses standard AWS credential resolution:

1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
2. Shared credential file (~/.aws/credentials)
3. IAM role for EC2 or ECS

You can also use a `.env` file in the current directory for credentials:

```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

## IAM Permissions

This tool requires specific AWS IAM permissions. See [IAM Permissions Guide](docs/iam_permissions.md) for detailed permission setups for:

- Read-only access (backup only)
- Read-write access (backup and restore)
- Sample policies for EC2, Lambda, and ECS deployments

For detailed AWS setup instructions, see [AWS Setup Guide](docs/aws_setup.md).

## Development

### Run Tests

```bash
# Run all tests
./scripts/dev.sh pytest

# Run with coverage
./scripts/dev.sh pytest --cov=alb_rules_tool

# Run specific test
./scripts/dev.sh pytest tests/test_specific_file.py::test_specific_function
```

### Code Style

This project uses:
- Black for code formatting
- flake8 for style checking
- mypy for type checking

```bash
# Format code
./scripts/dev.sh black src tests

# Check style
./scripts/dev.sh flake8 src tests

# Check types
./scripts/dev.sh mypy src
```

## Production Deployment

For production deployment, use the standard Dockerfile:

```bash
# Build and run the production image
docker build -t alb-rules-tool .
docker run -v ~/.aws:/home/appuser/.aws:ro alb-rules-tool backup arn:aws:elasticloadbalancing:...
```

You can also use docker-compose:

```bash
# Edit the command in docker-compose.yml, then run:
docker-compose run --rm alb-rules-tool
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.