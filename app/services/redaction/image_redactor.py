"""
SecureDocAI — Image Redactor (Stub)
=====================================
Redacts sensitive regions in images by applying opaque blur/mask.
Used for scanned PDFs where text is embedded in image layers.

Phase 2 Implementation.
"""

from pathlib import Path

import structlog

from app.services.redaction.base import BaseRedactor
from app.models.entity import RedactionMap
from app.core.exceptions import RedactionError

logger = structlog.get_logger(__name__)


class ImageRedactor(BaseRedactor):
    """
    Image-based redactor for scanned documents.

    Applies opaque masking to sensitive regions detected by OCR + NER.

    Phase 2 Implementation:
        - Use Pillow to draw opaque rectangles over bounding boxes
        - Support blur mode (Gaussian blur) or solid fill mode
        - Reconstruct redacted images back into PDF
    """

    def redact(
        self,
        input_path: Path,
        output_path: Path,
        redaction_map: RedactionMap,
    ) -> Path:
        """
        Apply image-based redaction to scanned documents.

        TODO (Phase 2):
            1. Load image / convert PDF page to image
            2. Draw opaque rectangles over entity bounding boxes
            3. Save redacted image / rebuild PDF
        """
        logger.warning(
            "image_redaction_stub",
            document_id=redaction_map.document_id,
            message="Image redaction not yet implemented",
        )
        # For now, copy original as placeholder
        import shutil
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(input_path), str(output_path))
        return output_path

    def verify_redaction(self, output_path: Path, redaction_map: RedactionMap) -> bool:
        """Verify image redaction (Phase 2)."""
        logger.warning("image_redaction_verify_stub", message="Not yet implemented")
        return True
