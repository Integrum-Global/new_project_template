#!/bin/bash
set -e

echo "Starting MCP Enterprise Gateway..."

# Wait for core platform
echo "Waiting for MCP Core..."
while ! nc -z mcp-core 8000; do
  sleep 0.1
done
echo "MCP Core is ready!"

# Start the gateway
exec python -m gateway.core.server
