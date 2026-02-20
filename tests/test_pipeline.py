import pytest
from pathlib import Path


def test_analyze_endpoint(client, auth_headers, sample_pdf):
    with open(sample_pdf, "rb") as f:
        files = {"file": ("test_document.pdf", f, "application/pdf")}
        data = {"policy": "default_policy"}
        response = client.post("/api/v1/analyze", headers=auth_headers, files=files, data=data)
        
    assert response.status_code == 200
    result = response.json()
    print("API RESPONSE:", result)
    assert result["entities_detected"] > 0
    assert "EMAIL" in result["entity_summary"]
    assert "PHONE" in result["entity_summary"]


def test_process_endpoint(client, auth_headers, sample_pdf):
    with open(sample_pdf, "rb") as f:
        files = {"file": ("test_document.pdf", f, "application/pdf")}
        data = {"policy": "default_policy"}
        response = client.post("/api/v1/process", headers=auth_headers, files=files, data=data)
        
    assert response.status_code == 200
    result = response.json()
    print("API RESPONSE:", result)
    assert result["status"] == "completed", f"Status was not completed: {result}"
    assert result.get("sanitized_path") is not None, f"sanitized_path missing: {result}"
    assert result.get("signed_path") is not None, f"signed_path missing or signature failed: {result}"
    assert result.get("signature_serial") is not None, f"signature_serial missing: {result}"
