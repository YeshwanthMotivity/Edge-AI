"""
SecureDocAI — LLM Gateway Models
===================================
Models for interacting with the external LLM provider safely.
"""

from pydantic import BaseModel, Field

class SafeAnalysisRequest(BaseModel):
    """
    Request to safely analyze a document using an LLM.
    Requires a previously processed document_id or accepts text/file directly.
    """
    document_id: str = Field(
        ..., 
        description="The ID of a document that was just processed locally."
    )
    prompt: str = Field(
        default="Summarize this document securely.",
        description="The instruction to send the LLM (e.g., 'Extract key clauses')."
    )
    llm_provider: str = Field(
        default="mock",
        description="'mock' for internal testing or 'openai' for production API."
    )
    reidentify_response: bool = Field(
        default=True,
        description="Whether to swap the [REDACTED] tokens back to original values in the response."
    )

class SafeAnalysisResponse(BaseModel):
    """
    Response from the Safe LLM Integration endpoint.
    """
    document_id: str
    prompt_sent: str
    llm_provider_used: str
    raw_llm_response: str = Field(
        ...,
        description="The exact text returned by the LLM (contains [REDACTED] tags)."
    )
    reidentified_response: str = Field(
        ...,
        description="The text after the local proxy re-injected the original sensitive values."
    )
    entities_protected: int = Field(
        ...,
        description="How many PII entities were safely hidden from the LLM."
    )
