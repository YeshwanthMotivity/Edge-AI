# 🔐 SecureDocAI — Privacy-Preserving Document Processing System

> **An edge-native AI security gateway that detects, removes, and cryptographically seals sensitive data in documents before external processing.**

## Overview

SecureDocAI is a secure, edge-deployed document sanitization platform that automatically detects and removes sensitive information (PII/PCI/PHI) from documents before they are processed by AI systems or shared externally. All processing happens locally — **no data ever leaves the device unredacted**.

## Architecture

```
Upload → Auth → Extract → Detect → Redact → Generate PDF
         → Log Processing → Sign → Log Signature → Output
```

## Quick Start

### Local Development

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env       # Windows
# cp .env.example .env       # Linux/Mac

# 4. Generate signing keys (POC)
python scripts/generate_keys.py

# 5. Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
docker-compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health check |
| `POST` | `/auth/token` | Get JWT access token |
| `POST` | `/api/v1/analyze` | Detect entities (no masking) |
| `POST` | `/api/v1/mask` | Apply redaction to document |
| `POST` | `/api/v1/sign` | Digitally sign a document |
| `POST` | `/api/v1/process` | Full pipeline (analyze + mask + sign) |

## Security Principle

```
Original document  → ❌ NEVER exposed to external AI
Sanitized document → ✅ Safe for AI processing / sharing
```

## Tech Stack

- **API**: FastAPI + Uvicorn
- **PDF Processing**: PyMuPDF + pdfplumber
- **OCR**: Tesseract / PaddleOCR
- **AI Detection**: ONNX Runtime + DistilBERT NER
- **Digital Signature**: PyHanko + X.509
- **Database**: SQLite (POC) / PostgreSQL (Production)
- **Deployment**: Docker + Compose

## License

Proprietary — Internal Use Only
