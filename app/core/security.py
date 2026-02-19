"""
SecureDocAI — Security Utilities
==================================
JWT token handling, password hashing, and authentication helpers.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from config.settings import get_settings


# ── Password Hashing ──

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Tokens ──

class TokenData(BaseModel):
    """Decoded JWT token payload."""
    username: str
    role: str = "user"
    exp: Optional[datetime] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data (must include 'sub' for username).
        expires_delta: Optional custom expiry duration.

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> TokenData:
    """
    Decode and validate a JWT access token.

    Args:
        token: The JWT string.

    Returns:
        Decoded TokenData.

    Raises:
        JWTError: If token is invalid or expired.
    """
    settings = get_settings()

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    username: str = payload.get("sub", "")
    role: str = payload.get("role", "user")

    if not username:
        raise JWTError("Token missing 'sub' claim")

    return TokenData(username=username, role=role)


# ── File Hashing ──

import hashlib


def compute_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the cryptographic hash of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (default: sha256).

    Returns:
        Hex digest string.
    """
    h = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()
