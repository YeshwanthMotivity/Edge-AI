"""
SecureDocAI — Text Redactor
===============================
True PDF text redaction using PyMuPDF (fitz).
Removes underlying text data and overlays opaque masking boxes.
Ensures data CANNOT be recovered via copy/paste or text extraction.
"""

from pathlib import Path

import structlog

from app.services.redaction.base import BaseRedactor
from app.models.entity import RedactionMap, BoundingBox
from app.core.exceptions import RedactionError

logger = structlog.get_logger(__name__)


class TextRedactor(BaseRedactor):
    """
    PDF text redactor using PyMuPDF.

    Performs TRUE redaction:
        1. Identifies text spans matching detected entities
        2. Applies redaction annotations (marks for removal)
        3. Executes redaction (permanently removes underlying text)
        4. Overlays opaque boxes with optional labels

    The original text is DESTROYED — not hidden behind a visual overlay.
    """

    def redact(
        self,
        input_path: Path,
        output_path: Path,
        redaction_map: RedactionMap,
    ) -> Path:
        """
        Apply true redaction to a PDF document.

        Steps:
            1. Open source PDF
            2. For each entity, search text and add redaction annotations
            3. Apply redactions (permanently removes text)
            4. Save sanitized copy

        Raises:
            RedactionError: If redaction fails.
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(input_path))
            redaction_count = 0

            for page_num in range(len(doc)):
                page = doc[page_num]
                page_entities = redaction_map.get_entities_by_page(page_num)

                for entity in page_entities:
                    if entity.is_allowlisted:
                        continue

                    # Search for the entity text on this page
                    text_instances = page.search_for(entity.value)

                    for inst in text_instances:
                        # Add redaction annotation
                        annot = page.add_redact_annot(
                            inst,
                            text=entity.masked_value or "[REDACTED]",
                            fontsize=8,
                            fill=(0, 0, 0),       # Black fill
                            text_color=(1, 1, 1),  # White text on black box
                        )
                        redaction_count += 1

                # Apply all redactions on this page (permanently removes text)
                page.apply_redactions()

            # Save sanitized document
            output_path.parent.mkdir(parents=True, exist_ok=True)
            doc.save(str(output_path), garbage=4, deflate=True)
            doc.close()

            logger.info(
                "text_redaction_complete",
                document_id=redaction_map.document_id,
                redactions_applied=redaction_count,
                output=str(output_path),
            )
            return output_path

        except ImportError:
            raise RedactionError(
                message="PyMuPDF (fitz) is not installed",
                document_id=redaction_map.document_id,
            )
        except Exception as e:
            raise RedactionError(
                message=f"Text redaction failed: {str(e)}",
                document_id=redaction_map.document_id,
            )

    def verify_redaction(self, output_path: Path, redaction_map: RedactionMap) -> bool:
        """
        Verify that redacted text cannot be extracted from the output PDF.

        Checks:
            1. Extract all text from the redacted PDF
            2. Ensure none of the original entity values appear
            3. Return False if any original value is found (redaction failed)
        """
        try:
            import fitz

            doc = fitz.open(str(output_path))
            full_text = ""
            for page in doc:
                full_text += page.get_text("text")
            doc.close()

            # Check that no original entity values remain in the text
            for entity in redaction_map.entities:
                if entity.is_allowlisted:
                    continue
                if entity.value in full_text:
                    logger.error(
                        "redaction_verification_failed",
                        document_id=redaction_map.document_id,
                        entity_type=entity.entity_type.value,
                        message="Original entity value found in redacted PDF",
                    )
                    return False

            logger.info(
                "redaction_verified",
                document_id=redaction_map.document_id,
            )
            return True

        except Exception as e:
            logger.error("redaction_verification_error", error=str(e))
            return False
