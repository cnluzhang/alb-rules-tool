#!/bin/bash

# Start development environment and run commands within it

# Create the container if it doesn't exist or start it if stopped
if ! docker-compose -f docker-compose.dev.yml ps -q dev &>/dev/null; then
    echo "Starting development container..."
    docker-compose -f docker-compose.dev.yml up -d
fi

if [ $# -eq 0 ]; then
    # If no arguments provided, open an interactive shell in the container
    echo "Opening shell in development container..."
    docker-compose -f docker-compose.dev.yml exec dev bash
else
    # If arguments provided, run the specified command in the container
    echo "Running command in development container: $@"
    docker-compose -f docker-compose.dev.yml exec dev "$@"
fi