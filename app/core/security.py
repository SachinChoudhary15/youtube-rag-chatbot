
import secrets
import logging

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from pwdlib import PasswordHash

from jwt.exceptions import InvalidTokenError

from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader

from app.core.config import settings


logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

password_hash = PasswordHash.recommended()


# API KEY AUTHENTICATION
def get_api_key(api_key: str | None = Security(api_key_header)) -> str:
    if not api_key or not api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
        )

    return api_key


def validate_api_key() -> bool:
    configured_api_key = settings.APP_API_KEY

    if not configured_api_key or not configured_api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API authentication is not configured",
        )

    return True


def verify_api_key(api_key: str = Depends(get_api_key)) -> bool:
    validate_api_key()

    configured_api_key = settings.APP_API_KEY

    if not secrets.compare_digest(api_key, configured_api_key):
        logger.warning("Invalid API key provided")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return True


# PASSWORD HASHING
def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


# JWT TOKEN GENERATION
def create_access_token(
    user_id: int,
    expires_delta: timedelta | None = None,
) -> str:

    if user_id <= 0:
        raise ValueError("User ID must be a positive integer.")

    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token


# JWT TOKEN VALIDATION
def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type.")

        if not payload.get("sub"):
            raise InvalidTokenError("Token subject is missing.")

        return payload

    except InvalidTokenError as exc:
        logger.warning("Invalid or expired access token.")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# SENSITIVE DATA MASKING
def mask_sensitive_data(data: str) -> str:
    if not data:
        return ""

    if len(data) <= 8:
        return "*" * len(data)

    return f"{data[:4]}{'*' * (len(data) - 8)}{data[-4:]}"
