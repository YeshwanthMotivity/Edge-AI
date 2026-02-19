"""
SecureDocAI — Centralized Configuration
========================================
Pydantic Settings for type-safe configuration with .env file support.
"""

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field


# ── Project Root ──
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / .env file."""

    # --- Application ---
    app_name: str = Field(default="SecureDocAI", description="Application name")
    app_env: str = Field(default="development", description="Environment: development | staging | production")
    app_debug: bool = Field(default=True, description="Enable debug mode")
    app_host: str = Field(default="0.0.0.0", description="Server bind host")
    app_port: int = Field(default=8000, description="Server bind port")
    log_level: str = Field(default="INFO", description="Logging level")

    # --- Database ---
    database_url: str = Field(
        default=f"sqlite:///{BASE_DIR / 'storage' / 'secure_doc_ai.db'}",
        description="Database connection URL"
    )

    # --- Authentication ---
    jwt_secret_key: str = Field(default="CHANGE_ME_USE_SECURE_RANDOM_VALUE", description="JWT signing key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(default=60, description="Token expiry in minutes")

    # --- Digital Signature ---
    signing_cert_path: Path = Field(default=BASE_DIR / "storage" / "keys" / "certificate.pem")
    signing_key_path: Path = Field(default=BASE_DIR / "storage" / "keys" / "private_key.pem")
    signing_p12_path: Path = Field(default=BASE_DIR / "storage" / "keys" / "keystore.p12")
    signing_p12_passphrase: str = Field(default="CHANGE_ME", description="PKCS#12 passphrase")

    # --- Storage Paths ---
    upload_dir: Path = Field(default=BASE_DIR / "storage" / "uploads")
    processed_dir: Path = Field(default=BASE_DIR / "storage" / "processed")
    signed_dir: Path = Field(default=BASE_DIR / "storage" / "signed")
    keys_dir: Path = Field(default=BASE_DIR / "storage" / "keys")

    # --- Detection Thresholds ---
    default_confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    default_policy: str = Field(default="default_policy", description="Default policy name")

    # --- Edge ML ---
    onnx_model_path: Path = Field(default=BASE_DIR / "models" / "ner_model.onnx")
    use_gpu: bool = Field(default=False, description="Enable GPU/NPU acceleration")

    # --- Supported Formats ---
    supported_extensions: list[str] = Field(
        default=[".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"],
        description="Accepted file extensions"
    )
    max_file_size_mb: int = Field(default=50, description="Max upload size in MB")

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False

    def ensure_directories(self) -> None:
        """Create storage directories if they don't exist."""
        for dir_path in [self.upload_dir, self.processed_dir, self.signed_dir, self.keys_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Singleton settings instance (cached)."""
    settings = Settings()
    settings.ensure_directories()
    return settings
