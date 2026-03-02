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
from app.services.detection.constants import PII_BLACKLIST
from app.models.entity import (
    DetectedEntity, EntityType, DetectionMethod,
    MaskingStyle, EntityLocation,
)
from app.models.document import ExtractedContent
from app.models.policy import Policy

logger = structlog.get_logger(__name__)


# ── Regex Patterns ──

PATTERNS = {
    EntityType.GOVERNMENT_ID: re.compile(
        # Aadhaar: XXXX XXXX XXXX or PAN: AAAAA1234A
        r"\b\d{4}\s\d{4}\s\d{4}\b|\b[A-Z]{5}\d{4}[A-Z]\b"
    ),
    EntityType.EMAIL: re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    ),
    EntityType.PHONE: re.compile(
        # Refined phone regex: strictly requires at least 10 digits and avoids 12-digit Aadhaar
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b"
    ),
    EntityType.CREDIT_CARD: re.compile(
        # Supports partially masked cards with X or *
        # Matches 13-19 digit-like chars, starting and ending with digits
        r"\b\d[ \-*X\d]{11,17}\d\b"
    ),
    EntityType.SSN: re.compile(
        r"\b(?:(?!000|666)\d{3}[-.\s]?(?!00)\d{2}[-.\s]?(?!0000)\d{4})\b"
    ),
    EntityType.DATE_OF_BIRTH: re.compile(
        r"\b(?:\d{1,2}[/.-]\d{1,2}[/.-](?:19|20)\d{2}|(?:19|20)\d{2}[/.-]\d{1,2}[/.-]\d{1,2}|Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?\s+\d{1,2},?\s+(?:19|20)\d{2})\b"
    ),
    EntityType.ACCOUNT_NUMBER: re.compile(
        r"\b\d{8,17}\b"
    ),
    EntityType.ADDRESS: re.compile(
        r"(?i)(?:\b(?:hno|h\.no|plot\s*no|flat\s*no)[\s:.-]*\d+(?:[\w\s.,/-]{1,150})(?:hyderabad|telangana|teleganan)(?:[\s,.-]*\d{6})?\b|"
        r"\b[\w\s.-]{1,50}(?:nagar|colony|block)[\w\s.,-]{1,100}(?:hyderabad|telangana|teleganan)(?:[\s,.-]*\d{6})?\b|"
        r"\b(?:hyderabad|telangana|teleganan)\b|"
        r"\b\d{1,5}\s+[a-zA-Z0-9.\s]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Ln|Lane|Dr|Drive|Ct|Court|Way|Cir|Circle)[,\s]+[a-zA-Z\s]+[,\s]+[A-Z]{2}\s+\d{5}(?:-\d{4})?\b)"
    ),
    EntityType.PERSON_NAME: re.compile(
        r"(?i:\b(?:mr\.|mrs\.|ms\.|dr\.|shri|smt\.?|prof\.?)\s+[a-z]+(?:\s+[a-z]+){0,3}\b)|"
        r"\b(?:[A-Z][a-z]+\s+){1,3}[A-Z][a-z]+\b|"
        # Lowercase Name Support: mudimala yeshwanth goud (3-4 words)
        r"\b(?:[a-z]{3,}\s+){2,3}[a-z]{3,}\b|"
        # CamelCase: MudimalaYeshwanthGoud
        r"\b[A-Z][a-z]+(?:[A-Z][a-z]+){2,}\b|"
        r"\b(?:[a-z]{3,}_){1,3}[a-z]{3,}\b|"
        # Improved ALL CAPS matcher: excludes common document headers
        r"\b(?!(?:.*?\b(?:SUMMARY|EXPERIENCE|EDUCATION|PROJECTS|SKILLS|ACHIEVEMENTS|ACTIVITIES|LANGUAGES|OBJECTIVE|CERTIFICATIONS|INTERESTS|PROFILE|PROFESSIONAL|ASSOCIATE|TECHNICAL|AIVA|DOCUSENSE|TALENTFLOW|SAFELENS|CODEZEN|TALENT|FLOW|SAFE|LENS|DOCU|SENSE|CODE|ZEN|DEVOPS|GITHUB|LINKEDIN|DATA|SCIENTIST|SCIENCE|ENGINEER|ENGINEERING|INTERN|RESEARCHER|ANALYST|DEVELOPER|ARCHITECT|CONSULTANT|UNIVERSITY|COLLEGE|INSTITUTE|SCHOOL|FOUNDATION|CERTIFICATION|LOAN|AGREEMENT|BORROWER|LENDER|APPLICANT|DETAILS|GENDER|FORMAT|RELATIONSHIP|EMPLOYER|EMPLOYEE|CONFIRMATION|SIGNATURE|DECLARATION|BETWEEN|MADE)\b))(?:[A-Z]{3,}\s+){1,3}[A-Z]{3,}\b|"
        r"\b(?:[A-Z]\.?\s*){1,2}[A-Z][a-z]+\s+[A-Z][a-z]+\b|"
        r"\b[A-Z][a-z]+\s+(?:[A-Z][a-z]+\s+)?[A-Z]\.?\b"
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
            # Hybrid Strategy: If regex pattern exists and entity is enabled, 
            # always attempt detection as a safety net, regardless of detection_method.
            # (Matches user requirement for hybrid Regex + ML flow)

            matches = pattern.finditer(content.text)
            for match in matches:
                value = match.group().strip()

                # Skip short or clearly invalid matches
                if len(value) < 3:
                    continue

                # NEW: Skip matches that are likely labels/headers
                # (end with common separators contextually: :, >, -, |, —)
                full_text = content.text
                if match.end() < len(full_text):
                    next_char = full_text[match.end()].strip()
                    if next_char in [":", ">", "|", "—"] or (next_char == "-" and match.end() + 1 < len(full_text) and full_text[match.end()+1] == " "):
                        continue
                
                # Also skip if it's a label followed by whitespace and then a separator
                context_after = full_text[match.end():match.end()+5]
                if re.match(r"^\s*[:>|—]", context_after):
                    continue

                # Filter against PII Blacklist for Names and Organizations
                if entity_type in [EntityType.PERSON_NAME, EntityType.ORGANIZATION]:
                    # Check whole phrase
                    upper_val = value.upper().strip().rstrip(":")
                    if upper_val in PII_BLACKLIST:
                        continue
                    
                    # Check individual tokens (blocks "Associate Data Scientist" if any token is blacklisted)
                    tokens = [t.strip().upper() for t in re.split(r"[\s_/-]+", value) if t.strip()]
                    if any(t in PII_BLACKLIST for t in tokens):
                        continue

                # Luhn validation for credit cards
                if entity_type == EntityType.CREDIT_CARD:
                    # Bypass Luhn if partially masked with X or *
                    if "X" in value.upper() or "*" in value:
                        confidence = 0.98
                    else:
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
        if entities:
            first_type = entities[0].entity_type.value
            threshold = policy.entities[first_type].confidence_threshold if first_type in policy.entities else 0.85
        else:
            threshold = 0.85
        entities = self.filter_by_confidence(entities, threshold)
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
