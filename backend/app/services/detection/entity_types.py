"""
SecureDocAI — Entity Type Definitions
========================================
Centralized entity type metadata: regex patterns, display names, and categories.
"""

from app.models.entity import EntityType


# ── Entity Metadata Registry ──

ENTITY_METADATA = {
    EntityType.EMAIL: {
        "display_name": "Email Address",
        "category": "contact",
        "pii_level": "medium",
        "regex_detectable": True,
    },
    EntityType.PHONE: {
        "display_name": "Phone Number",
        "category": "contact",
        "pii_level": "medium",
        "regex_detectable": True,
    },
    EntityType.CREDIT_CARD: {
        "display_name": "Credit Card Number",
        "category": "financial",
        "pii_level": "critical",
        "regex_detectable": True,
    },
    EntityType.SSN: {
        "display_name": "Social Security Number",
        "category": "government_id",
        "pii_level": "critical",
        "regex_detectable": True,
    },
    EntityType.PERSON_NAME: {
        "display_name": "Person Name",
        "category": "identity",
        "pii_level": "high",
        "regex_detectable": True,
    },
    EntityType.ADDRESS: {
        "display_name": "Physical Address",
        "category": "location",
        "pii_level": "high",
        "regex_detectable": True,
    },
    EntityType.ORGANIZATION: {
        "display_name": "Organization Name",
        "category": "identity",
        "pii_level": "medium",
        "regex_detectable": False,
    },
    EntityType.DATE_OF_BIRTH: {
        "display_name": "Date of Birth",
        "category": "identity",
        "pii_level": "high",
        "regex_detectable": True,
    },
    EntityType.ACCOUNT_NUMBER: {
        "display_name": "Account Number",
        "category": "financial",
        "pii_level": "critical",
        "regex_detectable": True,
    },
    EntityType.GOVERNMENT_ID: {
        "display_name": "Government ID",
        "category": "government_id",
        "pii_level": "critical",
        "regex_detectable": True,
    },
}


def get_regex_detectable_types() -> list[EntityType]:
    """Return entity types that can be detected via regex."""
    return [
        et for et, meta in ENTITY_METADATA.items()
        if meta["regex_detectable"]
    ]


def get_ner_detectable_types() -> list[EntityType]:
    """Return entity types that require NER model detection."""
    return [
        et for et, meta in ENTITY_METADATA.items()
        if not meta["regex_detectable"]
    ]


def get_critical_types() -> list[EntityType]:
    """Return entity types classified as critical PII."""
    return [
        et for et, meta in ENTITY_METADATA.items()
        if meta["pii_level"] == "critical"
    ]
