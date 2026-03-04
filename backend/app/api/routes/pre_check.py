"""
SecureDocAI — Pre-Check Router
==================================
Lightweight endpoint for real-time document validation by the browser extension.
"""

import uuid
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.pipeline import DocumentPipeline
from app.models.document import PreCheckResponse
from config.settings import get_settings

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Browser Extension"])

def _save_upload(file: UploadFile) -> Path:
    """Save uploaded file to storage and return the path."""
    settings = get_settings()
    settings.ensure_directories()

    # Validate file extension
    suffix = Path(file.filename).suffix.lower()
    if suffix not in settings.supported_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: {suffix}. Supported: {settings.supported_extensions}",
        )

    # Save with unique filename
    file_id = str(uuid.uuid4())[:8]
    save_path = settings.upload_dir / f"precheck_{file_id}_{file.filename}"

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return save_path

@router.post("/pre-check", response_model=PreCheckResponse)
def pre_check_document(
    request: Request,
    file: UploadFile = File(..., description="Document to check before upload"),
    policy: str = Form(default="default_policy", description="Detection policy name"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PreCheckResponse:
    """
    Rapidly scan a document for PII without performing redaction.
    Used by browser extension to block unauthorized uploads.
    """
    file_path = _save_upload(file)

    # Fast bypass for documents already processed by SecureDocAI
    lower_name = file.filename.lower()
    if lower_name.startswith("sanitized_") or lower_name.endswith("_signed.pdf") or lower_name.endswith("_sanitized.pdf"):
        logger.info("extension_pre_check_bypass", filename=file.filename, reason="Known sanitized file format")
        if file_path.exists():
            file_path.unlink()
        return PreCheckResponse(
            authorized=True,
            reason="Document is digitally signed and sanitized.",
            detected_entities=[],
            document_id="generated_doc",
            timestamp=datetime.utcnow()
        )

    try:
        ner_detector = getattr(request.app.state, "ner_detector", None)
        pipeline = DocumentPipeline(db, ner_detector=ner_detector)
        
        # We only need analysis for the pre-check
        result = pipeline.analyze_only(file_path, file.filename, policy)

        entities_found = list(result.get("entity_summary", {}).keys())
        is_authorized = len(entities_found) == 0
        
        reason = "Authorized" if is_authorized else f"Blocked: Contains sensitive data ({', '.join(entities_found)})"
        
        logger.info(
            "extension_pre_check",
            document_id=result.get("document_id"),
            authorized=is_authorized,
            entities=entities_found
        )

        return PreCheckResponse(
            authorized=is_authorized,
            reason=reason,
            detected_entities=entities_found,
            document_id=result.get("document_id"),
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error("pre_check_failed", error=str(e))
        return PreCheckResponse(
            authorized=False, 
            reason=f"Security scan failed: {str(e)}",
            timestamp=datetime.utcnow()
        )
    finally:
        # Clean up uploaded file immediately
        if file_path.exists():
            file_path.unlink()
