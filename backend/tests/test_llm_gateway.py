import pytest
from app.services.llm_gateway import LLMGateway
from app.models.entity import DetectedEntity, EntityType, DetectionMethod, EntityLocation, MaskingStyle, RedactionMap

def test_llm_gateway_reidentification():
    """Verify that the LLM gateway can map masked values back to real values."""
    gateway = LLMGateway()
    document_id = "test-doc-123"
    
    # Create fake entities that the pipeline would have generated
    entities = [
        DetectedEntity(
            entity_type=EntityType.PERSON_NAME,
            value="John Doe",
            confidence=0.99,
            detection_method=DetectionMethod.NER,
            location=EntityLocation(start_char=0, end_char=8, page=0),
            masking_style=MaskingStyle.FULL,
            masked_value="[PERSON_NAME_1]"
        ),
        DetectedEntity(
            entity_type=EntityType.EMAIL,
            value="john@example.com",
            confidence=0.99,
            detection_method=DetectionMethod.REGEX,
            location=EntityLocation(start_char=10, end_char=26, page=0),
            masking_style=MaskingStyle.FULL,
            masked_value="[EMAIL_1]"
        )
    ]
    
    redaction_map = RedactionMap(
        document_id=document_id,
        entities=entities,
        total_entities=len(entities),
        entity_counts={"PERSON_NAME": 1, "EMAIL": 1},
        policy_applied="test"
    )
    
    # 1. Register the document with the gateway
    gateway.register_document(document_id, redaction_map)
    
    assert document_id in gateway._active_mappings
    assert gateway._active_mappings[document_id]["[PERSON_NAME_1]"] == "John Doe"
    assert gateway._active_mappings[document_id]["[EMAIL_1]"] == "john@example.com"
    
    # 2. Simulate an LLM Response that uses the masked values
    mock_llm_response = (
        "The document is about [PERSON_NAME_1] whose email address is [EMAIL_1]. "
        "Also, [PERSON_NAME_1] is very important."
    )
    
    # 3. Re-identification
    reidentified = gateway.re_identify(document_id, mock_llm_response)
    
    # Assertions
    assert "John Doe" in reidentified
    assert "john@example.com" in reidentified
    assert "[PERSON_NAME_1]" not in reidentified
    assert "[EMAIL_1]" not in reidentified
    
    expected_response = (
        "The document is about John Doe whose email address is john@example.com. "
        "Also, John Doe is very important."
    )
    assert reidentified == expected_response
    
def test_mock_query_does_not_leak():
    """Ensure the mock provider builds correctly."""
    gateway = LLMGateway()
    
    prompt = "Summarize this securely."
    text = "The contract belongs to [REDACTED_PERSON]."
    
    resp = gateway.query("doc1", text, prompt, provider="mock")
    
    assert "SecureDocAI" in resp
    assert "Summarize this securely" in resp
    assert "REDACTED_PERSON" in resp
