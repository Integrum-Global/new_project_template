#!/bin/bash
set -e

echo "Starting MCP Core Management Platform..."

# Wait for database
echo "Waiting for database..."
while ! nc -z postgres 5432; do
  sleep 0.1
done
echo "Database is ready!"

# Run migrations if needed
# python -m alembic upgrade head

# Start the application
exec python -m core.main
