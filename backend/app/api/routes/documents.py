"""
SecureDocAI — Document Processing Routes
============================================
Core API endpoints for document analysis, masking, signing, and full processing.
"""

import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.pipeline import DocumentPipeline
from app.core.exceptions import SecureDocAIError
from app.models.document import ProcessResponse, AnalyzeResponse
from app.models.llm import SafeAnalysisRequest, SafeAnalysisResponse
from app.core.rate_limiter import limiter
from app.services.llm_gateway import LLMGateway
from config.settings import get_settings

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Document Processing"])

# Singleton LLM Gateway (usually injected via DI in a larger app)
llm_gateway_instance = LLMGateway()


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
    request: Request,
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
        ner_detector = getattr(request.app.state, "ner_detector", None)
        pipeline = DocumentPipeline(db, ner_detector=ner_detector)
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
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document to process (PDF/Image)"),
    policy: str = Form(default="default_policy", description="Detection policy name"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProcessResponse:
    """
    Execute the full document sanitization pipeline.

    Flow: Extract → Detect → Redact → Log Processing → Sign → Log Signature → Output
    """
    print(f"\n[DEBUG] === POST /api/v1/process ===")
    print(f"[DEBUG] Received file: {file.filename}, Policy: {policy}")
    file_path = _save_upload(file)
    print(f"[DEBUG] File saved temporarily to: {file_path}")

    try:
        settings = get_settings()
        ner_detector = getattr(request.app.state, "ner_detector", None)
        print(f"[DEBUG] Initializing Document Pipeline...")
        pipeline = DocumentPipeline(db, ner_detector=ner_detector)
        
        print(f"[DEBUG] Starting core pipeline execution...")
        result = pipeline.process(
            file_path=file_path,
            filename=file.filename,
            policy_name=policy,
            operator_id=current_user["username"],
            background_tasks=background_tasks if settings.app_env != "testing" else None,
        )
        print(f"[DEBUG] Pipeline finished successfully. Document ID: {result.document_id}")

        return ProcessResponse(
            document_id=result.document_id,
            status=result.status,
            original_text=result.original_text,
            redacted_text=result.redacted_text,
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
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document to mask (PDF/Image)"),
    policy: str = Form(default="default_policy", description="Detection policy name"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProcessResponse:
    """Apply redaction without signing — useful for preview or non-final outputs."""
    print(f"\n[DEBUG] === POST /api/v1/mask ===")
    print(f"[DEBUG] Received mask request for: {file.filename}")
    file_path = _save_upload(file)

    try:
        ner_detector = getattr(request.app.state, "ner_detector", None)
        pipeline = DocumentPipeline(db, ner_detector=ner_detector)
        result = pipeline.process(
            file_path=file_path,
            filename=file.filename,
            policy_name=policy,
            operator_id=current_user["username"],
            background_tasks=background_tasks,
        )
        print(f"[DEBUG] Masking completed. Detected: {result.entities_detected}, Redacted: {result.entities_redacted}")
        return ProcessResponse(
            document_id=result.document_id,
            status=result.status,
            original_text=result.original_text,
            redacted_text=result.redacted_text,
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


@router.post(
    "/analyze-safely",
    response_model=SafeAnalysisResponse,
    summary="Safe LLM Integration",
    description="Analyzes a document, redacts PII, sends clean text to an LLM, and re-injects real values into the response.",
)
@limiter.limit("10/minute")
def analyze_safely(
    request: Request,
    file: UploadFile = File(..., description="Document to safely analyze"),
    prompt: str = Form(default="Summarize this document securely.", description="Prompt for the LLM"),
    policy: str = Form(default="default_policy", description="Detection policy name"),
    llm_provider: str = Form(default="mock", description="'mock' or 'openai'"),
    reidentify: bool = Form(default=True, description="Re-inject original values in response"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SafeAnalysisResponse:
    """
    Phase 6: Pass-through secure proxy for LLM analysis.
    Executes standard redaction pipeline, but intercepts the masked text
    and routes it to the external LLM safely.
    """
    print(f"\n[DEBUG] === POST /api/v1/analyze-safely ===")
    print(f"[DEBUG] File: {file.filename}, Prompt: {prompt}")
    file_path = _save_upload(file)

    try:
        # 1. Pipeline Extraction and Detection
        ner_detector = getattr(request.app.state, "ner_detector", None)
        print(f"[DEBUG] Initializing Document Pipeline...")
        pipeline = DocumentPipeline(db, ner_detector=ner_detector)
        
        # We need the direct output text, so we'll use internal pipeline methods tailored for text analysis
        document_id = str(uuid.uuid4())
        print(f"[DEBUG] Starting text extraction for ID: {document_id}")
        extracted_content = pipeline._extract(file_path, document_id)
        
        # Run detection
        print(f"[DEBUG] Running entity detection rules...")
        policy_obj = pipeline.policy_loader.load(policy)
        redaction_map = pipeline._detect(extracted_content, policy_obj, document_id)
        print(f"[DEBUG] Entities successfully detected mapped.")
        
        # We need the raw masked text. TextRedactor does this naturally.
        # Since this is for the LLM, we generate a perfectly masked text string.
        masked_text = extracted_content.full_text
        if masked_text and redaction_map.entities:
            # Sort in reverse to replace from end to beginning to preserve offsets
            sorted_entities = sorted(
                (e for e in redaction_map.entities if not e.is_allowlisted and e.location), 
                key=lambda e: e.location.start_char, 
                reverse=True
            )
            for entity in sorted_entities:
                masked_text = (
                    masked_text[:entity.location.start_char] 
                    + f"{entity.masked_value}" 
                    + masked_text[entity.location.end_char:]
                )

        # 2. Register mapping with LLM Gateway
        print(f"[DEBUG] Registering sensitive map with LLM Edge Gateway...")
        llm_gateway_instance.register_document(document_id, redaction_map)
        
        # 3. Query LLM securely
        print(f"[DEBUG] Forwarding sanitized text to LLM (Provider: {llm_provider})...")
        raw_llm_response = llm_gateway_instance.query(
            document_id=document_id,
            sanitized_text=masked_text,
            prompt=prompt,
            provider=llm_provider
        )
        print(f"[DEBUG] LLM responded successfully.")
        
        # 4. Re-identify response
        final_response = raw_llm_response
        if reidentify:
            print(f"[DEBUG] Re-injecting original sensitive values into final response...")
            final_response = llm_gateway_instance.re_identify(document_id, raw_llm_response)

        return SafeAnalysisResponse(
            document_id=document_id,
            prompt_sent=prompt,
            llm_provider_used=llm_provider,
            raw_llm_response=raw_llm_response,
            reidentified_response=final_response,
            entities_protected=len([e for e in redaction_map.entities if not e.is_allowlisted])
        )

    except SecureDocAIError as e:
        raise HTTPException(status_code=500, detail=e.message)
    finally:
        if file_path.exists():
            file_path.unlink()

from fastapi.responses import FileResponse
from app.services.signing.digital_signer import DigitalSigner

@router.get(
    "/documents/{document_id}/download",
    summary="Download Processed Document",
    description="Download the sanitized or signed PDF.",
)
def download_document(
    document_id: str,
    type: str = "sanitized",  # "sanitized" or "signed"
    current_user: dict = Depends(get_current_user),
) -> FileResponse:
    """Download a processed document."""
    settings = get_settings()
    
    if type == "signed":
        file_path = settings.signed_dir / f"{document_id}_signed.pdf"
    else:
        # Default to sanitized (which might be pdf or png based on input, but usually pdf)
        file_path = settings.processed_dir / f"{document_id}_sanitized.pdf"
        if not file_path.exists():
            # Check for other extensions
            for ext in [".png", ".jpg", ".jpeg", ".tiff"]:
                alt_path = settings.processed_dir / f"{document_id}_sanitized{ext}"
                if alt_path.exists():
                    file_path = alt_path
                    break

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found for ID: {document_id} and type: {type}"
        )

    # Determine media_type natively
    extension = file_path.suffix.lower()
    if extension == ".pdf":
        media_type = "application/pdf"
    elif extension in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif extension == ".png":
        media_type = "image/png"
    elif extension in [".tif", ".tiff"]:
        media_type = "image/tiff"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=f"{document_id}_{type}{extension}"
    )


@router.post(
    "/verify",
    summary="Verify Document Signature",
    description="Upload a signed document to cryptographically verify its signature.",
)
def verify_document_signature(
    file: UploadFile = File(..., description="Signed PDF to verify"),
) -> dict:
    """Verify the digital signature of a document."""
    file_path = _save_upload(file)

    try:
        if file_path.suffix.lower() != ".pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF documents can have digital signatures verified."
            )
            
        signer = DigitalSigner(None)  # Verification doesn't require KeyManager
        result = signer.verify_signature(file_path)
        
        return result
    finally:
        if file_path.exists():
            file_path.unlink()
