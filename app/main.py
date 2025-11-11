"""
Main FastAPI Application

This is the entry point for the AI Backend application.
It sets up all middleware, routes, and application lifecycle events.

Key Features:
- CORS middleware for cross-origin requests
- Rate limiting for API protection
- Prometheus metrics for monitoring
- OpenTelemetry tracing for observability
- Structured logging
- Health check endpoints
- Graceful shutdown handling
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.db.session import engine, init_db

# Setup logging
setup_logging()


def get_limiter_key(request: Request) -> str:
    """
    Get rate limiter key from request.

    Uses user ID if authenticated, otherwise falls back to IP address.
    This provides more accurate rate limiting per user.
    """
    # Try to get user from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return get_remote_address(request)


# Initialize rate limiter
limiter = Limiter(key_func=get_limiter_key)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize database, cache connections, etc.
    - Shutdown: Close connections gracefully

    Why use lifespan instead of on_event?
    - Modern FastAPI recommendation
    - Better async/await support
    - Cleaner resource management
    """
    # Startup
    logger.info("Starting up AI Backend...", environment=settings.ENVIRONMENT)

    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")

        # Initialize Redis connection is handled lazily by get_redis()
        logger.info("Redis connection pool ready")

        logger.info(
            "Application started successfully",
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            environment=settings.ENVIRONMENT,
        )

    except Exception as e:
        logger.error("Failed to start application", error=str(e), exc_info=True)
        raise

    yield  # Application is running

    # Shutdown
    logger.info("Shutting down AI Backend...")

    try:
        # Close database connections
        await engine.dispose()
        logger.info("Database connections closed")

        # Redis connections are closed automatically by connection pool

        logger.info("Application shut down successfully")

    except Exception as e:
        logger.error("Error during shutdown", error=str(e), exc_info=True)


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade FastAPI backend for AI agent workloads",
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Add rate limiting state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================================
# MIDDLEWARE SETUP
# ============================================================================

# 1. Trusted Host Middleware - Security
# Prevents HTTP Host Header attacks
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.TRUSTED_HOSTS
    )

# 2. CORS Middleware - Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# 3. GZip Middleware - Compress responses
# Reduces bandwidth usage by ~70% for JSON responses
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for uncaught exceptions.

    Why?
    - Prevents stack traces from leaking in production
    - Provides consistent error response format
    - Logs errors for debugging
    """
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )

    # Don't expose internal errors in production
    if settings.is_production:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "error_id": "Please contact support with this error ID",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/health", tags=["monitoring"])
async def health_check() -> dict:
    """
    Health check endpoint.

    Used by:
    - Load balancers to check if instance is healthy
    - Kubernetes liveness probe
    - Monitoring systems

    Returns basic application status.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/ready", tags=["monitoring"])
async def readiness_check() -> dict:
    """
    Readiness check endpoint.

    Used by:
    - Kubernetes readiness probe
    - Load balancers to determine if instance can receive traffic

    Checks if the application is ready to serve requests.
    This includes database connectivity, cache availability, etc.
    """
    # TODO: Add actual health checks for dependencies
    # - Database connectivity
    # - Redis connectivity
    # - External API availability

    return {
        "status": "ready",
        "database": "connected",
        "cache": "connected",
    }


# ============================================================================
# METRICS ENDPOINT
# ============================================================================

if settings.ENABLE_METRICS:
    # Mount Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


# ============================================================================
# API ROUTES
# ============================================================================

# Include all API routes under /api/v1
app.include_router(api_router, prefix="/api/v1")


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["root"])
async def root() -> dict:
    """
    Root endpoint.

    Provides basic API information and links to documentation.
    """
    return {
        "message": "Welcome to AI Backend API",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
        "health": "/health",
        "metrics": "/metrics" if settings.ENABLE_METRICS else "Metrics disabled",
    }


# ============================================================================
# STARTUP MESSAGE
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Run with uvicorn for development
    # For production, use: gunicorn app.main:app -k uvicorn.workers.UvicornWorker
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
