# Scripts Directory (`scripts/`)

Utility scripts for common development and deployment tasks.

## Available Scripts

### `start.sh`

**Purpose**: Start the application for local development

**What it does**:
1. Checks for `.env` file (creates from example if missing)
2. Installs dependencies with `uv`
3. Starts PostgreSQL and Redis with Docker Compose
4. Runs database migrations
5. Starts FastAPI with hot reload

**Usage**:
```bash
./scripts/start.sh
```

**Requirements**:
- Python 3.11+
- uv package manager
- Docker and Docker Compose (optional but recommended)

### `test.sh`

**Purpose**: Run the test suite

**What it does**:
1. Creates test database if needed
2. Runs pytest with coverage
3. Generates HTML coverage report

**Usage**:
```bash
./scripts/test.sh
```

**View coverage**:
```bash
open htmlcov/index.html
```

## Creating New Scripts

When creating utility scripts:

1. **Make executable**:
   ```bash
   chmod +x scripts/your_script.sh
   ```

2. **Add shebang**:
   ```bash
   #!/bin/bash
   ```

3. **Use set -e**:
   ```bash
   set -e  # Exit on error
   ```

4. **Document in this README**

## Common Tasks

### Database

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Reset database (development only!)
alembic downgrade base && alembic upgrade head
```

### Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Rebuild
docker-compose up -d --build

# Stop all
docker-compose down
```

### Code Quality

```bash
# Format code
black app tests

# Lint
ruff check app tests

# Type check
mypy app
```

### Deployment

```bash
# Build Docker image
docker build -t ai-backend:latest .

# Tag for registry
docker tag ai-backend:latest registry.example.com/ai-backend:v1.0.0

# Push to registry
docker push registry.example.com/ai-backend:v1.0.0

# Deploy to Kubernetes
kubectl apply -f k8s/
```

## Environment Variables

Scripts use `.env` file for configuration:

```bash
# Copy example
cp .env.example .env

# Edit configuration
nano .env
```

## Troubleshooting

### Script Permission Denied

```bash
chmod +x scripts/script_name.sh
```

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Dependencies Not Found

```bash
# Reinstall dependencies
uv pip install -e .[dev]
```

---

**Note**: All scripts assume they are run from the project root directory.
