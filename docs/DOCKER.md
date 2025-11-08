# Docker Deployment Guide

Complete guide for running the AI Backend with Docker.

## Quick Start

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop all services
docker-compose down
```

## Building the Image

### Development Build

```bash
docker build -t ai-backend:dev .
```

### Production Build

```bash
# Multi-stage build (smaller image)
docker build -t ai-backend:latest -f Dockerfile .

# Build with specific tag
docker build -t ai-backend:v1.0.0 .
```

## Running Containers

### Standalone Container

```bash
# Run app only (requires external PostgreSQL & Redis)
docker run -d \
  --name ai-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e REDIS_URL=redis://... \
  -e SECRET_KEY=your-secret \
  ai-backend:latest
```

### With Docker Compose

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d postgres redis

# Scale application
docker-compose up -d --scale app=3
```

## Configuration

### Environment Variables

```bash
# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/ai_backend
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key-change-in-production
OPENAI_API_KEY=sk-your-key
ENVIRONMENT=production
DEBUG=False
