"""
SecureDocAI — Base Redactor
==============================
Abstract interface for document redaction.
All redactors (text, image) must implement this interface.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from app.models.entity import RedactionMap


class BaseRedactor(ABC):
    """
    Abstract base class for document redaction.

    Implements TRUE redaction — removes underlying data, not just visual overlay.

    Implementations:
        - TextRedactor: PDF text redaction (PyMuPDF)
        - ImageRedactor: Image region blur/mask (Pillow)
    """

    @abstractmethod
    def redact(
        self,
        input_path: Path,
        output_path: Path,
        redaction_map: RedactionMap,
    ) -> Path:
        """
        Apply redactions to a document and produce a sanitized copy.

        Args:
            input_path: Path to the original document.
            output_path: Path for the sanitized output.
            redaction_map: Map of all entities to redact with their locations.

        Returns:
            Path to the sanitized document.

        Raises:
            RedactionError: If redaction fails.
        """
        ...

    @abstractmethod
    def verify_redaction(self, output_path: Path, redaction_map: RedactionMap) -> bool:
        """
        Verify that redacted content cannot be recovered.

        Args:
            output_path: Path to the redacted document.
            redaction_map: Original redaction map.

        Returns:
            True if redaction is verified (data unrecoverable), False otherwise.
        """
        ...
