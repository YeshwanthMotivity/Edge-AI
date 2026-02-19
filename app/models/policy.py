"""
SecureDocAI — Policy Models
==============================
Pydantic models for detection policies, entity rules, and masking configuration.
"""

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class VisualRedactionConfig(BaseModel):
    """Visual appearance of redaction boxes in the output PDF."""
    box_color: list[int] = Field(default=[0, 0, 0], description="RGB color for redaction box")
    box_opacity: float = Field(default=1.0, ge=0.0, le=1.0)
    font_size: int = Field(default=8, description="Font size for redaction labels")
    label_redactions: bool = Field(default=True, description="Show entity type label on redaction box")


class EntityRule(BaseModel):
    """Detection and masking rule for a single entity type."""
    enabled: bool = Field(default=True)
    detection_method: str = Field(..., description="Detection method: regex | regex_luhn | ner | layout")
    confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    masking_style: str = Field(default="full", description="Masking style: full | partial | tokenize")
    replacement: str = Field(default="[REDACTED]", description="Replacement text")
    partial_mask: Optional[str] = Field(default=None, description="Partial mask pattern, e.g. XXXX-{last4}")


class AllowlistConfig(BaseModel):
    """Values that should NOT be redacted even if detected."""
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    names: list[str] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list, description="Regex patterns to exclude")


class Policy(BaseModel):
    """Complete detection and masking policy."""
    policy_name: str = Field(..., description="Unique policy identifier")
    description: str = Field(default="", description="Human-readable description")
    version: str = Field(default="1.0.0")
    entities: dict[str, EntityRule] = Field(default_factory=dict)
    allowlist: AllowlistConfig = Field(default_factory=AllowlistConfig)
    signing_required: bool = Field(default=True)
    audit_required: bool = Field(default=True)
    visual_redaction: VisualRedactionConfig = Field(default_factory=VisualRedactionConfig)

    def get_enabled_entities(self) -> dict[str, EntityRule]:
        """Return only enabled entity rules."""
        return {k: v for k, v in self.entities.items() if v.enabled}

    def get_entity_rule(self, entity_type: str) -> Optional[EntityRule]:
        """Get rule for a specific entity type."""
        return self.entities.get(entity_type)


class PolicyLoader:
    """Load and cache detection policies from JSON files."""

    def __init__(self, policies_dir: Path):
        self.policies_dir = policies_dir
        self._cache: dict[str, Policy] = {}

    def load(self, policy_name: str) -> Policy:
        """Load a policy by name (cached)."""
        if policy_name in self._cache:
            return self._cache[policy_name]

        policy_path = self.policies_dir / f"{policy_name}.json"
        if not policy_path.exists():
            raise FileNotFoundError(f"Policy not found: {policy_path}")

        with open(policy_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        policy = Policy(**data)
        self._cache[policy_name] = policy
        return policy

    def list_policies(self) -> list[str]:
        """List all available policy names."""
        return [
            p.stem for p in self.policies_dir.glob("*.json")
            if p.is_file()
        ]

    def clear_cache(self) -> None:
        """Clear the policy cache (useful after updates)."""
        self._cache.clear()
