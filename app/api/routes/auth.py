"""
SecureDocAI — Authentication Routes
=======================================
JWT token generation and user authentication.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import create_access_token, verify_password, hash_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── POC: In-memory user store (replace with DB in production) ──
# Password: "admin123" hashed with bcrypt
POC_USERS = {
    "admin": {
        "username": "admin",
        "hashed_password": hash_password("admin123"),
        "role": "admin",
    },
    "operator": {
        "username": "operator",
        "hashed_password": hash_password("operator123"),
        "role": "operator",
    },
}


class LoginRequest(BaseModel):
    """Login request payload."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


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
async def login(request: LoginRequest) -> TokenResponse:
    """
    Authenticate user and return a JWT access token.

    POC: Uses in-memory user store.
    Production: Replace with database-backed user management.
    """
    user = POC_USERS.get(request.username)

    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )

    return TokenResponse(
        access_token=access_token,
        username=user["username"],
        role=user["role"],
    )
