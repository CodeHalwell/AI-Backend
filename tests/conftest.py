"""
Pytest Configuration and Fixtures

Shared test fixtures for all tests.

Fixtures provide:
- Test database
- Test client
- Authenticated users
- Sample data
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

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


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
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
        await conn.execute(text("CREATE TYPE conversationstatus AS ENUM ('active', 'archived', 'completed')"))
        await conn.execute(text("CREATE TYPE messagerole AS ENUM ('user', 'assistant', 'system', 'tool')"))

        # Now create all tables (enums already exist)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

        # Clean up enum types
        await conn.execute(text("DROP TYPE IF EXISTS messagerole CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS conversationstatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session with transaction rollback for test isolation."""
    # Create a connection and start a transaction
    connection = await test_engine.connect()
    transaction = await connection.begin()

    # Create session bound to this connection
    session = AsyncSession(bind=connection, expire_on_commit=False)

    try:
        yield session
    finally:
        # Rollback transaction to undo any changes made during test
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user."""
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=hash_password("testpassword123"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create admin user."""
    user = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=hash_password("adminpassword123"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
