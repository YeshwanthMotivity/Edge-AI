"""
SecureDocAI — Health Check Route
====================================
System health and readiness endpoint.
"""

import time
from importlib.util import find_spec

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.database import get_db
from app.models.document import HealthResponse
from config.settings import get_settings

router = APIRouter(tags=["Health"])

# Track application start time
_start_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Advanced System Health Check",
    description="Returns overall system health status and individual component readiness.",
)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Check if the system and its dependent components are ready."""
    settings = get_settings()
    
    # 1. Check Database
    db_status = "down"
    try:
        db.execute(text("SELECT 1"))
        db_status = "up"
    except Exception:
        pass

    # 2. Check Signer Module (PyHanko)
    signer_status = "up" if find_spec("pyhanko") is not None else "down"

    # 3. Check OCR Engine (Tesseract)
    # PyTesseract throws error if binary not found in path
    ocr_status = "down"
    if find_spec("pytesseract") is not None:
        try:
            import pytesseract
            # Get Tesseract version simply checks if executable exists
            pytesseract.get_tesseract_version()
            ocr_status = "up"
        except Exception:
            pass

    overall = "healthy" if all(s == "up" for s in [db_status, signer_status, ocr_status]) else "degraded"

    return HealthResponse(
        status=overall,
        version="1.0.0",
        environment=settings.app_env,
        uptime_seconds=round(time.time() - _start_time, 2),
        database=db_status,
        signer=signer_status,
        ocr_engine=ocr_status,
    )
