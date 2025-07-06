#!/bin/bash
set -e

echo "Starting MCP Tool Server..."

# Wait for core platform
echo "Waiting for MCP Core..."
while ! nc -z mcp-core 8000; do
  sleep 0.1
done
echo "MCP Core is ready!"

# Start the production server
exec python -m tools.servers.production_server
