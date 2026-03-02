"""
SecureDocAI — Custom Exception Hierarchy
==========================================
Structured exceptions for each pipeline stage, enabling
precise error handling and audit logging.
"""


class SecureDocAIError(Exception):
    """Base exception for all SecureDocAI errors."""

    def __init__(self, message: str, document_id: str = "", details: dict = None):
        self.message = message
        self.document_id = document_id
        self.details = details or {}
        super().__init__(self.message)


class AuthorizationError(SecureDocAIError):
    """Raised when user authorization fails."""
    pass


class DocumentValidationError(SecureDocAIError):
    """Raised when an uploaded document fails validation (format, size, integrity)."""
    pass


class ExtractionError(SecureDocAIError):
    """Raised when text/OCR extraction fails."""
    pass


class DetectionError(SecureDocAIError):
    """Raised when PII/sensitive data detection fails."""
    pass


class RedactionError(SecureDocAIError):
    """Raised when document redaction fails."""
    pass


class SigningError(SecureDocAIError):
    """Raised when digital signing fails."""
    pass


class PolicyError(SecureDocAIError):
    """Raised when policy loading or validation fails."""
    pass


class AuditError(SecureDocAIError):
    """Raised when audit logging fails."""
    pass


class KeyManagementError(SecureDocAIError):
    """Raised when key loading, rotation, or access fails."""
    pass
