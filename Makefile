.PHONY: dev install test lint format clean build run help

help:
	@echo "Available commands:"
	@echo "  make dev       - Start development shell in Docker"
	@echo "  make install   - Install the package in development mode"
	@echo "  make test      - Run tests"
	@echo "  make lint      - Run linters (flake8, mypy)"
	@echo "  make format    - Format code with Black"
	@echo "  make clean     - Clean up build artifacts"
	@echo "  make build     - Build Docker image"
	@echo "  make run       - Run CLI with arguments (e.g., make run ARGS='backup --help')"

dev:
	./scripts/dev.sh

install:
	./scripts/dev.sh pip install -e ".[dev,test]"

test:
	./scripts/dev.sh pytest --cov=alb_rules_tool

lint:
	./scripts/dev.sh flake8 src tests
	./scripts/dev.sh mypy src

format:
	./scripts/dev.sh black src tests

clean:
	./scripts/dev.sh rm -rf build/ dist/ *.egg-info .pytest_cache/ .coverage

build:
	docker build -t alb-rules-tool .

run:
ifdef ARGS
	./scripts/dev.sh alb-rules $(ARGS)
else
	@echo "Please specify arguments with ARGS='...'"
	@echo "Example: make run ARGS='backup --help'"
endif