"""
SecureDocAI — Audit ORM Models
================================
SQLAlchemy models for immutable audit records.
Two-phase logging: ProcessingLog (pre-sign) + SignatureLog (post-sign).
"""

from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class ProcessingLog(Base):
    """
    Audit record for document processing (logged BEFORE signing).

    Records: what was uploaded, what was detected, what was masked.
    Contains NO raw PII — only entity type counts and metadata.
    """
    __tablename__ = "processing_logs"

    id = Column(String(36), primary_key=True, index=True)
    document_id = Column(String(36), nullable=False, index=True)
    operator_id = Column(String(100), nullable=False, default="system")
    filename = Column(String(255), nullable=False)
    original_hash = Column(String(64), nullable=False, comment="SHA-256 of original document")
    sanitized_hash = Column(String(64), nullable=True, comment="SHA-256 of sanitized document")
    file_size_bytes = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    extraction_method = Column(String(20), nullable=True, comment="pdf_text | ocr")
    policy_applied = Column(String(100), nullable=False, default="default_policy")
    entities_detected = Column(Integer, default=0)
    entities_redacted = Column(Integer, default=0)
    entity_summary = Column(JSON, nullable=True, comment="Count per entity type, no raw PII")
    status = Column(String(20), nullable=False, default="processing")
    processing_time_ms = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ML Model Tracing Data
    model_name = Column(String(255), nullable=True, comment="NER model used")
    model_version = Column(String(255), nullable=True)
    model_hash = Column(String(255), nullable=True, comment="SHA-256 parameter hash")

    # Relationship to signature log
    signature_log = relationship("SignatureLog", back_populates="processing_log", uselist=False)


class SignatureLog(Base):
    """
    Audit record for digital signature (logged AFTER signing).

    Records: signature serial, certificate info, verification status.
    This is the legal verification record.
    """
    __tablename__ = "signature_logs"

    id = Column(String(36), primary_key=True, index=True)
    processing_log_id = Column(String(36), ForeignKey("processing_logs.id"), nullable=False)
    document_id = Column(String(36), nullable=False, index=True)
    signed_hash = Column(String(64), nullable=False, comment="SHA-256 of signed document")
    signature_serial = Column(String(100), nullable=True)
    certificate_subject = Column(String(255), nullable=True)
    certificate_issuer = Column(String(255), nullable=True)
    certificate_valid_from = Column(DateTime, nullable=True)
    certificate_valid_to = Column(DateTime, nullable=True)
    signing_algorithm = Column(String(50), nullable=True)
    timestamp_authority = Column(String(255), nullable=True, comment="TSA URL if used")
    verification_status = Column(String(20), default="pending", comment="pending | valid | invalid")
    signed_path = Column(String(500), nullable=True)
    signed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship back to processing log
    processing_log = relationship("ProcessingLog", back_populates="signature_log")
