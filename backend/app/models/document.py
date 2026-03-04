"""
SecureDocAI — Document Models
==============================
Pydantic models for document upload, extraction, and processing results.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Supported document types."""
    PDF_DIGITAL = "pdf_digital"
    PDF_SCANNED = "pdf_scanned"
    IMAGE_PNG = "image_png"
    IMAGE_JPG = "image_jpg"
    IMAGE_TIFF = "image_tiff"


class ProcessingStatus(str, Enum):
    """Document processing lifecycle status."""
    UPLOADED = "uploaded"
    AUTHORIZED = "authorized"
    EXTRACTING = "extracting"
    DETECTING = "detecting"
    REDACTING = "redacting"
    SIGNING = "signing"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Request Models ──

class DocumentUpload(BaseModel):
    """Metadata accompanying a document upload."""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the document")
    policy_name: str = Field(default="default_policy", description="Detection policy to apply")
    callback_url: Optional[str] = Field(default=None, description="Optional webhook for async results")


# ── Internal Models ──

class ExtractedContent(BaseModel):
    """Result of text/OCR extraction from a document."""
    document_id: str = Field(..., description="Unique processing ID")
    text: str = Field(default="", description="Extracted full text")
    pages: list[dict] = Field(default_factory=list, description="Per-page text + bounding boxes")
    extraction_method: str = Field(..., description="Method used: pdf_text | ocr")
    page_count: int = Field(default=0, description="Total pages in document")
    has_embedded_text: bool = Field(default=False, description="Whether PDF had embedded text layer")
    metadata: dict = Field(default_factory=dict, description="Document metadata (author, creation date, etc.)")
    word_locations: list[dict] = Field(default_factory=list, description="Global mapping of words to bounding boxes")


class ProcessingResult(BaseModel):
    """Final result of the full processing pipeline."""
    document_id: str = Field(..., description="Unique processing ID")
    status: ProcessingStatus = Field(..., description="Final processing status")
    original_text: Optional[str] = Field(default=None, description="Original extracted text")
    redacted_text: Optional[str] = Field(default=None, description="Text after redaction")
    original_hash: str = Field(..., description="SHA-256 hash of the original document")
    sanitized_hash: Optional[str] = Field(default=None, description="SHA-256 hash of the sanitized document")
    sanitized_path: Optional[str] = Field(default=None, description="Path to sanitized PDF")
    signed_path: Optional[str] = Field(default=None, description="Path to signed PDF")
    signature_serial: Optional[str] = Field(default=None, description="Digital signature serial number")
    entities_detected: int = Field(default=0, description="Total entities detected")
    entities_redacted: int = Field(default=0, description="Total entities redacted")
    entity_summary: dict = Field(default_factory=dict, description="Count per entity type (no raw PII)")
    processing_time_ms: float = Field(default=0.0, description="Total processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    errors: list[str] = Field(default_factory=list, description="Any errors encountered")


# ── Response Models ──

class AnalyzeResponse(BaseModel):
    """Response for /analyze endpoint — detection only, no masking."""
    document_id: str
    entities_detected: int
    entity_summary: dict
    confidence_scores: dict
    processing_time_ms: float


class ProcessResponse(BaseModel):
    """Response for /process endpoint — full pipeline result."""
    document_id: str
    status: ProcessingStatus
    original_text: Optional[str] = None
    redacted_text: Optional[str] = None
    original_hash: str
    sanitized_hash: Optional[str] = None
    sanitized_path: Optional[str] = None
    signed_path: Optional[str] = None
    signature_serial: Optional[str] = None
    entities_detected: int
    entities_redacted: int
    entity_summary: dict
    processing_time_ms: float
    audit_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    environment: str = "development"
    uptime_seconds: float = 0.0
    database: str = "unknown"
    signer: str = "unknown"
    ocr_engine: str = "unknown"


class PreCheckResponse(BaseModel):
    """Real-time response for browser extension uploads."""
    authorized: bool = Field(..., description="Whether the document is allowed for upload")
    reason: str = Field(..., description="Reason for block or approval")
    detected_entities: list[str] = Field(default_factory=list, description="List of sensitive entity types found")
    document_id: Optional[str] = Field(None, description="Temporary processing ID for logging")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

