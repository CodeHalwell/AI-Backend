# Tests Directory (`tests/`)

Comprehensive test suite for the AI Backend application.

## Structure

```
tests/
├── conftest.py          # Pytest fixtures and configuration
├── unit/                # Unit tests (individual functions)
├── integration/         # Integration tests (multiple components)
├── api/                 # API endpoint tests
├── test_auth.py         # Authentication tests
└── README.md            # This file
```

## Test Files

### `conftest.py`

**What**: Pytest configuration and shared fixtures
**Why**: Reusable test setup across all tests
**Contains**:
- `test_engine`: Test database engine
- `db_session`: Test database session
- `client`: Test HTTP client
- `test_user`: Sample user for tests
- `admin_user`: Sample admin user
- `auth_headers`: Authentication headers

### `test_auth.py`

**What**: Authentication endpoint tests
**Tests**:
- User registration
- Login/logout
- Token refresh
- Password validation
- Duplicate email handling
- Unauthorized access

## Running Tests

### All Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Specific Tests

```bash
# Run specific file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::TestAuth::test_login_success

# Run by marker
pytest -m "not slow"
```

### Watch Mode

```bash
# Rerun on file changes
pytest-watch

# Or use watchdog
watchmedo shell-command --patterns="*.py" --recursive --command='pytest tests/'
```

## Test Database

Tests use a separate database: `ai_backend_test`

**Setup**:
```bash
# Create test database
createdb ai_backend_test

# Run tests (migrations run automatically)
pytest
```

**Cleanup**:
```bash
# Drop test database
dropdb ai_backend_test
```

## Writing Tests

### Basic Test Structure

```python
import pytest
from httpx import AsyncClient

class TestFeature:
    """Test suite for feature."""
    
    @pytest.mark.asyncio
    async def test_something(self, client: AsyncClient):
        """Test description."""
        # Arrange
        data = {"key": "value"}
        
        # Act
        response = await client.post("/endpoint", json=data)
        
        # Assert
        assert response.status_code == 200
        assert response.json()["key"] == "value"
```

### Using Fixtures

```python
@pytest.mark.asyncio
async def test_with_auth(self, client: AsyncClient, auth_headers: dict):
    """Test with authenticated user."""
    response = await client.get(
        "/api/v1/protected",
        headers=auth_headers
    )
    assert response.status_code == 200
```

### Database Tests

```python
from app.models.user import User

@pytest.mark.asyncio
async def test_database(self, db_session: AsyncSession):
    """Test database operations."""
    # Create
    user = User(email="test@example.com", ...)
    db_session.add(user)
    await db_session.commit()
    
    # Query
    result = await db_session.execute(select(User))
    users = result.scalars().all()
    
    assert len(users) == 1
```

## Test Coverage

### View Coverage Report

```bash
# Generate HTML report
pytest --cov=app --cov-report=html

# Open in browser
open htmlcov/index.html

# Terminal report
pytest --cov=app --cov-report=term-missing
```

### Coverage Goals

- **Target**: 80%+ coverage
- **Critical paths**: 100% (auth, payments)
- **Utilities**: 90%+
- **Integration**: 70%+

## Best Practices

### 1. Test Naming

```python
# Good: Descriptive names
def test_user_can_register_with_valid_email():
    ...

# Bad: Vague names
def test_1():
    ...
```

### 2. Arrange-Act-Assert Pattern

```python
def test_feature():
    # Arrange: Set up test data
    user = create_user()
    
    # Act: Perform action
    result = user.login()
    
    # Assert: Verify outcome
    assert result.is_authenticated
```

### 3. Independent Tests

Each test should:
- Be independent (no shared state)
- Clean up after itself
- Not depend on execution order

### 4. Use Fixtures

```python
@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

### 5. Mark Slow Tests

```python
@pytest.mark.slow
def test_expensive_operation():
    # Long-running test
    ...

# Run without slow tests
pytest -m "not slow"
```

### 6. Parameterized Tests

```python
@pytest.mark.parametrize("email,valid", [
    ("good@example.com", True),
    ("invalid", False),
    ("no@domain", False),
])
def test_email_validation(email, valid):
    result = validate_email(email)
    assert result == valid
```

## Test Types

### Unit Tests

Test individual functions in isolation.

```python
def test_hash_password():
    """Test password hashing."""
    password = "SecurePass123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
```

### Integration Tests

Test multiple components together.

```python
async def test_full_registration_flow(client):
    """Test complete user registration."""
    # Register
    response = await client.post("/auth/register", ...)
    assert response.status_code == 201
    
    # Login
    response = await client.post("/auth/login", ...)
    assert response.status_code == 200
    
    # Access protected route
    token = response.json()["access_token"]
    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

### API Tests

Test HTTP endpoints.

```python
async def test_api_endpoint(client):
    """Test API returns correct data."""
    response = await client.get("/api/v1/agents")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

## Mocking

### Mock External Services

```python
from unittest.mock import AsyncMock, patch

@patch("app.services.ai.openai_client")
async def test_ai_call(mock_client):
    """Test AI service call."""
    mock_client.create.return_value = {"response": "Hello"}
    
    result = await ai_service.generate("prompt")
    assert result == "Hello"
```

### Mock Database

```python
@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock(spec=AsyncSession)
    return db

async def test_with_mock_db(mock_db):
    """Test using mock database."""
    mock_db.execute.return_value = MagicMock()
    result = await get_user(mock_db, user_id)
    mock_db.execute.assert_called_once()
```

## Continuous Integration

Tests run automatically on:
- Every commit
- Pull requests
- Before deployment

See `.github/workflows/test.yml` for CI configuration.

## Troubleshooting

### Tests Failing Locally

```bash
# Ensure test database exists
createdb ai_backend_test

# Install test dependencies
uv pip install -e .[dev]

# Clear pytest cache
pytest --cache-clear
```

### Database Connection Errors

```bash
# Check PostgreSQL is running
pg_isready

# Check connection string
echo $DATABASE_URL
```

### Import Errors

```bash
# Ensure app is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install in editable mode
uv pip install -e .
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [AsyncIO Testing](https://docs.python.org/3/library/asyncio-dev.html#debug-mode)

---

Good tests = Confident deployments!
