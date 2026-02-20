"""
SecureDocAI — API Dependencies
==================================
Shared FastAPI dependencies: auth, database, policy loading.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import decode_access_token
from app.models.policy import PolicyLoader
from config.settings import get_settings, BASE_DIR

from jose import JWTError


# ── Security Scheme ──

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# ── Auth Dependency ──

async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> dict:
    """
    Validate JWT token and return current user info.

    Returns:
        Dict with username and role.

    Raises:
        HTTPException 401 if token is invalid.
    """
    try:
        token_data = decode_access_token(token)
        return {"username": token_data.username, "role": token_data.role}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Policy Dependency ──

def get_policy_loader() -> PolicyLoader:
    """Get a cached PolicyLoader instance."""
    policies_dir = BASE_DIR / "config" / "policies"
    return PolicyLoader(policies_dir)
