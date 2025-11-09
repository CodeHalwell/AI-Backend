"""
Database Session Management

Handles database connections and session lifecycle using SQLAlchemy.

Key Concepts:
- AsyncSession for async/await support
- Connection pooling for performance
- Session-per-request pattern
- Proper connection cleanup

Why AsyncSession?
- Non-blocking I/O for better performance
- Handle many concurrent requests
- Essential for FastAPI's async nature

Connection Pooling Benefits:
- Reuse connections instead of creating new ones
- Reduces connection overhead
- Limits max concurrent connections
- Automatic connection recycling
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import QueuePool

from app.core.config import settings
from app.core.logging import logger

# ============================================================================
# ENGINE CONFIGURATION
# ============================================================================

# Create async engine with optimized pooling
#
# Pool Configuration:
# - pool_size: Number of permanent connections to maintain
# - max_overflow: Additional connections allowed when pool is full
# - pool_timeout: Seconds to wait for connection from pool
# - pool_recycle: Recycle connections after N seconds (prevents stale connections)
#
# Why these settings?
# - pool_size=20: Handles moderate concurrent load
# - max_overflow=10: Allows bursts up to 30 total connections
# - pool_recycle=3600: Prevents MySQL "gone away" errors
# - pool_pre_ping=True: Validates connections before use

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    future=True,  # Use SQLAlchemy 2.0 style
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=True,  # Verify connection health before using
    poolclass=QueuePool,  # Thread-safe connection pool
)


# ============================================================================
# SESSION FACTORY
# ============================================================================

# Create session factory
#
# Configuration:
# - autocommit=False: Explicit transaction control (recommended)
# - autoflush=False: Manual flush control for better performance
# - expire_on_commit=False: Don't expire objects after commit (reduces queries)
#
# Session-per-request pattern:
# 1. Create session at request start
# 2. Use session for all database operations
# 3. Commit/rollback as needed
# 4. Close session at request end

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ============================================================================
# BASE MODEL
# ============================================================================

# Declarative base for all models
# All database models will inherit from this
Base = declarative_base()


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()

    How it works:
    1. Creates a new session for each request
    2. Yields session to route handler
    3. Automatically closes session after request
    4. Rolls back on exceptions

    Why use dependency injection?
    - Automatic session lifecycle management
    - Easy to test (can mock database)
    - Clean separation of concerns
    - Consistent error handling
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Commit successful transactions
        except Exception as e:
            await session.rollback()  # Rollback on errors
            logger.error("Database session error", error=str(e), exc_info=True)
            raise
        finally:
            await session.close()


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

async def init_db() -> None:
    """
    Initialize database.

    Creates all tables defined in models.

    Note: In production, use Alembic migrations instead.
    This is mainly for development and testing.
    """
    try:
        # Import all models here to ensure they're registered

        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")

    except Exception as e:
        logger.error("Failed to initialize database", error=str(e), exc_info=True)
        raise


async def close_db() -> None:
    """
    Close database connections.

    Called during application shutdown.
    """
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Error closing database", error=str(e), exc_info=True)


__all__ = ["engine", "AsyncSessionLocal", "Base", "get_db", "init_db", "close_db"]
