import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.detection.regex_detector import RegexDetector
from app.models.document import ExtractedContent
from app.models.policy import Policy

def run_performance_test():
    """Verify that regex detection is fast and catches our new targets."""
    print("Initializing Regex Detector...")
    detector = RegexDetector()
    
    # Create dummy policy with SSN and DOB enabled
    policy = Policy(
        policy_name="perf_test", 
        signing_required=False,
        entities={
            "SSN": {'detection_method': 'regex', 'masking_style': 'full', 'replacement': '[SSN]'},
            "DATE_OF_BIRTH": {'detection_method': 'regex', 'masking_style': 'full', 'replacement': '[DOB]'}
        }
    )
    
    # Create test text with 10k characters but lots of SSNs and DOBs
    text = "This is a test document. " * 100
    text += "John Doe's SSN is 123-45-6789 and his DOB is 01/01/1990. " * 50
    text += "Another SSN is 987-65-4321 and DOB is Jan 15 1985. " * 50
    
    content = ExtractedContent(
        document_id="test-123",
        text=text,
        has_embedded_text=True,
        extraction_method="test",
        page_count=1
    )
    
    print(f"Text length: {len(text)} characters")
    print("Running detection...")
    
    start_time = time.time()
    entities = detector.detect(content, policy)
    end_time = time.time()
    
    duration_ms = (end_time - start_time) * 1000
    
    print(f"Found {len(entities)} entities in {duration_ms:.2f} ms")
    
    # We expect 50 SSNs + 50 SSNs = 100 SSNs
    # And 50 DOBs + 50 DOBs = 100 DOBs
    # Total = 200 entities highly structured.
    ssn_count = sum(1 for e in entities if e.entity_type.value == "SSN")
    dob_count = sum(1 for e in entities if e.entity_type.value == "DATE_OF_BIRTH")
    
    print(f"- SSNs found: {ssn_count} (Expected 100)")
    print(f"- DOBs found: {dob_count} (Expected 100)")
    
    if len(entities) >= 200 and duration_ms < 50:
        print("\n[PASS] Performance test passed. Regex engine is blazingly fast.")
    else:
        print("\n[FAIL] Performance test failed or was too slow.")

if __name__ == "__main__":
    run_performance_test()
