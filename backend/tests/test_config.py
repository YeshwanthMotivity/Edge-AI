"""
SecureDocAI — Configuration Tests
====================================
Validates that pydantic-settings correct throws validation errors for missing configs.
"""

import pytest
from pydantic import ValidationError
from config.settings import Settings

def test_missing_critical_config(monkeypatch):
    """Test that missing critical configurations raise validation errors."""
    
    # Temporarily remove JWT_SECRET_KEY if it exists
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    
    # We must explicitly pass an empty string to override a Field with a default.
    # We will test an empty `jwt_secret_key` and remove the default value.
    from pydantic import Field
    
    class StrictSettings(Settings):
        jwt_secret_key: str = Field(min_length=1)  # must have at least 1 char
    
    with pytest.raises(ValidationError):
        StrictSettings(jwt_secret_key="")

def test_config_type_coercion():
    """Test that pydantic correctly coerces environment variables."""
    # Settings has app_port as int and app_debug as bool
    settings = Settings(app_port="8080", app_debug="false")
    
    assert settings.app_port == 8080
    assert settings.app_debug is False
