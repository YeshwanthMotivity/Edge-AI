"""
SecureDocAI — Base Detector
==============================
Abstract interface for sensitive data detection.
All detectors (regex, NER, layout) must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.entity import DetectedEntity, RedactionMap
from app.models.document import ExtractedContent
from app.models.policy import Policy


class BaseDetector(ABC):
    """
    Abstract base class for sensitive data detection.

    Implementations:
        - RegexDetector: Pattern-based detection (emails, phones, CC, SSN)
        - NerDetector: AI-based Named Entity Recognition (names, addresses, orgs)
    """

    @abstractmethod
    def detect(
        self,
        content: ExtractedContent,
        policy: Policy,
    ) -> list[DetectedEntity]:
        """
        Detect sensitive entities in extracted content.

        Args:
            content: Extracted text and layout from a document.
            policy: Active detection policy with thresholds and rules.

        Returns:
            List of detected entities with locations and confidence scores.

        Raises:
            DetectionError: If detection processing fails.
        """
        ...

    @abstractmethod
    def get_supported_entity_types(self) -> list[str]:
        """Return entity types this detector can identify."""
        ...

    def filter_by_confidence(
        self,
        entities: list[DetectedEntity],
        threshold: float = 0.85,
    ) -> list[DetectedEntity]:
        """Filter entities below the confidence threshold."""
        return [e for e in entities if e.confidence >= threshold]

    def filter_allowlisted(
        self,
        entities: list[DetectedEntity],
        policy: Policy,
    ) -> list[DetectedEntity]:
        """Remove entities that match allowlist patterns."""
        result = []
        for entity in entities:
            if self._is_allowlisted(entity, policy):
                entity.is_allowlisted = True
            else:
                result.append(entity)
        return result

    def _is_allowlisted(self, entity: DetectedEntity, policy: Policy) -> bool:
        """Check if an entity value matches any allowlist entry."""
        value_lower = entity.value.lower()

        if entity.entity_type.value == "EMAIL":
            return value_lower in [e.lower() for e in policy.allowlist.emails]
        elif entity.entity_type.value == "PHONE":
            return entity.value in policy.allowlist.phones
        elif entity.entity_type.value in ("PERSON_NAME", "ORGANIZATION"):
            return value_lower in [n.lower() for n in policy.allowlist.names]

        return False
