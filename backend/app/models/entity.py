"""
SecureDocAI — Entity Models
=============================
Pydantic models for detected entities, locations, and redaction maps.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Supported sensitive entity types for detection."""
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    CREDIT_CARD = "CREDIT_CARD"
    SSN = "SSN"
    PERSON_NAME = "PERSON_NAME"
    ADDRESS = "ADDRESS"
    ORGANIZATION = "ORGANIZATION"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    ACCOUNT_NUMBER = "ACCOUNT_NUMBER"
    GOVERNMENT_ID = "GOVERNMENT_ID"
    LINKEDIN = "LINKEDIN"
    URL = "URL"


class DetectionMethod(str, Enum):
    """How an entity was detected."""
    REGEX = "regex"
    REGEX_LUHN = "regex_luhn"
    NER = "ner"
    LAYOUT = "layout"
    HYBRID = "hybrid"


class MaskingStyle(str, Enum):
    """How to mask a detected entity."""
    FULL = "full"           # Complete replacement: [REDACTED]
    PARTIAL = "partial"     # Preserve last N chars: XXXX-1234
    TOKENIZE = "tokenize"   # Reversible token (future use)


class BoundingBox(BaseModel):
    """Location of an entity on a document page (in PDF points)."""
    x0: float = Field(..., description="Left edge (points from left)")
    y0: float = Field(..., description="Top edge (points from top)")
    x1: float = Field(..., description="Right edge")
    y1: float = Field(..., description="Bottom edge")
    page: int = Field(..., description="0-indexed page number")


class EntityLocation(BaseModel):
    """Precise location of a detected entity within the document."""
    start_char: int = Field(..., description="Start character offset in extracted text")
    end_char: int = Field(..., description="End character offset in extracted text")
    bounding_box: Optional[BoundingBox] = Field(default=None, description="Visual location on page")
    page: int = Field(default=0, description="Page number (0-indexed)")


class DetectedEntity(BaseModel):
    """A single detected sensitive entity."""
    entity_type: EntityType = Field(..., description="Type of sensitive data")
    value: str = Field(..., description="The detected text (will be cleared after redaction)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    detection_method: DetectionMethod = Field(..., description="How it was detected")
    location: EntityLocation = Field(..., description="Where in the document")
    masked_value: Optional[str] = Field(default=None, description="The replacement text after masking")
    masking_style: MaskingStyle = Field(default=MaskingStyle.FULL)
    is_allowlisted: bool = Field(default=False, description="Whether this entity is in the allowlist")


class RedactionMap(BaseModel):
    """Complete map of all entities to redact in a document."""
    document_id: str = Field(..., description="Processing ID")
    entities: list[DetectedEntity] = Field(default_factory=list)
    total_entities: int = Field(default=0)
    entity_counts: dict[str, int] = Field(default_factory=dict, description="Count per entity type")
    policy_applied: str = Field(default="default_policy")

    def get_entities_by_type(self, entity_type: EntityType) -> list[DetectedEntity]:
        """Filter entities by type."""
        return [e for e in self.entities if e.entity_type == entity_type]

    def get_entities_by_page(self, page: int) -> list[DetectedEntity]:
        """Filter entities by page number."""
        return [e for e in self.entities if e.location.page == page]

    def summary(self) -> dict[str, int]:
        """Generate a summary count per entity type (no raw PII exposed)."""
        counts: dict[str, int] = {}
        for entity in self.entities:
            key = entity.entity_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts
