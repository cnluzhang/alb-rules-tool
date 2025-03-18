# Using Docker with ALB Rules Tool

This guide demonstrates how to use Docker for both development and production with the ALB Rules Tool.

## Development Environment

The development environment is set up to provide a consistent experience across different machines.

### Starting the Dev Environment

```bash
# Start a shell in the dev environment
./scripts/dev.sh

# Or run a one-off command
./scripts/dev.sh pytest
```

### Using Make for Common Tasks

We've also included a Makefile for common development tasks:

```bash
# Start dev shell
make dev

# Run tests
make test

# Format code
make format

# Check code style and types
make lint
```

## Production Usage

For production use, we have two options:

### 1. Using the Production Docker Image

```bash
# Build the image
docker build -t alb-rules-tool .

# Run a command
docker run -v ~/.aws:/home/appuser/.aws:ro alb-rules-tool backup \
  arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-lb/1234567890/1234567890
```

### 2. Using Docker Compose

Edit the docker-compose.yml file to change the command:

```yaml
services:
  alb-rules-tool:
    # ...
    command: backup arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-lb/1234567890/1234567890
```

Then run:

```bash
docker-compose run --rm alb-rules-tool
```

## CI/CD Integration

If you're using GitHub Actions, our workflow in `.github/workflows/ci.yml` already handles:

1. Building the Docker image
2. Running tests in the container
3. Building the package for distribution

For other CI systems, you can use our Docker setup as a reference.