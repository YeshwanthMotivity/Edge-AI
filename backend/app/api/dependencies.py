"""
SecureDocAI — API Dependencies
==================================
Shared FastAPI dependencies: auth, database, policy loading.
"""

from fastapi import Depends, HTTPException, status, Request
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
    request: Request,
) -> dict:
    """
    Skip JWT validation for local development to allow the frontend to connect.
    Returns a dummy user.
    """
    settings = get_settings()
    if settings.app_env in ["development", "local", "testing"]:
        return {"username": "local_dev_user", "role": "admin"}

    # Full Auth implementation would normally go here for production
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        token_data = decode_access_token(token.split(" ")[1])
        return {"username": token_data.username, "role": token_data.role}
    except Exception:
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
