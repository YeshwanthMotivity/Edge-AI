"""
SecureDocAI — Regex Detector
===============================
Deterministic pattern-based detection for structured PII:
emails, phone numbers, credit cards (Luhn), SSN, DOB, account numbers.
"""

import re
from typing import Optional

import structlog

from app.services.detection.base import BaseDetector
from app.models.entity import (
    DetectedEntity, EntityType, DetectionMethod,
    MaskingStyle, EntityLocation,
)
from app.models.document import ExtractedContent
from app.models.policy import Policy

logger = structlog.get_logger(__name__)


# ── Regex Patterns ──

PATTERNS = {
    EntityType.EMAIL: re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    ),
    EntityType.PHONE: re.compile(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b"
    ),
    EntityType.CREDIT_CARD: re.compile(
        r"\b(?:\d[ -]*?){13,19}\b"
    ),
    EntityType.SSN: re.compile(
        r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"
    ),
    EntityType.DATE_OF_BIRTH: re.compile(
        r"\b(?:\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|\d{4}[/.-]\d{1,2}[/.-]\d{1,2})\b"
    ),
    EntityType.ACCOUNT_NUMBER: re.compile(
        r"\b\d{8,17}\b"
    ),
}


class RegexDetector(BaseDetector):
    """
    Deterministic regex-based PII detector.

    Uses pattern matching for structured data types:
    - Email addresses
    - Phone numbers (international formats)
    - Credit card numbers (with Luhn validation)
    - Social Security Numbers
    - Dates of birth
    - Account numbers
    """

    def get_supported_entity_types(self) -> list[str]:
        return [et.value for et in PATTERNS.keys()]

    def detect(
        self,
        content: ExtractedContent,
        policy: Policy,
    ) -> list[DetectedEntity]:
        """
        Scan extracted text for regex-matching PII patterns.

        Returns entities that pass confidence threshold and are not allowlisted.
        """
        entities: list[DetectedEntity] = []
        enabled = policy.get_enabled_entities()

        for entity_type, pattern in PATTERNS.items():
            type_key = entity_type.value
            if type_key not in enabled:
                continue

            rule = enabled[type_key]
            if rule.detection_method not in ("regex", "regex_luhn"):
                continue

            matches = pattern.finditer(content.text)
            for match in matches:
                value = match.group().strip()

                # Skip short or clearly invalid matches
                if len(value) < 3:
                    continue

                # Luhn validation for credit cards
                if entity_type == EntityType.CREDIT_CARD:
                    clean = re.sub(r"[\s-]", "", value)
                    if not self._luhn_check(clean):
                        continue
                    confidence = 0.95
                else:
                    confidence = 0.92

                # Create entity
                entity = DetectedEntity(
                    entity_type=entity_type,
                    value=value,
                    confidence=confidence,
                    detection_method=DetectionMethod.REGEX if entity_type != EntityType.CREDIT_CARD else DetectionMethod.REGEX_LUHN,
                    location=EntityLocation(
                        start_char=match.start(),
                        end_char=match.end(),
                        page=0,  # Will be mapped to pages in pipeline
                    ),
                    masking_style=MaskingStyle(rule.masking_style),
                    masked_value=rule.replacement,
                )
                entities.append(entity)

        # Apply confidence threshold and allowlist filtering
        entities = self.filter_by_confidence(entities, policy.entities.get(
            entities[0].entity_type.value, type("", (), {"confidence_threshold": 0.85})
        ).confidence_threshold if entities else 0.85)
        entities = self.filter_allowlisted(entities, policy)

        logger.info(
            "regex_detection_complete",
            document_id=content.document_id,
            entities_found=len(entities),
        )
        return entities

    @staticmethod
    def _luhn_check(number: str) -> bool:
        """
        Validate a number using the Luhn algorithm.
        Used for credit card number verification.
        """
        if not number.isdigit() or len(number) < 13:
            return False

        total = 0
        reverse = number[::-1]
        for i, digit in enumerate(reverse):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0
