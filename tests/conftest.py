"""
SecureDocAI — Test Configuration
===================================
Pytest fixtures for testing the document processing pipeline.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from app.db.database import Base, get_db
from app.models.user import User
from app.core.security import hash_password


# ── Test Database ──

TEST_DATABASE_URL = "sqlite:///./test_secure_doc_ai.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


def override_get_db():
    """Provide test database session."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Fixtures ──

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test database tables before tests and drop after."""
    Base.metadata.create_all(bind=test_engine)
    
    # Insert test admin user
    db = TestSessionLocal()
    try:
        if not db.query(User).filter_by(username="admin").first():
            user = User(
                username="admin",
                hashed_password=hash_password("admin123"),
                role="admin",
                is_active=True,
            )
            db.add(user)
            db.commit()
    finally:
        db.close()
        
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    
    # Clean up test DB file
    test_db_path = Path("./test_secure_doc_ai.db")
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture
def client():
    """FastAPI test client with overridden DB dependency."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Get auth headers by logging in as admin."""
    response = client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF with PII for testing."""
    try:
        import fitz

        pdf_path = tmp_path / "test_document.pdf"
        doc = fitz.open()
        page = doc.new_page()

        # Insert text with various PII types
        text = (
            "John Smith\n"
            "Email: john.smith@example.com\n"
            "Phone: +1-555-123-4567\n"
            "SSN: 123-45-6789\n"
            "Credit Card: 4532015112830366\n"
            "Address: 123 Main Street, Springfield, IL 62701\n"
        )
        page.insert_text((72, 72), text, fontsize=12)
        doc.save(str(pdf_path))
        doc.close()

        return pdf_path
    except ImportError:
        pytest.skip("PyMuPDF not installed")
