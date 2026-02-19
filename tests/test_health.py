"""
SecureDocAI — Health Endpoint Tests
======================================
Verify the /health endpoint returns correct system status.
"""


def test_health_check(client):
    """Health endpoint should return 200 with system info."""
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "uptime_seconds" in data
    assert "environment" in data


def test_root_endpoint(client):
    """Root endpoint should return service info."""
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "SecureDocAI"
    assert data["docs"] == "/docs"


def test_auth_login(client):
    """Auth endpoint should return JWT token for valid credentials."""
    response = client.post(
        "/auth/token",
        json={"username": "admin", "password": "admin123"},
    )

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == "admin"
    assert data["role"] == "admin"


def test_auth_invalid_credentials(client):
    """Auth should return 401 for invalid credentials."""
    response = client.post(
        "/auth/token",
        json={"username": "admin", "password": "wrong_password"},
    )

    assert response.status_code == 401


def test_protected_endpoint_without_token(client):
    """Protected endpoints should return 403 without auth token."""
    response = client.post("/api/v1/analyze")
    assert response.status_code in (403, 422)  # 403 Forbidden or 422 if missing file


def test_security_headers(client):
    """Responses should include security headers."""
    response = client.get("/health")

    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time-Ms" in response.headers
