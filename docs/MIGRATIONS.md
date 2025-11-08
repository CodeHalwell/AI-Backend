# Database Migrations Guide

Complete guide to managing database schema changes with Alembic.

## Table of Contents

- [Overview](#overview)
- [Initial Setup](#initial-setup)
- [Creating Migrations](#creating-migrations)
- [Applying Migrations](#applying-migrations)
- [Rollback](#rollback)
- [Best Practices](#best-practices)

## Overview

We use **Alembic** for database migrations because:

- **Version control for database schema**: Track all schema changes
- **Safe deployments**: Preview and test migrations before applying
- **Rollback capability**: Undo migrations if issues occur
- **Team collaboration**: Multiple developers can work on schema
- **Automatic detection**: Auto-generate migrations from model changes

## Initial Setup

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv pip install -e .

# Verify Alembic is installed
alembic --version
```

### 2. Configure Database Connection

Edit `.env` file:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_backend
```

### 3. Initialize Alembic (Already Done)

```bash
# This creates alembic/ directory and alembic.ini
# Already done in this project
alembic init alembic
```

## Creating Migrations

### Auto-generate from Model Changes

**Most common approach** - Alembic detects changes automatically:

```bash
# Create migration from model changes
alembic revision --autogenerate -m "Add user table"

# Example output:
# Generating /path/to/alembic/versions/20240115_1234_add_user_table.py
```

**What it detects:**
- New tables
- New columns
- Changed column types
- Indexes added/removed
- Foreign keys

**What it doesn't detect:**
- Table/column renames (use manual migration)
- Complex data transformations

### Manual Migration

For complex changes:

```bash
# Create empty migration
alembic revision -m "custom migration"

# Edit the generated file manually
```

Example manual migration:

```python
def upgrade():
    # Rename column
    op.alter_column('users', 'name', new_column_name='full_name')
    
    # Add index
    op.create_index('idx_email', 'users', ['email'])
    
    # Custom SQL
    op.execute("UPDATE users SET status = 'active' WHERE status IS NULL")

def downgrade():
    # Reverse all changes
    op.drop_index('idx_email')
    op.alter_column('users', 'full_name', new_column_name='name')
```

## Applying Migrations

### Development

```bash
# Apply all pending migrations
alembic upgrade head

# Verify current version
alembic current

# View migration history
alembic history --verbose
```

### Production

**Best practices for production deployments:**

```bash
# 1. Backup database first!
pg_dump -U postgres ai_backend > backup_$(date +%Y%m%d).sql

# 2. Preview what will change
alembic upgrade head --sql > migration.sql
# Review migration.sql carefully

# 3. Apply migration
alembic upgrade head

# 4. Verify
alembic current
psql -U postgres -d ai_backend -c "\dt"  # List tables
```

### Specific Version

```bash
# Upgrade to specific version
alembic upgrade abc123

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1
```

## Rollback

### Undo Last Migration

```bash
# Rollback one migration
alembic downgrade -1

# Verify
alembic current
```

### Rollback to Specific Version

```bash
# Show history
alembic history

# Rollback to specific version
alembic downgrade abc123
```

### Complete Rollback

```bash
# Rollback all migrations (dangerous!)
alembic downgrade base
```

## Best Practices

### 1. Always Review Auto-generated Migrations

```bash
# After generating
alembic revision --autogenerate -m "description"

# Review the file before applying!
cat alembic/versions/latest_file.py
```

**Check for:**
- Unintended changes
- Missing indexes
- Data loss operations

### 2. Test Migrations

```bash
# Test in development first
alembic upgrade head
alembic downgrade -1  # Test rollback
alembic upgrade head  # Re-apply

# Run application tests
pytest
```

### 3. Backup Before Production Migrations

```bash
# PostgreSQL backup
pg_dump -U postgres -Fc ai_backend > backup.dump

# Restore if needed
pg_restore -U postgres -d ai_backend backup.dump
```

### 4. Make Migrations Reversible

Always implement `downgrade()`:

```python
def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(20)))

def downgrade():
    op.drop_column('users', 'phone')
```

### 5. Handle Data Migrations Carefully

For data transformations:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    # Add new column
    op.add_column('users', sa.Column('full_name', sa.String(255)))
    
    # Migrate data
    users = table('users',
        column('first_name', sa.String),
        column('last_name', sa.String),
        column('full_name', sa.String)
    )
    
    conn = op.get_bind()
    conn.execute(
        users.update().values(
            full_name=sa.func.concat(
                users.c.first_name, ' ', users.c.last_name
            )
        )
    )
    
    # Remove old columns
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')
```

### 6. Deployment Workflow

```mermaid
graph TD
    A[Make Model Changes] --> B[Generate Migration]
    B --> C[Review Migration File]
    C --> D{Looks Good?}
    D -->|No| E[Edit Manually]
    E --> C
    D -->|Yes| F[Test Locally]
    F --> G[Commit to Git]
    G --> H[CI/CD Tests]
    H --> I[Deploy to Staging]
    I --> J[Test Staging]
    J --> K[Deploy to Production]
```

## Common Scenarios

### Adding a New Model

```bash
# 1. Create model in app/models/
# 2. Import in app/models/__init__.py
# 3. Generate migration
alembic revision --autogenerate -m "add new_model table"
# 4. Review and apply
alembic upgrade head
```

### Modifying Existing Column

```bash
# Change column type in model
# Generate migration
alembic revision --autogenerate -m "change column type"
# Review - may need manual adjustment
alembic upgrade head
```

### Adding Index for Performance

```bash
# Add index to model
# Generate migration
alembic revision --autogenerate -m "add index on user_email"
alembic upgrade head
```

## Troubleshooting

### Migration Failed Mid-way

```bash
# Check current state
alembic current

# Fix the issue in database manually or fix migration
# Then mark as applied
alembic stamp head
```

### Merge Conflicts

If multiple developers create migrations:

```bash
# Create merge migration
alembic merge -m "merge migrations" rev1 rev2
alembic upgrade head
```

### Reset Migrations (Development Only)

```bash
# Drop all tables
alembic downgrade base

# Drop alembic_version table
psql -U postgres -d ai_backend -c "DROP TABLE alembic_version;"

# Re-apply all
alembic upgrade head
```

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**Remember**: Always backup before production migrations!
