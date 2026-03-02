import pytest
import os
from pathlib import Path

def test_download_and_verify(client, auth_headers, sample_pdf):
    # Process a document first to get a signed file
    with open(sample_pdf, "rb") as f:
        files = {"file": ("test_document.pdf", f, "application/pdf")}
        data = {"policy": "default_policy"}
        process_response = client.post("/api/v1/process", headers=auth_headers, files=files, data=data)
        
    assert process_response.status_code == 200
    document_id = process_response.json()["document_id"]
    
    # 1. Test Download Endpoint
    download_response = client.get(f"/api/v1/documents/{document_id}/download?type=signed", headers=auth_headers)
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/pdf"
    
    # Save downloaded file temporarily
    downloaded_file = f"temp_{document_id}_signed.pdf"
    with open(downloaded_file, "wb") as f:
        f.write(download_response.content)
        
    try:
        # 2. Test Verification Endpoint
        with open(downloaded_file, "rb") as f:
            files = {"file": (downloaded_file, f, "application/pdf")}
            verify_response = client.post("/api/v1/verify", headers=auth_headers, files=files)
            
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        
        assert verify_data["valid"] is True
        assert verify_data["intact"] is True
        assert "signer" in verify_data
    finally:
        # Cleanup
        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)
