#!/bin/bash
# Startup script for local development

set -e

echo "🚀 Starting AI Backend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your configuration."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    pip install uv
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv pip install -e .
uv pip install -e .[dev]

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    echo "🐳 Starting PostgreSQL and Redis with Docker Compose..."
    docker-compose up -d postgres redis
    
    # Wait for databases to be ready
    echo "⏳ Waiting for databases to be ready..."
    sleep 5
else
    echo "⚠️  Docker Compose not found. Please start PostgreSQL and Redis manually."
fi

# Run migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Start application
echo "✨ Starting FastAPI application..."
echo "📡 API will be available at: http://localhost:8000"
echo "📚 API docs will be available at: http://localhost:8000/docs"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
