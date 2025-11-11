#!/bin/bash
# Test script

set -e

echo "🧪 Running tests..."

# Create test database if it doesn't exist
echo "📊 Setting up test database..."
psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'ai_backend_test'" | grep -q 1 || \
    psql -U postgres -c "CREATE DATABASE ai_backend_test"

# Run tests with coverage
echo "🏃 Running pytest..."
pytest --cov=app --cov-report=html --cov-report=term-missing -v

echo "✅ Tests completed!"
echo "📊 Coverage report available at: htmlcov/index.html"
