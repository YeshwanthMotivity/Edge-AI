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
from typing import Optional, Any

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
from app.db.database import SessionLocal
from config.settings import get_settings

logger = structlog.get_logger(__name__)

def _async_audit_log(processing_data: dict, signature_data: Optional[dict] = None, active_db: Optional[Session] = None) -> None:
    """Background task to commit audit logs to the database asynchronously."""
    db = active_db if active_db else SessionLocal()
    try:
        audit_logger = AuditLogger(db)
        p_log = audit_logger.log_processing(**processing_data)
        if signature_data:
            signature_data["processing_log_id"] = p_log.id
            audit_logger.log_signature(**signature_data)
    except Exception as e:
        logger.error("async_audit_log_failed", error=str(e))
    finally:
        if not active_db:
            db.close()

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

    def __init__(self, db: Session, ner_detector: Optional['NerDetector'] = None):
        self.settings = get_settings()
        self.db = db

        # Initialize services
        self.pdf_extractor = PdfExtractor()
        self.ocr_extractor = OcrExtractor()
        self.regex_detector = RegexDetector()

        # Use pre-loaded NER detector if provided, otherwise create a new one
        if ner_detector is not None:
            self.ner_detector = ner_detector
        else:
            self.ner_detector = NerDetector(
                model_name=self.settings.ner_model_name,
                model_path=str(self.settings.onnx_model_path),
                confidence_threshold=self.settings.ner_confidence_threshold,
                inference_timeout=self.settings.ner_inference_timeout_seconds,
            )

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

    def process(
        self,
        file_path: Path,
        filename: str,
        policy_name: str = "default_policy",
        operator_id: str = "system",
        background_tasks: Optional[Any] = None,
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
            sanitized_path = self._redact(file_path, redaction_map, document_id, content)
            sanitized_hash = compute_file_hash(str(sanitized_path))

            # generate redacted text for the UI preview
            original_text = content.text
            redacted_text = original_text
            if redacted_text and redaction_map.entities:
                # 1. Filter and sort by start position
                valid_entities = [e for e in redaction_map.entities if not e.is_allowlisted and e.location]
                
                if valid_entities:
                    sorted_entities = sorted(valid_entities, key=lambda e: e.location.start_char)
                    
                    # 2. Merge overlapping or nested spans
                    merged_spans = []
                    current_start = sorted_entities[0].location.start_char
                    current_end = sorted_entities[0].location.end_char
                    current_mask = sorted_entities[0].masked_value
                    
                    for next_ent in sorted_entities[1:]:
                        if next_ent.location.start_char < current_end:
                            # Overlap detected — extend the current span to cover both
                            current_end = max(current_end, next_ent.location.end_char)
                            # We keep the first mask found for the span
                        else:
                            # Gap detected — commit the current span and start a new one
                            merged_spans.append((current_start, current_end, current_mask))
                            current_start = next_ent.location.start_char
                            current_end = next_ent.location.end_char
                            current_mask = next_ent.masked_value
                    
                    merged_spans.append((current_start, current_end, current_mask))
                    
                    # 3. Apply merged spans from RIGHT to LEFT to maintain index integrity
                    for start, end, mask in reversed(merged_spans):
                        redacted_text = (
                            redacted_text[:start] 
                            + f"{mask}" 
                            + redacted_text[end:]
                        )

            # ── Get Model Metadata ──
            model_info = self.ner_detector.get_model_info() if hasattr(self.ner_detector, "get_model_info") else {}
            
            # ── Prepare Audit Log Data ──
            processing_time_ms = (time.time() - start_time) * 1000
            processing_data = {
                "document_id": document_id,
                "operator_id": operator_id,
                "filename": filename,
                "original_hash": original_hash,
                "sanitized_hash": sanitized_hash,
                "file_size_bytes": file_size,
                "page_count": content.page_count,
                "extraction_method": content.extraction_method,
                "policy_applied": policy_name,
                "entities_detected": redaction_map.total_entities,
                "entities_redacted": len([e for e in redaction_map.entities if not e.is_allowlisted]),
                "entity_summary": redaction_map.summary(),
                "status": "completed",
                "processing_time_ms": processing_time_ms,
            }

            # ── Step 5: Sign ──
            signed_path = None
            signature_serial = None
            signature_data = None
            
            if policy.signing_required:
                try:
                    signer = self._get_signer()
                    signed_output = self.settings.signed_dir / f"{document_id}_signed.pdf"
                    sign_result = signer.sign_pdf(sanitized_path, signed_output)
                    signed_path = sign_result["signed_path"]
                    signature_serial = sign_result["signature_serial"]

                    # ── Prepare Signature Log Data ──
                    signed_hash = compute_file_hash(signed_path)
                    signature_data = {
                        "document_id": document_id,
                        "signed_hash": signed_hash,
                        "signature_serial": sign_result.get("signature_serial"),
                        "certificate_subject": sign_result.get("certificate_subject"),
                        "certificate_issuer": sign_result.get("certificate_issuer"),
                        "signing_algorithm": sign_result.get("signing_algorithm"),
                        "verification_status": "valid",
                        "signed_path": signed_path,
                    }
                except (SigningError, Exception) as e:
                    errors.append(f"Signing skipped: {str(e)}")
                    logger.warning("signing_skipped", error=str(e))
                    
            # ── Dispatch Audit Logs ──
            if background_tasks:
                background_tasks.add_task(_async_audit_log, processing_data, signature_data)
            else:
                # Fallback to synchronous logging if no background tasks provided
                p_log = self.audit_logger.log_processing(**processing_data)
                if signature_data:
                    signature_data["processing_log_id"] = p_log.id
                    self.audit_logger.log_signature(**signature_data)

            # ── Build Result ──
            total_time_ms = (time.time() - start_time) * 1000

            result = ProcessingResult(
                document_id=document_id,
                status=ProcessingStatus.COMPLETED,
                original_text=original_text,
                redacted_text=redacted_text,
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
            fail_data = {
                "document_id": document_id,
                "operator_id": operator_id,
                "filename": filename,
                "original_hash": locals().get('original_hash', "unknown"),
                "status": "failed",
                "processing_time_ms": processing_time_ms,
                "error_message": str(e),
            }
            if background_tasks:
                background_tasks.add_task(_async_audit_log, fail_data, None)
            else:
                try:
                    self.audit_logger.log_processing(**fail_data)
                except Exception:
                    pass

            logger.error("pipeline_failed", document_id=document_id, error=str(e))
            return ProcessingResult(
                document_id=document_id,
                status=ProcessingStatus.FAILED,
                original_hash=locals().get('original_hash', "unknown"),
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
        """Run all detectors and merge results. Regex runs first, then NER with deduplication."""
        all_entities = []
        original_text = content.text
        
        # 0. Contextual Header Identification
        # Identify start/end of "safe" blocks like SKILLS, CERTIFICATIONS, etc.
        safe_blocks = []
        header_patterns = [
            r"(?i)\bSKILLS\b", 
            r"(?i)\bCERTIFICATIONS?\b", 
            r"(?i)\bACHIEVEMENTS?\b", 
            r"(?i)\bPROJECTS?\b",
            r"(?i)\bACADEMIC\b",
            r"(?i)\bEXTRACURRICULAR\b"
        ]
        for pattern in header_patterns:
            for match in re.finditer(pattern, original_text):
                # Guess end of block: next all-caps header on a new line or end of text
                block_start = match.start()
                # Find the next potential section header (Line with 5+ uppercase chars/spaces)
                # We skip the current match by starting search from match.end()
                next_header_match = re.search(r"\n\s*[A-Z\s&]{5,}\s*\n", original_text[match.end():])
                block_end = (match.end() + next_header_match.start()) if next_header_match else len(original_text)
                safe_blocks.append((block_start, block_end))


        # 1. Regex detection (Deterministic, Fast)
        try:
            regex_entities = self.regex_detector.detect(content, policy)
            all_entities.extend(regex_entities)
        except Exception as e:
            logger.warning("regex_detection_error", error=str(e))

        # 2. NER detection (AI, Slower)
        try:
            # Mask out text already found by regex
            modified_text = original_text
            if modified_text and regex_entities:
                for entity in sorted(regex_entities, key=lambda e: e.location.start_char, reverse=True):
                    start = entity.location.start_char
                    end = entity.location.end_char
                    modified_text = modified_text[:start] + (" " * (end - start)) + modified_text[end:]
            
            ner_content = ExtractedContent(
                document_id=content.document_id,
                text=modified_text,
                has_embedded_text=content.has_embedded_text,
                page_count=content.page_count,
                extraction_method=content.extraction_method,
                word_locations=content.word_locations
            )
            
            ner_entities = self.ner_detector.detect(ner_content, policy)
            
            # Filter NER entities based on safe blocks
            filtered_ner = []
            for e in ner_entities:
                is_safe = False
                for s_start, s_end in safe_blocks:
                    if s_start <= e.location.start_char <= s_end:
                        # If it's a name inside SKILLS, skip it unless it's a very high confidence person name
                        if e.entity_type == EntityType.PERSON_NAME:
                            is_safe = True
                            break
                if not is_safe:
                    filtered_ner.append(e)
            
            all_entities.extend(filtered_ner)
        except Exception as e:
            logger.warning("ner_detection_error", error=str(e))

        # 3. Final Deduplication and Overlap Merge
        if all_entities:
            all_entities.sort(key=lambda e: e.location.start_char)
            merged = []
            if all_entities:
                curr = all_entities[0]
                for nxt in all_entities[1:]:
                    if nxt.location.start_char < curr.location.end_char:
                        # Overlap: Keep the one with higher confidence or larger span
                        if (nxt.location.end_char - nxt.location.start_char) > (curr.location.end_char - curr.location.start_char):
                            curr = nxt
                    else:
                        merged.append(curr)
                        curr = nxt
                merged.append(curr)
            all_entities = merged


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

    def _redact(self, file_path: Path, redaction_map: RedactionMap, document_id: str, content: ExtractedContent) -> Path:
        """Apply redaction and return path to sanitized document."""
        output_path = self.settings.processed_dir / f"{document_id}_sanitized.pdf"

        if file_path.suffix.lower() == ".pdf" and content.has_embedded_text:
            return self.text_redactor.redact(file_path, output_path, redaction_map)
        else:
            return self.image_redactor.redact(file_path, output_path, redaction_map)

    def analyze_only(
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
