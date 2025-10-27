#!/bin/sh
set -e

echo "Starting Votez Backend..."

# Wait for database to be ready (optional, can be useful)
echo "Checking database connection..."

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting FastAPI application on port $PORT..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT
