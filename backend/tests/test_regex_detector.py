import pytest
from app.models.document import ExtractedContent
from app.models.policy import Policy, EntityRule
from app.services.detection.regex_detector import RegexDetector
from app.models.entity import EntityType


@pytest.fixture
def detector():
    return RegexDetector()


@pytest.fixture
def default_policy():
    """Create a policy with standard regex types enabled."""
    return Policy(
        policy_name="test_policy",
        entities={
            "EMAIL": EntityRule(enabled=True, detection_method="regex", confidence_threshold=0.85),
            "PHONE": EntityRule(enabled=True, detection_method="regex", confidence_threshold=0.85),
            "SSN": EntityRule(enabled=True, detection_method="regex", confidence_threshold=0.85),
            "CREDIT_CARD": EntityRule(enabled=True, detection_method="regex_luhn", confidence_threshold=0.85),
        }
    )


def test_detect_email(detector, default_policy):
    content = ExtractedContent(
        document_id="doc1",
        text="Contact us at support@example.com for help.",
        page_count=1,
        extraction_method="pdf",
        has_embedded_text=True
    )
    entities = detector.detect(content, default_policy)
    
    assert len(entities) == 1
    assert entities[0].entity_type == EntityType.EMAIL
    assert entities[0].value == "support@example.com"


def test_detect_phone(detector, default_policy):
    content = ExtractedContent(
        document_id="doc1",
        text="My number is 555-123-4567.",
        page_count=1,
        extraction_method="pdf",
        has_embedded_text=True
    )
    entities = detector.detect(content, default_policy)
    
    assert len(entities) == 1
    assert entities[0].entity_type == EntityType.PHONE
    assert entities[0].value == "555-123-4567"


def test_detect_ssn(detector, default_policy):
    content = ExtractedContent(
        document_id="doc1",
        text="SSN: 123-45-6789 is sensitive.",
        page_count=1,
        extraction_method="pdf",
        has_embedded_text=True
    )
    entities = detector.detect(content, default_policy)
    
    assert len(entities) == 1
    assert entities[0].entity_type == EntityType.SSN
    assert entities[0].value == "123-45-6789"


def test_luhn_validation(detector, default_policy):
    # Valid Visa number
    valid_cc = "4111111111111111" # Standard test valid VISA
    # Invalid Visa number (same length but fails Luhn)
    invalid_cc = "4111111111111112"
    
    content = ExtractedContent(
        document_id="doc1",
        text=f"Valid CC: {valid_cc}\nInvalid CC: {invalid_cc}",
        page_count=1,
        extraction_method="pdf",
        has_embedded_text=True
    )
    entities = detector.detect(content, default_policy)
    
    cc_entities = [e for e in entities if e.entity_type == EntityType.CREDIT_CARD]
    assert len(cc_entities) == 1
    assert cc_entities[0].value == valid_cc


def test_allowlist_filtering(detector, default_policy):
    default_policy.allowlist.emails = ["support@example.com"]
    
    content = ExtractedContent(
        document_id="doc1",
        text="Contact support@example.com or admin@example.com.",
        page_count=1,
        extraction_method="pdf",
        has_embedded_text=True
    )
    entities = detector.detect(content, default_policy)
    
    assert len(entities) == 1
    assert entities[0].value == "admin@example.com"


def test_empty_content(detector, default_policy):
    content = ExtractedContent(
        document_id="doc1",
        text="No PII here in this document.",
        page_count=1,
        extraction_method="pdf",
        has_embedded_text=True
    )
    entities = detector.detect(content, default_policy)
    
    assert len(entities) == 0
