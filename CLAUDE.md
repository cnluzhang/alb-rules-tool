# ALB Rules Tool Development Guide

## Build/Test Commands
```bash
# Start dev environment
./scripts/dev.sh

# Install dependencies
./scripts/dev.sh pip install -r requirements.txt

# Install development dependencies
./scripts/dev.sh pip install -e ".[dev,test]"

# Run all tests
./scripts/dev.sh pytest

# Run a specific test
./scripts/dev.sh pytest tests/test_specific_file.py::test_specific_function

# Run with coverage
./scripts/dev.sh pytest --cov=alb_rules_tool

# Typecheck with mypy
./scripts/dev.sh mypy src

# Lint code
./scripts/dev.sh flake8 src tests

# Format code
./scripts/dev.sh black src tests
```

## Code Style Guidelines
- **Python version**: 3.8+ required
- **Imports**: Group imports (stdlib, third-party, local), alphabetize within groups
- **Formatting**: Use Black with default settings, 4 spaces for indentation
- **Types**: Use type hints for all functions and methods
- **Naming**: snake_case for variables/functions, CamelCase for classes
- **Documentation**: Docstrings for all public functions/methods/classes using Google style
- **Error handling**: Use specific exceptions, proper logging via Python logging module
- **Configuration**: Use environment variables or .env for credentials
- **AWS access**: Use boto3, never hardcode credentials
- **Security**: Always use encryption for backups, follow least privilege for IAM roles
- **Testing**: Write unit tests for all public functions with moto for AWS mocking
- **Development**: Always run commands in Docker development environment via scripts/dev.sh