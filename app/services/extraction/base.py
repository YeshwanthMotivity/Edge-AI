"""
SecureDocAI — Base Extractor
==============================
Abstract interface for document text extraction.
All extractors (PDF text, OCR) must implement this interface.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from app.models.document import ExtractedContent


class BaseExtractor(ABC):
    """
    Abstract base class for document content extraction.

    Implementations:
        - PdfExtractor: Born-digital PDF text extraction (PyMuPDF/pdfplumber)
        - OcrExtractor: Scanned document OCR (Tesseract/PaddleOCR)
    """

    @abstractmethod
    def extract(self, file_path: Path, document_id: str) -> ExtractedContent:
        """
        Extract text and layout information from a document.

        Args:
            file_path: Path to the input document.
            document_id: Unique processing identifier.

        Returns:
            ExtractedContent with text, per-page data, and bounding boxes.

        Raises:
            ExtractionError: If extraction fails.
        """
        ...

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """
        Check if this extractor can handle the given file type.

        Args:
            file_path: Path to the document.

        Returns:
            True if this extractor supports the file format.
        """
        ...

    def _detect_document_type(self, file_path: Path) -> str:
        """Detect whether a PDF has embedded text or is scanned."""
        suffix = file_path.suffix.lower()
        if suffix in (".png", ".jpg", ".jpeg", ".tiff", ".tif"):
            return "image"
        return "pdf"
