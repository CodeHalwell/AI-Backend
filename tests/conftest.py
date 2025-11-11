"""
Pytest Configuration and Fixtures

Shared test fixtures for all tests.

Fixtures provide:
- Test database
- Test client with lifespan management
- Authenticated users
- Sample data

Key Design:
- Uses LifespanManager to properly manage FastAPI app lifecycle
- Database engine/pool managed by app startup/shutdown events
- Test isolation via database cleanup between tests
- No manual connection/transaction management in fixtures
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.security import hash_password
from app.db.session import Base, get_db
from app.main import app
from app.models.user import User, UserRole

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_backend_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Set up test database schema before tests run."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        # Drop all tables and enum types first (cleanup from previous runs)
        await conn.run_sync(Base.metadata.drop_all)

        # Drop enum types explicitly if they exist (handles orphaned enums)
        await conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS conversationstatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS messagerole CASCADE"))

        # Create enum types explicitly before creating tables
        await conn.execute(text("CREATE TYPE userrole AS ENUM ('admin', 'user', 'viewer')"))
        await conn.execute(
            text("CREATE TYPE conversationstatus AS ENUM ('active', 'archived', 'completed')")
        )
        await conn.execute(
            text("CREATE TYPE messagerole AS ENUM ('user', 'assistant', 'system', 'tool')")
        )

        # Now create all tables (enums already exist)
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup after all tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

        # Clean up enum types
        await conn.execute(text("DROP TYPE IF EXISTS messagerole CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS conversationstatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))

    await engine.dispose()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create test client with proper lifespan management.

    Uses LifespanManager to ensure FastAPI startup/shutdown events
    run correctly, preventing database connection cleanup issues.
    """
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac


@pytest.fixture
async def test_user(client: AsyncClient) -> User:
    """Create test user via API."""
    # Get a database session from the app's dependency
    async for session in get_db():
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=hash_password("testpassword123"),
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        yield user

        # Cleanup: delete test user after test
        await session.delete(user)
        await session.commit()
        break


@pytest.fixture
async def admin_user(client: AsyncClient) -> User:
    """Create admin user via API."""
    async for session in get_db():
        user = User(
            email="admin@example.com",
            full_name="Admin User",
            hashed_password=hash_password("adminpassword123"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        yield user

        # Cleanup: delete admin user after test
        await session.delete(user)
        await session.commit()
        break


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = await client.post(
        "/api/v1/auth/login", json={"email": "test@example.com", "password": "testpassword123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
