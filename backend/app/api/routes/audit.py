"""
SecureDocAI — Audit Processing Routes
=========================================
API endpoints for securely retrieving the immutable audit trails.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import io
import csv
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.services.audit.audit_logger import AuditLogger
from app.core.exceptions import SecureDocAIError

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/audit", tags=["Audit & Compliance"])


@router.get(
    "",
    summary="Retrieve All Recent Audit Logs",
    description="Get the most recent processing logs for all documents.",
)
def get_all_audits(
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve the recent audit logs formatted for the frontend."""
    try:
        audit_logger = AuditLogger(db)
        entries = audit_logger.get_all_audits(limit=limit)
        return {"entries": entries}
    except Exception as e:
        logger.error("audit_list_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit logs: {str(e)}"
        )


@router.get(
    "/summary",
    summary="Get Dashboard Metrics",
    description="Retrieve aggregate statistics for the dashboard metrics.",
)
def get_audit_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve summary metrics for the dashboard."""
    try:
        audit_logger = AuditLogger(db)
        return audit_logger.get_summary_metrics()
    except Exception as e:
        logger.error("metrics_retrieval_failed", error=str(e))
        return {
            "total_documents": 0,
            "total_redacted": 0,
            "avg_processing_time": 0.0,
            "privacy_protected_percentage": 100.0
        }


@router.get(
    "/export",
    summary="Export Audit Logs as CSV",
    description="Download a CSV file containing all audit log entries.",
)
def export_audits(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate and stream a CSV of audit logs."""
    try:
        audit_logger = AuditLogger(db)
        # Get more entries for export than the default dashboard view
        entries = audit_logger.get_all_audits(limit=1000)
        
        output = io.StringIO()
        if entries:
            # Define fields for CSV
            fieldnames = ["document_id", "timestamp", "filename", "status", "entitiesFound", "processingTime", "fileSize"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for entry in entries:
                # Filter entry to match fieldnames
                filtered_entry = {k: v for k, v in entry.items() if k in fieldnames}
                writer.writerow(filtered_entry)
            
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
        )
    except Exception as e:
        logger.error("audit_export_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export audit logs: {str(e)}"
        )


@router.get(
    "/{document_id}",
    summary="Retrieve Full Audit Trail",
    description="Get the combined chronologically ordered processing and signature logs for a document.",
)
def get_document_audit(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve the legal verification record of a sanitized document."""
    try:
        audit_logger = AuditLogger(db)
        audit_data = audit_logger.get_full_audit(document_id)

        if audit_data.get("status") == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No audit trail found for document ID: {document_id}"
            )

        return audit_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error("audit_retrieval_failed", error=str(e), document_id=document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit log: {str(e)}"
        )
