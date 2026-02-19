"""
SecureDocAI — Health Check Route
====================================
System health and readiness endpoint.
"""

import time

from fastapi import APIRouter

from app.models.document import HealthResponse
from config.settings import get_settings

router = APIRouter(tags=["Health"])

# Track application start time
_start_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health Check",
    description="Returns system health status, version, and uptime.",
)
async def health_check() -> HealthResponse:
    """Check if the system is healthy and responsive."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=settings.app_env,
        uptime_seconds=round(time.time() - _start_time, 2),
    )
