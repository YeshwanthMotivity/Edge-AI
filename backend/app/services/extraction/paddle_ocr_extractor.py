"""
SecureDocAI — PaddleOCR Dual-Engine Adapter
=============================================
An alternative OCR extractor utilizing PaddleOCR for enhanced accuracy
on noisy scans and complex documents.

This serves as a drop-in replacement for OcrExtractor but requires
the `paddlepaddle` and `paddleocr` libraries.
"""

from pathlib import Path
import structlog

from app.services.extraction.base import BaseExtractor
from app.models.document import ExtractedContent
from app.core.exceptions import ExtractionError

logger = structlog.get_logger(__name__)


class PaddleOcrExtractor(BaseExtractor):
    """
    Advanced OCR using PaddleOCR.
    Vastly improves detection on complex/noisy scans and automatically
    handles orientation normalization.
    """

    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".pdf"}

    def __init__(self, lang: str = "en", use_gpu: bool = False):
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=use_gpu)
            self._is_ready = True
        except ImportError:
            self.ocr = None
            self._is_ready = False
            logger.warning("paddleocr_not_installed", message="PaddleOCR dependencies missing")

    def can_handle(self, file_path: Path) -> bool:
        return self._is_ready and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def extract(self, file_path: Path, document_id: str) -> ExtractedContent:
        """
        Extract text via PaddleOCR.

        Applies the same coordinate normalization logic (pdf_width / image_width)
        as the Tesseract engine to ensure mapped PyMuPDF coordinates align.
        """
        if not self._is_ready:
            raise ExtractionError(
                message="PaddleOCR is not installed. Run `pip install paddlepaddle paddleocr`.",
                document_id=document_id,
            )

        try:
            from PIL import Image

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
            word_locations = []

            for page_num, img in enumerate(images):
                import numpy as np
                scale_x = pdf_scales[page_num]["scale_x"]
                scale_y = pdf_scales[page_num]["scale_y"]

                # PaddleOCR expects numpy arrays
                img_array = np.array(img.convert('RGB'))
                
                # Run PaddleOCR prediction
                result = self.ocr.ocr(img_array, cls=True)

                words = []
                text_parts = []
                
                if result and result[0]:
                    for line in result[0]:
                        # line is formatted as [[box], (text, confidence)]
                        box = line[0]
                        text, conf = line[1]
                        word = text.strip()
                        
                        if word and conf > 0:
                            # Box is [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                            x0 = min([p[0] for p in box]) * scale_x
                            y0 = min([p[1] for p in box]) * scale_y
                            x1 = max([p[0] for p in box]) * scale_x
                            y1 = max([p[1] for p in box]) * scale_y

                            word_info = {
                                "text": word,
                                "bbox": {"x0": x0, "y0": y0, "x1": x1, "y1": y1},
                                "confidence": float(conf),
                            }
                            words.append(word_info)
                            
                            current_char_idx = len(" ".join(text_parts)) + (1 if text_parts else 0)
                            if page_num > 0 and not text_parts:
                                current_char_idx = len("\n\n".join(full_text_parts)) + 2

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

            logger.info("paddleocr_extracted", document_id=document_id, pages=len(pages))

            return ExtractedContent(
                document_id=document_id,
                text="\n\n".join(full_text_parts),
                pages=pages,
                extraction_method="paddleocr",
                page_count=len(pages),
                has_embedded_text=False,
                metadata={},
                word_locations=word_locations,
            )

        except Exception as e:
            raise ExtractionError(message=f"PaddleOCR extraction failed: {str(e)}", document_id=document_id)

    def _pdf_to_images_with_scale(self, file_path: Path) -> tuple[list, list]:
        """Convert PDF pages to PIL Images, returning scale factors."""
        try:
            import fitz
            from PIL import Image
            import io

            doc = fitz.open(str(file_path))
            images = []
            scales = []

            for page in doc:
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                images.append(img)
                scales.append({"scale_x": page.rect.width / img.width, "scale_y": page.rect.height / img.height})

            doc.close()
            return images, scales
        except Exception as e:
            raise ExtractionError(message=f"PDF to image conversion failed: {str(e)}", document_id="")
