"""
SecureDocAI — Policy Management Routes
==========================================
API endpoints for listing and managing Data Loss Prevention (DLP) policies.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.api.dependencies import get_current_user
from app.models.policy import PolicyLoader

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/policies", tags=["Policy Management"])

# Setup Policy Loader
policies_dir = Path(__file__).resolve().parent.parent.parent.parent / "config" / "policies"
policy_loader = PolicyLoader(policies_dir)

@router.get(
    "",
    summary="List Available Policies",
    description="List all currently active DLP policies available for document processing.",
)
def list_policies(
    current_user: dict = Depends(get_current_user),
) -> List[str]:
    """Return a list of policy names."""
    try:
        return policy_loader.list_policies()
    except Exception as e:
        logger.error("policy_list_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list policies: {str(e)}"
        )

@router.get(
    "/{policy_name}",
    summary="Get Policy Details",
    description="Retrieve the exact configuration and entity rules for a specific policy.",
)
def get_policy(
    policy_name: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Return the JSON representation of a policy."""
    try:
        policy = policy_loader.load(policy_name)
        return policy.model_dump()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy '{policy_name}' not found."
        )
    except Exception as e:
        logger.error("policy_get_failed", error=str(e), policy=policy_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load policy: {str(e)}"
        )
