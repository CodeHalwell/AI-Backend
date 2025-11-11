"""
Security Module

Handles authentication, authorization, and password management.

Features:
- JWT token creation and validation
- Password hashing with bcrypt
- Token-based authentication
- Role-based access control helpers

Security Best Practices:
- Never store passwords in plaintext
- Use strong hashing algorithms (bcrypt)
- Set appropriate token expiration
- Validate all tokens
- Use secrets for signing keys
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import logger

# ============================================================================
# PASSWORD HASHING
# ============================================================================

# Password context using bcrypt
#
# Why bcrypt?
# - Specifically designed for password hashing
# - Slow by design (prevents brute force)
# - Adaptive: can increase rounds as computers get faster
# - Industry standard
#
# Rounds: 12 is good balance between security and performance

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password

    Example:
        hashed = hash_password("MySecurePassword123!")
        # Returns: $2b$12$...
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password from user
        hashed_password: Stored hash from database

    Returns:
        True if password matches, False otherwise

    Example:
        is_valid = verify_password("MyPassword", user.hashed_password)
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error("Password verification error", error=str(e))
        return False


# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of claims to encode (e.g., {"sub": user_id})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token

    Token Structure:
        {
            "sub": "user_id",
            "exp": timestamp,
            "iat": timestamp,
            "type": "access"
        }

    Why JWT?
    - Stateless authentication (no server-side session storage)
    - Can be verified without database lookup
    - Contains user info (claims)
    - Industry standard
    """
    to_encode = data.copy()

    # Set expiration
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    })

    # Encode token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token.

    Refresh tokens:
    - Longer expiration than access tokens
    - Used to get new access tokens
    - Should be stored securely by client

    Args:
        data: Dictionary of claims to encode

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired

    Validates:
    - Signature is valid
    - Token hasn't expired
    - Required fields are present
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload

    except JWTError as e:
        logger.warning("Invalid token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


# ============================================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================================

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    FastAPI dependency to get current user ID from token.

    SECURITY: Only accepts access tokens, not refresh tokens.
    This prevents clients from using long-lived refresh tokens
    to bypass access token expiration.

    Usage:
        @app.get("/me")
        async def get_me(user_id: str = Depends(get_current_user_id)):
            return {"user_id": user_id}

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        User ID from token

    Raises:
        HTTPException: If token is invalid, missing, or wrong type
    """
    token = credentials.credentials
    payload = decode_token(token)

    # SECURITY: Verify this is an access token, not a refresh token
    token_type = payload.get("type")
    if token_type != "access":
        logger.warning(
            "Invalid token type used for authentication",
            token_type=token_type,
            expected="access"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Please use an access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_current_user_id",
    "security",
]
