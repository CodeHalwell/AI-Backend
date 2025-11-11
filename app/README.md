# Application Directory (`app/`)

This directory contains all application code. The structure follows Domain-Driven Design and clean architecture principles.

## Directory Structure

```
app/
├── api/              # API layer (routes, endpoints)
├── core/             # Core functionality (config, security, logging)
├── models/           # Database models (SQLAlchemy)
├── schemas/          # Pydantic schemas for validation
├── services/         # Business logic layer
├── db/               # Database setup and session management
├── utils/            # Utility functions and helpers
├── main.py           # Application entry point
└── __init__.py       # Package initialization
```

## File Descriptions

### `main.py`

**What**: FastAPI application entry point
**Why**: Centralizes app creation, middleware setup, and route registration
**How**: 
- Creates FastAPI instance
- Configures CORS, compression, rate limiting
- Sets up health checks and metrics
- Registers API routers
- Handles application lifecycle (startup/shutdown)

**Key Features**:
- Lifespan context manager for resource management
- Global exception handling
- Structured logging
- Prometheus metrics endpoint
- Health and readiness probes for Kubernetes

### `api/`

Contains all API endpoints organized by version and domain.

**Structure**:
```
api/
├── v1/
│   ├── api.py           # Main API router aggregation
│   └── endpoints/
│       ├── auth.py      # Authentication endpoints
│       ├── agents.py    # Agent management
│       ├── conversations.py  # Conversation handling
│       └── tools.py     # Tool management
```

**Why versioned (`v1`)?**
- Backward compatibility when making breaking changes
- Support multiple API versions simultaneously
- Clear migration path for clients
- Professional API design

### `core/`

Core application functionality that's used everywhere.

**Files**:

#### `config.py`
- **What**: Application configuration using Pydantic Settings
- **Why**: 
  - Type-safe configuration
  - Environment variable parsing
  - Validation of settings
  - Easy testing with dependency injection
- **How**: Reads from `.env` file and environment variables

#### `security.py`
- **What**: Authentication and authorization logic
- **Why**: 
  - Centralized security functions
  - JWT token management
  - Password hashing with bcrypt
- **How**: 
  - `hash_password()`: Hash passwords with bcrypt
  - `verify_password()`: Verify password against hash
  - `create_access_token()`: Generate JWT access tokens
  - `create_refresh_token()`: Generate JWT refresh tokens
  - `decode_token()`: Validate and decode JWTs

#### `logging.py`
- **What**: Structured logging setup
- **Why**:
  - JSON logs for production (easy to parse)
  - Pretty console logs for development
  - Request tracking with IDs
  - Integration with log aggregation tools
- **How**: Uses `structlog` library for structured logging

### `models/`

SQLAlchemy database models (ORM).

**Files**:

#### `base.py`
- **What**: Base model mixins
- **Why**: DRY principle - reusable fields across all models
- **Contains**:
  - `UUIDMixin`: UUID primary keys
  - `TimestampMixin`: created_at, updated_at
  - `SoftDeleteMixin`: Soft delete support
  - `BaseModel`: Combination of UUID + Timestamp

**Why UUIDs instead of auto-increment IDs?**
- Globally unique (no collisions across databases)
- Security (can't guess other IDs)
- Better for distributed systems
- Can generate client-side

#### `user.py`
- **What**: User model for authentication
- **Fields**: email, hashed_password, role, is_active, is_verified
- **Relationships**: agents, conversations
- **Why**: RBAC (Role-Based Access Control) support

#### `agent.py`
- **What**: AI agent configuration
- **Fields**: name, model, system_prompt, temperature, tools
- **Why**: Reusable agent configurations
- **Use Case**: Create once, use in multiple conversations

#### `conversation.py`
- **What**: Chat session between user and agent
- **Fields**: title, status, total_messages, total_tokens
- **Relationships**: user, agent, messages
- **Why**: Track conversation context and costs

#### `message.py`
- **What**: Individual messages in conversations
- **Fields**: role (user/assistant), content, tokens, tool_calls
- **Why**: Full conversation history for context

#### `tool.py`
- **What**: Tools/functions that agents can call
- **Fields**: name, description, parameters, handler
- **Why**: Enable agents to perform actions (API calls, calculations, etc.)

### `schemas/`

Pydantic models for request/response validation.

**Why separate from database models?**
- Different concerns: API vs Database
- API might expose subset of fields
- Validation rules differ
- Better security (don't expose internal fields)

**Pattern**:
- `*Base`: Shared fields
- `*Create`: For POST requests
- `*Update`: For PUT/PATCH requests
- `*Response`: For API responses (with IDs, timestamps)

### `db/`

Database connection and session management.

#### `session.py`
- **What**: SQLAlchemy async engine and session factory
- **Why**: 
  - Async support for FastAPI
  - Connection pooling for performance
  - Session-per-request pattern
- **Key Features**:
  - Async engine with connection pooling
  - `get_db()` dependency for route handlers
  - Automatic session cleanup
  - Transaction management

**Connection Pool Settings**:
- `pool_size=20`: Maintain 20 permanent connections
- `max_overflow=10`: Allow 10 extra connections when busy
- `pool_recycle=3600`: Recycle connections after 1 hour

### `utils/`

Utility functions and helpers.

#### `cache.py`
- **What**: Redis caching utility
- **Why**: 
  - Speed up repeated queries (10-100x faster)
  - Reduce database load
  - Rate limiting
- **Features**:
  - Async Redis client
  - Automatic JSON serialization
  - TTL support
  - Connection pooling

### `services/`

Business logic layer (currently placeholder for future expansion).

**Purpose**: Complex business logic that doesn't belong in endpoints

**Examples**:
- AI service: Call OpenAI/Anthropic APIs
- Tool executor: Execute agent tools safely
- Email service: Send emails
- Analytics service: Track usage metrics

## Design Principles

### 1. Separation of Concerns

Each layer has clear responsibility:
- **API**: HTTP handling, request/response
- **Service**: Business logic
- **Model**: Data structure
- **Schema**: Validation

### 2. Dependency Injection

FastAPI's `Depends()` for:
- Database sessions
- Current user
- Configuration

**Benefits**:
- Easy to test (mock dependencies)
- Loose coupling
- Explicit dependencies

### 3. Async/Await Throughout

All I/O operations are async:
- Database queries
- Redis operations
- HTTP requests

**Why?**
- Handle thousands of concurrent requests
- Non-blocking I/O
- Better resource utilization

### 4. Type Hints Everywhere

Every function has type hints:

```python
async def get_user(db: AsyncSession, user_id: UUID) -> User:
    ...
```

**Benefits**:
- IDE autocomplete
- Catch errors before runtime
- Better documentation
- Runtime validation (with Pydantic)

## Adding New Features

### Add New Endpoint

1. Create Pydantic schema in `schemas/`
2. Create endpoint in `api/v1/endpoints/`
3. Register router in `api/v1/api.py`
4. Add tests in `tests/`

### Add New Model

1. Create model in `models/`
2. Import in `models/__init__.py`
3. Create Alembic migration
4. Create corresponding schema
5. Add CRUD endpoints

### Add New Service

1. Create service in `services/`
2. Inject dependencies (DB, cache, config)
3. Use in endpoints

## Common Patterns

### Database Query

```python
from sqlalchemy import select

result = await db.execute(
    select(User).where(User.email == email)
)
user = result.scalar_one_or_none()
```

### Caching

```python
from app.utils.cache import cache, make_cache_key

key = make_cache_key("user", user_id)

# Try cache first
cached = await cache.get(key)
if cached:
    return cached

# Query database
user = await db.get(User, user_id)

# Cache for next time
await cache.set(key, user, ttl=3600)
```

### Authentication

```python
from app.core.security import get_current_user_id

@router.get("/protected")
async def protected_route(
    user_id: str = Depends(get_current_user_id)
):
    # user_id is validated JWT token subject
    ...
```

## Best Practices

1. **Always use type hints**
2. **Validate input with Pydantic**
3. **Use async/await for I/O**
4. **Handle errors gracefully**
5. **Log important events**
6. **Cache expensive operations**
7. **Write tests for new features**
8. **Document complex logic**

## Security Considerations

1. **Never expose hashed passwords**
2. **Validate all inputs**
3. **Use parameterized queries** (SQLAlchemy does this)
4. **Rate limit sensitive endpoints**
5. **Require authentication for user data**
6. **Use HTTPS in production**
7. **Rotate secrets regularly**

---

For more details, see the main [README.md](../README.md)
