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
from app.api.routes import health, auth, documents
from app.api.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.core.exceptions import SecureDocAIError

# ── Structured Logging ──
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.PrintLoggerFactory(),
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
    logger.info("app_started", message="SecureDocAI is ready")

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
