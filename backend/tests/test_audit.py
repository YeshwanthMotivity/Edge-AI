import pytest

def test_audit_retrieval(client, auth_headers, sample_pdf):
    # First, run a document through the pipeline to generate an audit log
    with open(sample_pdf, "rb") as f:
        files = {"file": ("test_document.pdf", f, "application/pdf")}
        data = {"policy": "default_policy"}
        process_response = client.post("/api/v1/process", headers=auth_headers, files=files, data=data)
        
    assert process_response.status_code == 200
    document_id = process_response.json()["document_id"]
    
    # Now retrieve the audit log
    audit_response = client.get(f"/api/v1/audit/{document_id}", headers=auth_headers)
    assert audit_response.status_code == 200
    
    audit_data = audit_response.json()
    assert audit_data["document_id"] == document_id
    assert "processing" in audit_data
    assert "signature" in audit_data
    
    assert audit_data["processing"]["status"] == "completed"
    assert audit_data["signature"]["verification_status"] == "valid"

def test_audit_not_found(client, auth_headers):
    response = client.get("/api/v1/audit/invalid-doc-id-12345", headers=auth_headers)
    assert response.status_code == 404
