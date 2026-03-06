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
                images, pdf_scales = self._pdf_to_images_with_scale(file_path)
            else:
                img = Image.open(str(file_path))
                images = [img]
                pdf_scales = [{"scale_x": 1.0, "scale_y": 1.0} for _ in range(1)]

            pages = []
            full_text_parts = []
            
            # Extract text per page block, flattening words into lists
            word_locations = []
            
            # Keep a persistent running total of characters
            total_char_offset = 0

            for page_num, img in enumerate(images):
                scale_x = pdf_scales[page_num]["scale_x"]
                scale_y = pdf_scales[page_num]["scale_y"]
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
                        # Normalize 300 DPI image coordinates to 72 DPI PDF coordinates
                        x0 = ocr_data["left"][i] * scale_x
                        y0 = ocr_data["top"][i] * scale_y
                        x1 = (ocr_data["left"][i] + ocr_data["width"][i]) * scale_x
                        y1 = (ocr_data["top"][i] + ocr_data["height"][i]) * scale_y
                        
                        word_info = {
                            "text": word,
                            "bbox": {"x0": x0, "y0": y0, "x1": x1, "y1": y1},
                            "confidence": conf / 100.0,
                            "block": ocr_data["block_num"][i],
                            "line": ocr_data["line_num"][i],
                        }
                        words.append(word_info)
                        
                        # Store global word locations for NER _resolve_bounding_box mapping
                        # We calculate start_char and end_char sequentially
                        current_char_idx = total_char_offset + len(" ".join(text_parts)) + (1 if text_parts else 0)

                        word_locations.append({
                            "word": word,
                            "start_char": current_char_idx,
                            "end_char": current_char_idx + len(word),
                            "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                            "page": page_num
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
                
                # Advance total char offset for the next page block (+2 for \n\n)
                total_char_offset += len(page_text) + 2

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
                # Provide word locations so NER can map substrings to bounding boxes
                word_locations=word_locations,
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

    def _pdf_to_images_with_scale(self, file_path: Path) -> tuple[list, list]:
        """Convert PDF pages to PIL Images for OCR, returning scale factors."""
        try:
            import fitz  # PyMuPDF
            from PIL import Image
            import io

            doc = fitz.open(str(file_path))
            images = []
            scales = []

            for page in doc:
                # Render page at 300 DPI for good OCR quality
                pix = page.get_pixmap(dpi=300)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
                
                # Calculate normalization scale
                # page.rect represents the 72 DPI coordinate system
                scale_x = page.rect.width / img.width
                scale_y = page.rect.height / img.height
                scales.append({"scale_x": scale_x, "scale_y": scale_y})

            doc.close()
            return images, scales

        except Exception as e:
            raise ExtractionError(
                message=f"PDF to image conversion failed: {str(e)}",
                document_id="",
            )
