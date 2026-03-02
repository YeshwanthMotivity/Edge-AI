"""
SecureDocAI — Image Redactor
===============================
Redacts sensitive regions in images by applying opaque blur/mask.
Used for scanned PDFs where text is embedded in image layers as well as native images.

Phase 3 Implementation.
"""

from pathlib import Path
import shutil

import structlog

from app.services.redaction.base import BaseRedactor
from app.models.entity import RedactionMap
from app.core.exceptions import RedactionError

logger = structlog.get_logger(__name__)


class ImageRedactor(BaseRedactor):
    """
    Image-based redactor for scanned documents.

    Applies opaque masking to sensitive regions detected by OCR + NER.

    Features:
        - Uses Pillow to draw opaque rectangles over bounding boxes
        - Supports native image formats (PNG, JPG, TIFF)
        - Reconstructs PDF pages if input is a Scanned PDF
    """

    def redact(
        self,
        input_path: Path,
        output_path: Path,
        redaction_map: RedactionMap,
    ) -> Path:
        """
        Apply image-based redaction to scanned documents and images.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        suffix = input_path.suffix.lower()

        try:
            if suffix == ".pdf":
                # Handle Scanned PDF Redaction
                return self._redact_pdf(input_path, output_path, redaction_map)
            else:
                # Handle Native Image Redaction
                return self._redact_image(input_path, output_path, redaction_map)
        except Exception as e:
            logger.error(
                "image_redaction_failed",
                document_id=redaction_map.document_id,
                error=str(e),
            )
            # Fallback securely: do not return unredacted, raise error
            raise RedactionError(
                message=f"Image redaction failed: {str(e)}",
                document_id=redaction_map.document_id,
            )

    def _redact_pdf(
        self,
        input_path: Path,
        output_path: Path,
        redaction_map: RedactionMap,
    ) -> Path:
        """Render PDF pages to images, redact, and save as a new PDF."""
        import fitz  # PyMuPDF
        from PIL import Image, ImageDraw
        import io

        doc = fitz.open(str(input_path))
        redacted_images = []

        # Optimization: track which pages have entities
        page_entities = {}
        for entity in redaction_map.entities:
            if entity.is_allowlisted:
                continue
            if entity.location and entity.location.bounding_box:
                page_num = entity.location.bounding_box.page
                page_entities.setdefault(page_num, []).append(entity.location.bounding_box)

        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Since OCR was likely run on 300 DPI, we should match it
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data)).convert("RGB")

            # Scale factors: PyMuPDF page.rect is 72 DPI
            scale_x = img.width / page.rect.width
            scale_y = img.height / page.rect.height

            if page_num in page_entities:
                draw = ImageDraw.Draw(img)
                for bbox in page_entities[page_num]:
                    # BoundingBox from OCR is already scaled to 72 DPI layout coordinates
                    # We need to scale it UP to our 300 DPI image pixels
                    x0 = bbox.x0 * scale_x
                    y0 = bbox.y0 * scale_y
                    x1 = bbox.x1 * scale_x
                    y1 = bbox.y1 * scale_y

                    # Draw black rectangle
                    draw.rectangle([x0, y0, x1, y1], fill="black")

            redacted_images.append(img)

        doc.close()

        if not redacted_images:
            shutil.copy2(str(input_path), str(output_path))
            return output_path

        # Save the redacted images as a single PDF using fitz for better standard compliance
        new_doc = fitz.open()
        for img in redacted_images:
            # Convert PIL Image back to bytes for fitz
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            # Create a new page and insert the image
            # PIL images from get_pixmap(dpi=300) are high res, 
            # we should calculate dimensions properly
            page_rect = fitz.Rect(0, 0, img.width * 72/300, img.height * 72/300)
            page = new_doc.new_page(width=page_rect.width, height=page_rect.height)
            page.insert_image(page_rect, stream=img_bytes)
        
        new_doc.save(str(output_path))
        new_doc.close()

        logger.info(
            "scanned_pdf_redacted",
            document_id=redaction_map.document_id,
            pages=len(redacted_images),
            entities=redaction_map.total_entities,
        )

        return output_path

    def _redact_image(
        self,
        input_path: Path,
        output_path: Path,
        redaction_map: RedactionMap,
    ) -> Path:
        """Redact a native image file directly."""
        from PIL import Image, ImageDraw

        img = Image.open(str(input_path)).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Scale factor is 1.0 because OCR extractor sets PDF scales to 1.0 for native images
        for entity in redaction_map.entities:
            if entity.is_allowlisted:
                continue
            if entity.location and entity.location.bounding_box:
                bbox = entity.location.bounding_box
                # Draw black rectangle
                draw.rectangle([bbox.x0, bbox.y0, bbox.x1, bbox.y1], fill="black")

        # Save preserving the original format if possible, or convert to PDF based on convention
        if output_path.suffix.lower() == ".pdf":
            # Use fitz to create a proper PDF from the image
            import io
            import fitz
            new_doc = fitz.open()
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            # Use 100 DPI as convention for native images if not specified
            page_rect = fitz.Rect(0, 0, img.width * 72/100, img.height * 72/100)
            page = new_doc.new_page(width=page_rect.width, height=page_rect.height)
            page.insert_image(page_rect, stream=img_bytes)
            new_doc.save(str(output_path))
            new_doc.close()
        else:
            img.save(str(output_path))

        logger.info(
            "native_image_redacted",
            document_id=redaction_map.document_id,
            entities=redaction_map.total_entities,
        )

        return output_path

    def verify_redaction(self, output_path: Path, redaction_map: RedactionMap) -> bool:
        """Verification stub: confirm the file exists and is reasonably sized."""
        if not output_path.exists() or output_path.stat().st_size == 0:
            return False
        return True
