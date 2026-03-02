"""
SecureDocAI — PDF Text Extractor
==================================
Extracts text and bounding box coordinates from born-digital PDFs
using PyMuPDF (fitz). Falls back to OCR if no embedded text is found.
"""

from pathlib import Path

import structlog

from app.services.extraction.base import BaseExtractor
from app.models.document import ExtractedContent
from app.core.exceptions import ExtractionError

logger = structlog.get_logger(__name__)


class PdfExtractor(BaseExtractor):
    """
    Extract text from born-digital PDFs using PyMuPDF.

    Extracts:
        - Full text content per page
        - Word-level bounding boxes (for redaction mapping)
        - Document metadata (author, creation date, etc.)
    """

    SUPPORTED_EXTENSIONS = {".pdf"}

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def extract(self, file_path: Path, document_id: str) -> ExtractedContent:
        """
        Extract text and coordinates from a PDF.

        Steps:
            1. Open PDF with PyMuPDF
            2. Extract text blocks with coordinates per page
            3. Check if PDF has embedded text (or needs OCR fallback)
            4. Return normalized ExtractedContent

        Raises:
            ExtractionError: If PDF cannot be opened or parsed.
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(file_path))
            pages = []
            full_text_parts = []
            has_text = False

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")

                if text.strip():
                    has_text = True

                # Extract words with bounding boxes: (x0, y0, x1, y1, "word", block, line, word_idx)
                words = page.get_text("words")
                word_data = [
                    {
                        "text": w[4],
                        "bbox": {"x0": w[0], "y0": w[1], "x1": w[2], "y1": w[3]},
                        "block": w[5],
                        "line": w[6],
                    }
                    for w in words
                ]

                pages.append({
                    "page_number": page_num,
                    "text": text,
                    "words": word_data,
                    "width": page.rect.width,
                    "height": page.rect.height,
                })
                full_text_parts.append(text)

            # Extract document metadata
            metadata = doc.metadata or {}
            page_count = len(doc)
            doc.close()

            logger.info(
                "pdf_extracted",
                document_id=document_id,
                pages=page_count,
                has_text=has_text,
            )

            return ExtractedContent(
                document_id=document_id,
                text="\n\n".join(full_text_parts),
                pages=pages,
                extraction_method="pdf_text" if has_text else "pdf_no_text",
                page_count=page_count,
                has_embedded_text=has_text,
                metadata=metadata,
            )

        except ImportError:
            raise ExtractionError(
                message="PyMuPDF (fitz) is not installed",
                document_id=document_id,
            )
        except Exception as e:
            raise ExtractionError(
                message=f"PDF extraction failed: {str(e)}",
                document_id=document_id,
            )
