#!/bin/sh
set -e

echo "======================================"
echo "Starting Votez Backend..."
echo "======================================"

# Check if database URL is configured
if [ -z "$DATABASE_URL" ] && [ -z "$POSTGRES_SERVER" ]; then
    echo "⚠ WARNING: Database configuration is missing!"
    echo "Please set either DATABASE_URL or POSTGRES_* environment variables."
    echo ""
    echo "Available environment variables:"
    env | grep -E "(DATABASE|POSTGRES)" || echo "None found"
    echo ""
    echo "For Railway deployment, make sure you've added a PostgreSQL database service."
    echo "For local testing, set DATABASE_URL or POSTGRES_* variables."
    echo ""
fi

if [ -n "$DATABASE_URL" ] || [ -n "$POSTGRES_SERVER" ]; then
    echo "✓ Database configuration found."
    echo ""
fi

# Wait a moment for database to be ready (if freshly provisioned)
echo "Waiting 3 seconds for database to be ready..."
sleep 3

# Run migrations
echo "Running database migrations..."
echo "This may take a moment..."
if alembic upgrade head; then
    echo "✓ Migrations completed successfully"
else
    echo "⚠ Warning: Migration had issues. This might be OK if the database is already up-to-date."
    echo "Continuing anyway..."
fi

echo ""
echo "======================================"
echo "Starting FastAPI application..."
echo "Running on port: $PORT"
echo "======================================"
echo ""

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port $PORT
