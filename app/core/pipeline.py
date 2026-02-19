"""
SecureDocAI — Main Processing Pipeline
==========================================
Orchestrator implementing the corrected pipeline flow:

  Upload → Auth → Extract → Detect → Redact → Generate PDF
           → Log Processing → Sign → Log Signature → Output

This makes audit logs legally defensible:
  - Processing log = what was detected and masked
  - Signature log  = legal verification record (post-signing)
"""

import uuid
import time
from pathlib import Path
from typing import Optional

import structlog
from sqlalchemy.orm import Session

from app.core.security import compute_file_hash
from app.core.exceptions import (
    ExtractionError, DetectionError, RedactionError,
    SigningError, AuditError, DocumentValidationError,
)
from app.models.document import ExtractedContent, ProcessingResult, ProcessingStatus
from app.models.entity import RedactionMap
from app.models.policy import Policy, PolicyLoader
from app.services.extraction.pdf_extractor import PdfExtractor
from app.services.extraction.ocr_extractor import OcrExtractor
from app.services.detection.regex_detector import RegexDetector
from app.services.detection.ner_detector import NerDetector
from app.services.redaction.text_redactor import TextRedactor
from app.services.redaction.image_redactor import ImageRedactor
from app.services.signing.digital_signer import DigitalSigner
from app.services.signing.key_manager import KeyManager
from app.services.audit.audit_logger import AuditLogger
from config.settings import get_settings

logger = structlog.get_logger(__name__)


class DocumentPipeline:
    """
    Main document processing pipeline orchestrator.

    Corrected Flow (legally defensible):
        1. Validate document
        2. Extract text (PDF text / OCR)
        3. Detect sensitive entities (Regex + NER)
        4. Redact (true redaction)
        5. Generate sanitized PDF
        6. LOG PROCESSING ← audit record #1
        7. Sign sanitized PDF
        8. LOG SIGNATURE  ← audit record #2 (legal)
        9. Return result
    """

    def __init__(self, db: Session):
        self.settings = get_settings()
        self.db = db

        # Initialize services
        self.pdf_extractor = PdfExtractor()
        self.ocr_extractor = OcrExtractor()
        self.regex_detector = RegexDetector()
        self.ner_detector = NerDetector(model_path=str(self.settings.onnx_model_path))
        self.text_redactor = TextRedactor()
        self.image_redactor = ImageRedactor()
        self.audit_logger = AuditLogger(db)

        # Policy loader
        policies_dir = Path(__file__).resolve().parent.parent.parent / "config" / "policies"
        self.policy_loader = PolicyLoader(policies_dir)

        # Signing (initialized lazily when keys are available)
        self._signer: Optional[DigitalSigner] = None

    def _get_signer(self) -> DigitalSigner:
        """Lazy-load the digital signer with key management."""
        if self._signer is None:
            key_manager = KeyManager(
                cert_path=self.settings.signing_cert_path,
                key_path=self.settings.signing_key_path,
                p12_path=self.settings.signing_p12_path,
                p12_passphrase=self.settings.signing_p12_passphrase,
            )
            key_manager.load_keys()
            self._signer = DigitalSigner(key_manager)
        return self._signer

    async def process(
        self,
        file_path: Path,
        filename: str,
        policy_name: str = "default_policy",
        operator_id: str = "system",
    ) -> ProcessingResult:
        """
        Execute the full document processing pipeline.

        Args:
            file_path: Path to the uploaded document.
            filename: Original filename.
            policy_name: Detection policy to apply.
            operator_id: ID of the user/system triggering processing.

        Returns:
            ProcessingResult with all metadata.
        """
        document_id = str(uuid.uuid4())
        start_time = time.time()
        errors: list[str] = []

        logger.info("pipeline_start", document_id=document_id, filename=filename)

        try:
            # ── Step 0: Validate ──
            original_hash = compute_file_hash(str(file_path))
            file_size = file_path.stat().st_size
            policy = self.policy_loader.load(policy_name)

            # ── Step 1: Extract ──
            content = self._extract(file_path, document_id)

            # ── Step 2: Detect ──
            redaction_map = self._detect(content, policy, document_id)

            # ── Step 3: Redact ──
            sanitized_path = self._redact(file_path, redaction_map, document_id)
            sanitized_hash = compute_file_hash(str(sanitized_path))

            # ── Step 4: LOG PROCESSING (before signing) ──
            processing_time_ms = (time.time() - start_time) * 1000
            processing_log = self.audit_logger.log_processing(
                document_id=document_id,
                operator_id=operator_id,
                filename=filename,
                original_hash=original_hash,
                sanitized_hash=sanitized_hash,
                file_size_bytes=file_size,
                page_count=content.page_count,
                extraction_method=content.extraction_method,
                policy_applied=policy_name,
                entities_detected=redaction_map.total_entities,
                entities_redacted=len([e for e in redaction_map.entities if not e.is_allowlisted]),
                entity_summary=redaction_map.summary(),
                status="completed",
                processing_time_ms=processing_time_ms,
            )

            # ── Step 5: Sign ──
            signed_path = None
            signature_serial = None
            if policy.signing_required:
                try:
                    signer = self._get_signer()
                    signed_output = self.settings.signed_dir / f"{document_id}_signed.pdf"
                    sign_result = signer.sign_pdf(sanitized_path, signed_output)
                    signed_path = sign_result["signed_path"]
                    signature_serial = sign_result["signature_serial"]

                    # ── Step 6: LOG SIGNATURE (after signing) ──
                    signed_hash = compute_file_hash(signed_path)
                    self.audit_logger.log_signature(
                        processing_log_id=processing_log.id,
                        document_id=document_id,
                        signed_hash=signed_hash,
                        signature_serial=sign_result.get("signature_serial"),
                        certificate_subject=sign_result.get("certificate_subject"),
                        certificate_issuer=sign_result.get("certificate_issuer"),
                        signing_algorithm=sign_result.get("signing_algorithm"),
                        verification_status="valid",
                        signed_path=signed_path,
                    )
                except (SigningError, Exception) as e:
                    errors.append(f"Signing skipped: {str(e)}")
                    logger.warning("signing_skipped", error=str(e))

            # ── Build Result ──
            total_time_ms = (time.time() - start_time) * 1000

            result = ProcessingResult(
                document_id=document_id,
                status=ProcessingStatus.COMPLETED,
                original_hash=original_hash,
                sanitized_hash=sanitized_hash,
                sanitized_path=str(sanitized_path),
                signed_path=signed_path,
                signature_serial=signature_serial,
                entities_detected=redaction_map.total_entities,
                entities_redacted=len([e for e in redaction_map.entities if not e.is_allowlisted]),
                entity_summary=redaction_map.summary(),
                processing_time_ms=total_time_ms,
                errors=errors,
            )

            logger.info(
                "pipeline_complete",
                document_id=document_id,
                entities=redaction_map.total_entities,
                time_ms=total_time_ms,
            )
            return result

        except Exception as e:
            # Log failed processing
            processing_time_ms = (time.time() - start_time) * 1000
            try:
                self.audit_logger.log_processing(
                    document_id=document_id,
                    operator_id=operator_id,
                    filename=filename,
                    original_hash=original_hash if 'original_hash' in dir() else "unknown",
                    status="failed",
                    processing_time_ms=processing_time_ms,
                    error_message=str(e),
                )
            except Exception:
                pass

            logger.error("pipeline_failed", document_id=document_id, error=str(e))
            return ProcessingResult(
                document_id=document_id,
                status=ProcessingStatus.FAILED,
                original_hash=original_hash if 'original_hash' in dir() else "unknown",
                processing_time_ms=processing_time_ms,
                errors=[str(e)],
            )

    def _extract(self, file_path: Path, document_id: str) -> ExtractedContent:
        """Extract text using the appropriate extractor."""
        if self.pdf_extractor.can_handle(file_path):
            content = self.pdf_extractor.extract(file_path, document_id)
            # If PDF has no text, fall back to OCR
            if not content.has_embedded_text:
                logger.info("fallback_to_ocr", document_id=document_id)
                content = self.ocr_extractor.extract(file_path, document_id)
        else:
            content = self.ocr_extractor.extract(file_path, document_id)
        return content

    def _detect(self, content: ExtractedContent, policy: Policy, document_id: str) -> RedactionMap:
        """Run all detectors and merge results."""
        all_entities = []

        # Regex detection
        try:
            regex_entities = self.regex_detector.detect(content, policy)
            all_entities.extend(regex_entities)
        except Exception as e:
            logger.warning("regex_detection_error", error=str(e))

        # NER detection
        try:
            ner_entities = self.ner_detector.detect(content, policy)
            all_entities.extend(ner_entities)
        except Exception as e:
            logger.warning("ner_detection_error", error=str(e))

        # Build redaction map
        redaction_map = RedactionMap(
            document_id=document_id,
            entities=all_entities,
            total_entities=len(all_entities),
            entity_counts={},
            policy_applied=policy.policy_name,
        )
        redaction_map.entity_counts = redaction_map.summary()

        return redaction_map

    def _redact(self, file_path: Path, redaction_map: RedactionMap, document_id: str) -> Path:
        """Apply redaction and return path to sanitized document."""
        output_path = self.settings.processed_dir / f"{document_id}_sanitized.pdf"

        if file_path.suffix.lower() == ".pdf":
            return self.text_redactor.redact(file_path, output_path, redaction_map)
        else:
            return self.image_redactor.redact(file_path, output_path, redaction_map)

    async def analyze_only(
        self,
        file_path: Path,
        filename: str,
        policy_name: str = "default_policy",
    ) -> dict:
        """
        Detection only — no masking or signing.
        Used for the /analyze endpoint.
        """
        document_id = str(uuid.uuid4())
        start_time = time.time()

        content = self._extract(file_path, document_id)
        policy = self.policy_loader.load(policy_name)
        redaction_map = self._detect(content, policy, document_id)

        return {
            "document_id": document_id,
            "entities_detected": redaction_map.total_entities,
            "entity_summary": redaction_map.summary(),
            "confidence_scores": {
                e.entity_type.value: e.confidence
                for e in redaction_map.entities
            },
            "processing_time_ms": (time.time() - start_time) * 1000,
        }
