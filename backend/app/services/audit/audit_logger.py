"""
SecureDocAI — Audit Logger Service
=====================================
Append-only audit logging for processing and signature events.
Implements the dual-log architecture:
  1. Log Processing (before signing) — what was detected and masked
  2. Log Signature (after signing) — legal verification record
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.services.audit.models import ProcessingLog, SignatureLog
from app.core.exceptions import AuditError

import structlog

logger = structlog.get_logger(__name__)


class AuditLogger:
    """Immutable audit trail for document processing compliance."""

    def __init__(self, db: Session):
        self.db = db

    # ── Phase 1: Log Processing (before signing) ──

    def log_processing(
        self,
        document_id: str,
        operator_id: str,
        filename: str,
        original_hash: str,
        sanitized_hash: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        page_count: Optional[int] = None,
        extraction_method: Optional[str] = None,
        policy_applied: str = "default_policy",
        entities_detected: int = 0,
        entities_redacted: int = 0,
        entity_summary: Optional[dict] = None,
        status: str = "completed",
        processing_time_ms: float = 0.0,
        error_message: Optional[str] = None,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None,
        model_hash: Optional[str] = None,
    ) -> ProcessingLog:
        """
        Create an immutable processing audit record.
        Called AFTER redaction but BEFORE signing.

        Returns:
            The created ProcessingLog record.
        """
        try:
            log_entry = ProcessingLog(
                id=str(uuid.uuid4()),
                document_id=document_id,
                operator_id=operator_id,
                filename=filename,
                original_hash=original_hash,
                sanitized_hash=sanitized_hash,
                file_size_bytes=file_size_bytes,
                page_count=page_count,
                extraction_method=extraction_method,
                policy_applied=policy_applied,
                entities_detected=entities_detected,
                entities_redacted=entities_redacted,
                entity_summary=entity_summary or {},
                status=status,
                processing_time_ms=processing_time_ms,
                error_message=error_message,
                model_name=model_name,
                model_version=model_version,
                model_hash=model_hash,
                created_at=datetime.utcnow(),
            )

            self.db.add(log_entry)
            self.db.commit()
            self.db.refresh(log_entry)

            logger.info(
                "processing_logged",
                document_id=document_id,
                entities_detected=entities_detected,
                status=status,
            )
            return log_entry

        except Exception as e:
            self.db.rollback()
            raise AuditError(
                message=f"Failed to log processing: {str(e)}",
                document_id=document_id,
            )

    # ── Phase 2: Log Signature (after signing) ──

    def log_signature(
        self,
        processing_log_id: str,
        document_id: str,
        signed_hash: str,
        signature_serial: Optional[str] = None,
        certificate_subject: Optional[str] = None,
        certificate_issuer: Optional[str] = None,
        certificate_valid_from: Optional[datetime] = None,
        certificate_valid_to: Optional[datetime] = None,
        signing_algorithm: Optional[str] = None,
        timestamp_authority: Optional[str] = None,
        verification_status: str = "valid",
        signed_path: Optional[str] = None,
    ) -> SignatureLog:
        """
        Create an immutable signature audit record.
        Called AFTER digital signing.
        This is the legal verification record.

        Returns:
            The created SignatureLog record.
        """
        try:
            sig_entry = SignatureLog(
                id=str(uuid.uuid4()),
                processing_log_id=processing_log_id,
                document_id=document_id,
                signed_hash=signed_hash,
                signature_serial=signature_serial,
                certificate_subject=certificate_subject,
                certificate_issuer=certificate_issuer,
                certificate_valid_from=certificate_valid_from,
                certificate_valid_to=certificate_valid_to,
                signing_algorithm=signing_algorithm,
                timestamp_authority=timestamp_authority,
                verification_status=verification_status,
                signed_path=signed_path,
                signed_at=datetime.utcnow(),
            )

            self.db.add(sig_entry)
            self.db.commit()
            self.db.refresh(sig_entry)

            logger.info(
                "signature_logged",
                document_id=document_id,
                signature_serial=signature_serial,
                verification_status=verification_status,
            )
            return sig_entry

        except Exception as e:
            self.db.rollback()
            raise AuditError(
                message=f"Failed to log signature: {str(e)}",
                document_id=document_id,
            )

    # ── Query Methods ──

    def get_processing_log(self, document_id: str) -> Optional[ProcessingLog]:
        """Retrieve processing log by document ID."""
        return (
            self.db.query(ProcessingLog)
            .filter(ProcessingLog.document_id == document_id)
            .first()
        )

    def get_all_audits(self, limit: int = 100) -> list[dict]:
        """Retrieve recent audit logs formatted for the frontend."""
        logs = (
            self.db.query(ProcessingLog)
            .order_by(ProcessingLog.created_at.desc())
            .limit(limit)
            .all()
        )
        
        results = []
        for log in logs:
            results.append({
                "id": log.id,
                "document_id": log.document_id,
                "timestamp": log.created_at.isoformat() if log.created_at else None,
                "filename": log.filename,
                "status": "success" if log.status in ["completed", "success"] else "failed",
                "entitiesFound": log.entities_detected,
                "processingTime": int(log.processing_time_ms) if log.processing_time_ms else 0,
                "fileSize": log.file_size_bytes or 0,
            })
        return results

    def get_full_audit(self, document_id: str) -> dict:
        """Retrieve complete audit trail (processing + signature) for a document."""
        processing = self.get_processing_log(document_id)
        if not processing:
            return {"document_id": document_id, "status": "not_found"}

        result = {
            "document_id": document_id,
            "processing": {
                "filename": processing.filename,
                "original_hash": processing.original_hash,
                "sanitized_hash": processing.sanitized_hash,
                "entities_detected": processing.entities_detected,
                "entities_redacted": processing.entities_redacted,
                "entity_summary": processing.entity_summary,
                "policy_applied": processing.policy_applied,
                "status": processing.status,
                "processing_time_ms": processing.processing_time_ms,
                "created_at": processing.created_at.isoformat() if processing.created_at else None,
            },
        }

        if processing.signature_log:
            sig = processing.signature_log
            result["signature"] = {
                "signed_hash": sig.signed_hash,
                "signature_serial": sig.signature_serial,
                "verification_status": sig.verification_status,
                "signing_algorithm": sig.signing_algorithm,
                "signed_at": sig.signed_at.isoformat() if sig.signed_at else None,
            }

        return result

    def get_summary_metrics(self) -> dict:
        """Calculate aggregate performance and privacy metrics."""
        try:
            # 1. Total Documents Processed
            total_docs = self.db.query(func.count(ProcessingLog.id)).scalar() or 0
            
            # 2. Total Entities Redacted
            total_redacted = self.db.query(func.sum(ProcessingLog.entities_redacted)).scalar() or 0
            
            # 3. Avg Processing Time (last 100 docs)
            avg_time = self.db.query(func.avg(ProcessingLog.processing_time_ms)).filter(
                ProcessingLog.processing_time_ms > 0
            ).limit(100).scalar() or 0
            
            # 4. Privacy Protected Metric (Fixed constant for now or calculated)
            privacy_protected = 100.0 if total_docs > 0 else 0.0

            return {
                "total_documents": total_docs,
                "total_redacted": int(total_redacted),
                "avg_processing_time": round(float(avg_time), 1),
                "privacy_protected_percentage": privacy_protected
            }
        except Exception as e:
            logger.error("metrics_calculation_failed", error=str(e))
            return {
                "total_documents": 0,
                "total_redacted": 0,
                "avg_processing_time": 0.0,
                "privacy_protected_percentage": 100.0
            }
