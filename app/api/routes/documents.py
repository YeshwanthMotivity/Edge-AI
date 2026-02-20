"""
SecureDocAI — Document Processing Routes
============================================
Core API endpoints for document analysis, masking, signing, and full processing.
"""

import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.pipeline import DocumentPipeline
from app.core.exceptions import SecureDocAIError
from app.models.document import ProcessResponse, AnalyzeResponse
from app.core.rate_limiter import limiter
from config.settings import get_settings

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Document Processing"])


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
    save_path = settings.upload_dir / f"{file_id}_{file.filename}"

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Validate file size
    if save_path.stat().st_size > settings.max_file_size_mb * 1024 * 1024:
        save_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.max_file_size_mb}MB",
        )

    return save_path


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze Document",
    description="Detect sensitive entities without applying masking. Returns entity types, counts, and confidence scores.",
)
def analyze_document(
    file: UploadFile = File(..., description="Document to analyze (PDF/Image)"),
    policy: str = Form(default="default_policy", description="Detection policy name"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    """
    Detect sensitive entities in a document (read-only analysis).
    No masking or signing is performed.
    """
    file_path = _save_upload(file)

    try:
        pipeline = DocumentPipeline(db)
        result = pipeline.analyze_only(file_path, file.filename, policy)

        return AnalyzeResponse(
            document_id=result["document_id"],
            entities_detected=result["entities_detected"],
            entity_summary=result["entity_summary"],
            confidence_scores=result["confidence_scores"],
            processing_time_ms=result["processing_time_ms"],
        )
    except SecureDocAIError as e:
        raise HTTPException(status_code=500, detail=e.message)
    finally:
        # Clean up uploaded file
        if file_path.exists():
            file_path.unlink()


@router.post(
    "/process",
    response_model=ProcessResponse,
    summary="Full Pipeline Processing",
    description="Complete pipeline: analyze → mask → sign → audit. Returns signed sanitized document.",
)
@limiter.limit("20/minute")
def process_document(
    request: Request,
    file: UploadFile = File(..., description="Document to process (PDF/Image)"),
    policy: str = Form(default="default_policy", description="Detection policy name"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProcessResponse:
    """
    Execute the full document sanitization pipeline.

    Flow: Extract → Detect → Redact → Log Processing → Sign → Log Signature → Output
    """
    file_path = _save_upload(file)

    try:
        pipeline = DocumentPipeline(db)
        result = pipeline.process(
            file_path=file_path,
            filename=file.filename,
            policy_name=policy,
            operator_id=current_user["username"],
        )

        return ProcessResponse(
            document_id=result.document_id,
            status=result.status,
            original_hash=result.original_hash,
            sanitized_hash=result.sanitized_hash,
            sanitized_path=result.sanitized_path,
            signed_path=result.signed_path,
            signature_serial=result.signature_serial,
            entities_detected=result.entities_detected,
            entities_redacted=result.entities_redacted,
            entity_summary=result.entity_summary,
            processing_time_ms=result.processing_time_ms,
        )
    except SecureDocAIError as e:
        raise HTTPException(status_code=500, detail=e.message)


@router.post(
    "/mask",
    response_model=ProcessResponse,
    summary="Mask Document",
    description="Apply masking only (no signing). Returns sanitized document.",
)
@limiter.limit("30/minute")
def mask_document(
    request: Request,
    file: UploadFile = File(..., description="Document to mask (PDF/Image)"),
    policy: str = Form(default="default_policy", description="Detection policy name"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProcessResponse:
    """Apply redaction without signing — useful for preview or non-final outputs."""
    file_path = _save_upload(file)

    try:
        pipeline = DocumentPipeline(db)
        result = pipeline.process(
            file_path=file_path,
            filename=file.filename,
            policy_name=policy,
            operator_id=current_user["username"],
        )
        return ProcessResponse(
            document_id=result.document_id,
            status=result.status,
            original_hash=result.original_hash,
            sanitized_hash=result.sanitized_hash,
            sanitized_path=result.sanitized_path,
            entities_detected=result.entities_detected,
            entities_redacted=result.entities_redacted,
            entity_summary=result.entity_summary,
            processing_time_ms=result.processing_time_ms,
        )
    except SecureDocAIError as e:
        raise HTTPException(status_code=500, detail=e.message)
