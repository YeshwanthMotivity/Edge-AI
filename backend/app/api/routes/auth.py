"""
SecureDocAI — Authentication Routes
=======================================
JWT token generation and user authentication.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from app.core.security import create_access_token, verify_password, hash_password
from app.core.rate_limiter import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])


from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Get Access Token",
    description="Authenticate and receive a JWT access token.",
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate user and return a JWT access token.
    Uses the database-backed User model.
    """
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not user.is_active or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )

    return TokenResponse(
        access_token=access_token,
        username=user.username,
        role=user.role,
    )
