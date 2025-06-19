#!/bin/bash
# Kite Trading Server - Docker Entrypoint Script

set -e

# Create necessary directories
mkdir -p /app/data /app/logs

# Set proper permissions
chown -R appuser:appuser /app/data /app/logs

# Function to wait for dependencies
wait_for_dependencies() {
    echo "Checking dependencies..."
    # Add any dependency checks here if needed
    echo "Dependencies ready."
}

# Function to run FastAPI server
run_fastapi() {
    echo "Starting FastAPI Trading Server..."
    exec python fastapi_server.py
}

# Function to run MCP server
run_mcp() {
    echo "Starting MCP Trading Server..."
    exec python index.py
}

# Function to run setup authentication
run_setup_auth() {
    echo "Running authentication setup..."
    exec python setup_auth.py
}

# Main execution logic
case "${1:-fastapi}" in
    fastapi)
        wait_for_dependencies
        run_fastapi
        ;;
    mcp)
        wait_for_dependencies
        run_mcp
        ;;
    setup-auth)
        run_setup_auth
        ;;
    *)
        echo "Usage: $0 {fastapi|mcp|setup-auth}"
        echo "  fastapi    - Start FastAPI server (default)"
        echo "  mcp        - Start MCP server for Claude Desktop"
        echo "  setup-auth - Run authentication setup"
        exit 1
        ;;
esac
