"""
SecureDocAI — OCR Extractor
==============================
Extracts text from scanned PDFs and images using Tesseract OCR.
Produces word-level bounding boxes for redaction mapping.
"""

from pathlib import Path

import structlog

from app.services.extraction.base import BaseExtractor
from app.models.document import ExtractedContent
from app.core.exceptions import ExtractionError

logger = structlog.get_logger(__name__)


class OcrExtractor(BaseExtractor):
    """
    Extract text from scanned documents and images using OCR.

    Supports:
        - Scanned PDFs (converted to images first)
        - Direct images: PNG, JPG, JPEG, TIFF

    Uses Tesseract OCR with word-level bounding box output.
    """

    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".pdf"}

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def extract(self, file_path: Path, document_id: str) -> ExtractedContent:
        """
        Extract text via OCR from scanned documents or images.

        Steps:
            1. If PDF → convert pages to images
            2. Run Tesseract OCR on each image
            3. Extract word-level bounding boxes
            4. Return normalized ExtractedContent

        Raises:
            ExtractionError: If OCR processing fails.
        """
        try:
            from PIL import Image
            import pytesseract

            suffix = file_path.suffix.lower()
            images = []

            if suffix == ".pdf":
                images = self._pdf_to_images(file_path)
            else:
                images = [Image.open(str(file_path))]

            pages = []
            full_text_parts = []

            for page_num, img in enumerate(images):
                # Get detailed OCR data with bounding boxes
                ocr_data = pytesseract.image_to_data(
                    img, output_type=pytesseract.Output.DICT
                )

                # Build word list with bounding boxes
                words = []
                text_parts = []
                for i in range(len(ocr_data["text"])):
                    word = ocr_data["text"][i].strip()
                    conf = int(ocr_data["conf"][i])
                    if word and conf > 0:
                        words.append({
                            "text": word,
                            "bbox": {
                                "x0": ocr_data["left"][i],
                                "y0": ocr_data["top"][i],
                                "x1": ocr_data["left"][i] + ocr_data["width"][i],
                                "y1": ocr_data["top"][i] + ocr_data["height"][i],
                            },
                            "confidence": conf / 100.0,
                            "block": ocr_data["block_num"][i],
                            "line": ocr_data["line_num"][i],
                        })
                        text_parts.append(word)

                page_text = " ".join(text_parts)
                pages.append({
                    "page_number": page_num,
                    "text": page_text,
                    "words": words,
                    "width": img.width,
                    "height": img.height,
                })
                full_text_parts.append(page_text)

            logger.info(
                "ocr_extracted",
                document_id=document_id,
                pages=len(pages),
                total_words=sum(len(p["words"]) for p in pages),
            )

            return ExtractedContent(
                document_id=document_id,
                text="\n\n".join(full_text_parts),
                pages=pages,
                extraction_method="ocr",
                page_count=len(pages),
                has_embedded_text=False,
                metadata={},
            )

        except ImportError as e:
            raise ExtractionError(
                message=f"OCR dependency not installed: {str(e)} (try: pip install pytesseract Pillow)",
                document_id=document_id,
            )
        except pytesseract.TesseractNotFoundError:
            raise ExtractionError(
                message="Tesseract OCR engine is not installed or not in PATH. Please install Tesseract (https://github.com/tesseract-ocr/tesseract) to process scanned documents.",
                document_id=document_id,
            )
        except Exception as e:
            raise ExtractionError(
                message=f"OCR extraction failed: {str(e)}",
                document_id=document_id,
            )

    def _pdf_to_images(self, file_path: Path) -> list:
        """Convert PDF pages to PIL Images for OCR processing."""
        try:
            import fitz  # PyMuPDF
            from PIL import Image
            import io

            doc = fitz.open(str(file_path))
            images = []

            for page in doc:
                # Render page at 300 DPI for good OCR quality
                pix = page.get_pixmap(dpi=300)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)

            doc.close()
            return images

        except Exception as e:
            raise ExtractionError(
                message=f"PDF to image conversion failed: {str(e)}",
                document_id="",
            )
