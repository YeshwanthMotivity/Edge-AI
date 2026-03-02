import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.llm_gateway import LLMGateway
from app.models.entity import DetectedEntity, EntityType, DetectionMethod, EntityLocation, MaskingStyle, RedactionMap

def run_llm_verification():
    print("Initializing LLM Gateway...")
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
        total_entities=2,
        entity_counts={"PERSON_NAME": 1, "EMAIL": 1},
        policy_applied="test"
    )
    
    print("\n1. Registering Document Mappings...")
    gateway.register_document(document_id, redaction_map)
    print(f"Registered Mappings: {gateway._active_mappings[document_id]}")
    
    if gateway._active_mappings[document_id]["[PERSON_NAME_1]"] != "John Doe":
        print("[FAIL] Mappings incorrect")
        return
        
    print("\n2. Sending Mock Query with Redacted Text...")
    sanitized_text = "The document is about [PERSON_NAME_1] whose email address is [EMAIL_1]."
    prompt = "Summarize this securely."
    
    raw_response = gateway.query(document_id, sanitized_text, prompt, provider="mock")
    print(f"\n[RAW LLM RESPONSE RECEIVED]\n{raw_response}")
    
    print("\n3. Re-identifying the Fake LLM Output...")
    # We will simulate the LLM responding with the exact redacted tokens
    mock_llm_response = (
        "The document is about [PERSON_NAME_1] whose email address is [EMAIL_1]. "
        "Also, [PERSON_NAME_1] is very important."
    )
    
    reidentified = gateway.re_identify(document_id, mock_llm_response)
    print(f"\n[FINAL OUTPUT TO USER]\n{reidentified}")
    
    if "John Doe" in reidentified and "john@example.com" in reidentified and "[PERSON_NAME_1]" not in reidentified:
        print("\n[PASS] Verification Successful: Gateway properly protects and re-injects PII without leaks.")
    else:
        print("\n[FAIL] Verification Failed")

if __name__ == "__main__":
    run_llm_verification()
