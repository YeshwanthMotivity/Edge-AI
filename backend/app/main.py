"""
SecureDocAI — FastAPI Application Entry Point
=================================================
Privacy-Preserving Document Processing System
Edge AI Security Gateway

An edge-native AI security gateway that detects, removes,
and cryptographically seals sensitive data in documents
before external processing.
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import structlog

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import get_settings
from app.db.database import init_db
from app.models.user import User  # Ensure User is registered for init_db
from app.api.routes import health, auth, documents, audit, policies, pre_check

from app.api.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.core.exceptions import SecureDocAIError
from app.core.rate_limiter import setup_rate_limiting
from app.services.detection.ner_detector import NerDetector

# ── Structured Logging ──
import logging
from logging.handlers import RotatingFileHandler

# Ensure log directory exists
log_dir = Path("storage/logs")
log_dir.mkdir(parents=True, exist_ok=True)

# Configure handlers
file_handler = RotatingFileHandler(
    log_dir / "app.log", maxBytes=10*1024*1024, backupCount=5
)
stream_handler = logging.StreamHandler(sys.stdout)

logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    handlers=[stream_handler, file_handler]
)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger(__name__)


# ── Application Lifespan ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    settings = get_settings()

    # Startup
    logger.info("app_starting", app_name=settings.app_name, env=settings.app_env)
    settings.ensure_directories()
    init_db()

    # ── Load NER Model (Phase 4) ──
    ner_detector = NerDetector(
        model_name=settings.ner_model_name,
        confidence_threshold=settings.ner_confidence_threshold,
        inference_timeout=settings.ner_inference_timeout_seconds,
    )
    ner_detector.load_model()
    app.state.ner_detector = ner_detector

    logger.info("app_started", message="SecureDocAI is ready", ner_loaded=ner_detector._is_loaded)

    yield

    # Shutdown
    logger.info("app_shutdown", message="SecureDocAI shutting down")


# ── Create FastAPI App ──

app = FastAPI(
    title="SecureDocAI",
    description=(
        "Privacy-Preserving Document Processing System — "
        "An edge-native AI security gateway that detects, removes, "
        "and cryptographically seals sensitive data in documents "
        "before external processing."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ── Middleware ──

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)


# ── Global Exception Handler ──

@app.exception_handler(SecureDocAIError)
async def secure_doc_exception_handler(request: Request, exc: SecureDocAIError):
    """Handle all SecureDocAI custom exceptions."""
    logger.error(
        "application_error",
        error_type=type(exc).__name__,
        message=exc.message,
        document_id=exc.document_id,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": type(exc).__name__,
            "message": exc.message,
            "document_id": exc.document_id,
        },
    )


# ── Register Routes ──

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(audit.router)
app.include_router(policies.router)
app.include_router(pre_check.router)



# ── Root Redirect ──

@app.get("/", include_in_schema=False)
async def root():
    """Redirect to API documentation."""
    return {
        "service": "SecureDocAI",
        "version": "1.0.0",
        "description": "Privacy-Preserving Document Processing System",
        "docs": "/docs",
        "health": "/health",
    }
